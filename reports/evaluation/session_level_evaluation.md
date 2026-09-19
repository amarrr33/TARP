# VoxFlow Phase 7: Session-Level System Evaluation

## Objective 2 vs Objective 1 Distinction
Window-level ML metrics (Objective 1) evaluate 3-second isolated clips. Session-level metrics (Objective 2) evaluate the end-to-end continuous 30–60s monitoring system, including audio validation, overlapping window probabilities, temporal event aggregation, and aggregate fluency ratio.

## Measured Session-Level Evaluation Results

- **Evaluated Session Duration:** 45.0 seconds
- **Total 3.0s Windows Processed (1.0s Step):** 43
- **Fluent Windows Identified:** 8
- **Calculated Session Fluency Ratio:** 18.60%
- **Aggregated Detected Events:** 8
- **Ground Truth Target Disfluencies:** 13
- **Temporally Matched Detections:** 8
- **Extra Detections / False Positives:** 0

### Aggregated Event Timeline

| Detected Type | Start Time (s) | End Time (s) | Confidence | Supporting Windows |
|:---|:---|:---|:---|:---|
| Repetition | 0.00 | 3.00 | 63.3% | 1 |
| Repetition | 6.00 | 15.00 | 58.1% | 5 |
| Block | 15.00 | 18.00 | 60.2% | 1 |
| Prolongation | 18.00 | 21.00 | 70.0% | 1 |
| Repetition | 21.00 | 24.00 | 60.4% | 1 |
| Prolongation | 24.00 | 30.00 | 65.8% | 2 |
| Repetition | 35.00 | 39.00 | 57.6% | 2 |
| Prolongation | 39.00 | 45.00 | 61.5% | 3 |

### Limitations and Boundary Analysis
- Stuttering events occurring near 3.0s window edges can trigger support in adjacent overlapping windows, which the temporal aggregator coalesces into a continuous region.
- The fluency ratio represents an automated monitoring heuristic (`fluent_windows / valid_windows`) and must not be interpreted as a clinical stuttering severity index (e.g. SSI-4).
