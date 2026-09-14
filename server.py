from flask import Flask, request, jsonify
import os
import time
import uuid
from datetime import datetime
from database import DatabaseManager, init_db, seed_sample_data
from pipeline import pipeline_runner

# Initialize Database on Server Start
init_db()
seed_sample_data()

app = Flask(__name__)
db = DatabaseManager()
UPLOAD_DIR = r"c:\Users\amare\Downloads\TARP\audio_buffer"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected",
        "pipeline": "ready"
    }), 200

@app.route('/api/v1/audio/upload', methods=['POST'])
def handle_audio_upload():
    user_id = int(request.form.get('user_id', 1))
    audio_bytes = None
    
    if 'audio' in request.files:
        file = request.files['audio']
        if file.filename != '':
            audio_bytes = file.read()
    elif request.data:
        audio_bytes = request.data

    if not audio_bytes:
        return jsonify({'status': 'error', 'message': 'Missing audio file in upload payload'}), 400

    filename = f"audio_{int(time.time())}_{uuid.uuid4().hex[:6]}.wav"
    filepath = os.path.join(UPLOAD_DIR, filename)
    try:
        with open(filepath, 'wb') as f:
            f.write(audio_bytes)
    except Exception:
        pass

    # Trigger software audio chunk accumulator & processing pipeline
    result = pipeline_runner.process_chunk(audio_bytes, user_id=user_id, session_id=f"user_{user_id}")
    
    if result.get("status") == "rejected":
        return jsonify({
            'status': 'rejected',
            'message': 'Speaker verification match failed',
            'display_message': 'Speaker Mismatch'
        }), 403

    # Save completed prediction to SQLite Database if analyzed
    pred_id = None
    if result.get("status") == "analyzed":
        pred_id = db.save_prediction(
            user_id=user_id,
            fluency_score=result['fluency_score'],
            stutter_type=result['stutter_type'],
            confidence=result['confidence'],
            audio_path=filepath
        )

    response_data = {
        'status': 'success',
        'pipeline_status': result.get('status', 'analyzed'),
        'prediction_id': pred_id,
        'timestamp': datetime.now().isoformat(),
        'user_id': user_id,
        'fluency_score': result['fluency_score'],
        'stutter_detected': result['is_disfluent'],
        'stutter_type': result['stutter_type'],
        'confidence': result['confidence'],
        'buffer_sec': result.get('buffer_sec', 2.5),
        'display_message': result.get('display_message', f"Fluency: {result['fluency_score']:.1f}% ({result['stutter_type']})")
    }
    return jsonify(response_data), 200

@app.route('/api/v1/predictions/<int:user_id>', methods=['GET'])
def get_user_predictions(user_id):
    records = db.fetch_user_predictions(user_id)
    return jsonify({
        "status": "success",
        "user_id": user_id,
        "count": len(records),
        "predictions": records
    }), 200

@app.route('/api/v1/session/latest', methods=['GET'])
def get_latest_session():
    user_id = int(request.args.get('user_id', 1))
    records = db.fetch_user_predictions(user_id)
    if not records:
        return jsonify({"status": "error", "message": "No sessions found"}), 404
    latest = records[0]
    return jsonify({
        "status": "success",
        "latest_prediction": latest
    }), 200

if __name__ == '__main__':
    print("Starting VoxFlow Flask REST Backend Server on http://localhost:5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)
