"""
IAVARS — LangChain Tool Definitions
=====================================
Each function decorated with @tool becomes a capability the LLM agent can
invoke during its reasoning loop.  The LLM reads the docstring of every tool
to decide when and how to call it, so docstrings must be clear and concise.

INTEGRATION GUIDE (for backend developer)
──────────────────────────────────────────
Look for comments tagged  # BACKEND:  — these mark the exact lines where you
replace stub code with real downloader / parser calls.

Function signatures and JSON return formats must not change; only the internal
implementation of each stub should be replaced.

Tool execution order expected by the agent:
  1. parse_spreadsheet
  2. extract_urls
  3. detect_platforms
  4. filter_urls
  5. create_download_folders_tool
  6. download_videos
  7. organize_files
  8. generate_report
"""

import json
import os
import re
from typing import Optional

import pandas as pd
from langchain_core.tools import tool

from services.platform_detector import detect_platform
from services.instruction_parser import parse_instruction
from utils.helpers import (
    PLATFORM_FOLDERS,
    create_download_folders,
    sanitize_filename,
    save_json_report,
    timestamp_suffix,
    url_to_filename,
    logger,
)


# ══════════════════════════════════════════════════════════════════════════════
# Tool 1 — Parse Spreadsheet
# ══════════════════════════════════════════════════════════════════════════════

@tool
def parse_spreadsheet(file_path: str) -> str:
    """
    Read an Excel (.xlsx / .xls) or CSV spreadsheet and return its contents.
    This must be the FIRST tool called.  Provide the full file path.
    Returns a JSON string with keys: columns, row_count, rows.
    """
    try:
        file_path = file_path.strip().strip('"').strip("'")

        if file_path.lower().endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path, engine="openpyxl")

        result = {
            "columns": df.columns.tolist(),
            "row_count": len(df),
            "rows": df.fillna("").astype(str).to_dict(orient="records"),
        }
        logger.info("parse_spreadsheet: %d rows, %d columns", len(df), len(df.columns))
        return json.dumps(result)

    except FileNotFoundError:
        return json.dumps({"error": f"File not found: {file_path}"})
    except Exception as exc:
        logger.error("parse_spreadsheet failed: %s", exc)
        return json.dumps({"error": str(exc)})


# ══════════════════════════════════════════════════════════════════════════════
# Tool 2 — Extract URLs
# ══════════════════════════════════════════════════════════════════════════════

@tool
def extract_urls(spreadsheet_json: str, url_column: str = "") -> str:
    """
    Extract all video URLs from the parsed spreadsheet JSON.
    Pass the JSON string returned by parse_spreadsheet.
    Optionally supply the exact column name that contains URLs; if omitted the
    column is auto-detected by name hints and content inspection.
    Returns a JSON string with keys: url_count, url_column_detected, urls (list).
    """
    try:
        data = json.loads(spreadsheet_json)
        if "error" in data:
            return spreadsheet_json  # propagate error downstream

        rows: list = data.get("rows", [])
        columns: list = data.get("columns", [])

        url_col: Optional[str] = url_column.strip() or _auto_detect_url_column(columns, rows)

        url_pattern = re.compile(r"https?://[^\s\"'>]+", re.IGNORECASE)
        found: list = []

        for idx, row in enumerate(rows):
            if url_col and url_col in row:
                # Targeted extraction from the known URL column
                cell = str(row[url_col]).strip()
                if url_pattern.search(cell):
                    found.append({
                        "row_index": idx,
                        "url": cell,
                        "source_column": url_col,
                        "metadata": {k: v for k, v in row.items() if k != url_col},
                    })
            else:
                # Fallback: scan every column for URL-like strings
                for col, val in row.items():
                    for match in url_pattern.findall(str(val)):
                        found.append({
                            "row_index": idx,
                            "url": match.rstrip(".,;)\"'"),
                            "source_column": col,
                            "metadata": {k: v for k, v in row.items() if k != col},
                        })

        result = {
            "url_count": len(found),
            "url_column_detected": url_col,
            "urls": found,
        }
        logger.info("extract_urls: found %d URLs", len(found))
        return json.dumps(result)

    except Exception as exc:
        logger.error("extract_urls failed: %s", exc)
        return json.dumps({"error": str(exc)})


