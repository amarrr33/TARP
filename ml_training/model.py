import torch
import torch.nn as nn
import torch.nn.functional as F

class ConvBlock(nn.Module):
    """Convolutional Block with BatchNorm, ReLU activation, and MaxPool."""
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

    def forward(self, x):
        return self.conv(x)

class StutterTransferClassifier(nn.Module):
    """
    Transfer Learning Speech Disfluency Classifier for VoxFlow.
    Uses a deep 2D Conv feature backbone (pre-trained audio feature hierarchy)
    fine-tuned with a 4-class classification head (Fluent, Repetition, Prolongation, Block).
    """
    def __init__(self, num_classes=4):
        super().__init__()
        # Pre-trained Feature Extraction Backbone (Convolutional Pyramids)
        self.layer1 = ConvBlock(1, 32)    # 64x64 -> 32x32
        self.layer2 = ConvBlock(32, 64)   # 32x32 -> 16x16
        self.layer3 = ConvBlock(64, 128)  # 16x16 -> 8x8
        self.layer4 = ConvBlock(128, 256) # 8x8 -> 4x4
        
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        
        # Classification Head (Transfer Learning Fine-Tuning Head)
        self.classifier = nn.Sequential(
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes)
        )
        
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d) or isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def forward(self, x):
        # Feature Extraction Backbone
        feat = self.layer1(x)
        feat = self.layer2(feat)
        feat = self.layer3(feat)
        feat = self.layer4(feat)
        
        # Global Pooling
        pooled = self.global_pool(feat)
        flat = torch.flatten(pooled, 1)
        
        # Fine-tuned classification
        logits = self.classifier(flat)
        return logits

    def predict(self, x):
        """Returns predicted class label string and confidence score."""
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            probs = F.softmax(logits, dim=1)
            confidence, predicted_idx = torch.max(probs, dim=1)
        return predicted_idx.item(), confidence.item()
