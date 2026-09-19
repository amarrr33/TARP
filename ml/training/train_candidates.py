import os
import sys
import time
import json
import pathlib
from pathlib import Path

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support, confusion_matrix, f1_score
)

from configs.config import DATA_CONFIG, MODEL_CONFIG
from ml.features.extraction import (
    load_and_preprocess_audio,
    extract_log_mel_spectrogram,
    extract_mfcc_statistical_features
)
from ml.models.svm_baseline import SVMBaseline
from ml.models.cnn_model import VoxFlowCNN
from ml.models.cnn_gru_model import VoxFlowCNNGRU
from ml.models.wav2vec2_classifier import VoxFlowWav2Vec2Classifier

LABEL_TO_IDX = {"Fluent": 0, "Repetition": 1, "Prolongation": 2, "Block": 3}
IDX_TO_LABEL = {0: "Fluent", 1: "Repetition", 2: "Prolongation", 3: "Block"}

class StutterClipDataset(Dataset):
    def __init__(self, df, feature_type='log_mel'):
        self.df = df.reset_index(drop=True)
        self.feature_type = feature_type
        self.samples = []
        for idx in range(len(self.df)):
            row = self.df.iloc[idx]
            clip_path = row['ClipPath']
            label = LABEL_TO_IDX[row['VoxFlowLabel']]
            audio = load_and_preprocess_audio(clip_path)

            if self.feature_type == 'log_mel':
                feat = extract_log_mel_spectrogram(audio)
                self.samples.append((feat, torch.tensor(label, dtype=torch.long)))
            elif self.feature_type == 'waveform':
                wave = torch.from_numpy(audio)
                self.samples.append((wave, torch.tensor(label, dtype=torch.long)))
            elif self.feature_type == 'mfcc':
                mfcc = extract_mfcc_statistical_features(audio)
                self.samples.append((mfcc, label))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]


def compute_metrics(y_true, y_pred, latency_ms=0.0, model_size_kb=0.0):
    acc = accuracy_score(y_true, y_pred)
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(y_true, y_pred, average='macro', zero_division=0)
    p_weighted, r_weighted, f1_weighted, _ = precision_recall_fscore_support(y_true, y_pred, average='weighted', zero_division=0)
    
    # Per-class metrics
    p_class, r_class, f1_class, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=[0, 1, 2, 3], average=None, zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2, 3])

    return {
        "Accuracy": float(acc),
        "Macro Precision": float(p_macro),
        "Macro Recall": float(r_macro),
        "Macro F1": float(f1_macro),
        "Weighted F1": float(f1_weighted),
        "PerClass_F1": {IDX_TO_LABEL[i]: float(f1_class[i]) for i in range(4)},
        "PerClass_Precision": {IDX_TO_LABEL[i]: float(p_class[i]) for i in range(4)},
        "PerClass_Recall": {IDX_TO_LABEL[i]: float(r_class[i]) for i in range(4)},
        "ConfusionMatrix": cm.tolist(),
        "Latency_ms": float(latency_ms),
        "ModelSize_KB": float(model_size_kb)
    }