def _auto_detect_url_column(columns: list, rows: list) -> Optional[str]:
    """Heuristic: prefer columns whose name contains a URL hint; fall back to content scan."""
    url_hints = ["url", "link", "video", "href", "source", "path", "media"]
    for col in columns:
        if any(hint in col.lower() for hint in url_hints):
            return col
    # Content scan on first row
    url_re = re.compile(r"https?://", re.IGNORECASE)
    if rows:
        for col, val in rows[0].items():
            if url_re.search(str(val)):
                return col
    return None


# ══════════════════════════════════════════════════════════════════════════════
# Tool 3 — Detect Platforms
# ══════════════════════════════════════════════════════════════════════════════

@tool
def detect_platforms(urls_json: str) -> str:
    """
    Detect the hosting platform for every URL in the list.
    Pass the JSON string returned by extract_urls.
    Each URL record will receive a new 'platform' field.
    Returns a JSON string with keys: url_count, platform_distribution, urls.
    """
    try:
        data = json.loads(urls_json)
        if "error" in data:
            return urls_json

        url_records: list = data.get("urls", [])
        distribution: dict = {}

        for record in url_records:
            platform = detect_platform(record.get("url", ""))
            record["platform"] = platform
            distribution[platform] = distribution.get(platform, 0) + 1

        result = {
            "url_count": len(url_records),
            "platform_distribution": distribution,
            "urls": url_records,
        }
        logger.info("detect_platforms: %s", distribution)
        return json.dumps(result)

    except Exception as exc:
        logger.error("detect_platforms failed: %s", exc)
        return json.dumps({"error": str(exc)})


# ══════════════════════════════════════════════════════════════════════════════
# Tool 4 — Filter URLs
# ══════════════════════════════════════════════════════════════════════════════

@tool
def filter_urls(urls_json: str, filter_instruction: str) -> str:
    """
    Filter the URL list based on a natural language instruction.
    Pass the JSON from detect_platforms and the original user instruction text.
    Examples of filter_instruction: 'all', 'youtube only', 'advertisement videos'.
    Returns a JSON string with keys: filter_applied, original_count, filtered_count, urls.
    """
    try:
        data = json.loads(urls_json)
        if "error" in data:
            return urls_json

        url_records: list = data.get("urls", [])
        parsed = parse_instruction(filter_instruction)
        filter_type: str = parsed.get("filter", "all")

        # Platform-based filter
        if filter_type in PLATFORM_FOLDERS:
            filtered = [r for r in url_records if r.get("platform") == filter_type]

        # Content/metadata keyword filter
        elif filter_type != "all":
            kw = filter_type.lower()
            filtered = [
                r for r in url_records
                if kw in json.dumps(r.get("metadata", {})).lower()
                or kw in r.get("url", "").lower()
            ]

        else:
            filtered = url_records  # "all" — no filtering

        result = {
            "filter_applied": filter_type,
            "original_count": len(url_records),
            "filtered_count": len(filtered),
            "urls": filtered,
        }
        logger.info(
            "filter_urls [%s]: %d/%d URLs kept",
            filter_type, len(filtered), len(url_records),
        )
        return json.dumps(result)

    except Exception as exc:
        logger.error("filter_urls failed: %s", exc)
        return json.dumps({"error": str(exc)})


# ══════════════════════════════════════════════════════════════════════════════
# Tool 5 — Create Download Folders
# ══════════════════════════════════════════════════════════════════════════════

