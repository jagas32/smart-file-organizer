#!/usr/bin/env python3
"""Smart File Organizer pipeline runner.

Classify -> organize -> summarize a folder (or specific files), following the
skill contracts in skills/. Deterministic heuristics only — for content-aware
classification and prose summaries, run the pipeline through Claude with the
pipeline-orchestrator skill.

Usage:
  python3 scripts/run_pipeline.py                      # full pipeline on inputs/
  python3 scripts/run_pipeline.py path/to/file.pdf …   # specific files only
  python3 scripts/run_pipeline.py --source ~/Downloads # a different folder
  python3 scripts/run_pipeline.py --dry-run            # plan only, no copies
  python3 scripts/run_pipeline.py --stage classify     # single stage
  python3 scripts/run_pipeline.py --yes                # skip confirmation
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CATEGORIES = {
    ".pdf": "documents", ".txt": "documents", ".md": "documents", ".docx": "documents",
    ".csv": "spreadsheets", ".xlsx": "spreadsheets", ".tsv": "spreadsheets",
    ".png": "images", ".jpg": "images", ".jpeg": "images", ".heic": "images", ".svg": "images",
    ".pptx": "presentations", ".zip": "archives", ".tar": "archives", ".gz": "archives",
    ".py": "code", ".js": "code", ".sh": "code",
}

TOPIC_RULES = [
    ("invoices", ["invoice", "bill to", "total due"]),
    ("taxes", ["taxes", "w2", "w-2", "1099", "irs", "deduction"]),
    ("lease", ["lease agreement", "landlord", "tenant", "security deposit"]),
    ("work-meetings", ["attendees", "action:", "next sync", "meeting"]),
    ("recipes", ["serves ", "recipe", "bake ", "preheat", "ingredients"]),
    ("fitness", ["workout", "calories", "duration_min", "distance_mi"]),
    ("budget", ["budget", "groceries", "utilities"]),
    ("finance", ["account", "statement", "balance", "payroll"]),
]

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], 1)}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sample_text(path: Path, max_lines: int = 80) -> str:
    """Token-efficient content sample: PDFs via pypdf (first page), text head."""
    ext = path.suffix.lower()
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            return (PdfReader(path).pages[0].extract_text() or "").lower()
        except Exception:
            return ""
    if CATEGORIES.get(ext) in ("documents", "spreadsheets", "code"):
        try:
            with open(path, errors="ignore") as f:
                return "".join(f.readline() for _ in range(max_lines)).lower()
        except Exception:
            return ""
    return ""


def classify_topic(name: str, text: str) -> tuple[str, str]:
    blob = f"{name.lower()} {text}"
    for topic, kws in TOPIC_RULES:
        hits = sum(k in blob for k in kws)
        if hits:
            in_name = any(k in name.lower() for k in kws)
            return topic, "high" if (in_name or hits >= 2) else "medium"
    return "unknown", "low"


def classify_date(name: str, text: str, mtime: float) -> tuple[str, str]:
    m = re.search(r"(20\d{2})[-_ .](\d{2})", name)
    if m and 1 <= int(m.group(2)) <= 12:
        return f"{m.group(1)}-{m.group(2)}", "filename"
    m = re.search(r"(20\d{2})", name)
    if m:
        return m.group(1), "filename-year"
    m = re.search(r"(" + "|".join(MONTHS) + r")\s+\d{1,2},?\s+(20\d{2})", text)
    if m:
        return f"{m.group(2)}-{MONTHS[m.group(1)]:02d}", "content"
    m = re.search(r"(20\d{2})-(0[1-9]|1[0-2])-\d{2}", text)
    if m:
        return f"{m.group(1)}-{m.group(2)}", "content"
    return datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m"), "mtime"


# ---------------------------------------------------------------- stages

def stage_classify(paths: list[Path], outputs: Path) -> dict:
    # When duplicates exist, treat the cleaner-named file as canonical:
    # names containing "copy", "(1)", etc. sort after clean names.
    def messiness(p: Path):
        return (bool(re.search(r"\bcopy\b|\(\d+\)|final", p.stem.lower())), str(p))

    files, seen = [], {}
    for p in sorted(paths, key=messiness):
        text = sample_text(p)
        topic, conf = classify_topic(p.name, text)
        date, dsrc = classify_date(p.name, text, p.stat().st_mtime)
        digest = sha256(p)
        entry = {
            "path": str(p), "size_bytes": p.stat().st_size, "sha256": digest,
            "category": CATEGORIES.get(p.suffix.lower(), "other"),
            "extension": p.suffix.lstrip("."), "date": date, "date_source": dsrc,
            "topic": topic, "confidence": conf,
        }
        if digest in seen:
            entry["duplicate_of"] = seen[digest]
        seen.setdefault(digest, str(p))
        files.append(entry)

    stats = {
        "total": len(files),
        "by_category": {},
        "low_confidence": [f["path"] for f in files if f["confidence"] == "low"],
        "duplicates": [f["path"] for f in files if "duplicate_of" in f],
    }
    for f in files:
        stats["by_category"][f["category"]] = stats["by_category"].get(f["category"], 0) + 1

    result = {"generated_at": now(), "files": files, "stats": stats}
    write_json(outputs / "classification.json", result)
    return result


def stage_organize(classification: dict, dest_root: Path, outputs: Path,
                   dry_run: bool, assume_yes: bool, skip_duplicates: bool) -> dict:
    plan = []
    for f in classification["files"]:
        src = Path(f["path"])
        if skip_duplicates and "duplicate_of" in f:
            plan.append({"src": str(src), "dest": None, "action": "skip",
                         "reason": f"duplicate of {f['duplicate_of']}"})
            continue
        parts = [f["category"], f["date"]] + ([f["topic"]] if f["topic"] != "unknown" else [])
        plan.append({"src": str(src), "dest": str(dest_root.joinpath(*parts, src.name)),
                     "action": "copy"})
    write_json(outputs / "organize-plan.json", {"planned_at": now(), "operations": plan})

    print("\nPlan:")
    for op in plan:
        arrow = f"-> {op['dest']}" if op["dest"] else f"SKIP ({op['reason']})"
        print(f"  {op['src']}  {arrow}")
    if dry_run:
        print("\n--dry-run: no files copied.")
        return {"stats": {"copied": 0, "skipped": 0, "renamed": 0, "errors": 0}, "dry_run": True}

    warnings = classification["stats"]["low_confidence"] or classification["stats"]["duplicates"]
    if warnings and not assume_yes:
        reply = input("\nLow-confidence/duplicate items present. Proceed with copy? [y/N] ")
        if reply.strip().lower() not in ("y", "yes"):
            print("Aborted by user. Plan saved to outputs/organize-plan.json.")
            sys.exit(1)

    ops, stats = [], {"copied": 0, "skipped": 0, "renamed": 0, "errors": 0}
    for op in plan:
        if op["action"] == "skip":
            ops.append({**op, "action": "skipped", "verified": True})
            stats["skipped"] += 1
            continue
        src, dest = Path(op["src"]), Path(op["dest"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        action = "copied"
        if dest.exists():                      # never overwrite: suffix rename
            i = 1
            while dest.with_name(f"{dest.stem}__{i}{dest.suffix}").exists():
                i += 1
            dest = dest.with_name(f"{dest.stem}__{i}{dest.suffix}")
            action = "renamed"
        shutil.copy2(src, dest)
        verified = sha256(src) == sha256(dest)
        if not verified:
            stats["errors"] += 1
        ops.append({"src": str(src), "dest": str(dest), "action": action, "verified": verified})
        stats[action] += 1

    log = {"executed_at": now(), "operations": ops, "stats": stats}
    write_json(outputs / "organize-log.json", log)
    return log


def stage_summarize(classification: dict, log: dict, outputs: Path) -> Path:
    """Metadata-level summaries + report. Prose summaries need the Claude skill."""
    (outputs / "summaries").mkdir(parents=True, exist_ok=True)
    dest_of = {o["src"]: o.get("dest") for o in log.get("operations", [])}
    files = []
    for f in classification["files"]:
        flags = []
        if "duplicate_of" in f:
            flags.append("exact-duplicate")
        if f["confidence"] == "low":
            flags.append("needs-review")
        if re.search(r"(final|copy|untitled|^notes\.|^img_|\(\d\))", Path(f["path"]).name.lower()):
            flags.append("poorly-named")
        files.append({
            "path": dest_of.get(f["path"]) or f["path"], "sha256": f["sha256"],
            "summary": f"{f['category']}/{f['topic']} file, dated {f['date']} "
                       f"({f['date_source']}), {f['size_bytes']:,} bytes.",
            "keywords": [f["topic"], f["category"]], "flags": flags,
        })
    write_json(outputs / "summaries" / "files.json", {"generated_at": now(), "files": files})

    s, stats = classification["stats"], log.get("stats", {})
    flag_lines = [f"- `{Path(f['path']).name}` — {', '.join(f['flags'])}"
                  for f in files if f["flags"]] or ["- none"]
    lines = [
        "# File Organization Report", "",
        f"**Run:** {now()} · **Files:** {s['total']} · "
        f"**Copied:** {stats.get('copied', 0)} · **Skipped:** {stats.get('skipped', 0)} · "
        f"**Errors:** {stats.get('errors', 0)}", "",
        "## By Category", "",
        "| Category | Count |", "|---|---|",
        *[f"| {k} | {v} |" for k, v in sorted(s["by_category"].items())], "",
        "## Flags", "",
        *flag_lines, "",
        "*Generated by scripts/run_pipeline.py (heuristic mode). "
        "For content-aware prose summaries, run the summarizer skill via Claude.*",
    ]
    report = outputs / "report.md"
    report.write_text("\n".join(lines))
    return report


# ---------------------------------------------------------------- helpers

def now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def collect(source: Path, named: list[str]) -> list[Path]:
    if named:
        paths = [Path(p) for p in named]
        missing = [p for p in paths if not p.is_file()]
        if missing:
            sys.exit(f"error: not found: {', '.join(map(str, missing))}")
        return paths
    if not source.is_dir():
        sys.exit(f"error: source folder not found: {source}")
    return [p for p in source.iterdir() if p.is_file() and not p.name.startswith(".")]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", help="specific files (default: all of --source)")
    ap.add_argument("--source", type=Path, default=ROOT / "inputs", help="folder to organize")
    ap.add_argument("--dest", type=Path, default=ROOT / "organized", help="destination root")
    ap.add_argument("--outputs", type=Path, default=ROOT / "outputs", help="manifests/report dir")
    ap.add_argument("--stage", choices=["classify", "organize", "summarize", "all"], default="all")
    ap.add_argument("--dry-run", action="store_true", help="plan only, copy nothing")
    ap.add_argument("--yes", "-y", action="store_true", help="skip confirmation prompt")
    ap.add_argument("--keep-duplicates", action="store_true",
                    help="copy exact duplicates too (default: skip)")
    args = ap.parse_args()

    paths = collect(args.source, args.files)
    print(f"Pipeline: {len(paths)} file(s) | dest={args.dest} | stage={args.stage}"
          + (" | DRY RUN" if args.dry_run else ""))

    manifest = {"run_id": now(), "stages": {}, "totals": {"files_seen": len(paths)}}

    classification = stage_classify(paths, args.outputs)
    manifest["stages"]["classify"] = {"status": "completed", "output": "classification.json"}
    print(f"\nClassified {classification['stats']['total']} "
          f"({len(classification['stats']['duplicates'])} duplicate, "
          f"{len(classification['stats']['low_confidence'])} low-confidence)")
    if args.stage == "classify":
        write_json(args.outputs / "manifest.json", manifest)
        return

    log = stage_organize(classification, args.dest, args.outputs,
                         args.dry_run, args.yes, not args.keep_duplicates)
    manifest["stages"]["organize"] = {"status": "completed", "output": "organize-log.json"}
    manifest["totals"]["files_organized"] = log["stats"]["copied"] + log["stats"]["renamed"]
    if args.stage == "organize" or args.dry_run:
        write_json(args.outputs / "manifest.json", manifest)
        return

    report = stage_summarize(classification, log, args.outputs)
    manifest["stages"]["summarize"] = {"status": "completed", "output": "report.md"}
    manifest["totals"]["files_summarized"] = classification["stats"]["total"]
    write_json(args.outputs / "manifest.json", manifest)

    st = log["stats"]
    print(f"\nDone: {st['copied']} copied, {st['skipped']} skipped, "
          f"{st['renamed']} renamed, {st['errors']} errors")
    print(f"Report: {report}")


if __name__ == "__main__":
    main()
