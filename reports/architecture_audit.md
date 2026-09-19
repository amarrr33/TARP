# VoxFlow Phase 0: Architecture & Repository Audit Report

**Date:** 2026-09-19  
**Status:** Completed  
**Objective:** Thorough audit of legacy codebase against the Locked Master Software Plan.

---

## 1. Executive Summary
The legacy codebase in `TARP/` contains initial prototype scaffolding, but violates several core principles of the Locked Master Plan:
1. **Fabricated / Simulated Data**: Random numbers are used for fluency scores, SNR, and speaker verification.
2. **Synthetic Dataset as Real Evidence**: `ml_training/dataset.py` generates synthetic sine waves when data is missing, and `ml_training/evaluate.py` hardcodes a synthetic confusion matrix.
3. **Session Lifecycle Mismatch**: The backend operates on fragmented 0.5s chunks via continuous REST uploads instead of the specified 30–60 second session lifecycle (`start` → `audio` → `stop` → `analyze`).
4. **Database Schema Mismatch**: The SQLite schema lacks window-level probabilities and aggregated event persistence.
5. **Dashboard Mismatch**: The UI contains mock manga dialogue and real-time streaming assumptions instead of the 6 structured reviewer pages.

---

## 2. File-by-File Audit

### 2.1 `pipeline.py`
- **Issue 1 (Random Fluency Scores)**: Lines 142–146 generate fluency scores via `random.uniform(91.0, 98.5)` and `random.uniform(62.0, 79.5)`. This is completely unscientific.
- **Issue 2 (Simulated Preprocessing)**: `NoiseFilter` and `SpeakerVerifier` return fake random values (`random.uniform(18.0, 32.0)` and `random.uniform(0.88, 0.97)`).
- **Issue 3 (Fragmented Windowing)**: `AudioChunkAccumulator` assumes incoming 0.5s real-time streaming chunks rather than the locked 3-second overlapping windows with 1-second step on full 30–60s sessions.
- **Action**: Completely replace with `app/services/session_engine.py` and `app/services/event_aggregator.py`.

### 2.2 `ml_training/dataset.py` & `ml_training/train.py`
- **Issue 1 (Synthetic Audio as Production Evidence)**: Lines 14–67 of `dataset.py` synthesize sine waves and white noise as "synthetic SEP-28k". This violates Rule 11 of the Execution Contract.
- **Issue 2 (Lack of Model Comparison)**: Only a single CNN classifier was trained. The required 4-model comparison (SVM, CNN, CNN+GRU, Pretrained Speech Encoder) was never implemented.
- **Action**: Ingest real SEP-28k / FluencyBank clips, build a clean manifest, enforce speaker-independent splits, and execute Phase 2 model comparisons.

### 2.3 `ml_training/evaluate.py`
- **Issue 1 (Fabricated Confusion Matrix)**: Lines 61–68 define a hardcoded confusion matrix (`realistic_cm`) instead of computing metrics from real model inference on held-out test data. This violates Rule 2.
- **Action**: Rebuild evaluation to compute real Macro F1, per-class F1, Precision, Recall, and confusion matrices strictly from model outputs.

### 2.4 `database.py`
- **Issue 1 (Schema Inadequacy)**: Only tracks `users`, `sessions`, `predictions`, `reports`. It does not store individual window probabilities (`session_windows`) or deduplicated event regions (`session_events`).
- **Issue 2 (Fabricated Seed Data)**: `seed_sample_data()` inserts synthetic dates and scores generated with `random.uniform()`.
- **Action**: Migrate to the locked 5-table schema: `users`, `sessions`, `session_windows`, `session_events`, and `session_summary`.

### 2.5 `server.py`
- **Issue 1 (Incorrect API Contract)**: Exposes `/api/v1/audio/upload` and continuous micro-uploads instead of the required session lifecycle endpoints (`/api/v1/session/start`, `/api/v1/session/{id}/audio`, `/api/v1/session/{id}/stop`, `/api/v1/session/{id}/analyze`).
- **Action**: Rebuild with clean REST endpoints in `app/api/session_routes.py`.

### 2.6 `dashboard.py`
- **Issue 1 (Mock Visuals & Streaming Assumptions)**: Contains mock manga dialogue bubbles and continuous auto-refresh loops.
- **Action**: Rebuild with 6 clean reviewer-facing pages reading from SQLite: Home, Current Session (horizontal timeline), History, Trends, Model Info, and Reports.

---

## 3. Migration Roadmap
1. Build central configuration in `configs/config.py`.
2. Clean and ingest official SEP-28k audio and annotations in `data/` and `ml/data/`.
3. Implement and train the 4 candidate models in `ml/models/` and `ml/training/`.
4. Freeze winning model in `models/final/`.
5. Build session engine, event aggregation, and summary in `app/services/`.
6. Implement normalized SQLite persistence in `app/db/`.
7. Build Flask REST API in `app/api/` and `server.py`.
8. Implement 6-page Streamlit UI in `dashboard/dashboard.py`.
9. Execute automated integration and session-level evaluation.
