# Smart File Organizer + Summarizer

## Overview & Goal
Organize messy files by type, date, and topic, and generate concise summaries/reports of files and folders. Input files go in `inputs/`, get classified and moved into `organized/`, with summaries and reports written to `outputs/`.

## Folder Structure
```
inputs/      # Drop messy files here (read-only source; never modified in place)
outputs/     # Generated summaries, reports, manifests (JSON + Markdown)
organized/   # Files sorted into type/date/topic hierarchy
skills/      # Pipeline skills (one folder per skill, each with SKILL.md)
examples/    # Sample inputs and expected outputs for testing
scripts/     # Helper scripts (classification, moving, reporting)
docs/        # Project documentation
```

## Key Conventions
- **Structured JSON**: Every pipeline stage emits/consumes JSON manifests (see skills for schemas). Single source of truth: `outputs/manifest.json`.
- **Safe operations**: Copy, never move/delete originals in `inputs/`. No overwrites — collision-suffix duplicates (`name__1.ext`). Dry-run first; write a plan before executing.
- **Token efficiency**: Read file metadata and samples (first ~50 lines / headers) before full contents. Batch shell operations. Summarize incrementally; don't re-read unchanged files (track via content hash in manifest).

## Current Status (2026-06-06)
- ✅ All 4 skills implemented: file-classifier, file-organizer, summarizer, pipeline-orchestrator
- ✅ 10 sample test files in `inputs/` (PDFs, txt, CSVs, PNGs; includes 1 exact duplicate + 3 poorly named files)
- ✅ Full pipeline run completed: 10 classified, 9 organized (duplicate skipped per user), 0 errors, all copies hash-verified
- ✅ Outputs current: `manifest.json`, `classification.json`, `organize-plan.json`, `organize-log.json`, `summaries/`, `report.md`
- 📄 README.md added (portfolio-style)
- Next ideas: OCR for image classification, auto-rename suggestions as a skill, incremental re-run test with new files

## How to Run the Pipeline
1. Place files in `inputs/`.
2. Invoke the **pipeline-orchestrator** skill (`skills/pipeline-orchestrator/SKILL.md`) — it runs: classify → organize → summarize → report.
3. Or run stages individually:
   - `skills/file-classifier/` — scan inputs, emit `outputs/classification.json`
   - `skills/file-organizer/` — plan + execute moves into `organized/`, emit `outputs/organize-log.json`
   - `skills/summarizer/` — summarize files/folders, emit `outputs/summaries/` + `outputs/report.md`
4. Review `outputs/report.md` for results.
