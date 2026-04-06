# 🎬 Intelligent Agent-Based Video Asset Retrieval System (IAVARS)

**Automated bulk video retrieval, organization, and cloud storage management powered by intelligent agent orchestration and LLM-driven classification.**

[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-darkgreen?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [System Architecture](#system-architecture)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Usage](#usage)
7. [Project Structure](#project-structure)
8. [API Endpoints](#api-endpoints)
9. [Pipeline Workflow](#pipeline-workflow)
10. [Troubleshooting](#troubleshooting)
11. [Contributing](#contributing)
12. [License](#license)

---

## 🎯 Overview

IAVARS is an enterprise-grade, multi-stage pipeline system designed to streamline the bulk retrieval of video assets from diverse online platforms. It automates the complex workflows associated with:

- **Data Ingestion** – Parse spreadsheets (Excel/CSV) containing multimedia URLs
- **Intelligent Classification** – Use LLM reasoning to classify links and assign appropriate retrieval strategies
- **Parallel Execution** – Leverage autonomous agents to download assets concurrently
- **Cloud Storage** – Automatically organize and upload retrieved files to Google Drive
- **Reporting** – Generate comprehensive success/failure reports and audit trails

**Ideal for:** Marketing teams, content distributors, archivists, and media professionals managing large-scale video inventory.

---

## ✨ Key Features

### 1. **Multi-Platform Support**

- YouTube (public, unlisted, and private videos)
- Google Drive files
- Direct CDN and MP4 links
- Extensible architecture for new platforms

### 2. **LLM-Powered Intelligence**

- Semantic URL classification without hardcoded rules
- Contextual platform detection
- Adaptive tool assignment based on link characteristics
- Support for natural language constraints and filtering

### 3. **High-Performance Processing**

- Parallel execution via thread pooling (configurable workers)
- Retry logic with exponential backoff
- Streaming downloads to minimize memory footprint
- Automatic duplicate detection and removal

### 4. **Cloud Integration**

- Direct integration with Google Drive API
- Hierarchical folder organization based on platform/category
- Semantic file renaming using metadata
- Real-time sync capabilities

### 5. **Comprehensive Monitoring**

- JSONL-formatted audit logs with detailed telemetry
- Real-time progress updates and status tracking
- Structured error reporting
- HTML summary reports and broken-link detection

### 6. **Web-Based Interface**

- FastAPI REST backend with OpenAPI documentation
- Responsive HTML/CSS/JavaScript frontend
- File upload drag-and-drop support
- Real-time status streaming

---

## 🏗️ System Architecture

### High-Level Data Flow

```
┌─────────────────┐
│  User Upload    │
│  (Excel/CSV)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  Input Layer            │
│ (URL Extraction)        │
│ • Parse spreadsheet     │
│ • Regex sanitization    │
│ • Deduplication         │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  LLM Classification     │
│ • Platform detection    │
│ • Tool recommendation   │
│ • Domain analysis       │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Agent Assignment       │
│ • Match agents to tools │
│ • Load configurations   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Execution Layer        │
│ • Parallel downloads    │
│ • Retry logic           │
│ • Error handling        │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Storage & Sync         │
│ • Cloud upload          │
│ • Organization          │
│ • Report generation     │
└─────────────────────────┘
```

### Module Breakdown

| Module               | Responsibility                                   | Key Files                               |
| -------------------- | ------------------------------------------------ | --------------------------------------- |
| **Input Layer**      | Excel parsing, URL extraction, duplicate removal | `pipeline/url_extractor.py`             |
| **Classification**   | Platform detection, tool mapping                 | `pipeline/url_classifier.py`            |
| **Agent Assignment** | Autonomous agent orchestration                   | `pipeline/agent_assigner.py`            |
| **Execution**        | Download execution, retry logic, JSONL logging   | `pipeline/agent_executor.py`            |
| **API Backend**      | FastAPI endpoints, file serving                  | `api.py`                                |
| **Frontend**         | Web UI for uploads and monitoring                | `index.html`, `styles.css`, `script.js` |

---

## 📦 Installation

### Prerequisites

- **Python 3.8+** (3.10+ recommended)
- **pip** (Python package manager)
- **yt-dlp** (system binary for YouTube downloads)
- **Google Cloud Service Account** (for Drive integration)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd IAVARS
```

### Step 2: Create Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install System Dependencies

**For YouTube Support (yt-dlp):**

```bash
# On Windows (via pip)
pip install yt-dlp

# On macOS (via Homebrew)
brew install yt-dlp

# On Linux (via package manager)
sudo apt install yt-dlp  # Debian/Ubuntu
sudo yum install yt-dlp  # RedHat/CentOS
```

**For Google Drive Support (gdown):**

```bash
pip install gdown
```

### Step 5: Configure Google Cloud Credentials

1. Create a service account on [Google Cloud Console](https://console.cloud.google.com/)
2. Download the service account JSON file
3. Set the environment variable:

```bash
# On Windows (PowerShell)
$env:GOOGLE_CREDENTIALS_JSON = "C:\path\to\service_account.json"

# On macOS/Linux
export GOOGLE_CREDENTIALS_JSON="/path/to/service_account.json"
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Google Cloud
GOOGLE_CREDENTIALS_JSON=path/to/service_account.json
GOOGLE_DRIVE_FOLDER_ID=your_root_folder_id

# LLM Configuration (if using external API)
LLM_API_KEY=your_api_key
LLM_MODEL=your_model_name

# Server
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Processing
MAX_WORKERS=4
MAX_RETRIES=2
MAX_FILE_SIZE=52428800  # 50 MB
```

### Application Settings

Edit `pipeline/main.py` to customize:

```python
MAX_RETRIES = 2          # Number of retry attempts per download
MAX_WORKERS = 4          # Thread pool size for parallel execution
TIMEOUT_SECONDS = 300    # Download timeout (seconds)
```

---

## 🚀 Usage

### Option 1: Web Interface (Recommended)

1. **Start the API server:**

   ```bash
   python api.py
   ```

2. **Open the web interface:**

   Navigate to `http://localhost:8000` in your browser

3. **Upload spreadsheet:**
   - Drag and drop an Excel/CSV file
   - View real-time processing updates
   - Download results and reports

### Option 2: Python API (Programmatic)

```python
from pipeline.main import run_pipeline

# Process a spreadsheet
records, summary = run_pipeline("path/to/your_video_links.xlsx")

# Print results
print(f"Total: {summary['total']}")
print(f"Success: {summary['success']}")
print(f"Failure: {summary['failure']}")

# Access individual records
for record in records:
    print(f"URL: {record['url']}")
    print(f"Status: {record['status']}")
    print(f"Message: {record['message']}")
```

### Option 3: Command Line

```bash
# Run the pipeline directly
python run.py tests/sample_input.csv

# Start API server
python api.py

# Generate report from logs
python report_generator.py
```

### Option 4: Batch Scripts

**Windows:**

```bash
start_api.bat
```

**Unix/macOS:**

```bash
bash start_api.sh
```

---

## 📁 Project Structure

```
IAVARS/
├── api.py                          # FastAPI backend and REST endpoints
├── index.html                      # Web UI (frontend)
├── styles.css                      # Styling
├── script.js                       # Frontend logic
├── run.py                          # CLI entry point
├── report_generator.py             # Report generation utilities
├── requirements.txt                # Python dependencies
│
├── pipeline/                       # Core processing modules
│   ├── __init__.py
│   ├── main.py                     # Main pipeline orchestrator
│   ├── url_extractor.py            # Excel parsing & URL extraction
│   ├── url_classifier.py           # LLM-based classification
│   ├── agent_assigner.py           # Agent assignment logic
│   ├── agent_executor.py           # Download execution & retry logic
│   └── storage.py                  # Google Drive integration
│
├── tests/                          # Test suite
│   ├── sample_input.csv            # Sample input file
│   ├── test_url_extractor.py
│   ├── test_url_classifier.py
│   ├── test_agent_assigner.py
│   └── test_agent_executor.py
│
├── downloads/                      # Local video storage
├── logs/                           # Audit logs
│   └── download_log.jsonl          # Structured download records
│
├── INTEGRATION_GUIDE.md            # API integration documentation
├── system_architecture.md          # Detailed architecture reference
└── README.md                       # This file
```

---

## 🔌 API Endpoints

### Health Check

```http
GET /health
```

**Response:**

```json
{
  "status": "ok",
  "message": "Video Asset Processing API is running"
}
```

### Process Videos

```http
POST /api/process-videos/
Content-Type: multipart/form-data

file: <Excel/CSV file>
```

**Response:**

```json
{
  "records": [
    {
      "url": "https://www.youtube.com/watch?v=abc123",
      "platform": "YouTube_Public",
      "status": "success",
      "message": "Downloaded -> downloads/youtube_ab12.mp4",
      "download_link": "http://localhost:8000/downloads/youtube_ab12.mp4",
      "timestamp": "2026-04-06T12:00:00.000000+00:00"
    }
  ],
  "summary": {
    "total": 1,
    "success": 1,
    "failure": 0
  }
}
```

### Download File

```http
GET /downloads/{filename}
```

Returns the downloaded video file.

### API Documentation

Access interactive API docs at:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 🔄 Pipeline Workflow

### Step 1: URL Extraction

- Reads Excel/CSV spreadsheet
- Identifies URL columns via regex
- Validates and sanitizes URLs
- Removes duplicates
- Extracts metadata (title, category, etc.)

**Input:** Excel file
**Output:** Structured JSON with URLs and metadata

### Step 2: URL Classification

- Sends URL batch to LLM
- Classifies platform (YouTube, Google Drive, CDN, etc.)
- Determines asset type (video, audio, document)
- Recommends retrieval tool (yt-dlp, gdown, requests)

**Input:** JSON manifest
**Output:** Classification and tool assignment

### Step 3: Agent Assignment

- Matches agents to tools
- Loads platform-specific configurations
- Prepares execution batches
- Assigns retry strategies

**Input:** Classified records
**Output:** Agent-assigned task queue

### Step 4: Execution

- Spawns thread pool workers
- Downloads assets in parallel
- Implements retry logic on failure
- Logs each result to JSONL
- Updates status in real-time

**Input:** Task queue
**Output:** Downloaded files + JSONL log

### Step 5: Cloud Storage & Reporting

- Uploads files to Google Drive
- Organizes into hierarchical folders
- Renames files based on metadata
- Generates success/failure reports
- Creates audit trail

**Input:** Downloaded files + metadata
**Output:** Organized Drive structure + reports

---

## 🆘 Troubleshooting

### Issue: `yt-dlp executable not found`

**Solution:**

```bash
pip install yt-dlp
# Verify installation
yt-dlp --version
```

### Issue: `GOOGLE_CREDENTIALS_JSON environment variable not set`

**Solution:**

```bash
# Set environment variable
export GOOGLE_CREDENTIALS_JSON="/path/to/service_account.json"

# Verify
echo $GOOGLE_CREDENTIALS_JSON
```

### Issue: Downloads timeout

**Solution:** Increase timeout in `pipeline/agent_executor.py`:

```python
TIMEOUT_SECONDS = 600  # Increase from 300 to 600
```

### Issue: API fails to start on port 8000

**Solution:** Use a different port:

```bash
python api.py --port 8001
```

### Issue: File permissions denied on downloads folder

**Solution:**

```bash
# Linux/macOS
chmod -R 755 downloads/

# Or recreate the folder
rm -rf downloads && mkdir downloads
```

### Issue: LLM Classification returning incorrect platforms

**Solution:** Check `url_classifier.py` for classification rules and update prompts if needed.

---

## 📊 Sample Input Format

### CSV Format

```csv
Video Link,Title,Category,Campaign
https://www.youtube.com/watch?v=abc123,Promo Video 1,Commercial,Q1_2026
https://drive.google.com/file/d/xyz789/view,Product Demo,Tutorial,Q2_2026
https://example.com/video.mp4,Archived Content,Archive,Backup
```

### Excel Format

- Column headers: Video Link, Title, Category, Campaign
- Multiple sheets supported
- Handles up to 1M+ rows with chunked processing

---

## 📈 Output Examples

### Success Record (JSONL)

```json
{
  "url": "https://www.youtube.com/watch?v=UyefASVrtbw",
  "status": "success",
  "platform": "YouTube_Public",
  "message": "Downloaded -> downloads/youtube_abc123.mp4",
  "timestamp": "2026-04-06T06:50:38.431883+00:00",
  "file_path": "downloads/youtube_abc123.mp4",
  "file_size": 52428800
}
```

### Failure Record (JSONL)

```json
{
  "url": "https://www.youtube.com/watch?v=broken",
  "status": "failure",
  "platform": "YouTube_Public",
  "message": "Video unavailable or restricted",
  "timestamp": "2026-04-06T06:50:39.431883+00:00",
  "link_status": "broken"
}
```

---

## 🔐 Security Considerations

1. **Credential Management**
   - Never commit `.env` files or service account JSON
   - Use environment variables for sensitive data
   - Rotate service account keys regularly

2. **File Upload Restrictions**
   - Maximum file size: 50 MB (configurable)
   - Allowed types: `.csv`, `.xlsx` only
   - Validate file types server-side

3. **CORS Configuration**
   - Adjust `allow_origins` in `api.py` for production
   - Restrict to specific domains instead of `["*"]`

4. **Logging**
   - JSONL logs contain URLs; secure access accordingly
   - Consider personally identifiable information (PII)
   - Implement log rotation for large datasets

---

## 🧪 Testing

### Run Unit Tests

```bash
pytest tests/

# Run specific test
pytest tests/test_url_classifier.py

# Run with coverage
pytest --cov=pipeline tests/
```

### Test Sample Data

A sample input file is provided at `tests/sample_input.csv`:

```bash
python run.py tests/sample_input.csv
```

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/my-feature`)
3. **Commit** changes (`git commit -m 'Add my feature'`)
4. **Push** to branch (`git push origin feature/my-feature`)
5. **Open** a Pull Request

### Developer Guidelines

- Follow PEP 8 style guide
- Add docstrings to all functions
- Include unit tests for new features
- Update documentation accordingly

---

## 📝 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## 📞 Support & Contact

For issues, questions, or feature requests:

- **Issues:** Open a GitHub issue
- **Documentation:** See [system_architecture.md](system_architecture.md) and [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- **Email:** [Your contact email]

---

## 🙏 Acknowledgments

- **yt-dlp** – Video downloader
- **FastAPI** – Web framework
- **Google Drive API** – Cloud storage
- **pandas** – Data processing
- **LLM (Claude/GPT)** – Classification intelligence

---

## 📅 Version History

| Version | Date       | Changes                            |
| ------- | ---------- | ---------------------------------- |
| 1.0.0   | 2026-04-06 | Initial release with core pipeline |
| 0.9.0   | 2026-03-15 | Beta with web interface            |
| 0.1.0   | 2026-02-01 | Alpha prototype                    |

---

**Last Updated:** April 6, 2026  
**Status:** ✅ Production Ready
