from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_literature_adapter_uses_explicit_verified_candidates(tmp_path) -> None:
    module = _load(
        "build_source_record",
        "skills/research-model-literature/scripts/build_source_record.py",
    )
    candidates = tmp_path / "candidates.json"
    candidates.write_text(
        json.dumps(
            [
                {
                    "id": "method2024",
                    "title": "Verified method",
                    "author": "A. Author",
                    "year": 2024,
                    "type": "article",
                    "doi": "10.1000/example",
                    "purpose": "method definition",
                }
            ]
        ),
        encoding="utf-8",
    )
    module.main(tmp_path, candidates)
    validation = json.loads((tmp_path / "results" / "bib_validation.json").read_text(encoding="utf-8"))
    assert validation["status"] == "PASS"
    assert "@article{method2024" in (tmp_path / "paper" / "references.bib").read_text(encoding="utf-8")


def test_literature_adapter_rejects_duplicate_identifiers(tmp_path) -> None:
    module = _load(
        "build_source_record_duplicate",
        "skills/research-model-literature/scripts/build_source_record.py",
    )
    candidates = tmp_path / "candidates.json"
    candidates.write_text(
        json.dumps(
            [
                {"id": "a", "title": "A", "year": 2020, "type": "article", "doi": "10/x"},
                {"id": "b", "title": "B", "year": 2021, "type": "article", "doi": "10/x"},
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="validation failed"):
        module.main(tmp_path, candidates)
    validation = json.loads((tmp_path / "results" / "bib_validation.json").read_text(encoding="utf-8"))
    assert validation["status"] == "FAIL"


def test_c_topic_adapters_delegate_quality_work_to_generic_library() -> None:
    solve = (ROOT / "skills" / "solve-model" / "scripts" / "solve_supplier_chain.py").read_text(encoding="utf-8")
    figures = (ROOT / "skills" / "make-model-figures" / "scripts" / "render_supplier_figures.py").read_text(encoding="utf-8")
    assert "validate_state_balance(" in solve
    assert "compare_policy_metrics(" in solve
    assert "service_level_metrics(" in solve
    assert "export_publication_figure(" in figures
    assert ".savefig(" not in figures
    assert "dpi=240" not in figures


def test_second_pass_review_binds_contract_and_quality_hashes(tmp_path) -> None:
    module = _load(
        "second_pass_content_review",
        "skills/review-model-paper/scripts/second_pass_content_review.py",
    )
    (tmp_path / "paper").mkdir()
    (tmp_path / "results").mkdir()
    manuscript = tmp_path / "paper" / "main.md"
    result = tmp_path / "results" / "q1.json"
    validation = tmp_path / "results" / "q1-validation.json"
    contract = tmp_path / "results" / "decision_contract.json"
    quality = tmp_path / "results" / "quality_validation.json"
    manuscript.write_text("# 问题一\n结果及局限。\n", encoding="utf-8")
    result.write_text("{}", encoding="utf-8")
    validation.write_text("{}", encoding="utf-8")
    contract.write_text(
        json.dumps(
            {
                "questions": [
                    {
                        "id": "Q1",
                        "result_artifact": "results/q1.json",
                        "validation_artifact": "results/q1-validation.json",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    quality.write_text(json.dumps({"uncertainty": {"passed": True}}), encoding="utf-8")
    module.main(tmp_path, manuscript, contract, quality)
    report = json.loads((tmp_path / "reports" / "independent_review.json").read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    assert len(report["decision_contract_sha256"]) == 64
    assert len(report["quality_validation_sha256"]) == 64
