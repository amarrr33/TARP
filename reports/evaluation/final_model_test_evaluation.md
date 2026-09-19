# VoxFlow Final Model Held-Out Test Evaluation

**Selected Winning Model:** SVM (MFCC Baseline)
**Model Version:** voxflow-model-v1.0
**Test Set Samples (Unseen Speakers):** 201

## Measured Test Metrics

- **Accuracy:** 33.83%
- **Macro F1:** 29.52%
- **Macro Precision:** 38.32%
- **Macro Recall:** 31.43%
- **Weighted F1:** 30.56%

### Per-Class Test Performance

- **Fluent**: Precision = 0.3824, Recall = 0.2500, F1 = 0.3023
- **Repetition**: Precision = 0.3171, Recall = 0.6393, F1 = 0.4239
- **Prolongation**: Precision = 0.3333, Recall = 0.2791, F1 = 0.3038
- **Block**: Precision = 0.5000, Recall = 0.0889, F1 = 0.1509

### Test Confusion Matrix
```text
Labels: [Fluent, Repetition, Prolongation, Block]
[[13 32  5  2]
 [ 9 39 12  1]
 [ 3 27 12  1]
 [ 9 25  7  4]]
```
