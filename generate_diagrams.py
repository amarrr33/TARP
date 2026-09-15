import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(BASE_DIR, "diagrams")
os.makedirs(output_dir, exist_ok=True)

# Set global style parameters
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.dpi'] = 300

# Palette
NAVY = '#1A365D'
BLUE = '#2B6CB0'
LIGHT_BLUE = '#EBF8FF'
TEAL = '#319795'
GRAY = '#4A5568'
LIGHT_GRAY = '#F7FAFC'
BORDER_GRAY = '#CBD5E0'
GREEN = '#38A169'
AMBER = '#D69E2E'

# 1. Flowchart Diagram
def generate_flowchart():
    fig, ax = plt.subplots(figsize=(8, 11))
    ax.axis('off')
    
    steps = [
        ("1. Receive Audio Stream", "HTTP POST payload from ESP32 over Wi-Fi", LIGHT_BLUE, BLUE),
        ("2. Save Raw Audio File", "Temporary buffer storage & format validation", LIGHT_GRAY, GRAY),
        ("3. Preprocessing & Noise Removal", "Spectral gating & bandpass filtering", LIGHT_BLUE, TEAL),
        ("4. Speaker Verification", "MFCC embedding cosine similarity match", LIGHT_BLUE, TEAL),
        ("5. Feature Extraction", "13-MFCCs, Deltas, Spectral Centroid", LIGHT_BLUE, TEAL),
        ("6. AI Model Prediction", "Inference via trained CNN-LSTM pipeline", LIGHT_BLUE, BLUE),
        ("7. SQLite DB Storage", "Persist session, disfluency score & timestamp", LIGHT_GRAY, NAVY),
        ("8. Dashboard Live Update", "Streamlit UI query refresh & visualization", LIGHT_BLUE, GREEN),
        ("9. ESP32 Feedback Response", "JSON response with LED status & disfluency %", LIGHT_GRAY, AMBER)
    ]
    
    y = 0.95
    box_height = 0.075
    box_width = 0.8
    x = 0.1
    
    for i, (title, sub, bg, border) in enumerate(steps):
        rect = patches.FancyBboxPatch(
            (x, y - box_height), box_width, box_height,
            boxstyle="round,pad=0.02,rounding_size=0.02",
            ec=border, fc=bg, lw=2
        )
        ax.add_patch(rect)
        ax.text(x + box_width/2, y - 0.025, title, ha='center', va='center', fontsize=11, fontweight='bold', color=NAVY)
        ax.text(x + box_width/2, y - 0.055, sub, ha='center', va='center', fontsize=8.5, color=GRAY, fontstyle='italic')
        
        if i < len(steps) - 1:
            ax.annotate('', xy=(x + box_width/2, y - box_height - 0.035),
                        xytext=(x + box_width/2, y - box_height - 0.005),
                        arrowprops=dict(arrowstyle="->", color=BLUE, lw=2))
        y -= (box_height + 0.04)
        
    ax.set_title("VoxFlow - Software Processing Flowchart", fontsize=14, fontweight='bold', color=NAVY, pad=20)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "flowchart.png"), bbox_inches='tight')
    plt.close()

# 2. Software Architecture Diagram
def generate_architecture():
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.axis('off')
    
    layers = [
        ("Edge Hardware Layer", ["ESP32 Device", "INMP441 Microphone", "OLED & LED Feedback"], '#FEFCBF', '#D69E2E', 0.82),
        ("API Ingestion Layer", ["Flask REST Server", "HTTP Upload Handler", "Audio Validator"], '#EBF8FF', '#2B6CB0', 0.63),
        ("Audio & AI Core Layer", ["Noise Removal", "Speaker Verifier", "MFCC Extractor", "CNN-LSTM Engine"], '#E6FFFA', '#319795', 0.44),
        ("Persistence Layer", ["SQLite Local DB", "Sync Engine (Future)", "File System Buffer"], '#EDF2F7', '#4A5568', 0.25),
        ("Presentation Layer", ["Streamlit Dashboard", "Analytics & Reports", "Export Module"], '#F0FFF4', '#38A169', 0.06)
    ]
    
    for layer_name, comps, bg, border, y in layers:
        rect = patches.FancyBboxPatch(
            (0.05, y), 0.9, 0.13,
            boxstyle="round,pad=0.01,rounding_size=0.015",
            ec=border, fc=bg, lw=2
        )
        ax.add_patch(rect)
        ax.text(0.08, y + 0.095, layer_name, fontsize=10, fontweight='bold', color=NAVY)
        
        n = len(comps)
        for idx, comp in enumerate(comps):
            cx = 0.28 + idx * (0.64 / n)
            cw = (0.62 / n) - 0.02
            crect = patches.FancyBboxPatch(
                (cx, y + 0.02), cw, 0.06,
                boxstyle="round,pad=0.01,rounding_size=0.01",
                ec=border, fc='white', lw=1
            )
            ax.add_patch(crect)
            ax.text(cx + cw/2, y + 0.05, comp, ha='center', va='center', fontsize=8.5, fontweight='bold', color=GRAY)
            
    # Connectors
    for i in range(len(layers) - 1):
        y_top = layers[i][4]
        ax.annotate('', xy=(0.5, y_top - 0.03), xytext=(0.5, y_top),
                    arrowprops=dict(arrowstyle="->", color=NAVY, lw=2))

    ax.set_title("VoxFlow - Tiered Software Architecture", fontsize=14, fontweight='bold', color=NAVY, pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "architecture.png"), bbox_inches='tight')
    plt.close()

