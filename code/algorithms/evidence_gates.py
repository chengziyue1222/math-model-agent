"""Semantic checks shared by project advancement, paper review and finalization."""
import hashlib
import json
import re
from pathlib import Path

from .modeling_contracts import validate_decision_contract, validate_contract_artifacts, validate_quality_validation

PASS_ROLES = {"layout_validation", "cumcm_layout_validation", "visual_layout_audit", "paper_review_report",
              "submission_preflight", "reproduction_report", "review_hash_binding", "independent_content_review",
              "latex_compile_report", "docx_render_report"}
CHECK_ROLES = {"data_quality_report", "solver_validation", "leakage_report", "bib_validation", "figure_audit_report"}


def _failed_check(value):
    if isinstance(value, dict):
        return (value.get("passed") is False
                or str(value.get("status", "")).upper() in {"FAIL", "FAILED", "BLOCKED", "INFEASIBLE", "UNBOUNDED", "ERROR"}
                or any(_failed_check(item) for item in value.values()))
    return isinstance(value, list) and any(_failed_check(item) for item in value)


def validate_figure_registry(root, registry_path):
    """Consume current figure reviews, rather than cached registry verdicts."""
    from .figure_export import validate_figure_review

    root = Path(root).resolve()
    path = Path(registry_path)
    path = path if path.is_absolute() else root / path
    try:
        path.resolve().relative_to(root)
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("figures") if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            raise ValueError("expected a figure list or an object containing figures; use [] for no figures")
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        return [f"figure_registry: invalid evidence: {exc}"]
    errors = []
    for index, row in enumerate(rows, 1):
        label = str(row.get("figure_id", index)) if isinstance(row, dict) else str(index)
        prefix = f"figure_registry {label}: "
        if not isinstance(row, dict):
            errors.append(prefix + "figure entry must be an object")
            continue
        for key, hash_key in (("path", "sha256"), ("data_file", "data_sha256")):
            if key == "data_file" and not (row.get(key) or row.get(hash_key)):
                continue
            try:
                relative = row.get(key)
                if not isinstance(relative, str) or not relative:
                    raise ValueError(f"{key} is required")
                artifact = (root / relative).resolve()
                artifact.relative_to(root)
                if not artifact.is_file() or hashlib.sha256(artifact.read_bytes()).hexdigest() != row.get(hash_key):
                    raise ValueError(f"{key} is missing or its hash changed")
            except (OSError, ValueError, TypeError) as exc:
                errors.append(prefix + str(exc))
        try:
            relative = row.get("metadata")
            if not isinstance(relative, str) or not relative:
                raise ValueError("metadata is required for a completed formal figure")
            metadata = (root / relative).resolve()
            metadata.relative_to(root)
            errors.extend(prefix + error for error in validate_figure_review(metadata, source_root=root))
            rendered = (root / str(row.get("path", ""))).resolve()
            expected_stem = metadata.with_name(metadata.name.removesuffix(".figure.json"))
            if (not metadata.name.endswith(".figure.json") or rendered.suffix.lower() not in {".pdf", ".svg", ".png"}
                    or rendered.with_suffix("") != expected_stem):
                errors.append(prefix + "rendered path does not belong to its reviewed metadata bundle")
        except (OSError, ValueError, TypeError) as exc:
            errors.append(prefix + str(exc))
    return errors


def _manuscript_figure_errors(root, records, registry_paths):
    """Require actual Markdown/TeX figure references to use reviewed bundles."""
    def stem(path):
        if path.name.endswith(".figure.json"):
            return path.with_name(path.name.removesuffix(".figure.json"))
        return path.with_suffix("") if path.suffix.lower() in {".pdf", ".svg", ".png", ".jpg", ".jpeg"} else path

    registered = set()
    for relative in registry_paths:
        try:
            payload = json.loads((root / relative).read_text(encoding="utf-8"))
            rows = payload.get("figures") if isinstance(payload, dict) else payload
            for row in rows if isinstance(rows, list) else []:
                if isinstance(row, dict):
                    for key in ("metadata", "path"):
                        if isinstance(row.get(key), str):
                            registered.add(stem((root / row[key]).resolve()))
        except (OSError, UnicodeError, ValueError, TypeError):
            continue  # The registry validator reports the underlying failure.
    errors = []
    manuscripts = {str(record.get("path", "")) for role, record in records.items()
                   if role in {"manuscript", "main_markdown", "main_tex"} and isinstance(record, dict)}
    for relative in manuscripts:
        paper = root / relative
        if paper.suffix.lower() not in {".md", ".tex"}:
            continue
        try:
            text = paper.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"figure_registry: manuscript unreadable: {relative}: {exc}")
            continue
        if paper.suffix.lower() == ".md":
            targets = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
        else:
            # Comments are not inserted figures; escaped percent signs remain.
            text = re.sub(r"(?m)(?<!\\)%.*$", "", text)
            targets = re.findall(r"\\includegraphics\*?(?:\[[^\]]*\])?\{([^{}]+)\}", text)
        for target in targets:
            target = target.strip()
            if target.startswith("<") and ">" in target:
                target = target[1:target.index(">")]
            elif paper.suffix.lower() == ".md":
                target = re.split(r'\s+["\']', target, maxsplit=1)[0]
            candidates = {stem((base / target).resolve()) for base in (paper.parent, root)}
            if not candidates.intersection(registered):
                errors.append(f"figure_registry: unregistered manuscript figure: {relative}: {target}")
    return errors


