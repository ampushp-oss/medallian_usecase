from pathlib import Path

from medalliance.pipeline import run_pipeline


def test_run_pipeline_creates_bronze_silver_and_gold_outputs(tmp_path):
    input_dir = tmp_path / "raw"
    input_dir.mkdir()
    input_file = input_dir / "patients.csv"
    input_file.write_text(
        "patient_id,name,age,city,visit_date\n"
        "1, Alice, 32,New York,2024-01-10\n"
        "2, Bob, ,London,2024-01-12\n"
        "2, bob, 40, London,2024-01-12\n",
        encoding="utf-8",
    )

    output_dir = tmp_path / "warehouse"
    run_pipeline(input_dir=input_dir, output_dir=output_dir, use_claude=False)

    assert (output_dir / "bronze" / "patients.csv").exists()
    assert (output_dir / "silver" / "patients.csv").exists()
    assert (output_dir / "gold" / "patients.csv").exists()

    bronze = (output_dir / "bronze" / "patients.csv").read_text(encoding="utf-8")
    silver = (output_dir / "silver" / "patients.csv").read_text(encoding="utf-8")
    gold = (output_dir / "gold" / "patients.csv").read_text(encoding="utf-8")

    assert "patient_id" in bronze
    assert "city" in silver
    assert "patient_id" in gold
    assert "row_count" in gold or "city" in gold


def test_run_pipeline_reports_stage_progress(tmp_path):
    input_dir = tmp_path / "raw"
    input_dir.mkdir()
    (input_dir / "patients.csv").write_text(
        "patient_id,name,age,city\n1,Alice,32,New York\n",
        encoding="utf-8",
    )
    events = []

    run_pipeline(
        input_dir=input_dir,
        output_dir=tmp_path / "warehouse",
        use_claude=False,
        progress_callback=lambda stage, message: events.append((stage, message)),
    )

    assert any(stage == "bronze" for stage, _ in events)
    assert any(stage == "silver" for stage, _ in events)
    assert any(stage == "gold" for stage, _ in events)