# 3. Database ER Diagram
def generate_er_diagram():
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.axis('off')
    
    tables = [
        ("USERS", ["user_id (PK)", "name", "age", "therapist_id", "baseline_embedding", "created_at"], 0.1, 0.55),
        ("SESSIONS", ["session_id (PK)", "user_id (FK)", "session_name", "start_time", "end_time", "total_audio_length"], 0.55, 0.55),
        ("PREDICTIONS", ["pred_id (PK)", "session_id (FK)", "timestamp", "fluency_score", "stutter_type", "confidence"], 0.1, 0.05),
        ("REPORTS", ["report_id (PK)", "session_id (FK)", "user_id (FK)", "generated_at", "summary_notes", "pdf_path"], 0.55, 0.05)
    ]
    
    for tname, cols, x, y in tables:
        # Table Header
        hrect = patches.Rectangle((x, y + 0.3), 0.35, 0.06, fc=NAVY, ec=NAVY)
        ax.add_patch(hrect)
        ax.text(x + 0.175, y + 0.33, tname, ha='center', va='center', fontsize=10, fontweight='bold', color='white')
        
        # Table Body
        brect = patches.Rectangle((x, y), 0.35, 0.3, fc='#F7FAFC', ec=NAVY, lw=1.5)
        ax.add_patch(brect)
        for idx, col in enumerate(cols):
            fw = 'bold' if '(PK)' in col or '(FK)' in col else 'normal'
            clr = BLUE if '(PK)' in col else (TEAL if '(FK)' in col else GRAY)
            ax.text(x + 0.02, y + 0.25 - idx*0.045, col, fontsize=8.5, fontweight=fw, color=clr)
            
    # Relationships
    ax.annotate('1 : N', xy=(0.55, 0.7), xytext=(0.45, 0.7),
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.5), fontsize=8, fontweight='bold', color=BLUE)
    ax.annotate('1 : N', xy=(0.275, 0.35), xytext=(0.275, 0.55),
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.5), fontsize=8, fontweight='bold', color=BLUE)
    ax.annotate('1 : 1', xy=(0.725, 0.35), xytext=(0.725, 0.55),
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.5), fontsize=8, fontweight='bold', color=BLUE)
    
    ax.set_title("VoxFlow - SQLite Relational Entity-Relationship (ER) Diagram", fontsize=13, fontweight='bold', color=NAVY, pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "er_diagram.png"), bbox_inches='tight')
    plt.close()