def validate_skill_boundary(root, skill, records, *, phase):
    """Validate available formal Skill evidence without imposing future stages."""
    if phase not in {"inputs", "outputs"}:
        raise ValueError("phase must be inputs or outputs")
    return validate_gate_payloads(
        root, {record["role"]: record for record in records},
        require_results=skill in {"write-model-paper", "review-model-paper"} or (
            skill == "solve-model" and phase == "outputs"),
        require_figures=skill == "review-model-paper" or (
            phase == "outputs" and skill in {"make-model-figures", "write-model-paper"}),
    )


def validate_gate_payloads(root, records, *, require_results=False, require_figures=False):
    """Check machine evidence, failing closed for required report statuses.

    Human review is still required: a status is an execution attestation, not
    proof of mathematics. Question obligations and failed checks are inspected.
    """
    root = Path(root).resolve()
    payloads, errors = {}, []
    needed = PASS_ROLES | CHECK_ROLES | {"decision_contract", "quality_validation", "submission_readiness", "machine_results", "result_object"}
    for role, record in records.items():
        if role not in needed:
            continue
        try:
            data = json.loads((root / record["path"]).read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("expected JSON object")
            payloads[role] = data
        except (OSError, ValueError, TypeError, KeyError) as exc:
            errors.append(f"{role}: invalid evidence: {exc}")
            continue
        if role in PASS_ROLES and data.get("status", data.get("overall_status")) != "PASS":
            errors.append(f"{role}: explicit PASS required")
        if role == "submission_readiness" and (data.get("status") != "READY_FOR_SUBMISSION" or data.get("all_review_gates_passed") is not True):
            errors.append("submission_readiness: submission gates did not pass")
        if isinstance(data.get("gates"), dict) and any(v is not True for v in data["gates"].values()):
            errors.append(f"{role}: failed or unknown gate")
        if role in CHECK_ROLES and (_failed_check(data) or not data):
            errors.append(f"{role}: empty or failed validation")
        if role == "figure_audit_report" and require_figures and data.get("status") != "PASS":
            errors.append("figure_audit_report: completed formal figures require explicit PASS")
        if role == "quality_validation":
            if _failed_check(data) or not data:
                errors.append("quality_validation: empty or failed validation")
        if role in {"machine_results", "result_object"}:
            if str(data.get("status", "")).lower() in {"infeasible", "fail", "failed", "blocked", "unbounded", "error"} or data.get("passed") is False:
                errors.append(f"{role}: unsuccessful solver result cannot complete validation")
    contract = payloads.get("decision_contract")
    if contract is not None:
        checks = validate_contract_artifacts(contract, root) if require_results else validate_decision_contract(contract)
        if "quality_validation" in payloads:
            checks += validate_quality_validation(contract, payloads["quality_validation"])
        errors += [f"decision_contract: {i['message']}" for i in checks]
        if require_results:
            for question in contract.get("questions", []):
                if not isinstance(question, dict):
                    continue
                for key in ("result_artifact", "validation_artifact"):
                    path = root / str(question.get(key, ""))
                    if not path.is_file() or path.suffix != ".json":
                        continue
                    try:
                        data = json.loads(path.read_text(encoding="utf-8"))
                        if isinstance(data, dict):
                            status = str(data.get("status", data.get("overall_status", ""))).upper()
                            if status in {"FAIL", "BLOCKED", "INFEASIBLE", "UNBOUNDED", "ERROR", "FAILED"}:
                                errors.append(f"{question['id']} {key}: failed result or validation")
                            if data.get("passed") is False:
                                errors.append(f"{question['id']} {key}: validation did not pass")
                    except (OSError, ValueError) as exc:
                        errors.append(f"{question.get('id')} {key}: invalid JSON: {exc}")
    if require_results and contract is None:
        errors.append("decision_contract: required for question-level validation")
    if require_figures:
        registries = {str(record.get("path", "")) for role, record in records.items()
                      if role in {"figure_registry", "figure_inventory"} and isinstance(record, dict)}
        if not registries:
            registries = {str(path.relative_to(root)) for path in
                          (root / "paper/figure-registry.json", root / "figure-registry.json") if path.is_file()}
        if not registries:
            errors.append("figure_registry: required for completed formal figures; use [] for no figures")
        for path in sorted(registries):
            errors.extend(validate_figure_registry(root, path))
        errors.extend(_manuscript_figure_errors(root, records, registries))
    return errors
