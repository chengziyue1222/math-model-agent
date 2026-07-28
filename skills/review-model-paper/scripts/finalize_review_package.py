"""Bind source, rendered artifacts, and all review gates into submission readiness."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def finalize(
    project_root: Path,
    *,
    manuscript: Path,
    pdf: Path,
    docx: Path,
    official_problem: Path,
    decision_contract: Path,
    quality_validation: Path,
    result_object: Path,
    claim_registry: Path,
    figure_registry: Path,
    table_registry: Path,
    references_bib: Path,
    project_manifest: Path,
    layout_validation: Path,
    latex_compile_report: Path,
    docx_render_report: Path,
    visual_layout_audit: Path,
    paper_review_report: Path,
    independent_review: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    root = project_root.resolve()
    artifacts = {
        "manuscript": manuscript.resolve(),
        "main_pdf": pdf.resolve(),
        "main_docx": docx.resolve(),
        "official_problem": official_problem.resolve(),
        "decision_contract": decision_contract.resolve(),
        "quality_validation": quality_validation.resolve(),
        "result_object": result_object.resolve(),
        "claim_registry": claim_registry.resolve(),
        "figure_registry": figure_registry.resolve(),
        "table_registry": table_registry.resolve(),
        "references_bib": references_bib.resolve(),
        "project_manifest": project_manifest.resolve(),
        "cumcm_layout_validation": layout_validation.resolve(),
        "latex_compile_report": latex_compile_report.resolve(),
        "docx_render_report": docx_render_report.resolve(),
        "visual_layout_audit": visual_layout_audit.resolve(),
        "paper_review_report": paper_review_report.resolve(),
        "independent_content_review": independent_review.resolve(),
    }
    for role, path in artifacts.items():
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(f"{role} is missing or empty: {path}")

    gates = {
        "paper_review": load_object(artifacts["paper_review_report"]).get("overall_status") == "PASS",
        "independent_content_review": load_object(artifacts["independent_content_review"]).get("status") == "PASS",
        "cumcm_layout": load_object(artifacts["cumcm_layout_validation"]).get("status") == "PASS",
        "latex_compile": load_object(artifacts["latex_compile_report"]).get("status") == "PASS",
        "docx_render": load_object(artifacts["docx_render_report"]).get("status") == "PASS",
        "visual_layout": load_object(artifacts["visual_layout_audit"]).get("status") == "PASS",
    }
    binding = {
        "schema_version": "1.0",
        "status": "PASS" if all(gates.values()) else "FAIL",
        "artifacts": {
            role: {
                "path": str(path.relative_to(root)).replace("\\", "/"),
                "sha256": digest(path),
                "bytes": path.stat().st_size,
            }
            for role, path in artifacts.items()
        },
        "gates": gates,
    }
    readiness = {
        "schema_version": "1.0",
        "status": "READY_FOR_SUBMISSION" if binding["status"] == "PASS" else "BLOCKED",
        "all_rendered_formats_present": True,
        "all_review_gates_passed": all(gates.values()),
        "review_hash_binding_sha256": hashlib.sha256(
            json.dumps(binding, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "blocking_gates": sorted(name for name, passed in gates.items() if not passed),
    }
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "review_hash_binding.json").write_text(
        json.dumps(binding, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (reports / "submission_readiness.json").write_text(
        json.dumps(readiness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if readiness["status"] != "READY_FOR_SUBMISSION":
        raise ValueError("submission readiness is blocked")
    return binding, readiness


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--manuscript", type=Path, required=True)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--docx", type=Path, required=True)
    parser.add_argument("--official-problem", type=Path, required=True)
    parser.add_argument("--decision-contract", type=Path, required=True)
    parser.add_argument("--quality-validation", type=Path, required=True)
    parser.add_argument("--result-object", type=Path, required=True)
    parser.add_argument("--claim-registry", type=Path, required=True)
    parser.add_argument("--figure-registry", type=Path, required=True)
    parser.add_argument("--table-registry", type=Path, required=True)
    parser.add_argument("--references-bib", type=Path, required=True)
    parser.add_argument("--project-manifest", type=Path, required=True)
    parser.add_argument("--layout-validation", type=Path, required=True)
    parser.add_argument("--latex-compile-report", type=Path, required=True)
    parser.add_argument("--docx-render-report", type=Path, required=True)
    parser.add_argument("--visual-layout-audit", type=Path, required=True)
    parser.add_argument("--paper-review-report", type=Path, required=True)
    parser.add_argument("--independent-review", type=Path, required=True)
    args = parser.parse_args()
    finalize(
        args.project_root,
        manuscript=args.manuscript,
        pdf=args.pdf,
        docx=args.docx,
        official_problem=args.official_problem,
        decision_contract=args.decision_contract,
        quality_validation=args.quality_validation,
        result_object=args.result_object,
        claim_registry=args.claim_registry,
        figure_registry=args.figure_registry,
        table_registry=args.table_registry,
        references_bib=args.references_bib,
        project_manifest=args.project_manifest,
        layout_validation=args.layout_validation,
        latex_compile_report=args.latex_compile_report,
        docx_render_report=args.docx_render_report,
        visual_layout_audit=args.visual_layout_audit,
        paper_review_report=args.paper_review_report,
        independent_review=args.independent_review,
    )