# 4. Class Diagram
def generate_class_diagram():
    fig, ax = plt.subplots(figsize=(10, 7.5))
    ax.axis('off')
    
    classes = [
        ("AudioReceiver", ["+ save_audio(stream): str", "+ validate_format(file): bool"], 0.05, 0.65),
        ("NoiseFilter", ["+ denoise(audio_path): np.ndarray", "+ compute_snr(): float"], 0.38, 0.65),
        ("SpeakerVerifier", ["+ verify(audio, user_id): bool", "+ extract_embedding(): np.ndarray"], 0.70, 0.65),
        ("FeatureExtractor", ["+ extract_mfcc(audio): np.ndarray", "+ normalize(): np.ndarray"], 0.05, 0.15),
        ("FluencyPredictor", ["+ predict(features): Dict", "+ load_model(path): void"], 0.38, 0.15),
        ("DatabaseManager", ["+ save_prediction(data): int", "+ fetch_history(user): List"], 0.70, 0.15)
    ]
    
    for cname, methods, x, y in classes:
        hrect = patches.Rectangle((x, y + 0.2), 0.26, 0.05, fc=BLUE, ec=BLUE)
        ax.add_patch(hrect)
        ax.text(x + 0.13, y + 0.225, cname, ha='center', va='center', fontsize=9.5, fontweight='bold', color='white')
        
        brect = patches.Rectangle((x, y), 0.26, 0.2, fc='#EDF2F7', ec=NAVY, lw=1.5)
        ax.add_patch(brect)
        for idx, m in enumerate(methods):
            ax.text(x + 0.015, y + 0.15 - idx*0.06, m, fontsize=7.5, color=NAVY)

    # Connections
    ax.annotate('', xy=(0.38, 0.75), xytext=(0.31, 0.75), arrowprops=dict(arrowstyle="->", color=GRAY, lw=1.5))
    ax.annotate('', xy=(0.70, 0.75), xytext=(0.64, 0.75), arrowprops=dict(arrowstyle="->", color=GRAY, lw=1.5))
    ax.annotate('', xy=(0.18, 0.35), xytext=(0.18, 0.65), arrowprops=dict(arrowstyle="->", color=GRAY, lw=1.5))
    ax.annotate('', xy=(0.51, 0.35), xytext=(0.51, 0.65), arrowprops=dict(arrowstyle="->", color=GRAY, lw=1.5))
    ax.annotate('', xy=(0.70, 0.25), xytext=(0.64, 0.25), arrowprops=dict(arrowstyle="->", color=GRAY, lw=1.5))

    ax.set_title("VoxFlow - UML Class Diagram", fontsize=13, fontweight='bold', color=NAVY, pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "class_diagram.png"), bbox_inches='tight')
    plt.close()

# 5. Sequence Diagram
def generate_sequence_diagram():
    fig, ax = plt.subplots(figsize=(10, 7.5))
    ax.axis('off')
    
    lifelines = ["ESP32", "Flask API", "Pipeline", "CNN-LSTM", "SQLite DB", "Streamlit UI"]
    xs = np.linspace(0.08, 0.92, len(lifelines))
    
    for i, line in enumerate(lifelines):
        ax.text(xs[i], 0.92, line, ha='center', va='center', fontsize=9.5, fontweight='bold', color='white',
                bbox=dict(boxstyle="round,pad=0.4", fc=NAVY, ec=NAVY))
        ax.plot([xs[i], xs[i]], [0.08, 0.86], linestyle='--', color=GRAY, lw=1)
        
    messages = [
        (0, 1, "1. HTTP POST Audio Stream", 0.80),
        (1, 2, "2. Trigger Processing(audio_file)", 0.72),
        (2, 3, "3. Forward MFCC Features", 0.64),
        (3, 2, "4. Return Fluency Prediction", 0.56),
        (2, 4, "5. INSERT Prediction Record", 0.48),
        (1, 0, "6. HTTP 200 OK (Score + Status)", 0.40),
        (5, 4, "7. SELECT Recent Sessions", 0.30),
        (4, 5, "8. Return Session Dataset", 0.22),
        (5, 5, "9. Render Analytics & Charts", 0.14)
    ]
    
    for src, dst, label, y in messages:
        x1, x2 = xs[src], xs[dst]
        ls = '-' if src <= dst else '--'
        ax.annotate('', xy=(x2, y), xytext=(x1, y),
                    arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.5, ls=ls))
        mid_x = (x1 + x2) / 2
        ax.text(mid_x, y + 0.02, label, ha='center', va='bottom', fontsize=7.5, fontweight='bold', color=NAVY)

    ax.set_title("VoxFlow - UML Sequence Diagram", fontsize=13, fontweight='bold', color=NAVY, pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "sequence_diagram.png"), bbox_inches='tight')
    plt.close()