@tool
def create_download_folders_tool(base_dir: str = ".") -> str:
    """
    Create the standard platform-based folder tree for video downloads.
    Folders created: downloads/youtube/, downloads/google_drive/,
    downloads/vimeo/, downloads/dropbox/, downloads/direct_files/, downloads/unknown/
    Pass the base directory path (default is current working directory).
    Returns a JSON string with created folder paths.
    """
    try:
        folders = create_download_folders(base_dir.strip() or ".")
        logger.info("create_download_folders_tool: %d folders ready", len(folders))
        return json.dumps({"status": "success", "base_dir": base_dir, "folders": folders})
    except Exception as exc:
        logger.error("create_download_folders_tool failed: %s", exc)
        return json.dumps({"error": str(exc)})


# ══════════════════════════════════════════════════════════════════════════════
# Tool 6 — Download Videos
# ══════════════════════════════════════════════════════════════════════════════

@tool
def download_videos(urls_json: str, output_base_dir: str = ".") -> str:
    """
    Download all videos from the filtered URL list into platform-specific folders.
    Pass the JSON from filter_urls and the output base directory.
    Returns a JSON string with keys: total, succeeded, failed, download_status, errors.

    BACKEND INTEGRATION:
      Inside this function, the stub _stub_download() must be replaced with
      real calls to the platform-specific downloader modules, e.g.:
        from backend.youtube_downloader import download as yt_download
        from backend.gdrive_downloader  import download as gd_download
    """
    try:
        data = json.loads(urls_json)
        if "error" in data:
            return urls_json

        url_records: list = data.get("urls", [])
        output_base_dir = output_base_dir.strip() or "."

        download_status: dict = {}
        errors: list = []

        for record in url_records:
            url: str = record.get("url", "")
            platform: str = record.get("platform", "unknown")
            dest_folder = os.path.join(
                output_base_dir,
                PLATFORM_FOLDERS.get(platform, "downloads/unknown"),
            )
            os.makedirs(dest_folder, exist_ok=True)

            try:
                # ── BACKEND: replace _stub_download with real downloader ──────
                file_path = _stub_download(url, platform, dest_folder)
                # ────────────────────────────────────────────────────────────────

                download_status[url] = {
                    "status": "success",
                    "platform": platform,
                    "destination": file_path,
                }
                logger.info("Downloaded [%s] %s", platform, url)

            except Exception as dl_err:
                error_msg = str(dl_err)
                download_status[url] = {"status": "failed", "platform": platform, "error": error_msg}
                errors.append({"url": url, "platform": platform, "error": error_msg})
                logger.warning("Download failed [%s] %s — %s", platform, url, dl_err)

        result = {
            "total": len(url_records),
            "succeeded": sum(1 for v in download_status.values() if v["status"] == "success"),
            "failed": len(errors),
            "download_status": download_status,
            "errors": errors,
        }
        logger.info(
            "download_videos: %d/%d succeeded", result["succeeded"], result["total"]
        )
        return json.dumps(result)

    except Exception as exc:
        logger.error("download_videos failed: %s", exc)
        return json.dumps({"error": str(exc)})


def _stub_download(url: str, platform: str, dest_folder: str) -> str:
    """
    Stub downloader — simulates a download by writing a placeholder file.

    ┌─────────────────────────────────────────────────────────────────────┐
    │  BACKEND DEVELOPER: replace this function body with real logic.     │
    │  The function must:                                                  │
    │    • download the video at `url` into `dest_folder`                 │
    │    • return the absolute path of the saved file on success          │
    │    • raise any exception on failure (the caller handles it)         │
    └─────────────────────────────────────────────────────────────────────┘
    """
    filename = sanitize_filename(url_to_filename(url))
    file_path = os.path.join(dest_folder, f"[STUB]_{filename}")

    # Write a placeholder so the folder structure is visually verifiable
    with open(file_path, "w", encoding="utf-8") as fh:
        fh.write(f"# IAVARS stub placeholder\n# URL: {url}\n# Platform: {platform}\n")

    return os.path.abspath(file_path)


# ══════════════════════════════════════════════════════════════════════════════
# Tool 7 — Organize Files
# ══════════════════════════════════════════════════════════════════════════════

