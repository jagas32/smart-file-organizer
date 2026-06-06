# File Organization Report

**Run:** 2026-06-06 · **Source:** `inputs/` (10 files, ~37 KB) · **Status:** ✅ completed, 0 errors

## Overview

10 files scanned and classified; 9 copied into `organized/` (1 exact duplicate skipped per user decision). All copies hash-verified. Originals in `inputs/` untouched. Content spans March 2024 – June 2026 across 6 topics: invoices, lease, taxes, work meetings, recipes, budget, and fitness.

## By Category

| Category | Files | Size | Topics |
|---|---|---|---|
| documents | 6 | ~5.6 KB | invoices, lease, work-meetings, taxes, recipes |
| spreadsheets | 2 | ~1 KB | budget, fitness |
| images | 2 | ~30 KB | unreviewed screenshots |

## Highlights & Items Needing Attention

- **Exact duplicate:** `invoice_acme_2024-03 copy.pdf` is byte-identical (SHA-256 match) to `invoice_acme_2024-03.pdf`. It was **not** copied to `organized/` and can be safely deleted from `inputs/` manually.
- **Poorly named files** (renaming suggested):
  - `document_final.pdf` → it's a lease; suggest `lease_birchwood_2025.pdf`
  - `notes.txt` → it's a tax checklist; suggest `tax-prep-2025.txt`
  - `export-data-FINAL-final (1).csv` → workout log; suggest `workout-log-2025-11.csv`
- **Possible PII:** the lease (address), tax notes, and budget contain personal/financial details — flagged, not modified.
- **2 unreviewed images:** `IMG_4821.png` and the Nov 2025 screenshot were filed by date only (no OCR performed). `IMG_4821.png` has no date/topic signals at all — worth a manual look.

## File Summaries

**organized/documents/2024-03/invoices/**
- `invoice_acme_2024-03.pdf` — Invoice #INV-2024-0312 from Acme Web Services, $474.00 for hosting, domains, and SSL. Due April 11, 2024 (Net 30).

**organized/documents/2025-09/lease/**
- `document_final.pdf` — 12-month lease, 482 Birchwood Lane Apt 2B, Columbus OH. $1,650/mo, Sept 2025–Aug 2026, one cat allowed ($200 fee).

**organized/documents/2026-01/work-meetings/**
- `meeting notes jan.txt` — Jan 14, 2026 team sync: redesign kickoff moved to Jan 26, analytics migration blocked on API keys, billing hotfix Friday. Action: Jason sends vendor shortlist by EOW.

**organized/documents/2026-06/taxes/**
- `notes.txt` — 2025 tax prep checklist: awaiting 1099-INT, $390 charity receipts, IRA top-up of $2,000 before April 15, home-office question for accountant.

**organized/documents/2026-06/recipes/**
- `grandmas_lasagna.txt` — Family lasagna recipe (serves 8), beef + sausage sauce, nutmeg secret, 375°F for 50 min, rest 15 min.

**organized/spreadsheets/2025/budget/**
- `budget_2025.csv` — 12-month household budget: fixed rent/car/savings, variable groceries ($420–610), utilities, and dining.

**organized/spreadsheets/2025-11/fitness/**
- `export-data-FINAL-final (1).csv` — 8 workouts, Nov 3–19, 2025: runs to 6 mi, lifting, biking, yoga, with duration/distance/calories.

**organized/images/2025-11/**
- `Screenshot 2025-11-02 at 3.45.12 PM.png` — 900×560 window capture, dated from filename; content unreviewed.

**organized/images/2026-06/**
- `IMG_4821.png` — 900×560 capture, camera-roll name, no signals; needs manual review.

**Skipped (still in inputs/ only)**
- `invoice_acme_2024-03 copy.pdf` — exact duplicate, not organized.

## Pipeline Artifacts

`outputs/classification.json` · `outputs/organize-plan.json` · `outputs/organize-log.json` · `outputs/summaries/files.json` · `outputs/summaries/folders.json` · `outputs/manifest.json`
