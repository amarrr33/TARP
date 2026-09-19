import torch
import torch.nn as nn

class VoxFlowCNNGRU(nn.Module):
    """
    Candidate 3: CNN + Bidirectional GRU for temporal sequence modeling of Log-Mel Spectrograms.
    Input: (B, 1, n_mels=64, time_frames=301)
    Output: Logits for 4 classes (B, 4)
    """
    def __init__(self, num_classes=4, gru_hidden=128, num_gru_layers=2, dropout=0.3):
        super().__init__()
        # CNN blocks reduce spectral dimension while maintaining temporal resolution
        self.conv_blocks = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=(2, 1)),  # (32, 32, T)

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=(2, 1)),  # (64, 16, T)

            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=(2, 2)),  # (128, 8, T//2)
            nn.Dropout2d(0.1)
        )

        # After conv blocks, feature map is (B, 128, 8, T//2) -> flatten freq into feature dim: 128 * 8 = 1024
        self.gru = nn.GRU(
            input_size=1024,
            hidden_size=gru_hidden,
            num_layers=num_gru_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_gru_layers > 1 else 0.0
        )

        self.classifier = nn.Sequential(
            nn.Linear(gru_hidden * 2, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, num_classes)
        )

    def forward(self, x):
        # x: (B, 1, 64, T)
        conv_out = self.conv_blocks(x)  # (B, 128, 8, T_reduced)
        B, C, F, T = conv_out.shape
        # Reshape to (B, T, C*F) for GRU sequence
        seq = conv_out.permute(0, 3, 1, 2).contiguous().view(B, T, C * F)
        gru_out, _ = self.gru(seq)  # (B, T, 2 * gru_hidden)

        # Temporal attention / mean pooling over time
        pooled = torch.mean(gru_out, dim=1)  # (B, 2 * gru_hidden)
        logits = self.classifier(pooled)
        return logits
