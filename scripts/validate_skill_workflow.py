#!/usr/bin/env python3
"""Detect workflow bypasses and validate registered producer provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.skill_runtime import STANDARD_SKILLS, validate_skill_run


OFFICIAL_PRODUCERS = {
    "data_audit": "analyze-model-data",
    "model_selection_report": "select-model",
    "result_object": "solve-model",
    "formal_figure": "make-model-figures",
    "main_markdown": "write-model-paper",
    "main_tex": "write-model-paper",
    "main_pdf": "compile-latex",
    "main_docx": "paper-docx",
    "paper_review_report": "review-model-paper",
}
ALLOWED_EXTERNAL_PRODUCERS = {"compile-latex", "paper-docx"}
SUSPICIOUS = (
    ("direct_main_tex_write", re.compile(r"(?:write_text|open)\([^\n]{0,160}main\.tex|main\.tex[^\n]{0,160}(?:write_text|open)", re.I)),
    ("direct_latex_compile", re.compile(r"(?:xelatex|pdflatex|pandoc)\b", re.I)),
    ("manual_skill_trace", re.compile(r"(?:skill-runs\.jsonl|skill_execution_trace\.md)", re.I)),
    ("embedded_long_paper", re.compile(r"(?:'''|\"\"\")[\s\S]{8000,}?(?:'''|\"\"\")")),
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scan_project_scripts(project_root: str | Path) -> list[dict[str, str]]:
    root = Path(project_root).resolve()
    findings = []
    ignored = {".git", ".venv", "venv", "__pycache__", "node_modules", "mutation_tests"}
    for path in root.rglob("*.py"):
        if any(part in ignored for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError:
            continue
        for code, pattern in SUSPICIOUS:
            if pattern.search(text):
                findings.append({"code": "BYPASS_DETECTED", "rule": code, "path": str(path.relative_to(root)).replace("\\", "/")})
    return findings


def validate_producers(project_root: str | Path) -> list[str]:
    root = Path(project_root).resolve()
    registry_path = root / "manifests" / "artifact-producers.json"
    if not registry_path.is_file():
        return ["producer_registry_missing"]
    try:
        records = json.loads(registry_path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        return [f"producer_registry_invalid: {exc}"]
    if not isinstance(records, list):
        return ["producer_registry_invalid: root must be an array"]
    errors = []
    for record in records:
        if not isinstance(record, dict):
            errors.append("producer_record_invalid")
            continue
        path = root / str(record.get("path", ""))
        role = str(record.get("role", ""))
        expected = OFFICIAL_PRODUCERS.get(role)
        actual = str(record.get("producer_name", ""))
        if expected and actual != expected:
            errors.append(f"producer_mismatch: {record.get('path')} expects {expected}, got {actual}")
        if not path.is_file() or record.get("output_sha256") != _sha256(path):
            errors.append(f"producer_output_hash_mismatch: {record.get('path')}")
        if actual not in STANDARD_SKILLS and actual not in ALLOWED_EXTERNAL_PRODUCERS:
            errors.append(f"producer_not_allowed: {actual}")
    return errors


def validate_workflow(project_root: str | Path, project_id: str, *, require_all_skills: bool = True) -> dict[str, Any]:
    root = Path(project_root).resolve()
    trace_errors = validate_skill_run(root, project_id=project_id, required_skills=list(STANDARD_SKILLS) if require_all_skills else [])
    bypass = scan_project_scripts(root)
    producer_errors = validate_producers(root)
    return {
        "project_id": project_id,
        "status": "PASS" if not trace_errors and not bypass and not producer_errors else "FAIL",
        "trace_errors": trace_errors,
        "bypass_findings": bypass,
        "producer_errors": producer_errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--allow-partial-skills", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = validate_workflow(args.project_root, args.project_id, require_all_skills=not args.allow_partial_skills)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
