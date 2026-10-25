import argparse
from pathlib import Path
from typing import Iterable, List

import pandas as pd

try:
    from .agents import ClaudeAgent
    from .config import DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR
except ImportError:  # pragma: no cover
    from agents import ClaudeAgent
    from config import DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _list_csv_files(input_dir: Path) -> List[Path]:
    if not input_dir.exists():
        return []
    return sorted(input_dir.glob("*.csv"))


def bronze_layer(input_dir: Path, output_dir: Path, agent: ClaudeAgent | None = None, progress_callback=None) -> List[Path]:
    target_dir = output_dir / "bronze"
    target_dir.mkdir(parents=True, exist_ok=True)
    outputs: List[Path] = []
    progress = progress_callback or (lambda *args, **kwargs: None)
    progress("bronze", "Starting bronze layer")

    for csv_file in _list_csv_files(input_dir):
        progress("bronze", f"Reading {csv_file.name} for bronze processing")
        df = pd.read_csv(csv_file)
        output_path = target_dir / csv_file.name
        df.to_csv(output_path, index=False)
        if agent is not None:
            agent.bronze_agent(csv_file.name)
        progress("bronze", f"Bronze output saved for {csv_file.name}")
        outputs.append(output_path)
    progress("bronze", "Bronze layer completed")
    return outputs


def silver_layer(input_dir: Path, output_dir: Path, agent: ClaudeAgent | None = None, progress_callback=None) -> List[Path]:
    target_dir = output_dir / "silver"
    target_dir.mkdir(parents=True, exist_ok=True)
    outputs: List[Path] = []
    progress = progress_callback or (lambda *args, **kwargs: None)
    progress("silver", "Starting silver layer")

    for csv_file in _list_csv_files(input_dir):
        progress("silver", f"Cleaning {csv_file.name} for silver processing")
        df = pd.read_csv(output_dir / "bronze" / csv_file.name)
        df = df.drop_duplicates().reset_index(drop=True)
        for column in df.columns:
            if df[column].dtype == "object":
                df[column] = df[column].astype(str).str.strip()

        for column in df.columns:
            if column.lower() in {"age", "patient_id"}:
                df[column] = pd.to_numeric(df[column], errors="coerce")

        output_path = target_dir / csv_file.name
        df.to_csv(output_path, index=False)
        if agent is not None:
            agent.silver_agent(csv_file.name)
        progress("silver", f"Silver output saved for {csv_file.name}")
        outputs.append(output_path)
    progress("silver", "Silver layer completed")
    return outputs


def gold_layer(input_dir: Path, output_dir: Path, agent: ClaudeAgent | None = None, progress_callback=None) -> List[Path]:
    target_dir = output_dir / "gold"
    target_dir.mkdir(parents=True, exist_ok=True)
    outputs: List[Path] = []
    progress = progress_callback or (lambda *args, **kwargs: None)
    progress("gold", "Starting gold layer")

    for csv_file in _list_csv_files(input_dir):
        progress("gold", f"Aggregating {csv_file.name} for gold processing")
        df = pd.read_csv(output_dir / "silver" / csv_file.name)
        if "patient_id" in df.columns:
            grouped = (
                df.groupby("patient_id", as_index=False)
                .agg(row_count=("patient_id", "size"), distinct_cities=("city", lambda s: s.nunique() if "city" in df.columns else 0))
            )
            output_path = target_dir / csv_file.name
            grouped.to_csv(output_path, index=False)
        else:
            summary = df.copy()
            summary["row_count"] = 1
            output_path = target_dir / csv_file.name
            summary.to_csv(output_path, index=False)

        if agent is not None:
            agent.gold_agent(csv_file.name)
        progress("gold", f"Gold output saved for {csv_file.name}")
        outputs.append(output_path)
    progress("gold", "Gold layer completed")
    return outputs


def run_pipeline(input_dir: str | Path = DEFAULT_INPUT_DIR, output_dir: str | Path = DEFAULT_OUTPUT_DIR, use_claude: bool = False, progress_callback=None):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    progress = progress_callback or (lambda *args, **kwargs: None)
    progress("pipeline", "Starting data pipeline")

    agent = ClaudeAgent() if use_claude else None
    bronze_layer(input_path, output_path, agent, progress_callback=progress)
    silver_layer(input_path, output_path, agent, progress_callback=progress)
    gold_layer(input_path, output_path, agent, progress_callback=progress)
    progress("pipeline", "Pipeline completed successfully")
    return {
        "bronze": str(output_path / "bronze"),
        "silver": str(output_path / "silver"),
        "gold": str(output_path / "gold"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Medalliance bronze-to-gold CSV processing pipeline.")
    parser.add_argument("--input-dir", type=str, default=str(DEFAULT_INPUT_DIR), help="Directory containing raw CSV files.")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR), help="Directory where bronze/silver/gold outputs will be stored.")
    parser.add_argument("--use-claude", action="store_true", help="Use Claude to reason at each layer.")
    args = parser.parse_args()

    result = run_pipeline(args.input_dir, args.output_dir, use_claude=args.use_claude)
    print(result)


if __name__ == "__main__":
    main()
