# VoxFlow - AI-Assisted Speech Fluency System (Software Engineering Suite)

VoxFlow is a low-cost, AI-assisted speech fluency monitoring system designed to help individuals who stutter track their speech progress between speech therapy sessions.

This repository contains the **Software Engineering Codebase** (Member 3 responsibility) running on the host laptop:
- **Flask REST API Backend** (`server.py`)
- **SQLite Database Initialization & DAO** (`database.py`)
- **Streamlit Live Analytics Dashboard** (`dashboard.py`)
- **Audio Processing Pipeline Modules** (`pipeline.py`)
- **ESP32 Wi-Fi HTTP Upload Simulator** (`simulate_esp32.py`)
- **Document & Diagram Generators** (`build_voxflow_report.py`, `generate_diagrams.py`)

---

## Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Database & Seed Sample Data
```bash
python database.py
```

### 3. Launch Host Server & Dashboard
You can run the 1-click launcher on Windows:
```cmd
run_voxflow_system.bat
```
Or launch components separately:
- **Flask REST API Server**:
  ```bash
  python server.py
  ```
- **Streamlit Analytics Dashboard**:
  ```bash
  streamlit run dashboard.py
  ```

### 4. Test ESP32 Wi-Fi Audio Upload
In a new terminal window, simulate sending an audio stream from an ESP32 device to the Flask backend:
```bash
python simulate_esp32.py
```

---

## Software Architecture

```
ESP32 Hardware (Wi-Fi POST)
         │
         ▼
 Flask REST Backend (server.py)
         │
         ▼
 Audio Processing Pipeline (pipeline.py)
   ├── Spectral Noise Removal
   ├── Speaker Verification Match
   ├── 13-MFCC Feature Extraction
   └── CNN-LSTM Model Inference
         │
         ▼
 SQLite Database (database.py)
         │
         ▼
 Streamlit Web Dashboard (dashboard.py)
```

---

## Authors & Responsibility
- **Software Engineering Lead**: Member 3 (Host Server, APIs, Database, Analytics Dashboard)
- **Project**: Final Year Engineering Project - VoxFlow
