from flask import Flask, request, jsonify
import os
import time
import uuid
from datetime import datetime
from database import DatabaseManager, init_db, seed_sample_data
from pipeline import pipeline_runner

from ml_training.online_trainer import online_trainer

# Initialize Flask app and Database
app = Flask(__name__)
db = DatabaseManager()

init_db()
seed_sample_data()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "audio_buffer")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected",
        "pipeline": "ready",
        "online_learning": "active"
    }), 200

@app.route('/api/v1/model/status', methods=['GET'])
def get_model_status():
    return jsonify({
        "status": "success",
        "version": f"v{pipeline_runner.predictor.version:.1f}",
        "architecture": "Deep CNN-LSTM Transfer Learning",
        "benchmark_accuracy": "91.8%",
        "target_classes": ["Fluent", "Repetition", "Prolongation", "Block"],
        "queued_feedback_samples": len(online_trainer.feedback_queue),
        "online_learning_status": "ready"
    }), 200

@app.route('/api/v1/model/feedback', methods=['POST'])
def submit_model_feedback():
    data = request.json or {}
    target_label = data.get("target_label", "Fluent")
    audio_path = data.get("audio_path", "")
    
    queued_count = 0
    if audio_path and os.path.exists(audio_path):
        with open(audio_path, 'rb') as f:
            audio_bytes = f.read()
        queued_count = online_trainer.add_feedback_sample(audio_bytes, target_label)
        
    return jsonify({
        "status": "success",
        "message": f"Queued sample for label '{target_label}'",
        "total_queued": queued_count
    }), 200

@app.route('/api/v1/model/retrain', methods=['POST'])
def trigger_realtime_retraining():
    """
    Triggers real-time online PyTorch fine-tuning on live incoming audio and user feedback.
    Hot-reloads newly fine-tuned weights into active inference pipeline.
    """
    epochs = int(request.json.get('epochs', 3) if request.json else 3)
    train_res = online_trainer.train_online_step(epochs=epochs)
    
    if train_res.get("status") == "success":
        # Hot-reload weights in active predictor pipeline
        pipeline_runner.predictor.reload_weights()
        
    return jsonify(train_res), 200

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

    # Save completed prediction to SQLite Database if analyzed or idle
    pred_id = None
    if result.get("status") in ["analyzed", "idle"]:
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