# 6. Activity Diagram
def generate_activity_diagram():
    fig, ax = plt.subplots(figsize=(8, 10))
    ax.axis('off')
    
    nodes = [
        ("Start", "oval", LIGHT_BLUE, BLUE, 0.92),
        ("Receive Audio Stream", "rect", LIGHT_GRAY, GRAY, 0.82),
        ("Noise Filtering & Denoising", "rect", LIGHT_BLUE, TEAL, 0.72),
        ("Verify Speaker Match?", "diamond", '#FEFCBF', AMBER, 0.60),
        ("Extract 13-MFCC Features", "rect", LIGHT_BLUE, TEAL, 0.46),
        ("CNN-LSTM Inference", "rect", LIGHT_BLUE, BLUE, 0.36),
        ("Store Prediction in SQLite", "rect", LIGHT_GRAY, NAVY, 0.26),
        ("Refresh Streamlit Dashboard", "rect", LIGHT_BLUE, GREEN, 0.16),
        ("End Session Cycle", "oval", LIGHT_BLUE, BLUE, 0.06)
    ]
    
    for text, shape, bg, border, y in nodes:
        if shape == "oval":
            rect = patches.FancyBboxPatch((0.3, y), 0.4, 0.05, boxstyle="circle,pad=0.01", ec=border, fc=bg, lw=2)
            ax.add_patch(rect)
            ax.text(0.5, y + 0.025, text, ha='center', va='center', fontsize=9.5, fontweight='bold', color=NAVY)
        elif shape == "rect":
            rect = patches.FancyBboxPatch((0.2, y), 0.6, 0.05, boxstyle="round,pad=0.01,rounding_size=0.015", ec=border, fc=bg, lw=2)
            ax.add_patch(rect)
            ax.text(0.5, y + 0.025, text, ha='center', va='center', fontsize=9, fontweight='bold', color=NAVY)
        elif shape == "diamond":
            poly = patches.Polygon([[0.5, y+0.07], [0.75, y+0.035], [0.5, y], [0.25, y+0.035]], ec=border, fc=bg, lw=2)
            ax.add_patch(poly)
            ax.text(0.5, y + 0.035, text, ha='center', va='center', fontsize=8.5, fontweight='bold', color=NAVY)

    # Connections
    ax.annotate('', xy=(0.5, 0.87), xytext=(0.5, 0.92), arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.5))
    ax.annotate('', xy=(0.5, 0.77), xytext=(0.5, 0.82), arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.5))
    ax.annotate('', xy=(0.5, 0.67), xytext=(0.5, 0.72), arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.5))
    ax.annotate('Yes', xy=(0.5, 0.51), xytext=(0.5, 0.60), arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.5), fontsize=8.5, fontweight='bold', color=GREEN)
    ax.annotate('No (Reject)', xy=(0.85, 0.635), xytext=(0.75, 0.635), arrowprops=dict(arrowstyle="->", color='red', lw=1.5), fontsize=8, fontweight='bold', color='red')
    ax.annotate('', xy=(0.5, 0.41), xytext=(0.5, 0.46), arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.5))
    ax.annotate('', xy=(0.5, 0.31), xytext=(0.5, 0.36), arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.5))
    ax.annotate('', xy=(0.5, 0.21), xytext=(0.5, 0.26), arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.5))
    ax.annotate('', xy=(0.5, 0.11), xytext=(0.5, 0.16), arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.5))

    ax.set_title("VoxFlow - UML Activity Diagram", fontsize=13, fontweight='bold', color=NAVY, pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "activity_diagram.png"), bbox_inches='tight')
    plt.close()

# 7. Communication Diagram
def generate_communication_diagram():
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.axis('off')
    
    nodes = {
        "ESP32": (0.15, 0.75),
        "FlaskAPI": (0.50, 0.75),
        "Pipeline": (0.85, 0.75),
        "Model": (0.85, 0.25),
        "SQLiteDB": (0.50, 0.25),
        "Streamlit": (0.15, 0.25)
    }
    
    for name, (x, y) in nodes.items():
        rect = patches.FancyBboxPatch((x-0.1, y-0.05), 0.2, 0.1, boxstyle="round,pad=0.01", ec=NAVY, fc=LIGHT_BLUE, lw=2)
        ax.add_patch(rect)
        ax.text(x, y, name, ha='center', va='center', fontsize=9.5, fontweight='bold', color=NAVY)
        
    edges = [
        ("ESP32", "FlaskAPI", "1: postAudio()\n6: returnResult()"),
        ("FlaskAPI", "Pipeline", "2: processAudio()"),
        ("Pipeline", "Model", "3: predictFluency()"),
        ("Pipeline", "SQLiteDB", "4: savePrediction()"),
        ("Streamlit", "SQLiteDB", "5: queryHistory()")
    ]
    
    for n1, n2, label in edges:
        x1, y1 = nodes[n1]
        x2, y2 = nodes[n2]
        ax.plot([x1, x2], [y1, y2], color=BLUE, lw=1.5, linestyle='--')
        mx, my = (x1 + x2)/2, (y1 + y2)/2
        ax.text(mx, my, label, ha='center', va='center', fontsize=8, fontweight='bold', color=NAVY,
                bbox=dict(boxstyle="round,pad=0.2", fc='white', ec=BORDER_GRAY))

    ax.set_title("VoxFlow - UML Communication Diagram", fontsize=13, fontweight='bold', color=NAVY, pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "communication_diagram.png"), bbox_inches='tight')
    plt.close()

