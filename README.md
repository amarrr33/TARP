# VoxFlow — Speech Fluency & Stuttering Event Monitoring System

VoxFlow is a reproducible, measurable, end-to-end software prototype for speech fluency and stuttering-event monitoring. It classifies continuous speech into four clinically grounded categories (**Fluent**, **Repetition**, **Prolongation**, and **Block**), performs overlapping window inference, aggregates temporal events to prevent double counting, computes a session fluency ratio, and provides interactive review via an authenticated SQLite store and Streamlit dashboard.

> **Clinical Disclaimer**: VoxFlow is an automated speech fluency monitoring prototype designed for college research and longitudinal progress tracking. It is **not a medical diagnostic device** and does not make diagnostic or clinical severity claims.

---

## 1. System Architecture

```text
Continuous Session Audio (30–60s WAV)
         │
         ▼
 Flask REST API (server.py / app/api/session_routes.py)
         │
         ▼
 Session Engine (app/services/session_engine.py)
   ├── 16 kHz Mono Normalization & Silence Check
   └── Overlapping 3.0s Windows (1.0s Step)
         │
         ▼
 Frozen Inference Engine (ml/inference/engine.py: voxflow-model-v1.0)
   └── Softmax Class Probabilities [Fluent, Repetition, Prolongation, Block]
         │
         ▼
 Temporal Event Aggregator (app/services/event_aggregator.py)
   └── Window Merge (Merge gap <= 1.5s, Confidence >= 0.50) -> Event Regions
         │
         ▼
 Session Summary Calculator (app/services/session_summary.py)
   └── Fluency Ratio = (Fluent Windows / Valid Windows) * 100%
         │
         ▼
 SQLite Database (app/db/database.py: voxflow.db)
   ├── users
   ├── sessions
   ├── session_windows
   ├── session_events
   └── session_summary
         │
         ▼
 Streamlit Analytics Dashboard (dashboard/dashboard.py)
   ├── 🏠 Home: System status & latest session KPI cards
   ├── ⏱️ Current Session: Interactive Plotly timeline & window audit
   ├── 📜 History: Historical session table with detailed inspection
   ├── 📈 Trends: Multi-session longitudinal fluency analytics
   ├── 🧠 Model Info: Objective 1 benchmarks & model transparency
   └── 📄 Reports: Session clinical report generation & PDF export
```

---

## 2. Objective 1: ML Model Experiments & Benchmark

Four candidate models were implemented, trained, and benchmarked on real stuttering audio from the **SEP-28k** dataset under strict speaker-independent splitting (0% speaker leakage across Train, Validation, and Test cohorts):

| Model Candidate | Feature / Input Representation | Validation Accuracy | Validation Macro F1 | Test Accuracy | Test Macro F1 | Inference Latency | Selected Status |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **SVM Baseline** | MFCCs + $\Delta$ + $\Delta\Delta$ (mean/std) | **47.66%** | **0.3426** | **33.83%** | **0.2952** | **0.07 ms** | **WINNER (Selected & Frozen)** |
| **2D-CNN** | Log-Mel Spectrogram (128 mel bins) | 35.51% | 0.2815 | — | — | 5.01 ms | Evaluated |
| **CNN-GRU** | Log-Mel Spectrogram + Recurrent GRU | 35.51% | 0.3000 | — | — | 12.17 ms | Evaluated |
| **Wav2Vec2 Encoder** | 1D Conv Temporal Speech Representation | 31.78% | 0.2804 | — | — | 23.49 ms | Evaluated |

### Winner Selection & Freezing
- **Primary Metric:** Macro F1.
- **Winner:** SVM (MFCC Baseline) achieved highest validation Macro F1 (0.3426) with near-instantaneous latency (0.07 ms).
- **Frozen Artifact:** Packaged to `models/final/voxflow_model_v1.0.joblib` with reproducible metadata in `models/final/model_metadata.json`.
- **Held-Out Test Set Result:** Macro F1 = 29.52%, Accuracy = 33.83% across 201 unseen-speaker clips.

