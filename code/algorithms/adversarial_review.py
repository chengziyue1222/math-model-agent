"""Problem-agnostic semantic gates for adversarial modeling-paper review."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def _registrations(value: Any, key: str) -> list[dict[str, Any]]:
    rows = value.get(key, []) if isinstance(value, dict) else value if isinstance(value, list) else []
    return [row for row in rows if isinstance(row, dict)]


def semantic_issues(project_root: str | Path, paper_path: str | Path) -> list[dict[str, str]]:
    """Return blocking and warning semantic findings without relying on a problem ID."""
    root, paper = Path(project_root), Path(paper_path)
    text = paper.read_text(encoding="utf-8") if paper.is_file() else ""
    issues: list[dict[str, str]] = []
    spec = (paper.parent / "paper-spec.yaml").read_text(encoding="utf-8") if (paper.parent / "paper-spec.yaml").is_file() else ""
    required_count = re.search(r"required_supplier_count\s*:\s*(\d+)", spec)
    if required_count:
        required = int(required_count.group(1))
        identifiers = set(re.findall(r"\bS\d{3}\b", text, re.I))
        if len(identifiers) < required:
            issues.append({"gate": "evidence", "code": "required_list_incomplete", "severity": "blocking", "message": f"paper lists {len(identifiers)} of required {required} suppliers"})

    if re.search(r"(?:一体化\s*鲁棒|integrated\s+robust)", text, re.I):
        specs = list(root.rglob("model_specification.json"))
        payload = _load_json(specs[0]) if specs else None
        method = json.dumps(payload, ensure_ascii=False).lower() if payload is not None else ""
        if any(token in method for token in ("decomposition", "sequential", "stagewise", "分解", "分阶段")):
            issues.append({"gate": "mathematics", "code": "model_claim_code_mismatch", "severity": "blocking", "message": "paper claims integrated robust optimization but the registered specification declares decomposition"})

    result_files = list(root.rglob("result_object.json"))
    result = _load_json(result_files[0]) if result_files else None
    solution = result.get("solution", {}) if isinstance(result, dict) else {}
    supplier_count = solution.get("supplier_count") if isinstance(solution, dict) else None
    if isinstance(supplier_count, (int, float)) and supplier_count >= 150 and not re.search(r"(?:实施|管理复杂|implementation|management complexity)", text, re.I):
        issues.append({"gate": "validation", "code": "implementation_risk_undiscussed", "severity": "warning", "message": f"recommendation uses {supplier_count} suppliers without an implementation-complexity discussion"})
    if re.search(r"(?:24\s*weeks?|24\s*周).{0,100}(?:identical|完全相同|unchanged)", text, re.I | re.S) and not re.search(r"(?:切换成本|contract cost|switching cost)", text, re.I):
        issues.append({"gate": "validation", "code": "static_plan_without_switching_cost", "severity": "warning", "message": "static multi-week plan omits switching or contract-cost discussion"})

    formulas = _registrations(_load_json(paper.parent / "formula-registry.json"), "formulas")
    for index, formula in enumerate(formulas):
        required = {"latex", "variables", "units", "code_function", "parameter_source", "result_id"}
        missing = sorted(name for name in required if not formula.get(name))
        if missing:
            issues.append({"gate": "mathematics", "code": "formula_registry_incomplete", "severity": "blocking", "message": f"formula registry item {index} is missing {', '.join(missing)}"})
    tables = _registrations(_load_json(paper.parent / "table-registry.json"), "tables")
    for index, table in enumerate(tables):
        required = {"data_file", "row_filter", "column_filter", "generation_script", "sha256", "claim_ids"}
        missing = sorted(name for name in required if not table.get(name))
        if missing:
            issues.append({"gate": "figures_tables", "code": "table_registry_incomplete", "severity": "blocking", "message": f"table registry item {index} is missing {', '.join(missing)}"})
    questions = len(re.findall(r"(?:问题|question)\s*[一二三四1234]", text, re.I))
    if questions >= 4 and not issues:
        issues.append({"gate": "validation", "code": "REVIEW_SUSPICIOUSLY_SHALLOW", "severity": "blocking", "message": "complex paper produced no semantic findings; run an independent second review"})
    return issues
