"""Run first-pass, mandatory independent review, and rendered-artifact hash binding."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT / "code") not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT / "code"))

from algorithms.adversarial_review import semantic_issues
from algorithms.paper_readiness import Issue, review_paper, write_review_report
from finalize_review_package import finalize
from second_pass_content_review import main as run_second_pass


def main(args: argparse.Namespace) -> None:
    reports = args.project_root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    review = review_paper(args.project_root, args.manuscript, mode="competition_paper")
    if review.overall_status == "PASS":
        run_second_pass(
            args.project_root,
            args.manuscript,
            args.decision_contract,
            args.quality_validation,
        )
    for issue in semantic_issues(args.project_root, args.manuscript):
        if issue["severity"] == "blocking":
            review.fail(issue["gate"], issue["code"], issue["message"], "modeling")
        else:
            review.issues.append(Issue(**issue))
    write_review_report(
        review,
        reports / "paper_review_report.md",
        reports / "paper_review_report.json",
    )
    if review.overall_status != "PASS":
        raise ValueError("first-pass paper review failed")

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
        paper_review_report=reports / "paper_review_report.json",
        independent_review=reports / "independent_review.json",
    )


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
    main(parser.parse_args())
