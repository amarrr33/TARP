import os
import torch
import torch.nn as nn
import torchaudio


class VoxFlowWav2Vec2Classifier(nn.Module):
    """
    Candidate 4: Pretrained Speech Representation Model (Wav2Vec 2.0 style) + Classifier Head.
    Input: Raw waveform (B, 48000) at 16kHz
    Architecture:
    - 7-layer 1D CNN feature extractor (subsamples audio to ~50Hz frame rate)
    - Transformer encoder or projection layers
    - Temporal mean pooling
    - Classifier head for 4 classes
    """
    def __init__(self, num_classes=4, pretrained=True, freeze_extractor=True):
        super().__init__()
        self.encoder = None
        self.embed_dim = 768

        ckpt_path = os.path.expanduser("~/.cache/torch/hub/checkpoints/wav2vec2_fairseq_base_ls960.pth")
        if pretrained and os.path.exists(ckpt_path) and os.path.getsize(ckpt_path) > 300 * 1024 * 1024:
            try:
                bundle = torchaudio.pipelines.WAV2VEC2_BASE
                self.model = bundle.get_model()
                if freeze_extractor:
                    for param in self.model.parameters():
                        param.requires_grad = False
                self.embed_dim = 768
                self.is_custom = False
            except Exception:
                self.is_custom = True
        else:
            self.is_custom = True
            self.model = nn.Sequential(
                nn.Conv1d(1, 128, kernel_size=10, stride=5),
                nn.BatchNorm1d(128),
                nn.ReLU(),
                nn.Conv1d(128, 256, kernel_size=3, stride=2),
                nn.BatchNorm1d(256),
                nn.ReLU(),
                nn.Conv1d(256, 512, kernel_size=3, stride=2),
                nn.BatchNorm1d(512),
                nn.ReLU(),
                nn.Conv1d(512, 768, kernel_size=3, stride=2),
                nn.BatchNorm1d(768),
                nn.ReLU(),
                nn.AdaptiveAvgPool1d(1)
            )

        self.classifier = nn.Sequential(
            nn.Linear(self.embed_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes)
        )

    def forward(self, waveforms):
        # waveforms: (B, 48000)
        if not self.is_custom:
            # Pass through Wav2Vec2 model
            features, _ = self.model.extract_features(waveforms)
            # Take representations from top transformer layer
            top_features = features[-1]  # (B, T, 768)
            pooled = torch.mean(top_features, dim=1)  # (B, 768)
        else:
            x = waveforms.unsqueeze(1)  # (B, 1, 48000)
            pooled = self.model(x).squeeze(-1)  # (B, 768)

        logits = self.classifier(pooled)
        return logits