def train_svm(train_df, val_df):
    print("\n--- Training Candidate 1: SVM Baseline (MFCC Stats) ---")
    X_train = []
    y_train = []
    for _, row in train_df.iterrows():
        audio = load_and_preprocess_audio(row['ClipPath'])
        feat = extract_mfcc_statistical_features(audio)
        X_train.append(feat)
        y_train.append(LABEL_TO_IDX[row['VoxFlowLabel']])

    X_val = []
    y_val = []
    for _, row in val_df.iterrows():
        audio = load_and_preprocess_audio(row['ClipPath'])
        feat = extract_mfcc_statistical_features(audio)
        X_val.append(feat)
        y_val.append(LABEL_TO_IDX[row['VoxFlowLabel']])

    X_train = np.array(X_train)
    y_train = np.array(y_train)
    X_val = np.array(X_val)
    y_val = np.array(y_val)

    svm = SVMBaseline(C=2.0, kernel='rbf')
    t0 = time.time()
    svm.fit(X_train, y_train)
    train_time = time.time() - t0

    # Inference latency benchmark
    t0 = time.time()
    val_preds = svm.predict(X_val)
    latency_ms = ((time.time() - t0) / len(X_val)) * 1000.0

    # Model size
    svm_path = MODEL_CONFIG['save_dir'] / "candidate_svm.joblib"
    svm.save(svm_path)
    model_size_kb = os.path.getsize(svm_path) / 1024.0

    metrics = compute_metrics(y_val, val_preds, latency_ms, model_size_kb)
    metrics["ModelName"] = "SVM (MFCC Baseline)"
    metrics["TrainTimeSec"] = train_time
    print(f"SVM Validation Macro F1: {metrics['Macro F1']:.4f} | Accuracy: {metrics['Accuracy']:.4f}")
    return svm, metrics

def train_neural_model(model, train_loader, val_loader, model_name, class_weights, epochs=25, lr=1e-3, device='cpu'):
    print(f"\n--- Training {model_name} ---")
    model = model.to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights.to(device))
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_f1 = -1.0
    best_state = None
    t0 = time.time()

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for X_batch, y_batch in train_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            optimizer.zero_grad()
            logits = model(X_batch)
            loss = criterion(logits, y_batch)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        scheduler.step()

        # Validation
        model.eval()
        all_preds = []
        all_targets = []
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch = X_batch.to(device)
                logits = model(X_batch)
                preds = torch.argmax(logits, dim=1).cpu().numpy()
                all_preds.extend(preds)
                all_targets.extend(y_batch.numpy())

        val_macro_f1 = f1_score(all_targets, all_preds, average='macro', zero_division=0)
        if val_macro_f1 > best_val_f1:
            best_val_f1 = val_macro_f1
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

        if epoch % 5 == 0 or epoch == epochs:
            print(f"  Epoch {epoch:02d}/{epochs:02d} | Train Loss: {total_loss/len(train_loader):.4f} | Val Macro F1: {val_macro_f1:.4f}")

    train_time = time.time() - t0
    model.load_state_dict(best_state)
    model.eval()

    # Inference latency benchmark
    t0 = time.time()
    val_preds = []
    val_targets = []
    with torch.no_grad():
        for X_batch, y_batch in val_loader:
            X_batch = X_batch.to(device)
            logits = model(X_batch)
            val_preds.extend(torch.argmax(logits, dim=1).cpu().numpy())
            val_targets.extend(y_batch.numpy())
    latency_ms = ((time.time() - t0) / len(val_targets)) * 1000.0

    # Save candidate checkpoint
    save_path = MODEL_CONFIG['save_dir'] / f"candidate_{model_name.lower().replace(' ', '_')}.pt"
    torch.save(best_state, save_path)
    model_size_kb = os.path.getsize(save_path) / 1024.0

    metrics = compute_metrics(val_targets, val_preds, latency_ms, model_size_kb)
    metrics["ModelName"] = model_name
    metrics["TrainTimeSec"] = train_time
    print(f"{model_name} Best Validation Macro F1: {metrics['Macro F1']:.4f} | Accuracy: {metrics['Accuracy']:.4f}")
    return model, metrics

