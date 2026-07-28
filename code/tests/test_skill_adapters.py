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
                    "origin": "SEARCHED",
                    "retrieval_provider": "Crossref",
                    "retrieval_timestamp": "2026-07-26T12:00:00+00:00",
                    "source_fetch_status": "FETCHED",
                    "metadata_verification": {
                        "status": "VERIFIED",
                        "verified_identifier": "10.1000/example",
                        "evidence": "Crossref title, author, year, and DOI match",
                    },
                    "content_relevance_evidence": {
                        "supports": "method definition",
                        "location": "abstract",
                    },
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
                {
                    "id": "a", "title": "A", "year": 2020, "type": "article", "doi": "10/x",
                    "origin": "SEARCHED", "retrieval_provider": "Crossref",
                    "retrieval_timestamp": "2026-07-26T12:00:00+00:00", "source_fetch_status": "FETCHED",
                    "metadata_verification": {"status": "VERIFIED", "evidence": "match"},
                    "content_relevance_evidence": {"supports": "A", "location": "abstract"},
                },
                {
                    "id": "b", "title": "B", "year": 2021, "type": "article", "doi": "10/x",
                    "origin": "SEARCHED", "retrieval_provider": "Crossref",
                    "retrieval_timestamp": "2026-07-26T12:00:00+00:00", "source_fetch_status": "FETCHED",
                    "metadata_verification": {"status": "VERIFIED", "evidence": "match"},
                    "content_relevance_evidence": {"supports": "B", "location": "abstract"},
                },
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
    assert not (ROOT / "skills" / "write-model-paper" / "scripts" / "write_traceable_summary.py").exists()
    assert (ROOT / "skills" / "write-model-paper" / "scripts" / "write_supplier_competition_paper.py").is_file()


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


def test_review_package_requires_both_rendered_formats_and_all_gates(tmp_path) -> None:
    module = _load(
        "finalize_review_package",
        "skills/review-model-paper/scripts/finalize_review_package.py",
    )
    paths = {
        "manuscript": tmp_path / "paper" / "main.md",
        "pdf": tmp_path / "paper" / "main.pdf",
        "docx": tmp_path / "paper" / "main.docx",
        "official_problem": tmp_path / "problem" / "official.pdf",
        "decision_contract": tmp_path / "results" / "decision_contract.json",
        "quality_validation": tmp_path / "results" / "quality_validation.json",
        "result_object": tmp_path / "results" / "result_object.json",
        "claim_registry": tmp_path / "paper" / "claim-registry.json",
        "figure_registry": tmp_path / "paper" / "figure-registry.json",
        "table_registry": tmp_path / "paper" / "table-registry.json",
        "references_bib": tmp_path / "paper" / "references.bib",
        "project_manifest": tmp_path / "run-manifest.json",
        "layout_validation": tmp_path / "reports" / "cumcm_layout_validation.json",
        "latex_compile_report": tmp_path / "reports" / "latex_compile_report.json",
        "docx_render_report": tmp_path / "reports" / "docx_render_report.json",
        "visual_layout_audit": tmp_path / "reports" / "visual_layout_audit.json",
        "paper_review_report": tmp_path / "reports" / "paper_review_report.json",
        "independent_review": tmp_path / "reports" / "independent_review.json",
    }
    for name, path in paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if name == "paper_review_report":
            value = {"overall_status": "PASS"}
        elif path.suffix == ".json":
            value = {"status": "PASS"}
        else:
            path.write_bytes(b"rendered")
            continue
        path.write_text(json.dumps(value), encoding="utf-8")
    binding, readiness = module.finalize(tmp_path, **paths)
    assert binding["status"] == "PASS"
    assert readiness["status"] == "READY_FOR_SUBMISSION"
    assert {"main_pdf", "main_docx"} <= set(binding["artifacts"])


def test_review_package_fails_when_visual_audit_fails(tmp_path) -> None:
    module = _load(
        "finalize_review_package_failure",
        "skills/review-model-paper/scripts/finalize_review_package.py",
    )
    paths = {}
    for name, relative in {
        "manuscript": "paper/main.md",
        "pdf": "paper/main.pdf",
        "docx": "paper/main.docx",
        "official_problem": "problem/official.pdf",
        "decision_contract": "results/decision_contract.json",
        "quality_validation": "results/quality_validation.json",
        "result_object": "results/result_object.json",
        "claim_registry": "paper/claim-registry.json",
        "figure_registry": "paper/figure-registry.json",
        "table_registry": "paper/table-registry.json",
        "references_bib": "paper/references.bib",
        "project_manifest": "run-manifest.json",
        "layout_validation": "reports/cumcm_layout_validation.json",
        "latex_compile_report": "reports/latex_compile_report.json",
        "docx_render_report": "reports/docx_render_report.json",
        "visual_layout_audit": "reports/visual_layout_audit.json",
        "paper_review_report": "reports/paper_review_report.json",
        "independent_review": "reports/independent_review.json",
    }.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        paths[name] = path
        if name == "paper_review_report":
            payload = {"overall_status": "PASS"}
        elif path.suffix == ".json":
            payload = {"status": "FAIL" if name == "visual_layout_audit" else "PASS"}
        else:
            path.write_bytes(b"rendered")
            continue
        path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="submission readiness"):
        module.finalize(tmp_path, **paths)
