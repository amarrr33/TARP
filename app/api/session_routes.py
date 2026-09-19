import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify

from configs.config import API_CONFIG, SESSION_CONFIG, MODEL_CONFIG
from app.db.database import (
    save_session_record,
    save_session_analysis,
    get_session,
    get_latest_session,
    get_all_sessions
)
from app.services.session_engine import (
    validate_and_load_session_audio,
    process_session_windows,
    AudioValidationError
)
from app.services.event_aggregator import aggregate_window_events
from app.services.session_summary import calculate_session_summary

session_bp = Blueprint('session_bp', __name__, url_prefix='/api/v1')

# In-memory session tracking for active lifecycle transitions
ACTIVE_SESSIONS = {}

@session_bp.route('/session/start', methods=['POST'])
def start_session():
    data = request.get_json() or {}
    user_id = data.get('user_id', 'user_default')
    session_id = f"sess_{uuid.uuid4().hex[:10]}"
    started_at = datetime.utcnow().isoformat()

    ACTIVE_SESSIONS[session_id] = {
        "user_id": user_id,
        "started_at": started_at,
        "ended_at": None,
        "status": "STARTED",
        "audio_chunks": bytearray(),
        "audio_path": None,
        "duration": 0.0
    }

    save_session_record(
        session_id=session_id,
        user_id=user_id,
        started_at=started_at,
        ended_at=None,
        duration=0.0,
        audio_path="",
        model_version=MODEL_CONFIG['version'],
        status="STARTED"
    )

    return jsonify({
        "status": "success",
        "message": "Session started successfully",
        "session_id": session_id,
        "started_at": started_at
    }), 201

@session_bp.route('/session/<session_id>/audio', methods=['POST'])
def upload_session_audio(session_id):
    if session_id not in ACTIVE_SESSIONS:
        # Check if exists in DB
        db_s = get_session(session_id)
        if not db_s:
            return jsonify({"status": "error", "message": f"Session '{session_id}' not found"}), 404
        ACTIVE_SESSIONS[session_id] = {
            "user_id": db_s['user_id'],
            "started_at": db_s['started_at'],
            "ended_at": db_s['ended_at'],
            "status": db_s['status'],
            "audio_chunks": bytearray(),
            "audio_path": db_s['audio_path'],
            "duration": db_s['duration'] or 0.0
        }

    session = ACTIVE_SESSIONS[session_id]
    if session['status'] in ['ANALYZED']:
        return jsonify({"status": "error", "message": f"Session '{session_id}' is already finalized"}), 400

    # Accept raw bytes or multipart form file
    if 'audio' in request.files:
        audio_bytes = request.files['audio'].read()
    else:
        audio_bytes = request.get_data()

    if not audio_bytes:
        return jsonify({"status": "error", "message": "No audio payload provided"}), 400

    session['audio_chunks'].extend(audio_bytes)
    return jsonify({
        "status": "success",
        "message": f"Received {len(audio_bytes)} bytes",
        "total_buffer_bytes": len(session['audio_chunks'])
    }), 200

@session_bp.route('/session/<session_id>/stop', methods=['POST'])
def stop_session(session_id):
    if session_id not in ACTIVE_SESSIONS:
        db_s = get_session(session_id)
        if not db_s:
            return jsonify({"status": "error", "message": f"Session '{session_id}' not found"}), 404
        return jsonify({"status": "success", "message": "Session already stopped", "session_id": session_id}), 200

    session = ACTIVE_SESSIONS[session_id]
    session['ended_at'] = datetime.utcnow().isoformat()
    session['status'] = "STOPPED"

    # Save audio buffer to disk
    audio_dir = SESSION_CONFIG['storage_dir'] / "audio"
    os.makedirs(audio_dir, exist_ok=True)
    audio_file_path = audio_dir / f"{session_id}.wav"

    with open(audio_file_path, 'wb') as f:
        f.write(session['audio_chunks'])

    session['audio_path'] = str(audio_file_path)

    save_session_record(
        session_id=session_id,
        user_id=session['user_id'],
        started_at=session['started_at'],
        ended_at=session['ended_at'],
        duration=session['duration'],
        audio_path=str(audio_file_path),
        model_version=MODEL_CONFIG['version'],
        status="STOPPED"
    )

    return jsonify({
        "status": "success",
        "message": "Session stopped successfully",
        "session_id": session_id,
        "ended_at": session['ended_at'],
        "audio_file": str(audio_file_path)
    }), 200

