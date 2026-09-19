import os
import sys
import json
import pathlib
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from configs.config import MODEL_CONFIG, SESSION_CONFIG
from app.db.database import (
    init_db,
    get_latest_session,
    get_all_sessions,
    get_session,
    save_session_record,
    save_session_analysis
)
from app.services.session_engine import (
    validate_and_load_session_audio,
    process_session_windows,
    AudioValidationError
)
from app.services.event_aggregator import aggregate_window_events
from app.services.session_summary import calculate_session_summary

# Ensure DB initialized
init_db()

st.set_page_config(
    page_title="VoxFlow — Speech Fluency Analysis Platform",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Design System
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    .main {
        background-color: #F8FAFC;
    }
    .vox-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    .vox-stat-label {
        font-size: 13px;
        color: #64748B;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .vox-stat-val {
        font-size: 28px;
        font-weight: 800;
        color: #0F172A;
    }
    .disclaimer-banner {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 12px 16px;
        border-radius: 6px;
        color: #92400E;
        font-size: 13px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Navigation
st.sidebar.title("🎙️ VoxFlow Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Home", "Current Session", "History", "Trends", "Model Info", "Reports"]
)

st.sidebar.markdown("---")
st.sidebar.caption(f"**Engine Version:** `{MODEL_CONFIG['version']}`")
st.sidebar.caption("**Corpus:** `SEP-28k (Cleaned)`")
st.sidebar.caption("**Window:** `3.0s (1.0s step)`")

# -----------------------------------------------------------------------------
# PAGE 1: HOME
# -----------------------------------------------------------------------------
if page == "Home":
    st.title("🎙️ VoxFlow — Speech Fluency Platform")
    st.markdown("Automated stuttering-event monitoring and temporal speech fluency analysis prototype.")

    st.markdown("""
    <div class="disclaimer-banner">
        ⚠️ <strong>Notice:</strong> VoxFlow is an engineering prototype designed for speech fluency monitoring and stuttering-event localization. 
        It is <strong>not a medical diagnostic system</strong> and does not provide clinical diagnoses.
    </div>
    """, unsafe_allow_html=True)

    # Session Upload & Run Section
    st.subheader("Analyze New Audio Session")
    uploaded_file = st.file_uploader("Upload Session Audio WAV (30–60 seconds)", type=["wav"])

    if uploaded_file is not None:
        if st.button("Start Complete Session Analysis", type="primary"):
            import uuid
            session_id = f"sess_{uuid.uuid4().hex[:10]}"
            audio_bytes = uploaded_file.read()
            
            with st.spinner("Processing session audio through VoxFlow sliding window engine..."):
                try:
                    audio, sr, duration_sec = validate_and_load_session_audio(audio_bytes)
                    
                    # Save WAV file
                    save_dir = SESSION_CONFIG['storage_dir'] / "audio"
                    os.makedirs(save_dir, exist_ok=True)
                    audio_path = save_dir / f"{session_id}.wav"
                    with open(audio_path, "wb") as f:
                        f.write(audio_bytes)

                    # Run Pipeline
                    windows = process_session_windows(session_id, audio, sr, duration_sec)
                    events = aggregate_window_events(session_id, windows)
                    summary = calculate_session_summary(
                        session_id=session_id,
                        duration_sec=duration_sec,
                        windows=windows,
                        events=events,
                        model_version=MODEL_CONFIG['version']
                    )

                    from datetime import datetime
                    save_session_record(
                        session_id=session_id,
                        user_id="user_default",
                        started_at=datetime.utcnow().isoformat(),
                        ended_at=datetime.utcnow().isoformat(),
                        duration=duration_sec,
                        audio_path=str(audio_path),
                        model_version=MODEL_CONFIG['version'],
                        status="ANALYZED"
                    )
                    save_session_analysis(session_id, windows, events, summary)
                    st.success(f"Session {session_id} successfully analyzed! ({len(windows)} windows, {len(events)} events aggregated)")
                    st.session_state['selected_session_id'] = session_id
                except AudioValidationError as e:
                    st.error(f"Audio Validation Error: {e}")
                except Exception as e:
                    st.error(f"Analysis Error: {e}")

    st.markdown("---")
    st.subheader("Latest Recorded Session")
    latest = get_latest_session()

    if not latest or not latest.get('summary'):
        st.info("No sessions available yet. Record or upload a session audio file to see analysis.")
    else:
        sm = latest['summary']
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown('<div class="vox-stat-label">Fluency Ratio</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="vox-stat-val" style="color: #2563EB;">{sm["fluency_ratio"]*100:.1f}%</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="vox-stat-label">Duration</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="vox-stat-val">{latest["duration"]:.1f}s</div>', unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="vox-stat-label">Total Disfluency Events</div>', unsafe_allow_html=True)
            tot_events = sm["repetition_events"] + sm["prolongation_events"] + sm["block_events"]
            st.markdown(f'<div class="vox-stat-val">{tot_events}</div>', unsafe_allow_html=True)
        with c4:
            st.markdown('<div class="vox-stat-label">Model Version</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="vox-stat-val" style="font-size: 20px;">{latest["model_version"]}</div>', unsafe_allow_html=True)

        st.caption(f"Session ID: `{latest['id']}` | Started: {latest['started_at']}")

# -----------------------------------------------------------------------------
# PAGE 2: CURRENT SESSION
# -----------------------------------------------------------------------------
elif page == "Current Session":
    st.title("📊 Current Session Analysis")
    sessions = get_all_sessions()
    
    if not sessions:
        st.info("No sessions available yet.")
    else:
        session_ids = [s['id'] for s in sessions if s.get('summary')]
        if not session_ids:
            st.info("No analyzed sessions available.")
        else:
            default_idx = 0
            if 'selected_session_id' in st.session_state and st.session_state['selected_session_id'] in session_ids:
                default_idx = session_ids.index(st.session_state['selected_session_id'])
                
            selected_id = st.selectbox("Select Session to View", session_ids, index=default_idx)
            s_data = get_session(selected_id)

            if s_data:
                sm = s_data.get('summary', {})
                st.markdown(f"### Session Overview: `{s_data['id']}`")
                st.caption(f"Recorded: {s_data['started_at']} | Model Version: `{s_data['model_version']}` | Duration: {s_data['duration']:.2f}s")

                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Fluency Ratio", f"{sm.get('fluency_ratio', 0)*100:.1f}%")
                c2.metric("Valid Windows", sm.get('valid_windows', 0))
                c3.metric("Repetitions", sm.get('repetition_events', 0))
                c4.metric("Prolongations", sm.get('prolongation_events', 0))
                c5.metric("Blocks", sm.get('block_events', 0))

                # Timeline Chart
                st.subheader("Temporal Event Timeline")
                events = s_data.get('events', [])
                if not events:
                    st.success("No stuttering events detected in this session — Speech was fluent throughout.")
                else:
                    timeline_df = []
                    color_map = {"Repetition": "#F59E0B", "Prolongation": "#8B5CF6", "Block": "#EF4444"}
                    for e in events:
                        timeline_df.append({
                            "Event": e['event_type'],
                            "Start (s)": e['start_time'],
                            "End (s)": e['end_time'],
                            "Duration (s)": round(e['end_time'] - e['start_time'], 2),
                            "Confidence": f"{e['confidence']*100:.1f}%",
                            "Supporting Windows": e['supporting_window_count']
                        })
                    t_df = pd.DataFrame(timeline_df)

                    fig = px.timeline(
                        t_df,
                        x_start="Start (s)",
                        x_end="End (s)",
                        y="Event",
                        color="Event",
                        color_discrete_map=color_map,
                        hover_data=["Confidence", "Supporting Windows", "Duration (s)"]
                    )
                    fig.update_layout(
                        xaxis_title="Time (Seconds)",
                        yaxis_title="Detected Event Type",
                        height=280,
                        margin=dict(l=20, r=20, t=30, b=20)
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    st.markdown("#### Aggregated Event Registry")
                    st.dataframe(t_df, use_container_width=True)

                # Window Predictions Table
                with st.expander("Show Detailed 3-Second Window Predictions"):
                    windows = s_data.get('windows', [])
                    if windows:
                        w_df = pd.DataFrame(windows)[[
                            'start_time', 'end_time', 'predicted_class', 'confidence',
                            'fluent_probability', 'repetition_probability',
                            'prolongation_probability', 'block_probability'
                        ]]
                        w_df.columns = [
                            'Start (s)', 'End (s)', 'Prediction', 'Confidence',
                            'P(Fluent)', 'P(Repetition)', 'P(Prolongation)', 'P(Block)'
                        ]
                        st.dataframe(w_df, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE 3: HISTORY
# -----------------------------------------------------------------------------
elif page == "History":
    st.title("📋 Session History")
    sessions = get_all_sessions()

    if not sessions:
        st.info("No recorded sessions in database.")
    else:
        rows = []
        for s in sessions:
            sm = s.get('summary') or {}
            rows.append({
                "Session ID": s['id'],
                "Date": s['started_at'],
                "Duration (s)": round(s['duration'] or 0, 1),
                "Fluency Ratio": f"{sm.get('fluency_ratio', 0)*100:.1f}%" if sm else "N/A",
                "Repetitions": sm.get('repetition_events', 0) if sm else 0,
                "Prolongations": sm.get('prolongation_events', 0) if sm else 0,
                "Blocks": sm.get('block_events', 0) if sm else 0,
                "Model Version": s['model_version'],
                "Status": s['status']
            })
        hist_df = pd.DataFrame(rows)
        st.dataframe(hist_df, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE 4: TRENDS
# -----------------------------------------------------------------------------
elif page == "Trends":
    st.title("📈 Fluency Monitoring Trends")
    st.markdown("""
    <div class="disclaimer-banner">
        ⚠️ <strong>Note:</strong> Trends are model-derived acoustic monitoring metrics across recorded sessions. 
        They do not represent clinical progression or medical conclusions.
    </div>
    """, unsafe_allow_html=True)

    sessions = get_all_sessions()
    analyzed_sessions = [s for s in sessions if s.get('summary')]

    if len(analyzed_sessions) < 2:
        st.info("At least two analyzed sessions are required to plot trend trajectories.")
    else:
        trend_data = []
        for s in reversed(analyzed_sessions): # chronological
            sm = s['summary']
            trend_data.append({
                "Date": s['started_at'],
                "Session": s['id'],
                "Fluency Ratio (%)": sm['fluency_ratio'] * 100.0,
                "Repetition Events": sm['repetition_events'],
                "Prolongation Events": sm['prolongation_events'],
                "Block Events": sm['block_events'],
                "Total Disfluencies": sm['repetition_events'] + sm['prolongation_events'] + sm['block_events']
            })
        tdf = pd.DataFrame(trend_data)

        # Fluency Ratio Chart
        fig_f = px.line(tdf, x="Session", y="Fluency Ratio (%)", markers=True, title="Fluency Ratio Trajectory Over Sessions")
        fig_f.update_layout(yaxis_range=[0, 105])
        st.plotly_chart(fig_f, use_container_width=True)

        # Disfluency Events Chart
        fig_e = px.bar(
            tdf, x="Session",
            y=["Repetition Events", "Prolongation Events", "Block Events"],
            title="Disfluency Events Distribution Across Sessions",
            barmode="stack",
            color_discrete_map={"Repetition Events": "#F59E0B", "Prolongation Events": "#8B5CF6", "Block Events": "#EF4444"}
        )
        st.plotly_chart(fig_e, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE 5: MODEL INFO
# -----------------------------------------------------------------------------
elif page == "Model Info":
    st.title("🤖 ML Model Specifications & Objective 1 Benchmarks")

    meta_file = MODEL_CONFIG['save_dir'] / "model_metadata.json"
    meta = {}
    if os.path.exists(meta_file):
        with open(meta_file, 'r') as f:
            meta = json.load(f)

    st.markdown(f"**Current Frozen Model:** `{meta.get('winning_architecture', 'CNN-GRU')}`")
    st.markdown(f"**Model Version:** `{meta.get('model_version', MODEL_CONFIG['version'])}`")
    st.markdown(f"**Primary Metric for Model Selection:** `Macro F1`")

    # Load experimental comparison table if available
    comp_csv = ROOT_DIR / "reports" / "experiments" / "model_comparison_table.csv"
    if os.path.exists(comp_csv):
        st.subheader("Candidate Models Validation Comparison (Objective 1)")
        st.caption("Measured on held-out speaker-independent validation set (Zero Speaker Leakage).")
        comp_df = pd.read_csv(comp_csv)
        st.dataframe(comp_df, use_container_width=True)
    else:
        st.info("Model comparison experiments currently running or table not yet generated.")

    st.subheader("Audio & Processing Configuration")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        - **Sample Rate:** 16,000 Hz (Mono)
        - **Window Length:** 3.0 seconds (48,000 samples)
        - **Sliding Step:** 1.0 second (16,000 samples)
        - **Feature Extraction:** Log-Mel Spectrogram (64 Mels, 512 FFT, 160 Hop)
        """)
    with col2:
        st.markdown("""
        - **Target Classes (4):** Fluent, Repetition, Prolongation, Block
        - **Label Consensus:** $\ge 2/3$ annotator agreement on SEP-28k
        - **Quality Filter:** Excluded poor audio, music, and multi-label conflicts
        - **Evaluation Protocol:** Held-out test set evaluated once after freezing
        """)

    st.subheader("Architectural Limitations")
    st.markdown("""
    1. **Window Resolution:** A 3.0-second window cannot provide millisecond-accurate boundary localization.
    2. **Acoustic Generalization:** Performance can vary with ambient noise and microphone frequency responses.
    3. **Non-Diagnostic:** Fluency ratio is an automated monitoring indicator, not a clinical severity score.
    """)

# -----------------------------------------------------------------------------
# PAGE 6: REPORTS
# -----------------------------------------------------------------------------
elif page == "Reports":
    st.title("📄 Clinical Speech Audit Report")
    sessions = get_all_sessions()
    analyzed_sessions = [s for s in sessions if s.get('summary')]

    if not analyzed_sessions:
        st.info("No analyzed sessions available for reporting.")
    else:
        s_ids = [s['id'] for s in analyzed_sessions]
        chosen_id = st.selectbox("Select Session for Audit Report", s_ids)
        s_data = get_session(chosen_id)
        sm = s_data['summary']

        st.markdown("---")
        st.markdown(f"## VOXFLOW SPEECH FLUENCY AUDIT — `{chosen_id}`")
        st.markdown(f"**Date:** {s_data['started_at']} | **Engine:** `{s_data['model_version']}` | **Duration:** {s_data['duration']:.2f}s")
        st.markdown(f"**Fluency Ratio:** **{sm['fluency_ratio']*100:.1f}%** (Fluent Windows: {sm['fluent_windows']} / Valid Windows: {sm['valid_windows']})")
        st.markdown(f"**Detected Events:** Repetitions: {sm['repetition_events']} | Prolongations: {sm['prolongation_events']} | Blocks: {sm['block_events']}")

        st.markdown("### Aggregated Events List")
        events = s_data.get('events', [])
        if events:
            ev_df = pd.DataFrame(events)[['event_type', 'start_time', 'end_time', 'confidence', 'supporting_window_count']]
            ev_df.columns = ['Type', 'Start (s)', 'End (s)', 'Confidence', 'Supporting Windows']
            st.dataframe(ev_df, use_container_width=True)
        else:
            st.write("No stuttering events detected.")

        st.markdown("""
        ---
        **Audit Disclaimer:** This document contains automated machine learning inferences generated by VoxFlow prototype. 
        It is intended solely for research and fluency monitoring. It must not be interpreted as a clinical medical assessment.
        """)