@tool
def organize_files(download_result_json: str, organize_by: str = "platform") -> str:
    """
    Organise the downloaded video files into logical sub-groups.
    Pass the JSON from download_videos and one of: 'platform', 'brand', 'type'.
    Returns a JSON string with keys: organize_by, groups, group_count, total_organized.
    """
    try:
        data = json.loads(download_result_json)
        if "error" in data:
            return download_result_json

        download_status: dict = data.get("download_status", {})
        organize_by = organize_by.strip().lower() or "platform"

        organized: dict = {}

        for url, info in download_status.items():
            if info.get("status") != "success":
                continue

            if organize_by == "platform":
                key = info.get("platform", "unknown")
            elif organize_by == "brand":
                # BACKEND: enrich info dict with a "brand" field from metadata
                key = info.get("brand", info.get("platform", "unknown"))
            elif organize_by == "type":
                # BACKEND: enrich info dict with a "content_type" field from metadata
                key = info.get("content_type", "general")
            else:
                key = info.get("platform", "unknown")

            organized.setdefault(key, []).append({
                "url": url,
                "file_path": info.get("destination", ""),
            })

        result = {
            "organize_by": organize_by,
            "groups": organized,
            "group_count": len(organized),
            "total_organized": sum(len(v) for v in organized.values()),
        }
        logger.info(
            "organize_files [by %s]: %d files in %d groups",
            organize_by, result["total_organized"], result["group_count"],
        )
        return json.dumps(result)

    except Exception as exc:
        logger.error("organize_files failed: %s", exc)
        return json.dumps({"error": str(exc)})


# ══════════════════════════════════════════════════════════════════════════════
# Tool 8 — Generate Report
# ══════════════════════════════════════════════════════════════════════════════

@tool
def generate_report(
    organized_json: str,
    download_json: str,
    user_instruction: str = "",
    output_dir: str = ".",
) -> str:
    """
    Generate the final structured IAVARS report and save it to disk.
    Pass the JSON strings from organize_files and download_videos,
    the original user instruction text, and the output directory.
    Returns the full report as a JSON string (also saved as a .json file).
    """
    try:
        organized: dict = json.loads(organized_json) if organized_json else {}
        downloads: dict = json.loads(download_json) if download_json else {}

        # Build platform → [urls] mapping from download info
        platform_groups: dict = {}
        for url, info in downloads.get("download_status", {}).items():
            p = info.get("platform", "unknown")
            platform_groups.setdefault(p, []).append(url)

        report = {
            "action_plan": [
                "Step 1 — Parsed spreadsheet and loaded row data",
                "Step 2 — Extracted all video URLs from spreadsheet",
                "Step 3 — Detected hosting platform for each URL",
                "Step 4 — Applied user filter criteria",
                "Step 5 — Created platform-based download folder structure",
                "Step 6 — Downloaded videos into platform-specific folders",
                "Step 7 — Organised files by selected grouping strategy",
                "Step 8 — Generated this structured report",
            ],
            "user_instruction": user_instruction,
            "platform_groups": platform_groups,
            "download_status": downloads.get("download_status", {}),
            "summary": {
                "total_urls":  downloads.get("total", 0),
                "succeeded":   downloads.get("succeeded", 0),
                "failed":      downloads.get("failed", 0),
            },
            "organized_structure": organized.get("groups", {}),
            "errors": downloads.get("errors", []),
        }

        # Save report to disk
        report_path = os.path.join(
            output_dir.strip() or ".",
            f"reports/iavars_report_{timestamp_suffix()}.json",
        )
        save_json_report(report, report_path)

        logger.info("generate_report: report saved → %s", report_path)
        return json.dumps(report, indent=2)

    except Exception as exc:
        logger.error("generate_report failed: %s", exc)
        return json.dumps({"error": str(exc)})


# ─── Tool Registry (convenient import for ai_agent.py) ───────────────────────

ALL_TOOLS = [
    parse_spreadsheet,
    extract_urls,
    detect_platforms,
    filter_urls,
    create_download_folders_tool,
    download_videos,
    organize_files,
    generate_report,
]