@session_bp.route('/session/<session_id>/analyze', methods=['POST'])
def analyze_session(session_id):
    db_session = get_session(session_id)
    if not db_session:
        return jsonify({"status": "error", "message": f"Session '{session_id}' not found"}), 404

    audio_path = db_session['audio_path']
    if not audio_path or not os.path.exists(audio_path):
        # Check active session buffer
        if session_id in ACTIVE_SESSIONS and len(ACTIVE_SESSIONS[session_id]['audio_chunks']) > 0:
            audio_dir = SESSION_CONFIG['storage_dir'] / "audio"
            os.makedirs(audio_dir, exist_ok=True)
            audio_path = str(audio_dir / f"{session_id}.wav")
            with open(audio_path, 'wb') as f:
                f.write(ACTIVE_SESSIONS[session_id]['audio_chunks'])
        else:
            return jsonify({"status": "error", "message": "Session audio file missing or not uploaded"}), 400

    try:
        audio, sr, duration_sec = validate_and_load_session_audio(audio_path)
    except AudioValidationError as e:
        return jsonify({"status": "error", "type": "AudioValidationError", "message": str(e)}), 422
    except Exception as e:
        return jsonify({"status": "error", "type": "AudioProcessingError", "message": str(e)}), 500

    try:
        # 1. Sliding 3s window processing
        windows = process_session_windows(session_id, audio, sr, duration_sec)

        # 2. Temporal event aggregation
        events = aggregate_window_events(session_id, windows)

        # 3. Deterministic session summary calculation
        summary = calculate_session_summary(
            session_id=session_id,
            duration_sec=duration_sec,
            windows=windows,
            events=events,
            model_version=MODEL_CONFIG['version']
        )

        # 4. Save to SQLite database
        save_session_record(
            session_id=session_id,
            user_id=db_session['user_id'],
            started_at=db_session['started_at'],
            ended_at=db_session['ended_at'] or datetime.utcnow().isoformat(),
            duration=duration_sec,
            audio_path=audio_path,
            model_version=MODEL_CONFIG['version'],
            status="ANALYZED"
        )
        save_session_analysis(session_id, windows, events, summary)

        if session_id in ACTIVE_SESSIONS:
            ACTIVE_SESSIONS[session_id]['status'] = "ANALYZED"

        return jsonify({
            "status": "success",
            "message": "Session analysis completed",
            "session_id": session_id,
            "duration": duration_sec,
            "summary": summary,
            "event_count": len(events),
            "window_count": len(windows)
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "type": "AnalysisFailure", "message": str(e)}), 500

@session_bp.route('/session/<session_id>', methods=['GET'])
def get_session_details(session_id):
    session = get_session(session_id)
    if not session:
        return jsonify({"status": "error", "message": f"Session '{session_id}' not found"}), 404
    return jsonify({"status": "success", "session": session}), 200

@session_bp.route('/sessions/<user_id>', methods=['GET'])
def get_user_sessions(user_id):
    sessions = get_all_sessions(user_id=user_id)
    return jsonify({"status": "success", "sessions": sessions, "count": len(sessions)}), 200

@session_bp.route('/session/latest', methods=['GET'])
def get_latest():
    session = get_latest_session()
    if not session:
        return jsonify({"status": "empty", "message": "No analyzed sessions found"}), 200
    return jsonify({"status": "success", "session": session}), 200

@session_bp.route('/model/info', methods=['GET'])
def get_model_info():
    meta_path = MODEL_CONFIG['save_dir'] / "model_metadata.json"
    import json
    if os.path.exists(meta_path):
        with open(meta_path, 'r') as f:
            meta = json.load(f)
    else:
        meta = {
            "model_version": MODEL_CONFIG['version'],
            "status": "Pending training or loaded default"
        }
    return jsonify({
        "status": "success",
        "model_info": meta
    }), 200
