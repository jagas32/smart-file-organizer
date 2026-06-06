---
name: summarizer
description: Generate smart summaries of individual files and whole folders, plus a human-readable report. Reads organized/ (or any target dir) and emits outputs/summaries/*.json and outputs/report.md. Use when the user asks to summarize files, describe folder contents, or produce a report.
---

# Summarizer

Produce per-file summaries, folder rollups, and a final Markdown report.

## Inputs
- Target directory (default `organized/`, fall back to `inputs/`).
- `outputs/classification.json` and `outputs/organize-log.json` if present — reuse their metadata/hashes instead of re-scanning.

## Workflow
1. **Plan**: List target files. Skip files whose hash already has a summary in `outputs/summaries/` (incremental).
2. **Per-file summaries** (token-efficient, by type):
   - Text/docs/code: read first ~100 lines + headings; 2–3 sentence summary, key entities, dates.
   - Spreadsheets/CSV: headers + row count + first 10 rows; describe columns and what the data represents.
   - PDFs: extract text (use pdf skill); summarize first pages + TOC.
   - Images/media: filename, dimensions/duration via metadata only — no content analysis unless asked.
   - Large files (>1 MB text): sample beginning/middle/end only.
3. **Folder rollups**: For each folder in target, aggregate: file count, size, date range, dominant topics, 1-paragraph description.
4. **Emit** JSON to `outputs/summaries/` and render `outputs/report.md`.

## Output Schemas
Per file — `outputs/summaries/files.json`:
```json
{"files": [{
  "path": "organized/documents/2024-03/invoices/a.pdf",
  "sha256": "abc123...",
  "summary": "2–3 sentence summary.",
  "keywords": ["invoice", "acme"],
  "entities": {"dates": [], "people": [], "orgs": []},
  "flags": ["possible-duplicate", "contains-pii"]
}]}
```
Per folder — `outputs/summaries/folders.json`:
```json
{"folders": [{
  "path": "organized/documents/2024-03/",
  "file_count": 12, "total_bytes": 102400,
  "date_range": ["2024-03-01", "2024-03-29"],
  "topics": ["invoices", "contracts"],
  "description": "One-paragraph rollup."
}]}
```

## Report (`outputs/report.md`)
Sections: **Overview** (totals, date range), **By Category** (table: category, count, size, top topics), **Highlights** (notable files, duplicates, PII flags, low-confidence items needing review), **Folder Summaries**.

## Rules
- Read-only: never modify target files.
- Flag, don't act: duplicates and PII are reported, not deleted/redacted.
- Incremental: unchanged hash → reuse existing summary.
