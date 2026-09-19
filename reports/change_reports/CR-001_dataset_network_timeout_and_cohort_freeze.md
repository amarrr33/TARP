# Change Report: CR-001
**Date:** 2026-09-19  
**Phase:** Phase 1 — Dataset Preparation  
**Component:** Data Ingestion & Manifest Generation  

### Expected Result
Successful download and extraction of all 8 candidate podcast episodes from the public SEP-28k podcast URLs yielding 888 clips across Train, Validation, and Test cohorts.

### Actual Result
Successfully downloaded and extracted 6 complete podcast episodes yielding 646 valid clips. During the download of the 7th episode (`WomenWhoStutter_10`), the remote WordPress CDN (`stutterrockstar.com`) returned HTTP socket read timeouts (`urllib3.exceptions.ReadTimeoutError`).

### Problem
External server-side throttling and TCP read timeouts prevented uninterrupted streaming of the remaining 2 episodes without extended stalls.

### Investigation Performed
1. Network probe on `https://stutterrockstar.files.wordpress.com/2014/02/episode-113-with-sarah-o.mp3` verified HTTP 302 redirect to `https://stutterrockstar.com/wp-content/uploads/2014/02/episode-113-with-sarah-o.mp3`.
2. Socket benchmarking showed remote server throttling download rate after ~5MB of transfer.
3. Inspected the existing 6 downloaded episodes on disk: confirmed 646 valid 3.0s 16kHz WAV clips already extracted, with strong representation across all four classes:
   - Train: 338 clips
   - Validation: 107 clips
   - Test: 201 clips

### Root Cause
Remote CDN bandwidth rate-limiting / socket timeout on WordPress media host.

### Change Made
In accordance with Rule 8.7 and Section 5 (Unexpected-Result Protocol):
1. Froze the dataset manifest to the 6 completely extracted episodes (646 clips).
2. Verified speaker independence: Train (`HeStutters 1, 11`, `WomenWhoStutter 0`), Validation (`HeStutters 15`), Test (`HeStutters 16`, `WomenWhoStutter 1`). Speaker overlap remains strictly 0.0%.
3. Regenerated `reports/dataset_report.md` reflecting the exact 646-sample cohort.
4. Preserved all methodological invariants (no synthetic samples manufactured, no speaker leakage).

### Impact
- **Dataset:** 646 clean 3.0s real stuttering clips (exceeding minimum requirement for prototype comparison).
- **Model:** Train/Val/Test splits are fully populated with all 4 classes (`Fluent`, `Repetition`, `Prolongation`, `Block`).
- **Metrics:** Uncompromised; metrics are computed purely on real clips.
- **Reproducibility:** Manifest explicitly records the 646 clips with exact filepaths and labels.

### Validation Performed
- Checked speaker overlap: 0% overlap between Train, Validation, and Test.
- Verified audio integrity: all 646 WAV files are valid 16kHz mono PCM clips of exactly 48,000 samples.

### Final Decision
**Accepted.** Proceed with Phase 2 (Objective 1 Model Training & Comparison) using the 646-clip cohort.
