"""
IAVARS — Streamlit User Interface
===================================
The primary web interface for the Intelligent Agent-Based Video Asset
Retrieval System.

Run with:
    streamlit run ui/streamlit_app.py

Features:
  • Upload an Excel / CSV spreadsheet with video URLs
  • Type a natural language instruction
  • Launch the AI agent and watch real-time progress
  • View metrics, platform groups, download status, and errors in tabs
  • Download the full JSON report
"""

import json
import os
import sys
import tempfile

import streamlit as st

# ── Ensure project root is importable regardless of working directory ──────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from services.platform_detector import PLATFORM_PATTERNS

# ─── Page Configuration ───────────────────────────────────────────────────────

st.set_page_config(
    page_title="IAVARS — Video Asset Retrieval",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    .metric-box {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 18px;
        text-align: center;
    }
    .stButton > button[kind="primary"] {
        width: 100%;
        font-size: 1.1rem;
        padding: 0.6rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🎬 IAVARS")
    st.caption("Intelligent Agent-Based\nVideo Asset Retrieval System")
    st.divider()

    st.markdown("#### Supported Platforms")
    platform_icons = {
        "youtube": "▶️",
        "google_drive": "📁",
        "vimeo": "🎥",
        "dropbox": "📦",
        "direct_files": "🔗",
    }
    for platform in PLATFORM_PATTERNS.keys():
        icon = platform_icons.get(platform, "•")
        st.markdown(f"{icon} &nbsp; **{platform.replace('_', ' ').title()}**", unsafe_allow_html=True)

    st.divider()
    st.markdown("#### Example Instructions")
    examples = [
        "Download all videos",
        "Download only advertisement videos",
        "Organize videos platform-wise",
        "Download videos and group them by brand",
        "Validate all links first",
    ]
    for ex in examples:
        st.code(ex, language=None)

    st.divider()
    st.markdown("#### Output Structure")
    st.code(
        "downloads/\n"
        "  youtube/\n"
        "  google_drive/\n"
        "  vimeo/\n"
        "  dropbox/\n"
        "  direct_files/\n"
        "reports/",
        language=None,
    )

# ─── Main Header ──────────────────────────────────────────────────────────────

st.title("🎬 IAVARS — Video Asset Retrieval Agent")
st.markdown(
    "Upload a spreadsheet with video links and give the AI agent a natural language "
    "instruction.  The agent will detect platforms, download assets, organise them, "
    "and produce a structured report."
)

# ─── Input Section ────────────────────────────────────────────────────────────

col_upload, col_instruction = st.columns([1, 1], gap="large")

with col_upload:
    uploaded_file = st.file_uploader(
        "📂 Upload Spreadsheet",
        type=["xlsx", "xls", "csv"],
        help="Your file should contain at least one column with video URLs.",
    )
    if uploaded_file:
        st.success(f"✅ File ready: **{uploaded_file.name}**")

with col_instruction:
    user_instruction = st.text_area(
        "💬 Natural Language Instruction",
        placeholder="e.g.  Download all videos and organise them by platform",
        height=130,
        help="Tell the agent exactly what you want — it understands plain English.",
    )

# ─── Advanced Options ─────────────────────────────────────────────────────────

with st.expander("⚙️ Advanced options"):
    output_dir = st.text_input(
        "Output directory",
        value=".",
        help="Where to create the downloads/ and reports/ folders.",
    )

st.divider()

# ─── Run Button ───────────────────────────────────────────────────────────────

run_clicked = st.button(
    "🚀 Run IAVARS Agent",
    type="primary",
    disabled=(uploaded_file is None),
    help="Upload a spreadsheet to enable this button.",
)

# ─── Agent Execution ──────────────────────────────────────────────────────────

if run_clicked and uploaded_file:

    # Default instruction if the user left it blank
    if not user_instruction.strip():
        user_instruction = "Download all videos and organise them by platform"

    # Persist uploaded file to a temp path the agent can read from disk
    suffix = ".csv" if uploaded_file.name.lower().endswith(".csv") else ".xlsx"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    st.info(
        f"📋 **File:** {uploaded_file.name}  |  "
        f"**Instruction:** *{user_instruction}*"
    )

    result: dict = {}
    agent_error: str = ""

    # Import lazily so missing API key only surfaces at run time, not on page load
    try:
        from agent.ai_agent import IVARSAgent
    except ImportError as ie:
        agent_error = f"Import error — make sure all dependencies are installed: {ie}"

    if not agent_error:
        with st.spinner("🤖 AI Agent is thinking and executing…"):
            try:
                agent = IVARSAgent()
                result = agent.run(
                    user_instruction=user_instruction,
                    spreadsheet_path=tmp_path,
                    output_dir=output_dir,
                )
            except EnvironmentError as env_err:
                agent_error = str(env_err)
            except Exception as exc:
                agent_error = str(exc)
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    # ── Error Banner ──────────────────────────────────────────────────────────
    if agent_error:
        st.error(f"⛔ Agent error: {agent_error}")
        if "OPENAI_API_KEY" in agent_error:
            st.warning(
                "Set your OpenAI API key:  \n"
                "1. Create a `.env` file in the project root.  \n"
                "2. Add the line: `OPENAI_API_KEY=sk-...`  \n"
                "3. Restart the Streamlit app."
            )
        st.stop()

    # ── Success ───────────────────────────────────────────────────────────────
    st.success("✅ Agent completed successfully!")

    # ── Summary Metrics ───────────────────────────────────────────────────────
    summary = result.get("summary", {})
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total URLs", summary.get("total_urls", 0))
    m2.metric("Downloaded", summary.get("succeeded", 0))
    m3.metric("Failed", summary.get("failed", 0))
    m4.metric(
        "Platforms",
        len(result.get("platform_groups", {})),
    )

    st.divider()

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_plan, tab_platforms, tab_status, tab_errors, tab_json = st.tabs([
        "📋 Action Plan",
        "🌐 Platform Groups",
        "📥 Download Status",
        "⚠️ Errors",
        "🔍 Raw JSON",
    ])

    with tab_plan:
        st.markdown("### Steps executed by the AI agent")
        for step in result.get("action_plan", []):
            st.markdown(f"- {step}")

    with tab_platforms:
        platform_groups: dict = result.get("platform_groups", {})
        if platform_groups:
            for platform, urls in platform_groups.items():
                icon = platform_icons.get(platform, "•")
                label = platform.replace("_", " ").title()
                with st.expander(f"{icon} **{label}** — {len(urls)} video(s)"):
                    for url in urls:
                        st.code(url, language=None)
        else:
            st.info("No platform grouping data available yet.")

    with tab_status:
        dl_status: dict = result.get("download_status", {})
        if dl_status:
            rows = [
                {
                    "URL": url[:90] + ("…" if len(url) > 90 else ""),
                    "Platform": info.get("platform", "—"),
                    "Status": info.get("status", "—"),
                    "Destination": info.get("destination", info.get("error", "—")),
                }
                for url, info in dl_status.items()
            ]
            st.dataframe(rows, use_container_width=True)
        else:
            st.info("No download status data available.")

    with tab_errors:
        errors = result.get("errors", [])
        if errors:
            for err in errors:
                if isinstance(err, dict):
                    st.error(f"**{err.get('url', 'unknown URL')}** — {err.get('error', '')}")
                else:
                    st.error(str(err))
        else:
            st.success("🎉 No errors — all downloads completed!")

    with tab_json:
        st.markdown("#### Complete agent output (JSON)")
        st.json(result)
        st.download_button(
            label="⬇️ Download report as JSON",
            data=json.dumps(result, indent=2),
            file_name="iavars_report.json",
            mime="application/json",
        )

# ─── Footer ───────────────────────────────────────────────────────────────────

st.markdown("---")
st.caption("IAVARS · Intelligent Agent-Based Video Asset Retrieval System · Powered by LangChain + OpenAI")