# 8. Dashboard Wireframe
def generate_dashboard_wireframe():
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.axis('off')
    
    # Outer frame
    frame = patches.Rectangle((0.02, 0.02), 0.96, 0.94, fc='#F7FAFC', ec=NAVY, lw=2)
    ax.add_patch(frame)
    
    # Header bar
    header = patches.Rectangle((0.02, 0.86), 0.96, 0.10, fc=NAVY, ec=NAVY)
    ax.add_patch(header)
    ax.text(0.05, 0.91, "VoxFlow Analytics Dashboard", fontsize=14, fontweight='bold', color='white')
    ax.text(0.70, 0.91, "Patient: John Doe | ID: USR-102 | Live Monitor", fontsize=9, color='#CBD5E0')
    
    # Metric cards
    metrics = [
        ("Current Fluency Score", "84.2%", "Normal / Mild", GREEN, 0.05),
        ("Today's Disfluencies", "12 Blocks", "8 Stutters, 4 Reps", AMBER, 0.36),
        ("Weekly Progress", "+6.5%", "Improved Stability", BLUE, 0.67)
    ]
    for title, val, sub, color, x in metrics:
        card = patches.FancyBboxPatch((x, 0.67), 0.28, 0.16, boxstyle="round,pad=0.01", ec=BORDER_GRAY, fc='white', lw=1.5)
        ax.add_patch(card)
        ax.text(x + 0.02, 0.79, title, fontsize=8.5, fontweight='bold', color=GRAY)
        ax.text(x + 0.02, 0.73, val, fontsize=16, fontweight='bold', color=color)
        ax.text(x + 0.02, 0.69, sub, fontsize=7.5, color=GRAY)

    # Main Chart Panel (Left)
    chart_box = patches.FancyBboxPatch((0.05, 0.22), 0.59, 0.41, boxstyle="round,pad=0.01", ec=BORDER_GRAY, fc='white', lw=1.5)
    ax.add_patch(chart_box)
    ax.text(0.07, 0.59, "Speech Fluency Trend (Weekly & Monthly)", fontsize=10, fontweight='bold', color=NAVY)
    
    # Simulated Trendline
    t = np.linspace(0.08, 0.61, 30)
    y_val = 0.32 + 0.12 * np.sin(np.linspace(0, 5, 30)) + 0.04 * np.random.randn(30)
    ax.plot(t, y_val, color=BLUE, lw=2.5)
    ax.fill_between(t, 0.24, y_val, color=LIGHT_BLUE, alpha=0.5)
    
    # Side Panel (Right - Recent Sessions & Download)
    side_box = patches.FancyBboxPatch((0.67, 0.22), 0.28, 0.41, boxstyle="round,pad=0.01", ec=BORDER_GRAY, fc='white', lw=1.5)
    ax.add_patch(side_box)
    ax.text(0.69, 0.59, "Recent Sessions & Export", fontsize=10, fontweight='bold', color=NAVY)
    
    table_headers = ["Date", "Score", "Status"]
    for idx, th in enumerate(table_headers):
        ax.text(0.69 + idx*0.09, 0.53, th, fontsize=8, fontweight='bold', color=GRAY)
        
    rows = [("08/05 10:15", "84.2%", "Mild"), ("08/04 16:30", "78.0%", "Moderate"), ("08/03 11:00", "89.5%", "Fluent")]
    for r_idx, row in enumerate(rows):
        for c_idx, val in enumerate(row):
            ax.text(0.69 + c_idx*0.09, 0.47 - r_idx*0.05, val, fontsize=7.5, color=NAVY)
            
    # Download Button
    btn = patches.FancyBboxPatch((0.69, 0.25), 0.24, 0.06, boxstyle="round,pad=0.01", ec=TEAL, fc=TEAL, lw=1)
    ax.add_patch(btn)
    ax.text(0.81, 0.28, "Download PDF Report", ha='center', va='center', fontsize=8.5, fontweight='bold', color='white')

    # Footer controls
    ax.text(0.05, 0.05, "Settings | Thresholds | Dark Mode Toggle | Patient Search Filters", fontsize=8, color=GRAY)
    
    ax.set_title("VoxFlow - Streamlit Dashboard UI Wireframe Layout", fontsize=13, fontweight='bold', color=NAVY, pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "dashboard_wireframe.png"), bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    generate_flowchart()
    generate_architecture()
    generate_er_diagram()
    generate_class_diagram()
    generate_sequence_diagram()
    generate_activity_diagram()
    generate_communication_diagram()
    generate_dashboard_wireframe()
    print("All 8 diagram images successfully generated!")
