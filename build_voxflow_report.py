import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Document path
output_docx = r"c:\Users\amare\Downloads\TARP\VoxFlow_Software_Engineering_Report.docx"
diagrams_dir = r"c:\Users\amare\Downloads\TARP\diagrams"

# Color Palette Constants
COLOR_NAVY = RGBColor(0x1A, 0x36, 0x5D)
COLOR_BLUE = RGBColor(0x2B, 0x6C, 0xB0)
COLOR_SLATE = RGBColor(0x4A, 0x55, 0x68)
COLOR_DARK = RGBColor(0x2D, 0x37, 0x48)

HEX_NAVY = "1A365D"
HEX_BLUE = "2B6CB0"
HEX_LIGHT_BG = "F7FAFC"
HEX_BORDER = "CBD5E0"
HEX_CALLOUT_BG = "F0F4F8"

def set_cell_background(cell, hex_color):
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_report():
    doc = docx.Document()

    # Page Margins (1 inch)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Base Normal Style Settings
    style_normal = doc.styles['Normal']
    font = style_normal.font
    font.name = 'Calibri'
    font.size = Pt(11)
    font.color.rgb = COLOR_DARK
    style_normal.paragraph_format.line_spacing = 1.15
    style_normal.paragraph_format.space_after = Pt(6)

    # Helper formatters
    def add_title(text, subtitle):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(24)
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(24)
        run.font.bold = True
        run.font.color.rgb = COLOR_NAVY
        
        p2 = doc.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.paragraph_format.space_after = Pt(24)
        run2 = p2.add_run(subtitle)
        run2.font.name = 'Calibri'
        run2.font.size = Pt(14)
        run2.font.italic = True
        run2.font.color.rgb = COLOR_BLUE

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(18)
        run.font.bold = True
        run.font.color.rgb = COLOR_NAVY

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(14)
        run.font.bold = True
        run.font.color.rgb = COLOR_BLUE

    def add_h3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = COLOR_SLATE

    def add_callout(text, title="SYSTEM DESIGN NOTE"):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        set_cell_background(cell, HEX_CALLOUT_BG)
        set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
        
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(2)
        r_title = p.add_run(f"[{title}]\n")
        r_title.bold = True
        r_title.font.size = Pt(9.5)
        r_title.font.color.rgb = COLOR_NAVY
        
        r_text = p.add_run(text)
        r_text.font.size = Pt(10)
        r_text.font.italic = True
        r_text.font.color.rgb = COLOR_DARK
        doc.add_paragraph().paragraph_format.space_after = Pt(6)

    def add_code_block(code_text):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        set_cell_background(cell, "F4F5F7")
        set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(code_text)
        run.font.name = 'Consolas'
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x1A, 0x20, 0x2C)
        doc.add_paragraph().paragraph_format.space_after = Pt(6)

    def add_styled_table(headers, data):
        tbl = doc.add_table(rows=len(data) + 1, cols=len(headers))
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        # Header Row
        hdr_cells = tbl.rows[0].cells
        for i, header_text in enumerate(headers):
            cell = hdr_cells[i]
            set_cell_background(cell, HEX_NAVY)
            set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(0)
            run = p.add_run(header_text)
            run.font.bold = True
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            
        # Data Rows
        for r_idx, row_data in enumerate(data):
            row_cells = tbl.rows[r_idx + 1].cells
            bg_hex = HEX_LIGHT_BG if r_idx % 2 == 1 else "FFFFFF"
            for c_idx, cell_value in enumerate(row_data):
                cell = row_cells[c_idx]
                set_cell_background(cell, bg_hex)
                set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.space_after = Pt(0)
                run = p.add_run(str(cell_value))
                run.font.size = Pt(9.5)
                run.font.color.rgb = COLOR_DARK
                
        doc.add_paragraph().paragraph_format.space_after = Pt(6)

    def add_diagram_image(img_name, caption):
        img_path = os.path.join(diagrams_dir, img_name)
        if os.path.exists(img_path):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run()
            run.add_picture(img_path, width=Inches(6.2))
            
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_after = Pt(12)
            run_cap = p_cap.add_run(f"Figure: {caption}")
            run_cap.font.size = Pt(9.5)
            run_cap.font.italic = True
            run_cap.font.color.rgb = COLOR_SLATE

    # ==================== DOCUMENT CONTENT GENERATION ====================

    # Title & Metadata
    add_title("VoxFlow - Software Engineering Specification Report", 
              "AI-Assisted Speech Fluency Monitoring System\nMember 3 Deliverable: Host Server, Database, Analytics Dashboard & APIs")
    
    doc.add_paragraph("Author: Software Engineering Lead (Member 3)\n"
                      "Project: Final Year B.Tech Engineering Project - VoxFlow\n"
                      "Scope: Host-side Software Architecture, Communication Protocol, Data Persistence & Dashboard UI\n"
                      "Document Version: 1.0.0 (Production Release)")

    add_callout(
        "VoxFlow is a low-cost, AI-assisted speech fluency monitoring system designed to provide objective, non-intrusive feedback to individuals who stutter between formal speech therapy sessions. VoxFlow is NOT a diagnostic tool and DOES NOT replace licensed speech pathologists. The host software component detailed in this report ingests audio streams from an ESP32 edge device over Wi-Fi, executes a multi-stage speech processing pipeline (noise reduction, speaker verification, feature extraction, CNN-LSTM fluency inference), persists historical metrics in a local SQLite relational store, and renders clinical dashboards for therapy tracking.",
        "EXECUTIVE SUMMARY & SYSTEM CONTEXT"
    )

    # ----------------------------------------------------
    # SECTION 1: PYTHON ECOSYSTEM
    # ----------------------------------------------------
    add_h1("1. Python Technical Rationale & Library Ecosystem")
    
    add_h2("1.1 Language Rationale & Engineering Selection Criteria")
    doc.add_paragraph(
        "For the host workstation component of VoxFlow, Python 3.10+ was chosen as the primary software development language. "
        "A rigorous comparative evaluation against compiled and alternative interpreted languages (C++, Java, Node.js, and Go) "
        "demonstrated that Python provides the optimal balance between rapid signal processing prototyping, asynchronous web networking, "
        "and native integration with deep learning execution runtimes."
    )
    
    lang_comp_headers = ["Language", "Audio Processing Ecosystem", "Deep Learning Integration", "Web REST Throughput", "Development Velocity", "Selection Outcome"]
    lang_comp_data = [
        ["Python", "Extensive (Librosa, SciPy, PyAudio)", "Native (PyTorch, TensorFlow, C++ bindings)", "High (Flask WSGI, FastAPI, Gunicorn)", "Very High", "SELECTED"],
        ["C++", "Low-level (PortAudio, FFTW)", "Complex (LibTorch C++ API, TensorRT)", "Moderate (Crow, Pistache)", "Low (Manual Memory Management)", "Rejected"],
        ["Java", "Limited (JavaSound API)", "Moderate (Deeplearning4j)", "High (Spring Boot)", "Moderate", "Rejected"],
        ["Node.js", "Minimal (Web Audio API wrappers)", "Moderate (TensorFlow.js)", "Very High (Express.js, Fastify)", "High", "Rejected"],
        ["Go", "Minimal (PortAudio bindings)", "Low (ONNX wrappers)", "Very High (Gin, Fiber)", "High", "Rejected"]
    ]
    add_styled_table(lang_comp_headers, lang_comp_data)

    doc.add_paragraph(
        "Key engineering advantages of Python in VoxFlow include:"
    )
    doc.add_paragraph("• Uniform Memory Representation: NumPy C-contiguous ndarrays serve as a common zero-copy exchange format between audio signal processing routines (Librosa) and AI inference engines (PyTorch/TensorFlow).")
    doc.add_paragraph("• Ecosystem Interoperability: Seamless integration between HTTP REST servers (Flask), relational ORMs/DAOs (SQLite3), and live dashboard visualization tools (Streamlit) within a single runtime environment.")
    doc.add_paragraph("• Production Maintainability: Readable, modular object-oriented structures reducing software debt during team integration.")

    add_h2("1.2 Detailed Comprehensive Library Analysis")
    doc.add_paragraph(
        "Every Python module incorporated into VoxFlow fulfills a strict functional requirement within the host processing pipeline. "
        "The complete inventory of libraries, their precise roles, underlying data structures, and key API methods are detailed below."
    )

    lib_headers = ["Library Name", "Primary Role in VoxFlow", "Core Data Structures / APIs Used", "Technical Justification"]
    lib_data = [
        ["Flask", "WSGI REST API Web Server", "Flask(app), request.files, jsonify(), make_response()", "Lightweight, synchronous WSGI microframework capable of handling multipart/form-data uploads from ESP32 with zero overhead."],
        ["Streamlit", "Real-Time Patient & Therapist Dashboard", "st.set_page_config(), st.line_chart(), st.metric(), @st.cache_data", "Declarative UI rendering framework allowing instant dynamic visualization of fluency scores without frontend JS build steps."],
        ["sqlite3", "ACID-Compliant Relational Database", "sqlite3.connect(), Cursor.execute(), Transaction isolation", "Built-in zero-configuration SQL engine ensuring persistent local storage of speech sessions and disfluency predictions."],
        ["Librosa", "Digital Audio Signal Processing", "librosa.load(), librosa.feature.mfcc(), librosa.stft()", "Gold standard Python library for Short-Time Fourier Transforms (STFT), Mel-spectrogram generation, and MFCC feature extraction."],
        ["NumPy", "Multidimensional Numerical Computing", "np.ndarray, np.mean(), np.std(), np.dot()", "High-performance C-optimized array manipulation used for audio frame vectorization, feature scaling, and distance metrics."],
        ["Pandas", "Temporal Data Aggregation", "pd.DataFrame, pd.to_datetime(), df.groupby(), df.resample()", "Tabular data structure management for rolling weekly/monthly trend analysis and clinical report export generation."],
        ["Matplotlib", "Static Visualizations & Custom Plots", "plt.subplots(), Figure, Axes, Patches", "Generates high-resolution publication-grade technical figures, embedded diagrams, and clinical summary charts."],
        ["Plotly", "Interactive Chart Engine", "plotly.graph_objects.Figure, px.timeline()", "Provides hoverable, zoomable time-series charts for speech disfluency distribution across patient recording sessions."],
        ["Scikit-learn", "Data Normalization & Speaker Embeddings", "StandardScaler(), cosine_similarity()", "Used for standardizing feature vectors prior to neural network inference and calculating speaker verification similarity scores."],
        ["PyTorch / TensorFlow", "CNN-LSTM Deep Learning Inference Engine", "torch.jit.load() / tf.keras.models.load_model()", "Executes deep learning inference on extracted MFCC feature sequences to classify speech frames into Fluent vs. Disfluent categories."],
        ["Requests", "HTTP Client Fallback / External Sync", "requests.post(), requests.get(), Session()", "Handles outbound REST calls during cloud synchronization and external notification dispatching."],
        ["OS", "Filesystem I/O & Path Operations", "os.path.join(), os.makedirs(), os.remove()", "Manages temporary audio file buffers, safe directory resolution, and local file storage lifecycle."],
        ["Datetime", "Timestamp Serialization & Time Delta", "datetime.now(), timedelta, isoformat()", "Generates standardized ISO-8601 timestamps for session tracking, database indexing, and clinical timeline filtering."],
        ["JSON", "Payload Serialization / Deserialization", "json.dumps(), json.loads(), json.JSONDecodeError", "Converts complex python dictionaries into standardized JSON strings for ESP32 hardware response payloads and REST APIs."]
    ]
    add_styled_table(lib_headers, lib_data)

    # ----------------------------------------------------
    # SECTION 2: FLASK BACKEND
    # ----------------------------------------------------
    add_h1("2. Flask Backend & Hardware Communication Architecture")
    
    add_h2("2.1 WSGI Microframework Selection & Architectural Rationale")
    doc.add_paragraph(
        "Flask is selected as the primary backend server due to its minimal WSGI overhead, explicit request routing, "
        "and straightforward handling of binary stream uploads. Unlike Django, which imposes heavy ORM abstractions and unused template engines, "
        "or FastAPI, which relies heavily on asynchronous event loops that offer no latency benefit for single-device binary stream writes, "
        "Flask provides direct, synchronous execution matching the serial processing lifecycle of audio ingestion."
    )

    add_h2("2.2 ESP32 Audio Upload Protocol & HTTP Request Flow")
    doc.add_paragraph(
        "Communication between the ESP32 microcontroller and the Flask backend takes place over a local Wi-Fi network using standard HTTP/1.1 POST requests. "
        "The ESP32 captures 16-bit PCM audio from the INMP441 I2S microphone, encapsulates it into a WAV file header, and transmits it via `multipart/form-data` "
        "or raw binary payload stream to the `/api/v1/audio/upload` REST endpoint."
    )

    add_code_block(
        "POST /api/v1/audio/upload HTTP/1.1\n"
        "Host: 192.168.1.100:5000\n"
        "User-Agent: ESP32-VoxFlow-Hardware/1.0\n"
        "Content-Type: multipart/form-data; boundary=----VoxFlowBoundary7MA4YWxk\n"
        "Content-Length: 64104\n\n"
        "------VoxFlowBoundary7MA4YWxk\n"
        "Content-Disposition: form-data; name=\"audio\"; filename=\"rec_20260805_101500.wav\"\n"
        "Content-Type: audio/wav\n\n"
        "[BINARY WAV DATA: 16kHz, 16-bit Mono PCM, 4 seconds]\n"
        "------VoxFlowBoundary7MA4YWxk--"
    )

    add_h2("2.3 Endpoint Route Specifications & HTTP Response Handler")
    doc.add_paragraph(
        "The Flask backend exposes structured REST endpoints to handle audio ingestion, health diagnostics, prediction retrieval, and historical queries. "
        "Below is a Flask implementation snippet showing audio stream reception, temporary file staging, audio validation, pipeline execution trigger, "
        "and JSON response encoding back to the ESP32."
    )

    add_code_block(
        "from flask import Flask, request, jsonify\n"
        "import os, time, uuid\n"
        "from datetime import datetime\n\n"
        "app = Flask(__name__)\n"
        "UPLOAD_DIR = './audio_buffer'\n"
        "os.makedirs(UPLOAD_DIR, exist_ok=True)\n\n"
        "@app.route('/api/v1/audio/upload', methods=['POST'])\n"
        "def handle_audio_upload():\n"
        "    if 'audio' not in request.files:\n"
        "        return jsonify({'status': 'error', 'message': 'Missing audio payload'}), 400\n"
        "    \n"
        "    file = request.files['audio']\n"
        "    if file.filename == '' or not file.filename.endswith('.wav'):\n"
        "        return jsonify({'status': 'error', 'message': 'Invalid file format. WAV expected'}), 415\n"
        "    \n"
        "    # Stage audio file to temporary disk buffer\n"
        "    filename = f\"audio_{int(time.time())}_{uuid.uuid4().hex[:6]}.wav\"\n"
        "    filepath = os.path.join(UPLOAD_DIR, filename)\n"
        "    file.save(filepath)\n"
        "    \n"
        "    # Trigger Pipeline Execution (Denoise -> Verify -> Extract -> Predict -> DB)\n"
        "    result = pipeline_runner.execute(filepath, user_id=request.form.get('user_id', 1))\n"
        "    \n"
        "    # Response Payload for ESP32 Feedback (LEDs & OLED Display)\n"
        "    response_data = {\n"
        "        'status': 'success',\n"
        "        'timestamp': datetime.now().isoformat(),\n"
        "        'fluency_score': result['fluency_score'],\n"
        "        'stutter_detected': result['is_disfluent'],\n"
        "        'stutter_type': result['stutter_type'],\n"
        "        'display_message': f\"Score: {result['fluency_score']:.1f}%\"\n"
        "    }\n"
        "    return jsonify(response_data), 200\n\n"
        "if __name__ == '__main__':\n"
        "    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)"
    )

    add_callout(
        "Upon receiving HTTP 200 OK, the ESP32 parses the JSON payload. If `stutter_detected` is True, it illuminates the amber/red LED indicator and updates the OLED display with `display_message`. If False, a green LED illuminates, providing immediate visual feedback to the user.",
        "HARDWARE-SOFTWARE FEEDBACK LOOP"
    )

    # ----------------------------------------------------
    # SECTION 3: DATABASE
    # ----------------------------------------------------
    add_h1("3. Database Architecture & Storage Flow")
    
    add_h2("3.1 SQLite Architectural Rationale & Normalization")
    doc.add_paragraph(
        "VoxFlow utilizes SQLite3 as its embedded relational database engine. SQLite requires zero server installation, provides full ACID transactional compliance, "
        "and stores all tables in a single cross-platform file (`voxflow_local.db`). "
        "The relational schema is fully normalized to Third Normal Form (3NF) to eliminate duplicate patient metadata and ensure referential integrity."
    )

    add_h2("3.2 Entity-Relationship (ER) Diagram")
    doc.add_paragraph(
        "The SQLite database contains four primary entities: USERS, SESSIONS, PREDICTIONS, and REPORTS. "
        "The ER diagram below illustrates entity attributes, primary keys (PK), foreign keys (FK), and cardinality relationships."
    )
    add_diagram_image("er_diagram.png", "Relational Entity-Relationship (ER) Schema for VoxFlow SQLite Storage")

    add_h2("3.3 Data Storage Flow & CRUD Operations")
    doc.add_paragraph(
        "The host software accesses the database using an encapsulated Data Access Object (DAO) pattern (`DatabaseManager`). "
        "Thread-safe connection pooling is implemented by opening short-lived database connections per API request cycle."
    )

    crud_headers = ["CRUD Operation", "SQL Pattern", "Pipeline Trigger Event", "Data Returned / Stored"]
    crud_data = [
        ["CREATE", "INSERT INTO predictions (session_id, timestamp, fluency_score, stutter_type, confidence) VALUES (?, ?, ?, ?, ?)", "Immediate completion of CNN-LSTM inference pass.", "Stores newly calculated disfluency metrics with auto-incrementing `pred_id`."],
        ["READ", "SELECT * FROM predictions WHERE session_id = ? ORDER BY timestamp DESC", "Streamlit dashboard load or patient history query.", "Fetches chronological disfluency records for visual plotting and metric computation."],
        ["UPDATE", "UPDATE sessions SET total_audio_length = total_audio_length + ? WHERE session_id = ?", "ESP32 stream completion callback.", "Updates cumulative session duration and active status."],
        ["DELETE", "DELETE FROM predictions WHERE session_id = ?; DELETE FROM sessions WHERE session_id = ?", "Therapist session archive / purge action.", "Removes obsolete recording sessions while preserving patient baseline metadata."]
    ]
    add_styled_table(crud_headers, crud_data)

    add_h2("3.4 Future Cloud Migration Strategy (Firebase & MongoDB Atlas)")
    doc.add_paragraph(
        "To support multi-device access, remote therapist oversight, and automatic offsite backups, VoxFlow features an abstracted storage layer "
        "enabling seamless future migration to NoSQL cloud databases:"
    )
    doc.add_paragraph("• Firebase Firestore: Document-oriented cloud database featuring real-time websocket listeners. Enables instant live synchronization between the host laptop and a remote mobile application used by speech therapists.")
    doc.add_paragraph("• MongoDB Atlas: Scalable JSON document database suitable for storing large unstructured audio metadata, feature embeddings, and multi-tenant patient records.")
    doc.add_paragraph("• Hybrid Synchronization Engine: A background worker thread periodically queries local SQLite records flagged as `synced=0`, pushes JSON payloads to cloud APIs, and sets `synced=1` upon receiving HTTP 201 Created.")

    # ----------------------------------------------------
    # SECTION 4: STREAMLIT DASHBOARD
    # ----------------------------------------------------
    add_h1("4. Streamlit Dashboard Design & Functional Mechanics")
    
    add_h2("4.1 User Interface Architecture & Reactivity Model")
    doc.add_paragraph(
        "Streamlit was selected for the VoxFlow monitoring dashboard because of its Python-native declarative UI model. "
        "Whenever a new speech prediction is inserted into the SQLite database, Streamlit reruns the script context, updating charts and metric tiles in real time. "
        "Computationally expensive operations—such as querying historical session DataFrames—are optimized using `@st.cache_data` with time-to-live (TTL) invalidation."
    )

    add_h2("4.2 Comprehensive Widget Justification & Functional Breakdown")
    doc.add_paragraph(
        "Every UI element on the dashboard serves a specific clinical or technical monitoring purpose:"
    )

    widget_headers = ["Widget Component", "Streamlit API Primitive", "Clinical / Technical Purpose", "User Interaction Behavior"]
    widget_data = [
        ["Patient Selector", "st.sidebar.selectbox()", "Select active patient profile for multi-tenant monitoring.", "Filters database queries to display user-specific disfluency records."],
        ["Date Range Filter", "st.sidebar.date_input()", "Select temporal range (Daily, Weekly, Monthly).", "Dynamically resamples time-series charts to display progress trends."],
        ["Fluency Gauge Tile", "st.metric('Fluency Score')", "Displays latest speech fluency percentage (0-100%).", "Updates live after every ESP32 upload; highlights improvement in green."],
        ["Disfluency Breakdown", "st.bar_chart()", "Visualizes distribution of disfluency types (Block, Repetition, Prolongation).", "Allows therapists to identify specific stuttering patterns."],
        ["Weekly Trend Line", "st.line_chart()", "Plots rolling 7-day fluency average.", "Helps track long-term speech stability across multiple home practice sessions."],
        ["Prediction Timeline Table", "st.dataframe()", "Detailed row-by-row session log with timestamps and confidence scores.", "Provides searchable, sortable clinical audit trail."],
        ["Report Export Button", "st.download_button()", "Generates downloadable PDF/CSV clinical summary report.", "Triggers PDF compilation service for offline therapy review."],
        ["Dark/Light Mode Toggle", "st.sidebar.radio()", "Adapts UI contrast for low-light home usage or clinical environments.", "Swaps Streamlit CSS theme variables dynamically."]
    ]
    add_styled_table(widget_headers, widget_data)

    add_h2("4.3 Dashboard UI Wireframe Layout")
    doc.add_paragraph(
        "The visual mockup below demonstrates the spatial organization of header metrics, main trend charts, recent session logs, and clinical export controls."
    )
    add_diagram_image("dashboard_wireframe.png", "Streamlit Monitoring Dashboard UI Wireframe & Component Layout")

    # ----------------------------------------------------
    # SECTION 5: SOFTWARE MODULES
    # ----------------------------------------------------
    add_h1("5. Modular Software Component Breakdown")
    
    doc.add_paragraph(
        "VoxFlow follows a modular software design pattern to isolate functional concerns, simplify unit testing, and enable concurrent development. "
        "The software architecture comprises seven core modules operating in sequence."
    )

    modules_headers = ["Module Name", "Input Format", "Output Format", "Core Responsibilities", "Key Architectural Advantage"]
    modules_data = [
        ["1. Audio Receiver", "HTTP POST Stream (WAV)", "Staged Audio File (.wav)", "Ingests network audio payload, validates WAV headers, stages file to disk buffer.", "Network protocol isolation; prevents malformed network bytes from corrupting processing pipeline."],
        ["2. Noise Removal", "Raw WAV File Path", "Denoised Float32 Array", "Applies spectral gating and 80Hz-4000Hz bandpass filtering to remove background acoustic noise.", "Improves downstream SNR, ensuring robust model performance in noisy home environments."],
        ["3. Speaker Verifier", "Denoised Array + User ID", "Boolean (Pass / Reject)", "Computes speaker embeddings and calculates cosine similarity against stored baseline.", "Ensures disfluency metrics are assigned strictly to the registered patient, discarding background voices."],
        ["4. Feature Extractor", "Denoised Audio Array", "MFCC Tensor (39 x T)", "Extracts 13 MFCCs, Delta, and Delta-Delta coefficients; normalizes feature distributions.", "Transforms high-dimensional raw audio into compact, noise-robust spectral representations."],
        ["5. AI Predictor Interface", "MFCC Feature Tensor", "Prediction Dict (Score, Type)", "Wraps CNN-LSTM model inference execution; outputs fluency probabilities and stutter classifications.", "Encapsulates AI framework details behind clean Python interface functions."],
        ["6. Database Access Layer", "Prediction Dictionary", "Persisted DB Row (ID)", "Manages SQLite connections, executes parameterized SQL queries, ensures ACID writes.", "Abstracts database interactions; enables seamless future cloud migration."],
        ["7. Dashboard Visualizer", "SQLite DB Queries", "Interactive HTML/CSS UI", "Queries persisted session data, computes rolling clinical metrics, renders interactive charts.", "Decouples presentation layer from data ingestion pipelines."]
    ]
    add_styled_table(modules_headers, modules_data)

    # ----------------------------------------------------
    # SECTION 6: REST API SPECIFICATION
    # ----------------------------------------------------
    add_h1("6. REST API Specification & Endpoint Documentation")
    
    add_h2("6.1 REST Architectural Principles")
    doc.add_paragraph(
        "The VoxFlow API is built according to RESTful principles: it is stateless, resource-oriented, uses standard HTTP methods (GET, POST), "
        "and returns structured JSON payloads with standard HTTP status codes."
    )

    api_headers = ["HTTP Method", "Endpoint Path", "Request Body / Params", "Success Status", "Description & Purpose"]
    api_data = [
        ["GET", "/api/v1/health", "None", "200 OK", "System health check. Returns host server status, DB status, and model readiness."],
        ["POST", "/api/v1/audio/upload", "multipart/form-data (audio file, user_id)", "200 OK / 201 Created", "Ingests WAV audio stream from ESP32, triggers pipeline, returns immediate prediction JSON."],
        ["GET", "/api/v1/predictions/{user_id}", "Params: limit, offset, start_date", "200 OK", "Retrieves historical disfluency prediction logs for a specific patient."],
        ["GET", "/api/v1/session/latest", "Params: user_id", "200 OK", "Fetches the most recent session summary metrics for live OLED updates."],
        ["GET", "/api/v1/reports/export", "Params: user_id, format (pdf/csv)", "200 OK", "Generates downloadable clinical summary reports for therapy sessions."]
    ]
    add_styled_table(api_headers, api_data)

    add_h2("6.2 Sample Request & Response JSON Payloads")
    doc.add_paragraph("Sample HTTP POST `/api/v1/audio/upload` Response Payload (Returned to ESP32):")
    add_code_block(
        "{\n"
        "  \"status\": \"success\",\n"
        "  \"request_id\": \"req_9920a4b1\",\n"
        "  \"timestamp\": \"2026-08-05T10:15:30Z\",\n"
        "  \"user_id\": 102,\n"
        "  \"processing_time_ms\": 342,\n"
        "  \"audio_duration_sec\": 4.0,\n"
        "  \"speaker_verified\": true,\n"
        "  \"fluency_score\": 84.2,\n"
        "  \"is_disfluent\": false,\n"
        "  \"stutter_type\": \"Fluent\",\n"
        "  \"confidence\": 0.941,\n"
        "  \"display_message\": \"Fluency: 84.2% (Good)\"\n"
        "}"
    )

    add_h2("6.3 Future JWT Authentication Workflow")
    doc.add_paragraph(
        "To secure network endpoints when deployed across public Wi-Fi networks, a JSON Web Token (JWT) authentication handshake will be added:"
    )
    doc.add_paragraph("1. Authentication Request: ESP32 or Dashboard client sends credentials to `POST /api/v1/auth/login`.")
    doc.add_paragraph("2. Token Issuance: Server validates credentials and returns a signed HS256 JWT access token valid for 24 hours.")
    doc.add_paragraph("3. Protected Requests: Subsequent requests must include header `Authorization: Bearer <JWT_TOKEN>`. Flask decorator `@jwt_required()` validates signature before serving resources.")

    # ----------------------------------------------------
    # SECTION 7: CLOUD INTEGRATION
    # ----------------------------------------------------
    add_h1("7. Future Cloud Integration & Multi-Tenant Architecture")
    
    doc.add_paragraph(
        "While the current implementation operates entirely locally on the host laptop using SQLite, VoxFlow is designed for seamless cloud scaling. "
        "The proposed cloud architecture enables remote therapy monitoring, multi-device dashboard synchronization, and automated data backup."
    )

    add_callout(
        "Hybrid Cloud Synchronization Engine Architecture:\n"
        "• Local SQLite database acts as a reliable primary buffer, ensuring zero data loss if Wi-Fi or Internet connectivity is interrupted.\n"
        "• A background Python daemon (`CloudSyncWorker`) monitors local un-synced records (`synced_flag = 0`).\n"
        "• When an active Internet connection is detected, the worker batches records into JSON payloads and uploads them to Firebase Firestore or MongoDB Atlas via secure HTTPS REST calls.\n"
        "• Remote speech therapists access real-time patient analytics through a cloud-hosted web portal, enabling continuous care between clinic visits.",
        "CLOUD ARCHITECTURE & SYNC STRATEGY"
    )

    # ----------------------------------------------------
    # SECTION 8: DASHBOARD DESIGN
    # ----------------------------------------------------
    add_h1("8. Dashboard Visual Specification & Wireframe Details")
    
    doc.add_paragraph(
        "The VoxFlow Streamlit dashboard UI is organized into structured visual zones to optimize clinical usability:"
    )
    doc.add_paragraph("1. Control Sidebar: Patient profile selection dropdown, date range pickers, disfluency sensitivity threshold sliders, and visual theme toggles.")
    doc.add_paragraph("2. Metric Header Cards: High-contrast summary cards showing Current Session Score (%), Total Speech Duration (min), and Disfluency Count.")
    doc.add_paragraph("3. Primary Visualization Area: Dual-axis time-series chart rendering daily disfluency occurrences against a rolling 7-day progress trendline.")
    doc.add_paragraph("4. Disfluency Breakdown Panel: Categorical bar charts breaking down disfluency instances into Blocks, Repetitions, and Prolongations.")
    doc.add_paragraph("5. Interactive Data Table: Searchable table listing historical session logs with instant CSV/PDF export options.")

    # ----------------------------------------------------
    # SECTION 9: DATABASE SCHEMA
    # ----------------------------------------------------
    add_h1("9. Complete Relational Database Schema & DDL Queries")
    
    doc.add_paragraph("Below are the complete DDL SQL queries used to initialize the SQLite database tables (`voxflow_local.db`):")

    add_code_block(
        "-- 1. USERS TABLE\n"
        "CREATE TABLE IF NOT EXISTS users (\n"
        "    user_id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    full_name TEXT NOT NULL,\n"
        "    age INTEGER NOT NULL,\n"
        "    therapist_name TEXT,\n"
        "    baseline_embedding BLOB,\n"
        "    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n"
        ");\n\n"
        "-- 2. SESSIONS TABLE\n"
        "CREATE TABLE IF NOT EXISTS sessions (\n"
        "    session_id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    user_id INTEGER NOT NULL,\n"
        "    session_name TEXT NOT NULL,\n"
        "    start_time TIMESTAMP NOT NULL,\n"
        "    end_time TIMESTAMP,\n"
        "    total_audio_length REAL DEFAULT 0.0,\n"
        "    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE\n"
        ");\n\n"
        "-- 3. PREDICTIONS TABLE\n"
        "CREATE TABLE IF NOT EXISTS predictions (\n"
        "    pred_id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    session_id INTEGER NOT NULL,\n"
        "    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n"
        "    fluency_score REAL NOT NULL,\n"
        "    stutter_type TEXT NOT NULL,\n"
        "    confidence REAL NOT NULL,\n"
        "    audio_file_path TEXT,\n"
        "    synced_flag INTEGER DEFAULT 0,\n"
        "    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE\n"
        ");\n\n"
        "-- 4. REPORTS TABLE\n"
        "CREATE TABLE IF NOT EXISTS reports (\n"
        "    report_id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    session_id INTEGER NOT NULL,\n"
        "    user_id INTEGER NOT NULL,\n"
        "    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n"
        "    summary_notes TEXT,\n"
        "    pdf_file_path TEXT,\n"
        "    FOREIGN KEY (session_id) REFERENCES sessions(session_id),\n"
        "    FOREIGN KEY (user_id) REFERENCES users(user_id)\n"
        ");"
    )

    # ----------------------------------------------------
    # SECTION 10: SOFTWARE FLOWCHART
    # ----------------------------------------------------
    add_h1("10. Software Processing Flowchart & Step Breakdown")
    
    doc.add_paragraph(
        "The end-to-end execution flow of the host software—from receiving Wi-Fi audio packets to updating the live dashboard and returning feedback to the ESP32—is illustrated below."
    )
    add_diagram_image("flowchart.png", "Step-by-Step Software Processing Flowchart for VoxFlow")

    doc.add_paragraph("Operational Sequence Explanation:")
    doc.add_paragraph("1. HTTP POST Audio Stream Ingestion: Flask server accepts WAV stream from ESP32 over local Wi-Fi.")
    doc.add_paragraph("2. Buffer Staging & Format Verification: Validates header parameters (16kHz, 16-bit PCM) and writes bytes to temporary disk buffer.")
    doc.add_paragraph("3. Noise Filtering: Spectral gating reduces stationary ambient background noise.")
    doc.add_paragraph("4. Speaker Verification: Computes MFCC cosine similarity against stored patient baseline vector. If similarity < threshold, request is rejected.")
    doc.add_paragraph("5. Feature Extraction: Extracts 13 MFCCs, Delta, and Delta-Delta coefficients across 25ms sliding frames.")
    doc.add_paragraph("6. Deep Learning Prediction: Passes feature matrix into trained CNN-LSTM model to compute disfluency probability.")
    doc.add_paragraph("7. Relational Persistence: Writes prediction record, fluency score, and timestamp to SQLite database.")
    doc.add_paragraph("8. UI Refresh: Triggers Streamlit dashboard re-render via state invalidation.")
    doc.add_paragraph("9. Hardware Feedback Payload: Returns JSON response containing score and status flags back to ESP32 for LED/OLED updates.")

    # ----------------------------------------------------
    # SECTION 11: SOFTWARE ARCHITECTURE
    # ----------------------------------------------------
    add_h1("11. Tiered Software Architecture Specification")
    
    doc.add_paragraph(
        "VoxFlow follows a 5-tier software architecture model that isolates hardware interfacing, network ingestion, signal processing, data storage, and presentation."
    )
    add_diagram_image("architecture.png", "5-Tiered Software Architecture Diagram for VoxFlow")

    doc.add_paragraph("Tier Breakdown:")
    doc.add_paragraph("• Edge Hardware Layer: ESP32, INMP441 microphone, OLED display, and status LEDs.")
    doc.add_paragraph("• API Ingestion Layer: Flask REST WSGI server, request parsing, and input validation routines.")
    doc.add_paragraph("• Audio & AI Processing Core: Spectral noise filter, speaker verification module, MFCC extractor, and CNN-LSTM inference engine.")
    doc.add_paragraph("• Persistence Layer: SQLite local database, file system buffer manager, and cloud sync daemon.")
    doc.add_paragraph("• Presentation Layer: Declarative Streamlit dashboard, Plotly chart engine, and PDF report exporter.")

    # ----------------------------------------------------
    # SECTION 12: UML DIAGRAMS
    # ----------------------------------------------------
    add_h1("12. Formal Object-Oriented UML Diagrams")
    
    doc.add_paragraph(
        "To provide a complete object-oriented software engineering specification, formal UML diagrams were constructed. "
        "Each diagram is presented below as both a high-resolution visual figure and copy-pasteable PlantUML / Mermaid source code."
    )

    add_h2("12.1 UML Class Diagram")
    doc.add_paragraph("Illustrates host domain classes, operational methods, attributes, and relationships.")
    add_diagram_image("class_diagram.png", "UML Class Diagram for VoxFlow Host Software Architecture")

    add_code_block(
        "@startuml\n"
        "class AudioReceiver {\n"
        "  + save_audio(stream): str\n"
        "  + validate_format(file): bool\n"
        "}\n"
        "class NoiseFilter {\n"
        "  + denoise(path): ndarray\n"
        "  + compute_snr(): float\n"
        "}\n"
        "class SpeakerVerifier {\n"
        "  + verify(audio, user_id): bool\n"
        "  + extract_embedding(): ndarray\n"
        "}\n"
        "class FeatureExtractor {\n"
        "  + extract_mfcc(audio): ndarray\n"
        "}\n"
        "class FluencyPredictor {\n"
        "  + predict(features): Dict\n"
        "}\n"
        "class DatabaseManager {\n"
        "  + save_prediction(data): int\n"
        "  + fetch_history(user): List\n"
        "}\n"
        "AudioReceiver --> NoiseFilter\n"
        "NoiseFilter --> SpeakerVerifier\n"
        "SpeakerVerifier --> FeatureExtractor\n"
        "FeatureExtractor --> FluencyPredictor\n"
        "FluencyPredictor --> DatabaseManager\n"
        "@enduml"
    )

    add_h2("12.2 UML Sequence Diagram")
    doc.add_paragraph("Triggers, lifelines, and message interactions across execution boundaries.")
    add_diagram_image("sequence_diagram.png", "UML Sequence Diagram for ESP32-Flask Ingestion & Prediction Loop")

    add_code_block(
        "sequenceDiagram\n"
        "    autonumber\n"
        "    participant ESP32 as ESP32 Device\n"
        "    participant Flask as Flask REST Server\n"
        "    participant Core as Processing Pipeline\n"
        "    participant Model as CNN-LSTM Model\n"
        "    participant DB as SQLite DB\n"
        "    participant UI as Streamlit Dashboard\n"
        "    ESP32->>Flask: POST /api/v1/audio/upload (WAV Stream)\n"
        "    Flask->>Core: execute(audio_path, user_id)\n"
        "    Core->>Model: predict(MFCC_features)\n"
        "    Model-->>Core: return fluency_score, stutter_type\n"
        "    Core->>DB: INSERT INTO predictions\n"
        "    Flask-->>ESP32: HTTP 200 OK (JSON Score & Status)\n"
        "    UI->>DB: SELECT * FROM predictions\n"
        "    DB-->>UI: Return Session Records\n"
        "    UI->>UI: Render Live Charts & Metrics"
    )

    add_h2("12.3 UML Activity Diagram")
    doc.add_paragraph("Decision paths for noise filtering, speaker verification match, and disfluency prediction.")
    add_diagram_image("activity_diagram.png", "UML Activity Diagram for Audio Ingestion and Decision Workflows")

    add_h2("12.4 UML Communication Diagram")
    doc.add_paragraph("Object interaction networks and numbered message paths across software components.")
    add_diagram_image("communication_diagram.png", "UML Communication Diagram for VoxFlow Host Subsystems")

    # Save Document
    doc.save(output_docx)
    print(f"Document successfully created and saved to: {output_docx}")

if __name__ == "__main__":
    create_report()
