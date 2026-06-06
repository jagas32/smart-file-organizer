---
name: file-classifier
description: Scan files in inputs/ and classify each by type, date, and topic. Emits structured JSON (outputs/classification.json) consumed by file-organizer. Use when the user asks to classify, scan, analyze, or inventory files.
---

# File Classifier

Classify every file in `inputs/` by **type**, **date**, and **topic**, producing a single JSON manifest.

## Workflow
1. **Inventory**: `find inputs/ -type f` — collect path, size, extension, mtime. Skip hidden/system files (`.DS_Store`, `Thumbs.db`).
2. **Type**: Map extension → category: `documents` (pdf, docx, txt, md), `spreadsheets` (xlsx, csv), `presentations` (pptx), `images` (png, jpg, svg, heic), `audio`, `video`, `code` (py, js, sh...), `archives` (zip, tar), `other`. Verify ambiguous files with `file` command.
3. **Date**: Prefer date embedded in filename (e.g. `2024-03-15_report.pdf`), else file mtime. Record as `YYYY-MM`.
4. **Topic** (token-efficient): For text-based files, read only the first ~50 lines or filename keywords; assign a 1–3 word topic (e.g. `finance`, `recipes`, `tax-2024`). Use `unknown` when unclear — never guess wildly.
5. **Emit** `outputs/classification.json`.

## Output Schema
```json
{
  "generated_at": "ISO-8601",
  "source_dir": "inputs/",
  "files": [
    {
      "path": "inputs/scan_001.pdf",
      "size_bytes": 24576,
      "sha256": "abc123...",
      "category": "documents",
      "extension": "pdf",
      "date": "2024-03",
      "topic": "invoices",
      "confidence": "high|medium|low"
    }
  ],
  "stats": {"total": 0, "by_category": {}, "low_confidence": []}
}
```

## Rules
- Read-only stage: never modify or move files.
- Flag `low` confidence items in `stats.low_confidence` for user review.
- Hash files so downstream stages can skip unchanged ones.
