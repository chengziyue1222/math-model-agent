import json
from pathlib import Path

from scripts.skill_runtime import (
    STANDARD_SKILLS,
    finish_skill_run,
    start_skill_run,
    validate_skill_run,
)
from scripts.validate_skill_workflow import scan_project_scripts, validate_producers
from scripts.skill_contracts import contract_for


def _write(root: Path, relative: str, text: str = "{}") -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_runtime_records_start_finish_and_producer_hashes(tmp_path):
    _write(tmp_path, "input.json")
    _write(tmp_path, "results/result_object.json")
    start = start_skill_run(tmp_path, "case", "solve-model", inputs=[("selected_model_plan", "input.json")])
    finish_skill_run(tmp_path, start["run_id"], outputs=[("result_object", "results/result_object.json")])

    assert validate_skill_run(tmp_path, project_id="case", required_skills=["solve-model"]) == []
    registry = json.loads((tmp_path / "manifests" / "artifact-producers.json").read_text(encoding="utf-8"))
    assert registry[0]["producer_name"] == "solve-model"
    assert validate_producers(tmp_path) == []


def test_runtime_detects_tampered_trace_and_output(tmp_path):
    _write(tmp_path, "input.json")
    _write(tmp_path, "results/result_object.json")
    start = start_skill_run(tmp_path, "case", "solve-model", inputs=["input.json"])
    finish_skill_run(tmp_path, start["run_id"], outputs=[("result_object", "results/result_object.json")])
    _write(tmp_path, "results/result_object.json", '{"changed": true}')
    errors = validate_skill_run(tmp_path, project_id="case", required_skills=["solve-model"])
    assert any("output_hash_mismatch" in error for error in errors)
    trace = tmp_path / "manifests" / "skill-runs.jsonl"
    trace.write_text(trace.read_text(encoding="utf-8").replace("solve-model", "fake-skill", 1), encoding="utf-8")
    assert any("trace_signature_invalid" in error for error in validate_skill_run(tmp_path, project_id="case"))


def test_runtime_requires_each_standard_skill(tmp_path):
    assert set(STANDARD_SKILLS) == {
        "run-modeling-project", "select-model", "analyze-model-data", "research-model-literature",
        "solve-model", "make-model-figures", "write-model-paper", "review-model-paper",
    }
    errors = validate_skill_run(tmp_path, project_id="case", required_skills=list(STANDARD_SKILLS))
    assert len([item for item in errors if item.startswith("missing_passed_skill_run")]) == 8


def test_bypass_scanner_flags_direct_paper_writes(tmp_path):
    _write(tmp_path, "run_project.py", "Path('main.tex').write_text('paper')\n")
    findings = scan_project_scripts(tmp_path)
    assert findings and findings[0]["code"] == "BYPASS_DETECTED"


def test_quality_evidence_roles_are_required_across_the_competition_pipeline():
    assert "decision_contract" in contract_for("select-model")["outputs"]
    assert "decision_contract" in contract_for("solve-model")["inputs"]
    assert "quality_validation" in contract_for("solve-model")["outputs"]
    assert "quality_validation" in contract_for("make-model-figures")["inputs"]
    assert {"decision_contract", "quality_validation"} <= set(contract_for("write-model-paper")["inputs"])
    assert {"decision_contract", "quality_validation"} <= set(contract_for("review-model-paper")["inputs"])
