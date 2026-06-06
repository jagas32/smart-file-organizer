---
name: file-organizer
description: Plan and execute safe file organization — copy files from inputs/ into organized/<category>/<YYYY-MM>/<topic>/ based on outputs/classification.json. Use when the user asks to organize, sort, tidy, or restructure files.
---

# File Organizer

Move classified files into a clean `organized/` hierarchy. Requires `outputs/classification.json` (run file-classifier first if missing).

## Target Layout
```
organized/<category>/<YYYY-MM>/<topic>/<filename>
e.g. organized/documents/2024-03/invoices/scan_001.pdf
```
Omit `<topic>` level when topic is `unknown`.

## Workflow
1. **Load** `outputs/classification.json`; abort with a clear message if missing or stale (input hashes changed).
2. **Plan (dry-run)**: Compute source → destination for every file. Write plan to `outputs/organize-plan.json` and show the user a summary table (counts per destination, any collisions or low-confidence items).
3. **Confirm**: Ask the user before executing if there are collisions or low-confidence classifications.
4. **Execute**: Copy (`cp -n`) — never move or delete originals. On name collision, suffix `__1`, `__2`, etc. Verify each copy by size/hash.
5. **Log** results to `outputs/organize-log.json`.

## Log Schema
```json
{
  "executed_at": "ISO-8601",
  "operations": [
    {"src": "inputs/a.pdf", "dest": "organized/documents/2024-03/invoices/a.pdf",
     "action": "copied|skipped|renamed", "verified": true}
  ],
  "stats": {"copied": 0, "skipped": 0, "renamed": 0, "errors": 0}
}
```

## Safety Rules
- Originals in `inputs/` are immutable — copy only.
- Never overwrite: collision → suffix rename.
- Idempotent: re-running skips files already verified in the log.
- Any error: log it, continue with remaining files, report at end.