---

## 3. Objective 2: Complete-Session Continuous Pipeline

VoxFlow operates on standard continuous recordings (30 to 60 seconds):
1. **Window Generation**: Audio is divided into 3.0-second sliding windows with a 1.0-second step (e.g. 0–3s, 1–4s, 2–5s).
2. **Deterministic Inference**: Each window is evaluated by the frozen production model, generating confidence and calibrated probabilities for all 4 classes.
3. **Temporal Event Aggregation**: Contiguous or overlapping windows predicting the same disfluent class are coalesced into continuous event intervals. Overlapping windows are **never** counted as independent events.
4. **Session Fluency Ratio**: Calculated as:
   $$\text{Fluency Ratio} = \frac{\text{Fluent Valid Speech Windows}}{\text{Total Valid Speech Windows}}$$
5. **Database Persistence**: Session records, window probability time series, aggregated events, and summary statistics are permanently stored in SQLite (`voxflow.db`).

---

## 4. REST API Specification

VoxFlow exposes a RESTful session lifecycle API (`server.py`):

| Endpoint | Method | Description |
|:---|:---:|:---|
| `/api/v1/session/start` | POST | Initialize a new monitoring session (`{"user_id": "user-001"}`) |
| `/api/v1/session/<id>/audio` | POST | Upload session audio payload (multipart/form-data or binary WAV) |
| `/api/v1/session/<id>/stop` | POST | Conclude audio recording for the session |
| `/api/v1/session/<id>/analyze` | POST | Run window inference, temporal aggregation, summary, and DB persistence |
| `/api/v1/session/<id>` | GET | Retrieve full session summary, events, and window details |
| `/api/v1/sessions/<user_id>` | GET | Retrieve all historical sessions for a user |
| `/api/v1/session/latest` | GET | Retrieve the most recently analyzed session |
| `/api/v1/model/info` | GET | Inspect frozen model version, metadata, and performance metrics |

---

## 5. Streamlit Reviewer Dashboard

The multi-page Streamlit dashboard (`dashboard/dashboard.py`) enables real-time visual inspection:
- **Home**: Overall system health, model version, and KPI metrics of the latest recorded session.
- **Current Session**: Interactive timeline chart visualizing event durations and confidence, accompanied by full window probability audits.
- **History**: Historical session table with filtering and drill-down inspection.
- **Trends**: Multi-session longitudinal trends for fluency ratio and disfluency counts.
- **Model Info**: Comprehensive breakdown of candidate model experiments, feature extraction parameters, confusion matrix, and error analysis.
- **Reports**: Clinical session report generation with markdown/PDF export capabilities.

Launch the dashboard:
```bash
streamlit run dashboard.py
```

---

## 6. Verification and Test Suite

VoxFlow includes automated unit, integration, and end-to-end system tests:

```bash
# Run Unit Tests (Components & Edge Cases)
pytest tests/unit/ -v

# Run Full Integration Pipeline Test
pytest tests/integration/test_full_pipeline.py -v

# Run Objective 2 Session-Level Evaluation
python tests/evaluation/test_session_evaluation.py

# Run Final Objective 2 End-to-End Session Run
python tests/evaluation/run_final_objective2.py
```

---

## 7. Limitations & Ethical Boundary Considerations

1. **Not a Clinical Diagnostic Instrument**: Fluency ratios and detected events are monitoring heuristics, not medical diagnostic indicators or formal SSI-4 severity equivalents.
2. **Temporal Window Localization**: Events detected via 3.0-second sliding windows have an approximate boundary resolution of 1.0 second; millisecond-level phonetic localization is neither claimed nor supported.
3. **Acoustic Generalization**: Stuttering manifestations (especially silent blocks) are highly speaker-dependent. Environmental background noise, microphone differences, and conversational pacing may affect accuracy.
