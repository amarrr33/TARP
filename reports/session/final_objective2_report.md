# VoxFlow Final Objective 2 Complete-Session Report

## Executive Summary
This report documents the final validation of the complete-session Objective 2 pipeline for VoxFlow on an end-to-end continuous recording.

## Session Metadata
- **Session ID:** `test-obj2-final-001`
- **Audio File:** `C:\Users\amare\Downloads\TARP\data\processed\final_obj2_test_session_42s.wav`
- **Audio Duration:** 42.00 seconds (Meets 30–60s standard requirement)
- **Model Version:** `voxflow-model-v1.0`
- **Sampling Rate:** 16,000 Hz Mono

## Processing & Window Statistics
- **Sliding Window Duration:** 3.0 seconds
- **Sliding Window Step Size:** 1.0 second
- **Total Windows Generated:** 40
- **Valid Speech Windows:** 40
- **Fluent Windows:** 3
- **Session Fluency Ratio:** 7.50% (`fluent_windows / valid_windows`)

## Detected Disfluent Events (Post Temporal Aggregation)
- **Total Aggregated Events:** 2
- **Repetition Events:** 2
- **Prolongation Events:** 0
- **Block Events:** 0

### Aggregated Event Timeline
| Event Type | Start Time | End Time | Confidence | Supporting Windows |
|:---|:---|:---|:---|:---|
| Repetition | 2.00s | 5.00s | 55.7% | 1 |
| Repetition | 20.00s | 26.00s | 50.9% | 2 |


## Verification of Quality Rules
1. **Overlap Prevention:** Contiguous overlapping windows predicting identical disfluencies were merged into distinct temporal regions (no double counting).
2. **Deterministic Processing:** Inference executed using frozen production model `voxflow-model-v1.0`.
3. **Database Integrity:** Session, windows, events, and summary successfully persisted in SQLite (`voxflow.db`).
4. **Clinical Disclaimer:** Session Fluency Ratio is an automated speech fluency monitoring index; it is not a clinical diagnostic score.
