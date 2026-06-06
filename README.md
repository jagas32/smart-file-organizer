# 📂 Smart File Organizer + Summarizer

An AI-driven pipeline that turns a messy folder of files into a clean, dated, topic-sorted hierarchy — with per-file summaries and a human-readable report. Built as a skill-based agent workflow: each pipeline stage is a self-contained skill that reads and writes structured JSON, coordinated by an orchestrator.

## Overview

Drop files into `inputs/` and run the pipeline. The system classifies each file by **type, date, and topic** (reading content, not just filenames), copies them into an `organized/` hierarchy, and generates summaries plus a final Markdown report. Originals are never touched.

```
inputs/ (messy)          organized/ (clean)                    outputs/
├── document_final.pdf   ├── documents/2025-09/lease/          ├── report.md
├── notes.txt        →   ├── documents/2026-06/taxes/      +   ├── manifest.json
├── IMG_4821.png         ├── images/2026-06/                   └── summaries/*.json
└── ...                  └── ...
```

## Key Features

- **Content-aware classification** — identifies a lease agreement hiding in `document_final.pdf` and tax notes in `notes.txt` by sampling file contents, not just extensions and names
- **Safe by design** — copy-only (originals immutable), no overwrites (collision suffixing), dry-run plan + user confirmation before any file operation, hash-verified copies
- **Duplicate detection** — SHA-256 hashing catches byte-identical files regardless of name
- **Smart summaries** — 2–3 sentence per-file summaries with extracted entities (dates, people, orgs) and flags (PII, poor names, duplicates, items needing review)
- **Resumable & incremental** — every stage checkpoints to `outputs/manifest.json`; unchanged files (by hash) are skipped on re-runs
- **Token-efficient** — samples first ~50–100 lines instead of full contents; passes data between stages as JSON, never re-reads files

## How to Run

1. Drop files into `inputs/`
2. Ask Claude to **"run the pipeline"** — the `pipeline-orchestrator` skill executes:
   `classify → organize (with confirmation) → summarize → report`
3. Review `outputs/report.md`

Stages can also run individually via their skills:

| Skill | Does | Emits |
|---|---|---|
| `skills/file-classifier/` | Scan + classify by type/date/topic | `outputs/classification.json` |
| `skills/file-organizer/` | Plan, confirm, copy into `organized/` | `outputs/organize-plan.json`, `organize-log.json` |
| `skills/summarizer/` | Per-file + folder summaries, report | `outputs/summaries/`, `outputs/report.md` |
| `skills/pipeline-orchestrator/` | Coordinates all stages, checkpoints | `outputs/manifest.json` |

## Example

A test run on 10 deliberately messy files (vague names, duplicates, mixed topics) produced:

- `document_final.pdf` → correctly identified as a **lease** → `organized/documents/2025-09/lease/`
- `notes.txt` → identified as **tax prep notes** → `organized/documents/2026-06/taxes/`
- `invoice_acme_2024-03 copy.pdf` → caught as an **exact duplicate** (hash match) and skipped after user confirmation
- `export-data-FINAL-final (1).csv` → recognized as a **workout log**, renaming suggested
- Final report flagged 3 poorly named files, 3 files containing PII, and 2 images needing manual review

Result: 9/10 files organized, 0 errors, all copies hash-verified, originals intact.

## Tech Stack

- **Claude (Cowork mode)** — agent reasoning, classification, summarization
- **Agent Skills pattern** — `SKILL.md` per stage with schemas, workflows, and safety rules
- **Python 3** — hashing, file ops, JSON manifests (`pypdf`, `Pillow`, `fpdf2` for test fixtures)
- **Structured JSON contracts** — each stage's output is the next stage's validated input

## Portfolio Value

This project demonstrates **agentic workflow design**: decomposing a fuzzy task ("clean up my files") into discrete, contracted stages with a coordinating orchestrator. The patterns shown — JSON manifests as inter-stage contracts, dry-run-then-confirm for destructive-adjacent operations, hash-based idempotency, checkpointed resumability, and token-budget-conscious file sampling — transfer directly to production agent systems: ETL pipelines, document processing, content moderation queues, and any workflow where an LLM coordinates file or data operations safely.

---

*Project structure, conventions, and pipeline status: see [CLAUDE.md](CLAUDE.md)*
