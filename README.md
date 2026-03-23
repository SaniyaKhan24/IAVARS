# IAVARS — Intelligent Agent-Based Video Asset Retrieval System

> **AI Agent Layer** — Built with Python · LangChain · Streamlit · OpenAI

---

## What is IAVARS?

IAVARS is a Generative AI project that uses an **LLM-powered ReAct agent** to
automatically download and organise video assets listed in an Excel spreadsheet.

A user uploads a spreadsheet containing video links (from YouTube, Google Drive,
Vimeo, Dropbox, or direct file URLs) and types a natural language instruction.
The AI agent interprets the instruction, detects platforms, chooses the right
download tool for each link, organises the files, and produces a structured report.

---

## Project Structure

```
IAVARS/
│
├── agent/                  # AI Agent Layer  ← this repo
│   ├── ai_agent.py         # Main LangChain agent controller
│   ├── prompts.py          # System prompts and instruction templates
│   └── tools.py            # LangChain @tool definitions (8 tools)
│
├── services/
│   ├── platform_detector.py   # URL → platform classifier (regex)
│   └── instruction_parser.py  # Natural language → structured command
│
├── ui/
│   └── streamlit_app.py    # Streamlit web UI
│
├── config/
│   └── llm_config.py       # LLM provider setup (OpenAI)
│
├── utils/
│   └── helpers.py          # Shared utilities (folders, filenames, logging)
│
├── .env.example            # Environment variable template
├── requirements.txt        # Python dependencies
└── README.md
```

---

## Agent Workflow

```
User instruction + Excel file
           │
           ▼
  ┌─────────────────────────────────────┐
  │     LangChain Tool-Calling Agent    │
  │  (gpt-4o-mini / any OpenAI model)  │
  └──────────────┬──────────────────────┘
                 │  reasons & calls tools in order:
                 ▼
  1. parse_spreadsheet          load rows from Excel / CSV
  2. extract_urls               find all video URLs
  3. detect_platforms           classify each URL by platform
  4. filter_urls                apply user's filter criteria
  5. create_download_folders    mkdir downloads/{platform}/
  6. download_videos            download to correct folder
  7. organize_files             group by platform / brand / type
  8. generate_report            produce structured JSON report
```

### Output folder structure

```
downloads/
├── youtube/
├── google_drive/
├── vimeo/
├── dropbox/
├── direct_files/
└── unknown/
reports/
└── iavars_report_YYYYMMDD_HHMMSS.json
```

### Result schema

```json
{
  "action_plan":     ["Step 1 — ...", "Step 2 — ..."],
  "platform_groups": {"youtube": ["url1", "url2"], "vimeo": ["url3"]},
  "download_status": {
    "https://youtu.be/xyz": {"status": "success", "platform": "youtube", "destination": "..."}
  },
  "summary":         {"total_urls": 10, "succeeded": 9, "failed": 1},
  "errors":          [{"url": "...", "error": "..."}]
}
```

---

## Supported Platforms

| Platform | Example URL pattern |
|---|---|
| YouTube | `youtube.com/watch?v=…`, `youtu.be/…` |
| Google Drive | `drive.google.com/…` |
| Vimeo | `vimeo.com/123456` |
| Dropbox | `dropbox.com/s/…` |
| Direct files | Any URL ending in `.mp4`, `.mov`, `.mkv`, … |

---

## Quick Start

### 1 — Clone & install

```bash
git clone https://github.com/SaniyaKhan24/IAVARS.git
cd IAVARS
pip install -r requirements.txt
```

### 2 — Configure API key

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...
```

### 3 — Launch the UI

```bash
streamlit run ui/streamlit_app.py
```

### 4 — Or run from the command line

```bash
python agent/ai_agent.py path/to/links.xlsx \
  --instruction "Download only advertisement videos" \
  --output-dir ./output
```

---

## Backend Integration Guide

The agent layer is designed to integrate with separately implemented backend
modules.  Look for comments tagged `# BACKEND:` in [agent/tools.py](agent/tools.py).

Replace the stub `_stub_download()` function with real calls:

```python
# BACKEND developer: replace the body of _stub_download() with:
from backend.youtube_downloader import download as yt_download
from backend.gdrive_downloader  import download as gd_download
# etc.
```

The function contract is:
- **Input:** `url: str`, `platform: str`, `dest_folder: str`
- **Output:** absolute path of the saved file (str)
- **On failure:** raise any `Exception` — the agent handles it gracefully

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | **Required.** Your OpenAI secret key |
| `LLM_MODEL` | `gpt-4o-mini` | Any OpenAI chat model name |
| `LLM_TEMPERATURE` | `0` | 0 = deterministic, 1 = creative |
| `MAX_AGENT_ITERATIONS` | `15` | Safety cap on reasoning steps |

---

## Tech Stack

- **LangChain** — agent framework and tool-calling
- **OpenAI GPT-4o-mini** — default LLM (swappable)
- **Streamlit** — web UI
- **Pandas / openpyxl** — spreadsheet parsing
- **Python 3.10+**