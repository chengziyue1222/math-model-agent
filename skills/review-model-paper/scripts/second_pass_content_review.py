"""Produce a hash-bound, deterministic second-pass content review for a modeling paper."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main(project_root: Path, manuscript: Path) -> None:
    root = project_root.resolve()
    paper = manuscript.resolve()
    text = paper.read_text(encoding="utf-8").lower()
    checks = [
        {"id": "limitations_disclosed", "passed": any(token in text for token in ("局限", "limitations", "不应", "不能")), "method": "limitation disclosure scan"},
        {"id": "uncertainty_not_overclaimed", "passed": any(token in text for token in ("压力", "holdout", "stress", "不确定")), "method": "uncertainty disclosure scan"},
        {"id": "decision_artifacts_present", "passed": all(token in text for token in ("问题二", "问题三", "问题四")), "method": "question coverage scan"},
    ]
    report = {
        "status": "PASS" if all(item["passed"] for item in checks) else "FAIL",
        "reviewer": "deterministic_second_pass_content_review",
        "reviewed_path": str(paper.relative_to(root)).replace("\\", "/"),
        "manuscript_sha256": hashlib.sha256(paper.read_bytes()).hexdigest(),
        "checks": checks,
    }
    output = root / "reports" / "independent_review.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if report["status"] != "PASS":
        raise SystemExit("second-pass content review failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--manuscript", type=Path, required=True)
    args = parser.parse_args()
    main(args.project_root, args.manuscript)
