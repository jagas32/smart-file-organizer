---
name: pipeline-orchestrator
description: Coordinate the full Smart File Organizer workflow — classify → organize → summarize → report — with checkpoints, error handling, and a single manifest. Use when the user says "run the pipeline", "organize and summarize everything", or wants the end-to-end flow.
---

# Pipeline Orchestrator

Run the complete workflow over `inputs/`, delegating to the other skills in order.

## Stages
| # | Stage | Skill | Output |
|---|-------|-------|--------|
| 1 | Classify | `skills/file-classifier/` | `outputs/classification.json` |
| 2 | Organize | `skills/file-organizer/` | `outputs/organize-plan.json`, `outputs/organize-log.json` |
| 3 | Summarize | `skills/summarizer/` | `outputs/summaries/`, `outputs/report.md` |
| 4 | Finalize | (this skill) | `outputs/manifest.json` |

## Workflow
1. **Pre-flight**: Verify `inputs/` has files; ensure `outputs/` and `organized/` exist; load prior `outputs/manifest.json` if present to enable incremental runs.
2. **Run stages 1–3 in order.** Read each stage's SKILL.md and follow it. A stage's output JSON is the next stage's input — validate it exists and parses before proceeding.
3. **Checkpoint between stages**: Update `outputs/manifest.json` after each stage so an interrupted run resumes where it stopped.
4. **User confirmation gate**: Pause before stage 2 execution if the organize plan contains collisions or low-confidence classifications; show the summary table and ask.
5. **Finalize**: Write manifest, then present `outputs/report.md` to the user.

## Manifest Schema (`outputs/manifest.json`)
```json
{
  "run_id": "2026-06-06T12:00:00Z",
  "incremental": true,
  "stages": {
    "classify":  {"status": "completed|failed|skipped", "output": "outputs/classification.json", "errors": []},
    "organize":  {"status": "pending", "output": "outputs/organize-log.json", "errors": []},
    "summarize": {"status": "pending", "output": "outputs/report.md", "errors": []}
  },
  "totals": {"files_seen": 0, "files_organized": 0, "files_summarized": 0}
}
```

## Error Handling
- Stage fails → record error in manifest, stop pipeline, report clearly what succeeded and how to resume.
- Partial failures within a stage (some files error) → continue, collect errors, surface in final report.
- Never leave `organized/` half-verified: organize stage's own log is authoritative.

## Rules
- Inherit all safety rules from child skills (copy-only, no overwrites, read-only inputs).
- Incremental by default: skip files whose hash is unchanged since the last successful run.
- Keep token use low: pass data between stages via JSON files, not by re-reading file contents.
