# VoxFlow Objective 1: Four-Model Measured Experimental Comparison

Evaluation performed on the held-out speaker-independent Validation Split (Zero Speaker Leakage).

| Model Architecture   |   Macro F1 |   Accuracy |   Macro Precision |   Macro Recall |   Weighted F1 |   Fluent F1 |   Repetition F1 |   Prolongation F1 |   Block F1 |   Latency (ms) |   Model Size (KB) |
|:---------------------|-----------:|-----------:|------------------:|---------------:|--------------:|------------:|----------------:|------------------:|-----------:|---------------:|------------------:|
| SVM (MFCC Baseline)  |     0.3426 |     0.4766 |            0.3581 |         0.3641 |        0.4331 |      0.3125 |          0.4474 |            0.6105 |     0      |           0.07 |             658.8 |
| 2D-CNN (Log-Mel)     |     0.2815 |     0.3551 |            0.2923 |         0.3302 |        0.3293 |      0.4444 |          0.2817 |            0.4    |     0      |           5.01 |            1663.5 |
| CNN-GRU (Log-Mel)    |     0.3    |     0.3551 |            0.3774 |         0.3283 |        0.3384 |      0.3284 |          0.475  |            0.2857 |     0.1111 |          12.17 |            5064.1 |
| Wav2Vec2-Encoder     |     0.2804 |     0.3178 |            0.3331 |         0.405  |        0.2605 |      0.4138 |          0      |            0.3922 |     0.3158 |          23.49 |            6962.4 |

### Detailed Per-Model Confusion Matrices (Validation Cohort)

#### SVM (MFCC Baseline)
```text
Labels: [Fluent, Repetition, Prolongation, Block]
[[ 5 13  4  0]
 [ 0 17 18  0]
 [ 3  7 29  0]
 [ 2  4  5  0]]
```

#### 2D-CNN (Log-Mel)
```text
Labels: [Fluent, Repetition, Prolongation, Block]
[[16  5  1  0]
 [20 10  5  0]
 [ 9 18 12  0]
 [ 5  3  3  0]]
```

#### CNN-GRU (Log-Mel)
```text
Labels: [Fluent, Repetition, Prolongation, Block]
[[11  7  1  3]
 [13 19  2  1]
 [16 14  7  2]
 [ 5  5  0  1]]
```

#### Wav2Vec2-Encoder
```text
Labels: [Fluent, Repetition, Prolongation, Block]
[[18  0  0  4]
 [25  0  2  8]
 [17  3 10  9]
 [ 5  0  0  6]]
```

