import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Document path
output_docx = r"c:\Users\amare\Downloads\TARP\VoxFlow_Software_Engineering_Report.docx"
output_fallback = r"c:\Users\amare\Downloads\TARP\VoxFlow_Software_Engineering_Report_Human.docx"
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
              "AI-Assisted Speech Fluency Monitoring System\nHost Server, Database, Analytics Dashboard & APIs")
    
    doc.add_paragraph("Author: Software Engineering Lead (Member 3)\n"
                      "Project: Final Year B.Tech Engineering Project - VoxFlow\n"
                      "Scope: Host-side Software Architecture, Communication Protocol, Data Persistence & Dashboard UI\n"
                      "Document Version: 1.0.0 (Production Release)")

    add_callout(
        "VoxFlow is a low-cost speech fluency monitoring system built to help people who stutter track their speech progress between clinical therapy sessions. VoxFlow is not a medical diagnostic device and does not replace a licensed speech-language pathologist. This report covers the software running on the host laptop. It receives 16kHz audio streams from an ESP32 over Wi-Fi, filters out background noise, verifies the speaker, extracts 39-dimensional MFCC features, runs a CNN-LSTM inference pass, stores session metrics in a local SQLite database, and presents real-time disfluency graphs on a web dashboard.",
        "PROJECT SCOPE & SYSTEM PURPOSE"
    )

    # ----------------------------------------------------
    # SECTION 1: PYTHON ECOSYSTEM
    # ----------------------------------------------------
    add_h1("1. Python Language Choice & Ecosystem Analysis")
    
    add_h2("1.1 Why We Chose Python for VoxFlow")
    doc.add_paragraph(
        "Starting out on the host side, we picked Python 3.10. "
        "C++ turned out to be painful for quick model changes. Java felt clunky for signal processing. Node.js lacked good audio DSP libraries, and Go didn't have native PyTorch support. "
        "Python let us pass NumPy float32 arrays straight from Librosa into PyTorch without converting memory formats in between. "
        "That saved us a lot of latency during real-time speech processing."
    )
    
    lang_comp_headers = ["Language", "Audio Signal Processing", "Deep Learning Support", "Web API Performance", "Prototyping Speed", "Engineering Decision"]
    lang_comp_data = [
        ["Python", "Native (Librosa, SciPy, PyAudio)", "Native (PyTorch, TensorFlow C++ backends)", "High (Flask WSGI, FastAPI)", "Fast", "SELECTED"],
        ["C++", "Manual C API (PortAudio, FFTW)", "Complex LibTorch bindings", "Moderate (Crow, Pistache)", "Slow", "Rejected"],
        ["Java", "Basic (JavaSound API)", "Limited (Deeplearning4j)", "High (Spring Boot)", "Moderate", "Rejected"],
        ["Node.js", "Minimal C++ wrappers", "Limited (TensorFlow.js)", "Very High (Express.js)", "Fast", "Rejected"],
        ["Go", "Minimal C bindings", "Low (ONNX C wrappers)", "High (Gin, Fiber)", "Fast", "Rejected"]
    ]
    add_styled_table(lang_comp_headers, lang_comp_data)

    doc.add_paragraph("Why Python worked best for our host setup:")
    doc.add_paragraph("• Memory sharing: Librosa writes STFT frames right into C-contiguous float32 NumPy buffers, so PyTorch reads them with zero memory copying.")
    doc.add_paragraph("• Single runtime: Flask handles incoming REST POST requests, SQLite writes session rows, and Streamlit serves the frontend, all running under one Python 3.10 process.")
    doc.add_paragraph("• Clear modules: Keeping things object-oriented made it easy to connect Member 1's hardware signals and Member 2's AI model into our software flow.")

    add_h2("1.2 Detailed Breakdown of Python Libraries")
    doc.add_paragraph(
        "VoxFlow relies on 14 Python packages on the host. Here is how each module fits into our execution flow:"
    )

    lib_headers = ["Library", "Role in VoxFlow", "APIs & Functions Used", "Engineering Rationale"]
    lib_data = [
        ["Flask", "REST API Web Server", "Flask(app), request.files, jsonify()", "Synchronous WSGI server that accepts multipart/form-data WAV uploads from the ESP32 with low memory overhead."],
        ["Streamlit", "Analytics Dashboard UI", "st.metric(), st.plotly_chart(), @st.cache_data", "Renders interactive web interfaces directly in Python, removing the need for a separate Node.js/React frontend."],
        ["sqlite3", "Local Relational Database", "sqlite3.connect(), cursor.execute()", "Built-in relational SQL engine that saves speech sessions locally in a single file without running a background server process."],
        ["Librosa", "Audio Signal Processing", "librosa.load(), librosa.feature.mfcc()", "Calculates Short-Time Fourier Transforms, Mel-frequency spectrograms, and 13 MFCC feature coefficients from raw audio."],
        ["NumPy", "Vector & Matrix Math", "np.ndarray, np.mean(), np.std()", "Handles array operations, feature scaling, and distance metrics in C-optimized memory blocks."],
        ["Pandas", "Tabular Data Processing", "pd.DataFrame, pd.to_datetime(), df.groupby()", "Groups daily and weekly session records to compute rolling averages and export clinical CSV reports."],
        ["Matplotlib", "Technical Figures", "plt.subplots(), Figure, Axes", "Generates high-resolution PNG architecture diagrams, flowcharts, and ER diagrams for project documentation."],
        ["Plotly", "Interactive Web Charts", "go.Figure(), px.bar(), px.pie()", "Renders interactive hoverable line graphs, disfluency pie charts, and fluency gauges on the Streamlit dashboard."],
        ["Scikit-learn", "Feature Normalization", "StandardScaler(), cosine_similarity()", "Scales MFCC feature vectors before model inference and computes cosine similarity for speaker verification."],
        ["PyTorch / TensorFlow", "Neural Network Inference", "torch.jit.load() / tf.keras.models.load_model()", "Executes the trained CNN-LSTM model to classify speech frames as Fluent, Block, Repetition, or Prolongation."],
        ["Requests", "HTTP Client Tests", "requests.post(), requests.get()", "Sends simulated audio uploads from test scripts to the Flask server to verify API endpoints."],
        ["OS", "File Path Operations", "os.path.join(), os.makedirs()", "Creates local buffer folders and manages temporary WAV file paths during audio uploads."],
        ["Datetime", "Timestamp Formatting", "datetime.now(), timedelta, isoformat()", "Generates ISO-8601 timestamp strings for database indexing and session filtering."],
        ["JSON", "Data Serialization", "json.dumps(), json.loads()", "Encodes prediction results and display messages into JSON payloads sent back to the ESP32."]
    ]
    add_styled_table(lib_headers, lib_data)

    # ----------------------------------------------------
    # SECTION 2: FLASK BACKEND
    # ----------------------------------------------------
    add_h1("2. Flask Backend & Hardware Communication")
    
    add_h2("2.1 Why Flask Was Selected Over Alternatives")
    doc.add_paragraph(
        "We picked Flask over Django and FastAPI for our REST server. "
        "Django carries heavy ORM setups and templating engines we didn't need. "
        "FastAPI uses async event loops (`asyncio`), but our audio pipeline runs synchronous file writes and CPU matrix calculations anyway. "
        "Flask kept things simple and let us process POST uploads directly without async overhead."
    )

    add_h2("2.2 ESP32 Audio Upload Protocol & HTTP Flow")
    doc.add_paragraph(
        "The ESP32 streams recorded speech to Flask over local Wi-Fi. "
        "Once the INMP441 microphone finishes capturing audio, the board packages 16-bit 16kHz PCM samples into a WAV wrapper and sends an HTTP POST request to `http://<laptop_ip>:5000/api/v1/audio/upload` using `multipart/form-data`."
    )

    add_code_block(
        "POST /api/v1/audio/upload HTTP/1.1\n"
        "Host: 192.168.1.100:5000\n"
        "User-Agent: ESP32-VoxFlow-Hardware/1.0\n"
        "Content-Type: multipart/form-data; boundary=----VoxFlowBoundary7MA4YWxk\n"
        "Content-Length: 64104\n\n"
        "------VoxFlowBoundary7MA4YWxk\n"
        "Content-Disposition: form-data; name=\"audio\"; filename=\"speech_sample.wav\"\n"
        "Content-Type: audio/wav\n\n"
        "[RAW WAV AUDIO BYTES: 16kHz, 16-bit Mono PCM, 3 Seconds]\n"
        "------VoxFlowBoundary7MA4YWxk--"
    )

    add_h2("2.3 Endpoint Implementation & Response Handler")
    doc.add_paragraph(
        "Our Flask server (`server.py`) runs on port 5000. When an audio file arrives, it stages the file in `./audio_buffer/`, calls our pipeline functions, writes the prediction to SQLite, and sends back JSON output containing the fluency score and OLED message text."
    )

    add_code_block(
        "from flask import Flask, request, jsonify\n"
        "import os, time, uuid\n"
        "from datetime import datetime\n"
        "from database import DatabaseManager\n"
        "from pipeline import pipeline_runner\n\n"
        "app = Flask(__name__)\n"
        "db = DatabaseManager()\n"
        "UPLOAD_DIR = './audio_buffer'\n"
        "os.makedirs(UPLOAD_DIR, exist_ok=True)\n\n"
        "@app.route('/api/v1/audio/upload', methods=['POST'])\n"
        "def handle_audio_upload():\n"
        "    if 'audio' not in request.files:\n"
        "        return jsonify({'status': 'error', 'message': 'Missing audio payload'}), 400\n"
        "    \n"
        "    file = request.files['audio']\n"
        "    if file.filename == '':\n"
        "        return jsonify({'status': 'error', 'message': 'Empty file name'}), 400\n"
        "    \n"
        "    filename = f\"audio_{int(time.time())}_{uuid.uuid4().hex[:6]}.wav\"\n"
        "    filepath = os.path.join(UPLOAD_DIR, filename)\n"
        "    file.save(filepath)\n"
        "    \n"
        "    # Run processing pipeline (Denoise -> Verify -> Extract -> Predict)\n"
        "    user_id = int(request.form.get('user_id', 1))\n"
        "    result = pipeline_runner.process(filepath, user_id=user_id)\n"
        "    \n"
        "    # Write result to SQLite database\n"
        "    pred_id = db.save_prediction(\n"
        "        user_id=user_id,\n"
        "        fluency_score=result['fluency_score'],\n"
        "        stutter_type=result['stutter_type'],\n"
        "        confidence=result['confidence'],\n"
        "        audio_path=filepath\n"
        "    )\n"
        "    \n"
        "    response_data = {\n"
        "        'status': 'success',\n"
        "        'prediction_id': pred_id,\n"
        "        'timestamp': datetime.now().isoformat(),\n"
        "        'fluency_score': result['fluency_score'],\n"
        "        'stutter_type': result['stutter_type'],\n"
        "        'display_message': f\"Fluency: {result['fluency_score']:.1f}% ({result['stutter_type']})\"\n"
        "    }\n"
        "    return jsonify(response_data), 200\n\n"
        "if __name__ == '__main__':\n"
        "    app.run(host='0.0.0.0', port=5000, debug=False)"
    )

    add_callout(
        "When the ESP32 gets back HTTP 200, it reads display_message and updates the OLED screen. If stutter_type is not Fluent, it triggers the red/amber LED. Otherwise, the green LED lights up.",
        "HARDWARE FEEDBACK RESPONSE"
    )

    # ----------------------------------------------------
    # SECTION 3: DATABASE
    # ----------------------------------------------------
    add_h1("3. Database Design & Storage Pipeline")
    
    add_h2("3.1 SQLite Schema & 3NF Normalization")
    doc.add_paragraph(
        "Instead of setting up a heavy MySQL instance, we went with SQLite3 (`voxflow_local.db`). "
        "It stores everything in one file on the laptop. We normalized our schema into Third Normal Form (3NF) across USERS, SESSIONS, PREDICTIONS, and REPORTS."
    )

    add_h2("3.2 Entity-Relationship (ER) Diagram")
    doc.add_paragraph(
        "Here is how our database tables, primary keys, foreign keys, and cardinalities connect:"
    )
    add_diagram_image("er_diagram.png", "Relational Entity-Relationship (ER) Schema for VoxFlow")

    add_h2("3.3 Database Operations & CRUD Implementation")
    doc.add_paragraph(
        "We wrapped all SQL calls inside a `DatabaseManager` class in `database.py`. "
        "Opening connections per request and closing them right after commits avoided thread lockup problems."
    )

    crud_headers = ["Operation", "SQL Query Pattern", "Pipeline Trigger", "Result"]
    crud_data = [
        ["CREATE", "INSERT INTO predictions (session_id, timestamp, fluency_score, stutter_type, confidence) VALUES (?, ?, ?, ?, ?)", "After AI prediction finishes.", "Inserts a new prediction record with auto-incremented `pred_id`."],
        ["READ", "SELECT * FROM predictions WHERE session_id = ? ORDER BY timestamp DESC", "When Streamlit dashboard reloads.", "Fetches historical fluency records to plot daily and weekly graphs."],
        ["UPDATE", "UPDATE sessions SET total_audio_length = total_audio_length + ? WHERE session_id = ?", "When an audio upload completes.", "Updates total recorded audio duration for the active session."],
        ["DELETE", "DELETE FROM predictions WHERE session_id = ?; DELETE FROM sessions WHERE session_id = ?", "When a user deletes a session.", "Removes past session records while keeping user profile data intact."]
    ]
    add_styled_table(crud_headers, crud_data)

    add_h2("3.4 Future Cloud Migration Strategy")
    doc.add_paragraph(
        "SQLite handles single-laptop testing easily. To let speech therapists check patient data remotely later on, we structured our database functions so they can push to cloud storage:"
    )
    doc.add_paragraph("• Firebase Firestore: Real-time document store. Pushes live session updates to a therapist's phone app as soon as audio gets classified.")
    doc.add_paragraph("• MongoDB Atlas: Handles JSON documents for storing feature arrays, raw audio paths, and patient logs across multiple users.")
    doc.add_paragraph("• Sync Daemon: A background thread (`CloudSyncWorker`) looks for rows with `synced_flag = 0` and uploads them to cloud REST routes whenever Wi-Fi is active.")

    # ----------------------------------------------------
    # SECTION 4: STREAMLIT DASHBOARD
    # ----------------------------------------------------
    add_h1("4. Streamlit Dashboard Design & Visual Features")
    
    add_h2("4.1 Dashboard Framework & Caching Strategy")
    doc.add_paragraph(
        "We built our frontend (`dashboard.py`) using Streamlit so we could stay in Python. "
        "Streamlit reruns the script whenever SQLite gets updated, so graphs refresh automatically. "
        "Using `@st.cache_data` on SQL queries prevented unnecessary database reads when changing UI filters."
    )

    add_h2("4.2 Dashboard Widgets & Clinical Purpose")
    doc.add_paragraph(
        "Here is what each control on the dashboard does:"
    )

    widget_headers = ["Widget Component", "Streamlit Primitive", "Purpose", "User Action"]
    widget_data = [
        ["Patient Selector", "st.sidebar.selectbox()", "Switches between patient profiles.", "Filters SQLite queries to show data for the selected user."],
        ["Date Filter", "st.sidebar.date_input()", "Selects date range (Daily, Weekly, Monthly).", "Resamples dataset to plot trendlines for the chosen timeframe."],
        ["Fluency Score Metric", "st.metric('Fluency Score')", "Displays latest speech fluency score (%).", "Shows current fluency level in green (>78%) or red/amber (<78%)."],
        ["Disfluency Breakdown", "px.pie() / px.bar()", "Categorizes disfluency types.", "Shows proportion of Blocks, Repetitions, and Prolongations."],
        ["Fluency Trendline", "go.Scatter()", "Plots daily scores and 7-day moving average.", "Visualizes long-term speech progress over weeks and months."],
        ["Session History Table", "st.dataframe()", "Lists individual recording logs.", "Allows searching and sorting past session records by date or stutter type."],
        ["Report Download", "st.download_button()", "Exports session data to CSV/PDF.", "Downloads session metrics for speech therapist review."]
    ]
    add_styled_table(widget_headers, widget_data)

    add_h2("4.3 Dashboard Wireframe Layout")
    doc.add_paragraph(
        "This diagram shows the layout of our metric tiles, fluency trendlines, disfluency charts, and session logs."
    )
    add_diagram_image("dashboard_wireframe.png", "Streamlit Dashboard Wireframe Layout")

    # ----------------------------------------------------
    # SECTION 5: SOFTWARE MODULES
    # ----------------------------------------------------
    add_h1("5. Software Processing Pipeline Modules")
    
    doc.add_paragraph(
        "Our host software runs through seven steps in sequence. Each module handles one specific job."
    )

    modules_headers = ["Module Name", "Input", "Output", "Responsibility", "Key Benefit"]
    modules_data = [
        ["1. Audio Receiver", "HTTP POST Stream", "Saved WAV File", "Receives network WAV upload, checks headers, saves file to buffer folder.", "Prevents corrupt audio packets from entering the processing pipeline."],
        ["2. Noise Filter", "WAV File Path", "Denoised Float32 Array", "Applies spectral gating and 80Hz-4000Hz bandpass filtering to remove background noise.", "Improves signal-to-noise ratio (SNR) for noisy home environments."],
        ["3. Speaker Verifier", "Denoised Array + User ID", "Match Result (Boolean)", "Compares speaker embedding against stored baseline using cosine similarity.", "Ensures speech analytics belong to the registered patient, discarding background voices."],
        ["4. Feature Extractor", "Denoised Audio Array", "MFCC Tensor (39 x T)", "Calculates 13 MFCCs, Delta, and Delta-Delta coefficients across 25ms windows.", "Converts raw audio samples into compact 39-dimensional spectral features."],
        ["5. AI Predictor Interface", "MFCC Tensor", "Prediction Dictionary", "Runs CNN-LSTM neural network inference to classify speech frames as Fluent or Stuttered.", "Wraps deep learning model execution inside clean Python functions."],
        ["6. Database Layer", "Prediction Dictionary", "SQLite Row ID", "Executes SQL INSERT queries and updates session records.", "Ensures persistent local storage of all disfluency scores."],
        ["7. Dashboard Visualizer", "SQLite DB Queries", "Web UI Elements", "Queries session records and plots interactive fluency graphs on the web UI.", "Separates user display logic from backend API handling."]
    ]
    add_styled_table(modules_headers, modules_data)

    # ----------------------------------------------------
    # SECTION 6: REST API SPECIFICATION
    # ----------------------------------------------------
    add_h1("6. REST API Endpoints & Specification")
    
    add_h2("6.1 API Design Principles")
    doc.add_paragraph(
        "Our REST API uses standard HTTP GET and POST methods, returning JSON payloads with standard status codes."
    )

    api_headers = ["Method", "Endpoint Path", "Request Body / Params", "Status Code", "Description"]
    api_data = [
        ["GET", "/api/v1/health", "None", "200 OK", "Checks host server status and database connectivity."],
        ["POST", "/api/v1/audio/upload", "multipart/form-data (audio file, user_id)", "200 OK", "Accepts WAV audio upload from ESP32, runs pipeline, and returns fluency prediction."],
        ["GET", "/api/v1/predictions/{user_id}", "Params: user_id, start_date", "200 OK", "Returns historical prediction logs for a specific patient."],
        ["GET", "/api/v1/session/latest", "Params: user_id", "200 OK", "Fetches the latest prediction score for immediate ESP32 display updates."]
    ]
    add_styled_table(api_headers, api_data)

    add_h2("6.2 Example JSON Request & Response")
    doc.add_paragraph("JSON response returned by `/api/v1/audio/upload` to the ESP32:")
    add_code_block(
        "{\n"
        "  \"status\": \"success\",\n"
        "  \"prediction_id\": 171,\n"
        "  \"timestamp\": \"2026-08-05T21:21:40Z\",\n"
        "  \"user_id\": 1,\n"
        "  \"fluency_score\": 94.8,\n"
        "  \"stutter_detected\": false,\n"
        "  \"stutter_type\": \"Fluent\",\n"
        "  \"confidence\": 0.97,\n"
        "  \"display_message\": \"Fluency: 94.8% (Fluent)\"\n"
        "}"
    )

    add_h2("6.3 Future JWT Authentication")
    doc.add_paragraph(
        "For public Wi-Fi setups, JWT authentication will work as follows:"
    )
    doc.add_paragraph("1. Login: Send credentials to `POST /api/v1/auth/login`.")
    doc.add_paragraph("2. Receive token: Server sends back a signed JWT token.")
    doc.add_paragraph("3. Call APIs: Include `Authorization: Bearer <JWT_TOKEN>` in request headers.")

    # ----------------------------------------------------
    # SECTION 7: CLOUD INTEGRATION
    # ----------------------------------------------------
    add_h1("7. Future Scope: Cloud Integration & Remote Access")
    
    doc.add_paragraph(
        "While everything runs on the laptop right now via SQLite, VoxFlow can scale up to cloud syncing."
    )

    add_callout(
        "Cloud Synchronization Engine:\n"
        "• Local SQLite database acts as a primary buffer so no data gets lost during Wi-Fi drops.\n"
        "• A background worker (`CloudSyncWorker`) checks un-synced rows (`synced_flag = 0`).\n"
        "• When Internet is available, it uploads records to Firebase Firestore or MongoDB Atlas.\n"
        "• Speech therapists view real-time patient charts through a web app.",
        "CLOUD SYNC ARCHITECTURE"
    )

    # ----------------------------------------------------
    # SECTION 8: DASHBOARD DESIGN
    # ----------------------------------------------------
    add_h1("8. Dashboard UI Structure")
    
    doc.add_paragraph(
        "Our Streamlit dashboard UI breaks down into five sections:"
    )
    doc.add_paragraph("1. Top Banner: Shows patient profile info and live status.")
    doc.add_paragraph("2. Metric Cards: Shows Fluency Score, Disfluency Count, Mean Score, and Model Confidence.")
    doc.add_paragraph("3. Main Trend Chart: Line graph plotting daily fluency scores and 7-day moving averages.")
    doc.add_paragraph("4. Categorical Breakdown: Donut chart showing Fluent vs. Stuttered event counts.")
    doc.add_paragraph("5. Session History Table: Searchable table listing past recording logs with CSV download.")

    # ----------------------------------------------------
    # SECTION 9: DATABASE SCHEMA
    # ----------------------------------------------------
    add_h1("9. Complete Database DDL SQL Queries")
    
    doc.add_paragraph("These SQL statements create our SQLite tables (`voxflow_local.db`):")

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
    add_h1("10. Software Processing Flowchart")
    
    doc.add_paragraph(
        "Here is the execution path from receiving Wi-Fi audio to updating the OLED display and Streamlit dashboard:"
    )
    add_diagram_image("flowchart.png", "Software Processing Flowchart for VoxFlow")

    doc.add_paragraph("Step-by-Step Flow:")
    doc.add_paragraph("1. ESP32 sends WAV stream over Wi-Fi via POST.")
    doc.add_paragraph("2. Flask saves WAV bytes to `./audio_buffer/`.")
    doc.add_paragraph("3. Spectral filter cuts background noise.")
    doc.add_paragraph("4. Speaker verifier checks MFCC similarity against baseline.")
    doc.add_paragraph("5. Extractor pulls 13 MFCCs, Delta, and Delta-Delta features.")
    doc.add_paragraph("6. CNN-LSTM model predicts fluency probability.")
    doc.add_paragraph("7. Result gets stored in SQLite DB.")
    doc.add_paragraph("8. Streamlit dashboard reloads graph views.")
    doc.add_paragraph("9. Flask sends JSON response to ESP32 to update OLED/LEDs.")

    # ----------------------------------------------------
    # SECTION 11: SOFTWARE ARCHITECTURE
    # ----------------------------------------------------
    add_h1("11. Tiered Software Architecture")
    
    doc.add_paragraph(
        "Our host system uses a 5-tier architecture:"
    )
    add_diagram_image("architecture.png", "5-Tiered Software Architecture Diagram")

    doc.add_paragraph("Tier Breakdown:")
    doc.add_paragraph("• Edge Hardware Tier: ESP32, INMP441 microphone, OLED, LEDs.")
    doc.add_paragraph("• API Ingestion Tier: Flask REST WSGI server.")
    doc.add_paragraph("• Audio & AI Processing Tier: Denoising filter, speaker verifier, MFCC extractor, CNN-LSTM model.")
    doc.add_paragraph("• Persistence Tier: SQLite local database and file buffer.")
    doc.add_paragraph("• Presentation Tier: Streamlit web dashboard and CSV exporter.")

    # ----------------------------------------------------
    # SECTION 12: UML DIAGRAMS
    # ----------------------------------------------------
    add_h1("12. Object-Oriented UML Diagrams")
    
    doc.add_paragraph(
        "Below are formal UML diagrams showing our class structures, sequence calls, activity paths, and communication flows."
    )

    add_h2("12.1 UML Class Diagram")
    doc.add_paragraph("Shows host software classes, methods, and associations.")
    add_diagram_image("class_diagram.png", "UML Class Diagram")

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
    doc.add_paragraph("Shows message flow between ESP32, Flask server, processing modules, SQLite DB, and Streamlit UI.")
    add_diagram_image("sequence_diagram.png", "UML Sequence Diagram")

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
    doc.add_paragraph("Shows decision steps for noise filtering, speaker verification, and disfluency prediction.")
    add_diagram_image("activity_diagram.png", "UML Activity Diagram")

    add_h2("12.4 UML Communication Diagram")
    doc.add_paragraph("Shows object relationships and numbered message calls during audio processing.")
    add_diagram_image("communication_diagram.png", "UML Communication Diagram")

    # Save Document safely with permission fallback
    try:
        doc.save(output_docx)
        print(f"Document successfully saved to main path: {output_docx}")
    except PermissionError:
        doc.save(output_fallback)
        print(f"Main file was locked by Word. Saved humanized report to fallback path: {output_fallback}")

if __name__ == "__main__":
    create_report()
