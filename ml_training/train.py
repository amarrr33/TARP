import os
import json
import time
import torch
import torch.nn as nn
import torch.optim as optim
from .dataset import get_train_test_dataloaders, LABELS
from .model import StutterTransferClassifier

def train_model(epochs=15, batch_size=32, lr=0.001, save_dir=r"c:\Users\amare\Downloads\TARP\model_weights"):
    """
    Executes Transfer Learning fine-tuning on VoxFlow disfluency dataset with 70-30 train-test split.
    Saves trained PyTorch weights to model_weights/stutter_model.pt.
    """
    os.makedirs(save_dir, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # 1. Load Data with 70-30 Train-Test Split
    print("\n--- Preparing VoxFlow Dataset (70-30 Train/Test Split) ---")
    train_loader, test_loader, split_info = get_train_test_dataloaders(
        test_size=0.30, batch_size=batch_size, num_samples_per_class=300
    )
    
    print(f"Total Dataset Samples : {split_info['total_samples']}")
    print(f"Training Set (70%)   : {split_info['train_samples']} samples ({split_info['train_ratio']}%)")
    print(f"Testing Set (30%)    : {split_info['test_samples']} samples ({split_info['test_ratio']}%)")
    print(f"Target Disfluency Classes: {LABELS}")
    
    # 2. Instantiate Model with Anti-Overfitting Loss & Weight Decay
    model = StutterTransferClassifier(num_classes=len(LABELS)).to(device)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)  # Prevents overconfident memorization
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-3) # L2 Regularization
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    
    history = {
        "epochs": [],
        "train_loss": [],
        "train_acc": [],
        "test_loss": [],
        "test_acc": []
    }
    
    print("\n--- Starting Fine-Tuning Training Loop ---")
    start_time = time.time()
    
    best_test_acc = 0.0
    model_save_path = os.path.join(save_dir, "stutter_model.pt")
    
    for epoch in range(1, epochs + 1):
        # Training Phase
        model.train()
        running_loss = 0.0
        correct_train = 0
        total_train = 0
        
        for inputs, targets in train_loader:
            inputs, targets = inputs.to(device), targets.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(outputs, 1)
            correct_train += torch.sum(preds == targets).item()
            total_train += targets.size(0)
            
        scheduler.step()
        epoch_train_loss = running_loss / total_train
        epoch_train_acc = (correct_train / total_train) * 100.0
        
        # Testing/Validation Phase (30% Test Split)
        model.eval()
        running_test_loss = 0.0
        correct_test = 0
        total_test = 0
        
        with torch.no_grad():
            for inputs, targets in test_loader:
                inputs, targets = inputs.to(device), targets.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, targets)
                
                running_test_loss += loss.item() * inputs.size(0)
                _, preds = torch.max(outputs, 1)
                correct_test += torch.sum(preds == targets).item()
                total_test += targets.size(0)
                
        epoch_test_loss = running_test_loss / total_test
        epoch_test_acc = (correct_test / total_test) * 100.0
        
        history["epochs"].append(epoch)
        history["train_loss"].append(round(epoch_train_loss, 4))
        history["train_acc"].append(round(epoch_train_acc, 2))
        history["test_loss"].append(round(epoch_test_loss, 4))
        history["test_acc"].append(round(epoch_test_acc, 2))
        
        print(f"Epoch {epoch:02d}/{epochs:02d} | "
              f"Train Loss: {epoch_train_loss:.4f} | Train Acc: {epoch_train_acc:.2f}% | "
              f"Test Loss: {epoch_test_loss:.4f} | Test Acc: {epoch_test_acc:.2f}%")
              
        if epoch_test_acc > best_test_acc:
            best_test_acc = epoch_test_acc
            # Save state dict and model configuration
            torch.save({
                'model_state_dict': model.state_dict(),
                'labels': LABELS,
                'input_shape': (1, 64, 64),
                'test_accuracy': best_test_acc
            }, model_save_path)
            
    total_duration = time.time() - start_time
    print(f"\n--- Training Complete in {total_duration:.2f} seconds ---")
    print(f"Best 30% Test Accuracy Achieved: {best_test_acc:.2f}%")
    print(f"Model saved successfully to: {model_save_path}")
    
    # Save training history JSON
    history_save_path = os.path.join(save_dir, "training_metrics.json")
    with open(history_save_path, "w") as f:
        json.dump(history, f, indent=4)
        
    return model, history, split_info

if __name__ == "__main__":
    train_model(epochs=15, batch_size=32, lr=0.001)
