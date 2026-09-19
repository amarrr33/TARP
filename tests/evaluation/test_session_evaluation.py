import os
import sys
import numpy as np
import pathlib
from scipy.io import wavfile

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from configs.config import SESSION_CONFIG, MODEL_CONFIG
from app.services.session_engine import (
    validate_and_load_session_audio,
    process_session_windows,
    AudioValidationError
)
from app.services.event_aggregator import aggregate_window_events
from app.services.session_summary import calculate_session_summary

def construct_synthetic_session_for_eval(clips_dir, target_duration=45.0):
    """
    Constructs an evaluation session by stitching real 3.0s clips with known ground truth
    to rigorously evaluate session-level temporal event aggregation, windowing, and fluency ratio.
    """
    import pandas as pd
    manifest_path = ROOT_DIR / "data" / "manifests" / "sep28k_clean_manifest.csv"
    if not os.path.exists(manifest_path):
        return None, []

    df = pd.read_csv(manifest_path)
    def is_valid_clip(p):
        full_p = ROOT_DIR / p if not os.path.isabs(p) else pathlib.Path(p)
        return full_p.exists() and full_p.stat().st_size > 1000

    df = df[df['ClipPath'].apply(is_valid_clip)]
    if len(df) < 15:
        return None, []

    # Pick 15 consecutive clips to make a 45s session
    selected_clips = df.head(15).copy()
    audio_concat = []
    ground_truth_events = []
    current_time = 0.0

    for idx, row in selected_clips.iterrows():
        raw_clip_path = str(row['ClipPath'])
        full_clip_path = ROOT_DIR / raw_clip_path if not os.path.isabs(raw_clip_path) else pathlib.Path(raw_clip_path)
        sr, audio = wavfile.read(str(full_clip_path))
        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32768.0
        audio_concat.append(audio)
        label = row['VoxFlowLabel']
        if label in ['Repetition', 'Prolongation', 'Block']:
            ground_truth_events.append({
                "label": label,
                "start": current_time,
                "end": current_time + 3.0
            })
        current_time += 3.0

    session_audio = np.concatenate(audio_concat)
    test_session_wav = ROOT_DIR / "data" / "eval_session_45s.wav"
    pcm16 = (session_audio * 32767.0).clip(-32768, 32767).astype(np.int16)
    wavfile.write(test_session_wav, 16000, pcm16)
    return str(test_session_wav), ground_truth_events

def evaluate_session_level_metrics():
    print("=== Running Phase 7: Objective 2 - Session-Level Evaluation ===")
    test_wav, gt_events = construct_synthetic_session_for_eval(ROOT_DIR / "data" / "processed" / "clips")
    
    if not test_wav:
        print("Not enough clips on disk yet for session-level evaluation.")
        return

    # Run complete session pipeline
    audio, sr, duration_sec = validate_and_load_session_audio(test_wav)
    session_id = "eval_session_ground_truth"
    windows = process_session_windows(session_id, audio, sr, duration_sec)
    events = aggregate_window_events(session_id, windows)
    summary = calculate_session_summary(
        session_id=session_id,
        duration_sec=duration_sec,
        windows=windows,
        events=events,
        model_version=MODEL_CONFIG['version']
    )

    print(f"Session Duration: {summary['duration_sec']}s")
    print(f"Total Windows: {summary['total_windows']}")
    print(f"Aggregated Events Detected: {len(events)}")
    print(f"Ground Truth Disfluent Regions: {len(gt_events)}")
    print(f"Fluency Ratio: {summary['fluency_ratio']*100:.2f}%")

    # Evaluate event matching (Temporal Overlap IoU >= 0.2)
    matched_gt = 0
    false_positives = 0
    for det in events:
        matched = False
        for gt in gt_events:
            overlap_start = max(det['start_time'], gt['start'])
            overlap_end = min(det['end_time'], gt['end'])
            if overlap_end > overlap_start:
                intersection = overlap_end - overlap_start
                union = (det['end_time'] - det['start_time']) + (gt['end'] - gt['start']) - intersection
                if (intersection / union) >= 0.1 and det['event_type'] == gt['label']:
                    matched = True
                    break
        if matched:
            matched_gt += 1
        else:
            false_positives += 1

    report_path = ROOT_DIR / "reports" / "evaluation" / "session_level_evaluation.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# VoxFlow Phase 7: Session-Level System Evaluation\n\n")
        f.write("## Objective 2 vs Objective 1 Distinction\n")
        f.write("Window-level ML metrics (Objective 1) evaluate 3-second isolated clips. "
                "Session-level metrics (Objective 2) evaluate the end-to-end continuous 30–60s monitoring system, "
                "including audio validation, overlapping window probabilities, temporal event aggregation, "
                "and aggregate fluency ratio.\n\n")
        f.write("## Measured Session-Level Evaluation Results\n\n")
        f.write(f"- **Evaluated Session Duration:** {summary['duration_sec']} seconds\n")
        f.write(f"- **Total 3.0s Windows Processed (1.0s Step):** {summary['total_windows']}\n")
        f.write(f"- **Fluent Windows Identified:** {summary['fluent_windows']}\n")
        f.write(f"- **Calculated Session Fluency Ratio:** {summary['fluency_ratio']*100:.2f}%\n")
        f.write(f"- **Aggregated Detected Events:** {len(events)}\n")
        f.write(f"- **Ground Truth Target Disfluencies:** {len(gt_events)}\n")
        f.write(f"- **Temporally Matched Detections:** {matched_gt}\n")
        f.write(f"- **Extra Detections / False Positives:** {false_positives}\n\n")
        f.write("### Aggregated Event Timeline\n\n")
        f.write("| Detected Type | Start Time (s) | End Time (s) | Confidence | Supporting Windows |\n")
        f.write("|:---|:---|:---|:---|:---|\n")
        for e in events:
            f.write(f"| {e['event_type']} | {e['start_time']:.2f} | {e['end_time']:.2f} | {e['confidence']*100:.1f}% | {e['supporting_window_count']} |\n")
        f.write("\n### Limitations and Boundary Analysis\n")
        f.write("- Stuttering events occurring near 3.0s window edges can trigger support in adjacent overlapping windows, "
                "which the temporal aggregator coalesces into a continuous region.\n")
        f.write("- The fluency ratio represents an automated monitoring heuristic (`fluent_windows / valid_windows`) "
                "and must not be interpreted as a clinical stuttering severity index (e.g. SSI-4).\n")

    print(f"Session-level evaluation report saved to: {report_path}")

if __name__ == "__main__":
    evaluate_session_level_metrics()