def run_objective1_experiments():
    print("=================================================================")
    print("        VoxFlow Phase 2: Objective 1 - Model Experiments         ")
    print("=================================================================")

    manifest_path = DATA_CONFIG['manifests_dir'] / "sep28k_clean_manifest.csv"
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")

    df = pd.read_csv(manifest_path)
    # Only keep clips that actually exist on disk and have valid size
    df = df[df['ClipPath'].apply(lambda p: os.path.exists(p) and os.path.getsize(p) > 1000)].copy()
    print(f"Total available clips with audio on disk: {len(df)}")

    train_df = df[df['Split'] == 'Train'].copy()
    val_df = df[df['Split'] == 'Validation'].copy()
    test_df = df[df['Split'] == 'Test'].copy()

    print(f"Split sizes on disk: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")

    # Class weights for loss weighting
    class_counts = train_df['VoxFlowLabel'].value_counts()
    weights = []
    for label in ["Fluent", "Repetition", "Prolongation", "Block"]:
        count = class_counts.get(label, 1)
        weights.append(len(train_df) / (4.0 * count))
    class_weights = torch.tensor(weights, dtype=torch.float32)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using compute device: {device}")

    # Datasets and Loaders
    train_mel_ds = StutterClipDataset(train_df, feature_type='log_mel')
    val_mel_ds = StutterClipDataset(val_df, feature_type='log_mel')
    test_mel_ds = StutterClipDataset(test_df, feature_type='log_mel')

    train_wave_ds = StutterClipDataset(train_df, feature_type='waveform')
    val_wave_ds = StutterClipDataset(val_df, feature_type='waveform')
    test_wave_ds = StutterClipDataset(test_df, feature_type='waveform')

    batch_size = 32
    train_mel_loader = DataLoader(train_mel_ds, batch_size=batch_size, shuffle=True)
    val_mel_loader = DataLoader(val_mel_ds, batch_size=batch_size, shuffle=False)
    test_mel_loader = DataLoader(test_mel_ds, batch_size=batch_size, shuffle=False)

    train_wave_loader = DataLoader(train_wave_ds, batch_size=batch_size, shuffle=True)
    val_wave_loader = DataLoader(val_wave_ds, batch_size=batch_size, shuffle=False)
    test_wave_loader = DataLoader(test_wave_ds, batch_size=batch_size, shuffle=False)

    all_results = []
    models_dict = {}

    # Candidate 1: SVM Baseline
    svm_model, svm_metrics = train_svm(train_df, val_df)
    all_results.append(svm_metrics)
    models_dict["SVM"] = (svm_model, 'svm')

    # Candidate 2: VoxFlowCNN
    cnn_model = VoxFlowCNN(num_classes=4, dropout=0.3)
    cnn_model, cnn_metrics = train_neural_model(
        cnn_model, train_mel_loader, val_mel_loader,
        model_name="2D-CNN (Log-Mel)", class_weights=class_weights, epochs=10, lr=1e-3, device=device
    )
    all_results.append(cnn_metrics)
    models_dict["CNN"] = (cnn_model, 'cnn')

    # Candidate 3: VoxFlowCNNGRU
    cnn_gru_model = VoxFlowCNNGRU(num_classes=4, gru_hidden=128, num_gru_layers=2, dropout=0.3)
    cnn_gru_model, cnn_gru_metrics = train_neural_model(
        cnn_gru_model, train_mel_loader, val_mel_loader,
        model_name="CNN-GRU (Log-Mel)", class_weights=class_weights, epochs=10, lr=1e-3, device=device
    )
    all_results.append(cnn_gru_metrics)
    models_dict["CNN-GRU"] = (cnn_gru_model, 'cnn_gru')

    # Candidate 4: Pretrained Speech Encoder (Wav2Vec2 Architecture)
    w2v_model = VoxFlowWav2Vec2Classifier(num_classes=4, pretrained=False)
    w2v_model, w2v_metrics = train_neural_model(
        w2v_model, train_wave_loader, val_wave_loader,
        model_name="Wav2Vec2-Encoder", class_weights=class_weights, epochs=8, lr=5e-4, device=device
    )
    all_results.append(w2v_metrics)
    models_dict["Wav2Vec2"] = (w2v_model, 'w2v')

    # Build Comparison Table
    comp_rows = []
    for r in all_results:
        comp_rows.append({
            "Model Architecture": r["ModelName"],
            "Macro F1": f"{r['Macro F1']:.4f}",
            "Accuracy": f"{r['Accuracy']:.4f}",
            "Macro Precision": f"{r['Macro Precision']:.4f}",
            "Macro Recall": f"{r['Macro Recall']:.4f}",
            "Weighted F1": f"{r['Weighted F1']:.4f}",
            "Fluent F1": f"{r['PerClass_F1']['Fluent']:.4f}",
            "Repetition F1": f"{r['PerClass_F1']['Repetition']:.4f}",
            "Prolongation F1": f"{r['PerClass_F1']['Prolongation']:.4f}",
            "Block F1": f"{r['PerClass_F1']['Block']:.4f}",
            "Latency (ms)": f"{r['Latency_ms']:.2f}",
            "Model Size (KB)": f"{r['ModelSize_KB']:.1f}"
        })
    comp_df = pd.DataFrame(comp_rows)

    comp_csv_path = Path(ROOT_DIR) / "reports" / "experiments" / "model_comparison_table.csv"
    comp_df.to_csv(comp_csv_path, index=False)

    # Markdown Comparison Report
    comp_md_path = Path(ROOT_DIR) / "reports" / "experiments" / "model_comparison.md"
    with open(comp_md_path, "w", encoding="utf-8") as f:
        f.write("# VoxFlow Objective 1: Four-Model Measured Experimental Comparison\n\n")
        f.write("Evaluation performed on the held-out speaker-independent Validation Split (Zero Speaker Leakage).\n\n")
        f.write(comp_df.to_markdown(index=False) + "\n\n")
        f.write("### Detailed Per-Model Confusion Matrices (Validation Cohort)\n\n")
        for r in all_results:
            f.write(f"#### {r['ModelName']}\n")
            f.write("```text\n")
            f.write(f"Labels: [Fluent, Repetition, Prolongation, Block]\n")
            cm_arr = np.array(r["ConfusionMatrix"])
            f.write(f"{cm_arr}\n")
            f.write("```\n\n")

    print(f"\nModel comparison table saved to: {comp_csv_path}")
    print(f"Model comparison report saved to: {comp_md_path}")

    # =========================================================================
    # Objective 1 Winner Selection (Strictly by Macro F1)
    # =========================================================================
    best_result = max(all_results, key=lambda x: x["Macro F1"])
    winner_name = best_result["ModelName"]
    print(f"\n>>> WINNING MODEL SELECTED BY VALIDATION MACRO F1: {winner_name} (Macro F1 = {best_result['Macro F1']:.4f}) <<<")

    # Save frozen final model packaging for Phase 3
    final_model_dir = MODEL_CONFIG['save_dir']
    os.makedirs(final_model_dir, exist_ok=True)
    final_meta = {
        "model_version": MODEL_CONFIG['version'],
        "winning_architecture": winner_name,
        "sample_rate": 16000,
        "window_duration_sec": 3.0,
        "step_sec": 1.0,
        "validation_macro_f1": best_result["Macro F1"],
        "validation_accuracy": best_result["Accuracy"],
        "class_mapping": LABEL_TO_IDX,
        "classes": ["Fluent", "Repetition", "Prolongation", "Block"]
    }

    if "CNN-GRU" in winner_name:
        final_model_path = final_model_dir / "voxflow_model_v1.0.pt"
        torch.save({
            "state_dict": cnn_gru_model.state_dict(),
            "model_type": "cnn_gru",
            "metadata": final_meta
        }, final_model_path)
    elif "CNN" in winner_name:
        final_model_path = final_model_dir / "voxflow_model_v1.0.pt"
        torch.save({
            "state_dict": cnn_model.state_dict(),
            "model_type": "cnn",
            "metadata": final_meta
        }, final_model_path)
    elif "Wav2Vec2" in winner_name:
        final_model_path = final_model_dir / "voxflow_model_v1.0.pt"
        torch.save({
            "state_dict": w2v_model.state_dict(),
            "model_type": "w2v",
            "metadata": final_meta
        }, final_model_path)
    else:
        final_model_path = final_model_dir / "voxflow_model_v1.0.joblib"
        svm_model.save(final_model_path)

    with open(final_model_dir / "model_metadata.json", "w") as f:
        json.dump(final_meta, f, indent=2)

    print(f"Final model packaged and frozen at: {final_model_path}")

    # =========================================================================
    # Final Test Set Single Evaluation Protocol
    # =========================================================================
    print("\n--- Evaluating Frozen Final Model on Unseen Held-out Test Split ---")
    if "CNN-GRU" in winner_name:
        test_loader = test_mel_loader
        test_m = cnn_gru_model
    elif "CNN" in winner_name:
        test_loader = test_mel_loader
        test_m = cnn_model
    elif "Wav2Vec2" in winner_name:
        test_loader = test_wave_loader
        test_m = w2v_model
    else:
        test_m = None

    if test_m is not None:
        test_m.eval()
        t_preds = []
        t_targets = []
        with torch.no_grad():
            for X_b, y_b in test_loader:
                X_b = X_b.to(device)
                logits = test_m(X_b)
                t_preds.extend(torch.argmax(logits, dim=1).cpu().numpy())
                t_targets.extend(y_b.numpy())
    else:
        X_test = [extract_mfcc_statistical_features(load_and_preprocess_audio(p)) for p in test_df['ClipPath']]
        t_targets = [LABEL_TO_IDX[l] for l in test_df['VoxFlowLabel']]
        t_preds = svm_model.predict(np.array(X_test))

    test_metrics = compute_metrics(t_targets, t_preds)
    test_eval_path = Path(ROOT_DIR) / "reports" / "evaluation" / "final_model_test_evaluation.md"
    with open(test_eval_path, "w", encoding="utf-8") as f:
        f.write("# VoxFlow Final Model Held-Out Test Evaluation\n\n")
        f.write(f"**Selected Winning Model:** {winner_name}\n")
        f.write(f"**Model Version:** {MODEL_CONFIG['version']}\n")
        f.write(f"**Test Set Samples (Unseen Speakers):** {len(test_df)}\n\n")
        f.write("## Measured Test Metrics\n\n")
        f.write(f"- **Accuracy:** {test_metrics['Accuracy']*100:.2f}%\n")
        f.write(f"- **Macro F1:** {test_metrics['Macro F1']*100:.2f}%\n")
        f.write(f"- **Macro Precision:** {test_metrics['Macro Precision']*100:.2f}%\n")
        f.write(f"- **Macro Recall:** {test_metrics['Macro Recall']*100:.2f}%\n")
        f.write(f"- **Weighted F1:** {test_metrics['Weighted F1']*100:.2f}%\n\n")
        f.write("### Per-Class Test Performance\n\n")
        for c in ["Fluent", "Repetition", "Prolongation", "Block"]:
            f.write(f"- **{c}**: Precision = {test_metrics['PerClass_Precision'][c]:.4f}, Recall = {test_metrics['PerClass_Recall'][c]:.4f}, F1 = {test_metrics['PerClass_F1'][c]:.4f}\n")
        f.write("\n### Test Confusion Matrix\n")
        f.write("```text\n")
        f.write(f"Labels: [Fluent, Repetition, Prolongation, Block]\n")
        f.write(f"{np.array(test_metrics['ConfusionMatrix'])}\n")
        f.write("```\n")

    print(f"Final test evaluation report written to: {test_eval_path}")
    print(f"Held-out Test Macro F1: {test_metrics['Macro F1']:.4f} | Accuracy: {test_metrics['Accuracy']:.4f}")
    return winner_name, best_result, test_metrics

if __name__ == "__main__":
    run_objective1_experiments()
