import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.reasoning_engine import analyse_instruction
from data_processing.spreadsheet_reader import read_spreadsheet
from data_processing.metadata_extractor import extract_data
from storage.file_manager import create_folder
from tools.downloader import download_video
from tools.url_validator import is_valid_url


def _normalize_token(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


st.title("AI Video Asset Retrieval Agent")

st.write(
    "Upload a spreadsheet containing video links and provide instructions "
    "for the AI agent to retrieve and organize the assets."
)

uploaded_file = st.file_uploader("Upload Spreadsheet (Excel or CSV)", type=["xlsx", "xls", "csv"])

instruction = st.text_input(
    "Agent Instruction",
    placeholder="Example: Download only Nike videos",
)

if st.button("Run Agent"):

    if uploaded_file is None:
        st.warning("Please upload a spreadsheet first.")

    else:
        # Save uploaded file
        input_dir = PROJECT_ROOT / "data" / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        file_path = input_dir / uploaded_file.name

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success("Spreadsheet uploaded successfully.")

        # Read spreadsheet
        df = read_spreadsheet(file_path)

        st.subheader("Spreadsheet Preview")
        st.dataframe(df)

        # Extract structured data
        data = extract_data(df)

        # -------- FILTER LOGIC --------

        intent = {"filter": "none", "group_by": "none"}

        if instruction:
            try:
                intent = analyse_instruction(instruction)
            except Exception:
                intent = {"filter": "none", "group_by": "none"}

        filter_value = intent["filter"]
        normalized_filter = _normalize_token(filter_value)

        filtered_data = []

        for item in data:
            if not is_valid_url(item["link"]):
                continue

            if filter_value == "none":
                filtered_data.append(item)
            elif normalized_filter and normalized_filter in _normalize_token(item["brand"]):
                filtered_data.append(item)

        # -------- OUTPUT --------

        st.subheader("Filtered Data")
        st.write(filtered_data)

        # Create output folder
        output_folder = PROJECT_ROOT / "data" / "outputs"
        create_folder(str(output_folder))

        st.subheader("Downloading Videos")

        if not filtered_data:
            st.warning("No matching videos found based on instruction.")

        else:
            progress_bar = st.progress(0)

            for i, item in enumerate(filtered_data):
                link = item["link"]

                try:
                    download_video(link, str(output_folder))
                    st.write(f"Downloaded: {link}")

                except Exception as e:
                    st.error(f"Failed: {link}. Error: {e}")

                progress_bar.progress((i + 1) / len(filtered_data))

            st.success("Download process completed!")
            st.write("Files saved in:", str(output_folder))

        # Show instruction
        if instruction.strip():
            st.caption(f"Instruction captured: {instruction}")
