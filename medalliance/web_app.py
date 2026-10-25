import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

try:
    from .pipeline import run_pipeline
except ImportError:  # pragma: no cover
    from pipeline import run_pipeline

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "warehouse"
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_uploaded_files(files):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for uploaded_file in files:
        if not uploaded_file.name:
            continue
        if not uploaded_file.name.lower().endswith(".csv"):
            continue
        (RAW_DIR / uploaded_file.name).write_bytes(uploaded_file.getvalue())


def update_progress(stage: str, message: str, progress_bar, status_slot):
    progress_lookup = {"bronze": 0.33, "silver": 0.66, "gold": 1.0}
    progress_bar.progress(progress_lookup.get(stage, 0.0))
    status_slot.write(f"{stage.title()}: {message}")


def main():
    st.set_page_config(page_title="Medalliance Data Pipeline", layout="wide")
    st.title("Medalliance Bronze → Silver → Gold Pipeline")
    st.caption("Upload raw CSV files and track the workflow as each layer transforms them.")

    uploaded_files = st.file_uploader("Upload CSV files", type=["csv"], accept_multiple_files=True)
    use_claude = st.checkbox("Use Claude agent processing", value=bool(os.getenv("ANTHROPIC_API_KEY")))

    if st.button("Process files") and uploaded_files:
        save_uploaded_files(uploaded_files)
        progress_bar = st.progress(0)
        status_slot = st.empty()
        status_slot.write("Starting pipeline...")

        try:
            run_pipeline(
                input_dir=str(RAW_DIR),
                output_dir=str(OUTPUT_DIR),
                use_claude=use_claude,
                progress_callback=lambda stage, message: update_progress(stage, message, progress_bar, status_slot),
            )
            st.success("Pipeline completed successfully.")
            st.write("Output folders:")
            st.code(str(OUTPUT_DIR / "bronze"))
            st.code(str(OUTPUT_DIR / "silver"))
            st.code(str(OUTPUT_DIR / "gold"))
        except Exception as exc:  # pragma: no cover
            st.error(f"Pipeline failed: {exc}")

    else:
        st.info("No files processed yet. Upload one or more CSV files and click Process files.")


if __name__ == "__main__":
    main()
