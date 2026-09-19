import os
import sys
import pathlib

ROOT_DIR = pathlib.Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from flask import Flask, jsonify
from configs.config import API_CONFIG, MODEL_CONFIG
from app.db.database import init_db
from app.api.session_routes import session_bp

app = Flask(__name__)
app.register_blueprint(session_bp)

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "VoxFlow Session API",
        "model_version": MODEL_CONFIG['version'],
        "storage": "SQLite + Local Audio Vault"
    }), 200

# Initialize schema on launch
init_db()

if __name__ == '__main__':
    print("=" * 60)
    print(f"VoxFlow Production Server starting on {API_CONFIG['host']}:{API_CONFIG['port']}")
    print(f"Model Version: {MODEL_CONFIG['version']}")
    print("=" * 60)
    app.run(host=API_CONFIG['host'], port=API_CONFIG['port'], debug=False)
