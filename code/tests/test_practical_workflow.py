"""Meaningful failure/recovery, contracts and generic-report regressions."""
import importlib.util
import json
from pathlib import Path

import pytest

from algorithms.paper_readiness import review_paper
from scripts.skill_contracts import contract_for, export_contracts, validate_records

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("practical_project_state", ROOT / "skills/run-modeling-project/scripts/project_state.py")
state = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(state)


def put(root, role, data):
    path = root / f"{role}.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return f"{role}={path.name}"


def test_failed_validation_preserved_and_rewind_recovery(tmp_path):
    s = state.initialize(tmp_path, "case", "run_manifest.json")
    s["current_stage"] = "modeling"
    state._write_state(tmp_path, s)
    evidence = [put(tmp_path, r, {"status": "PASS"}) for r in ("implementation", "machine_results", "run_manifest")]
    evidence.append(put(tmp_path, "quality_validation", {"baseline": {"passed": False}}))
    with pytest.raises(ValueError, match="failed validation"):
        state.advance(tmp_path, "validation", evidence, "must fail")
    assert state._read_state(tmp_path)["failed_gates"][0]["to"] == "validation"
    put(tmp_path, "quality_validation", {"baseline": {"passed": True}})
    s = state.advance(tmp_path, "validation", evidence, "corrected")
    assert s["evidence"]["machine_results"]["sha256"]
    (tmp_path / "machine_results.json").write_text('{"value":2}', encoding="utf-8")
    assert state.verify_evidence(tmp_path, s)
    s = state.rewind(tmp_path, "modeling", "result changed")
    assert not s["evidence"] and len(s["stale_evidence"]) == 4
    assert (tmp_path / "machine_results.json").is_file()
    assert s["transitions"][-1]["action"] == "rewind"
    state.advance(tmp_path, "validation", evidence, "recomputed")


def test_legacy_venue_explicit_and_unknown_contract_rejected(tmp_path):
    s = state.initialize(tmp_path, "legacy", "run.json")
    s["schema_version"] = "1.1"
    s.pop("venue")
    s.pop("venue_config")
    state._write_state(tmp_path, s)
    with pytest.raises(ValueError, match="venue selection"):
        state.advance(tmp_path, "analysis", [], "")
    assert state.select_venue(tmp_path, "CUMCM")["schema_version"] == "1.2"
    for version in ("1.1", "1.2", "1.3", "1.4"):
        assert "cumcm_layout_validation" in contract_for("review-model-paper", version=version)["inputs"] if version in {"1.3", "1.4"} else True
    with pytest.raises(ValueError, match="unsupported"):
        contract_for("solve-model", version="99")


def test_contract_schema_and_cumcm_alias():
    import jsonschema
    schema = json.loads((ROOT / "schemas/skill-contracts.schema.json").read_text(encoding="utf-8"))
    for profile in ("rapid", "competition", "audit"):
        catalogue = json.loads(json.dumps(export_contracts(profile)))
        jsonschema.validate(catalogue, schema)
    c = contract_for("write-model-paper", venue="CUMCM")
    inputs = [{"role": r} for r in c["inputs"]]
    outputs = [{"role": "cumcm_layout_validation" if r == "layout_validation" else r} for r in c["outputs"]]
    assert validate_records("write-model-paper", inputs, outputs, venue="CUMCM") == []
    assert validate_records("write-model-paper", inputs, outputs, venue="generic-research-report")


def test_generic_prediction_without_fixed_counts_or_optimization_words(tmp_path):
    (tmp_path / "results").mkdir()
    result = tmp_path / "results/prediction.json"
    result.write_text('{"predicted": [1,2]}', encoding="utf-8")
    quality = tmp_path / "results/quality_validation.json"
    quality.write_text('{"baseline": {"passed": true}}', encoding="utf-8")
    (tmp_path / "results/decision_contract.json").write_text(json.dumps({"questions": [{"id": "q1", "result_artifact": "results/prediction.json", "validation_artifact": "results/quality_validation.json"}], "requirements": {"baseline_comparison_required": True}}), encoding="utf-8")
    (tmp_path / "paper-spec.yaml").write_text("venue: generic-research-report\nproblem_type: prediction\n", encoding="utf-8")
    (tmp_path / "figure-registry.json").write_text("[]", encoding="utf-8")
    import hashlib
    (tmp_path / "evidence-index.json").write_text(json.dumps([{"evidence_id": "E1", "path": "results/prediction.json", "sha256": hashlib.sha256(result.read_bytes()).hexdigest()}]), encoding="utf-8")
    paper = tmp_path / "paper.md"
    paper.write_text("# 预测报告\n## q1\n保存预测为1和2。基线检查通过。", encoding="utf-8")
    assert review_paper(tmp_path, paper).overall_status == "PASS"
    quality.write_text('{"baseline": {"passed": false}}', encoding="utf-8")
    assert review_paper(tmp_path, paper).overall_status == "FAIL"


def test_saved_venue_rejects_conflicting_yaml(tmp_path):
    from algorithms.venue_config import resolve_project_venue
    state.initialize(tmp_path, "venue-conflict", "run.json", venue="CUMCM")
    (tmp_path / "config").mkdir()
    (tmp_path / "config/venue.yaml").write_text("venue: generic-research-report\n", encoding="utf-8")
    with pytest.raises(ValueError, match="differs from project state"):
        resolve_project_venue(tmp_path)


def test_rewind_old_evidence_infers_latest_production_stage(tmp_path):
    s = state.initialize(tmp_path, "legacy-stage", "run.json")
    s["current_stage"] = "validation"
    s["evidence"] = {"problem_statement": {"path": "problem.md"}, "machine_results": {"path": "results.json"}, "unknown": {"path": "unknown.json"}}
    s["transitions"] = [{"from": "intake", "to": "analysis", "evidence_roles": ["problem_statement"]}, {"from": "modeling", "to": "validation", "evidence_roles": ["machine_results"]}]
    state._write_state(tmp_path, s)
    rewound = state.rewind(tmp_path, "modeling", "legacy result must be recomputed")
    assert set(rewound["evidence"]) == {"problem_statement"}
    assert {e["role"] for e in rewound["stale_evidence"]} == {"machine_results", "unknown"}
