# VoxFlow Model Error Analysis (Objective 1)

## 1. Overview
This report provides an in-depth error analysis of the winning model (`voxflow-model-v1.0`, SVM with MFCC acoustic summary statistics) evaluated on the completely held-out, unseen-speaker test cohort (201 test clips from `SEP-28k`).

## 2. Test Set Evaluation Summary
- **Test Samples:** 201 clips (16 kHz mono, 3.0s duration)
- **Overall Accuracy:** 33.83%
- **Macro F1:** 29.52%
- **Weighted F1:** 30.56%
- **Random Guessing Baseline (4 balanced classes):** 25.00%

### Test Confusion Matrix
```text
True \\ Predicted    Fluent    Repetition    Prolongation    Block    Total True
--------------------------------------------------------------------------------
Fluent                13          32              5            2          52
Repetition             9          39             12            1          61
Prolongation           3          27             12            1          43
Block                  9          25              7            4          45
--------------------------------------------------------------------------------
Total Predicted       34         123             36            8         201
```

## 3. Class-Specific Performance Breakdown

| Class | Support (N) | Precision | Recall | F1-Score | Primary Misclassification Mode |
|:---|:---:|:---:|:---:|:---:|:---|
| **Fluent** | 52 | 0.3824 | 0.2500 | 0.3023 | 61.5% misclassified as Repetition (32/52) |
| **Repetition** | 61 | 0.3171 | **0.6393** | **0.4239** | Highest recall; model biased toward Repetition |
| **Prolongation** | 43 | 0.3333 | 0.2791 | 0.3038 | 62.8% misclassified as Repetition (27/43) |
| **Block** | 45 | **0.5000** | 0.0889 | 0.1509 | Severely under-predicted (only 8 predicted total) |

## 4. Root Cause Analysis

### 4.1 Severe Under-Recall of Silent Blocks (Recall: 8.89%)
- **Symptom:** Blocks had the lowest recall (8.89%) and F1 (15.09%), with only 4 correctly identified out of 45 true instances.
- **Acoustic Cause:** Blocks in speech stuttering are characterized by tense silent pauses, glottal stops, and lack of voicing. In static MFCC feature extraction (mean, standard deviation, deltas across 3 seconds), silent periods average out or resemble quiet fluent speech pauses.
- **Consequence:** True blocks were predominantly misclassified as Repetition (25/45) or Fluent (9/45).

### 4.2 Repetition Bias & Over-Prediction (123 / 201 Predictions)
- **Symptom:** 61.2% of all predictions were assigned to "Repetition", driving up Repetition recall to 63.93% but lowering precision to 31.71%.
- **Acoustic Cause:** Rhythmic acoustic energy fluctuations, ambient background variations, and natural syllable pacing in conversational podcasts exhibit high variance in delta-MFCCs, which the linear/RBF kernel easily conflates with syllable repetitions.

### 4.3 Prolongation Confusion (F1: 30.38%)
- **Symptom:** Prolongations were frequently confused with repetitions (27/43).
- **Acoustic Cause:** A sustained vowel or fricative sound creates high spectral stability, but when occurring alongside normal co-articulation within a 3.0s window, the overall summary statistics lose temporal resolution.

### 4.4 Speaker & Acoustic Generalization
- **Speaker Independence:** The test split strictly evaluates speakers never seen during training or hyperparameter tuning. Stuttering manifests with high idiosyncrasy across individuals (e.g. pitch shifts, unique filler patterns, varying speech rates), resulting in lower test generalization compared to speaker-dependent setups.

## 5. Recommended Future Mitigations
1. **Dynamic Pitch / Voice-Onset Feature Integration:** Explicitly extracting fundamental frequency ($F_0$), jitter, shimmer, and voice-onset time (VOT) to distinguish tense blocks from fluent pauses.
2. **Class-Weighted Cost Sensitivity:** Adjusting the SVM decision hyperplane or implementing class-specific probability thresholds to balance block and prolongation recall.
3. **Larger Multi-Corpus Training:** Scaling beyond the 6-episode cohort to multi-speaker diversity (e.g., full FluencyBank corpus).
