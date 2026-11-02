"""Behavioral regressions for current runs, semantic boundaries and formal figures."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from algorithms.evidence_gates import validate_gate_payloads, validate_figure_registry
from algorithms.figure_export import VISUAL_CHECKS, implementation_hashes
from scripts.run_standard_skill import main as run_skill
from scripts.skill_contracts import contract_for
from scripts.skill_runtime import finish_skill_run, list_project_skill_runs, start_skill_run, validate_skill_run


def _put(root, path, value):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value), encoding="utf-8")
    return target


def _attempt(root, status, *, project="case", profile="competition"):
    start = start_skill_run(root, project, "solve-model", profile=profile)
    if status != "RUNNING":
        finish_skill_run(root, start["run_id"], status=status)
    return start["run_id"]


@pytest.mark.parametrize("profile", ["competition", "audit"])
@pytest.mark.parametrize("latest", ["RUNNING", "FAIL", "BLOCKED"])
def test_latest_attempt_cannot_reuse_old_pass_and_new_pass_recovers(tmp_path, latest, profile):
    _attempt(tmp_path, "PASS", profile=profile)
    _attempt(tmp_path, latest, profile=profile)
    errors = validate_skill_run(tmp_path, project_id="case", profile=profile)
    assert errors
    assert any("unfinished" in error or "current_skill_run_not_passed" in error for error in errors)
    _attempt(tmp_path, "PASS", profile=profile)
    assert validate_skill_run(tmp_path, project_id="case", profile=profile) == []
    assert len(list_project_skill_runs(tmp_path, "case")) == 3


def test_current_attempt_is_scoped_by_project_and_profile(tmp_path):
    _attempt(tmp_path, "PASS", project="a")
    _attempt(tmp_path, "FAIL", project="b")
    _attempt(tmp_path, "BLOCKED", project="a", profile="audit")
    assert validate_skill_run(tmp_path, project_id="a", profile="competition") == []
    assert validate_skill_run(tmp_path, project_id="b", profile="competition")
    assert validate_skill_run(tmp_path, project_id="a", profile="audit")


def _runner_arguments(root, skill, *, profile="competition"):
    contract = contract_for(skill, profile=profile)
    arguments = ["--project-root", str(root), "--project-id", "case", "--skill", skill,
                 "--skill-path", str(root), "--profile", profile]
    outputs = {}
    for role in contract["inputs"]:
        payload = {"status": "PASS"}
        if role == "decision_contract":
            payload = {"questions": [{"id": "q1", "result_artifact": "outputs/result_object.json",
                                      "validation_artifact": "outputs/quality_validation.json"}]}
        if role == "model_config":
            payload = {"observations": [2, 4, 6]}
        if role == "quality_validation":
            payload = {"baseline": {"passed": True}}
        if role == "figure_registry":
            payload = []
        _put(root, f"inputs/{role}.json", payload)
        arguments += ["--input", f"{role}=inputs/{role}.json"]
    for role in contract["outputs"]:
        path = f"outputs/{role}.json"
        arguments += ["--output", f"{role}={path}"]
        outputs[path] = {"status": "PASS"}
    return arguments, outputs


def test_runner_exit_zero_with_failed_validation_is_not_pass_and_retry_recovers(tmp_path):
    arguments, outputs = _runner_arguments(tmp_path, "solve-model")
    script = tmp_path / "solve.py"
    # Compute a real saved result in the child process, then deliberately fail
    # its quality check. A second real execution repairs that check.
    script.write_text(
        "import json, statistics, sys\nfrom pathlib import Path\n"
        f"outputs={outputs!r}\n"
        "values=json.loads(Path('inputs/model_config.json').read_text())['observations']\n"
        "outputs['outputs/result_object.json']={'status':'optimal','value':statistics.mean(values)}\n"
        "outputs['outputs/quality_validation.json']={'baseline':{'passed':sys.argv[1]=='pass'}}\n"
        "for name, payload in outputs.items():\n"
        " p=Path(name); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload))\n",
        encoding="utf-8",
    )
    assert run_skill([*arguments, "--", sys.executable, str(script), "fail"]) == 1
    failed = list_project_skill_runs(tmp_path, "case")[-1]
    assert failed["status"] == "FAIL" and failed["outputs"]
    assert any("semantic" in warning for warning in failed["warnings"])
    assert json.loads((tmp_path / "outputs/result_object.json").read_text())["value"] == 4
    assert run_skill([*arguments, "--", sys.executable, str(script), "pass"]) == 0
    assert validate_skill_run(tmp_path, project_id="case", required_skills=["solve-model"], profile="competition") == []


def test_runner_rejects_failed_quality_before_drawing(tmp_path):
    arguments, _ = _runner_arguments(tmp_path, "make-model-figures")
    _put(tmp_path, "inputs/quality_validation.json", {"baseline": {"passed": False}})
    command = "from pathlib import Path; Path('should-not-draw').write_text('ran')"
    assert run_skill([*arguments, "--", sys.executable, "-c", command]) == 1
    assert not (tmp_path / "should-not-draw").exists()
    assert list_project_skill_runs(tmp_path, "case")[-1]["status"] == "BLOCKED"


def test_direct_finish_cannot_bypass_required_skill_semantic_verification(tmp_path):
    _, outputs = _runner_arguments(tmp_path, "solve-model")
    outputs["outputs/result_object.json"] = {"status": "optimal", "value": 4}
    outputs["outputs/quality_validation.json"] = {"baseline": {"passed": False}}
    for path, payload in outputs.items():
        _put(tmp_path, path, payload)
    contract = contract_for("solve-model")
    start = start_skill_run(tmp_path, "case", "solve-model", profile="competition",
                            inputs=[(role, f"inputs/{role}.json") for role in contract["inputs"]])
    finish_skill_run(tmp_path, start["run_id"],
                     outputs=[(role, f"outputs/{role}.json") for role in contract["outputs"]])
    assert validate_skill_run(tmp_path, project_id="case", profile="competition") == []  # trace integrity only
    errors = validate_skill_run(tmp_path, project_id="case", profile="competition", required_skills=["solve-model"])
    assert any("current_skill_semantic_invalid" in error and "quality_validation" in error for error in errors)


def test_required_skill_request_needs_full_roles_even_for_direct_finish(tmp_path):
    _attempt(tmp_path, "PASS")
    errors = validate_skill_run(tmp_path, project_id="case", profile="competition", required_skills=["solve-model"])
    assert any("current_skill_contract_invalid" in error for error in errors)


def test_current_legacy_trace_keeps_its_original_contract_interpretation(tmp_path):
    contract = contract_for("solve-model", version="1.4")
    for role in (*contract["inputs"], *contract["outputs"]):
        _put(tmp_path, f"legacy/{role}.json", {"old-format": "record"})
    start = start_skill_run(tmp_path, "legacy", "solve-model", profile="competition",
                            inputs=[(role, f"legacy/{role}.json") for role in contract["inputs"]])
    finish_skill_run(tmp_path, start["run_id"], outputs=[(role, f"legacy/{role}.json") for role in contract["outputs"]])
    path = tmp_path / "manifests/skill-runs.jsonl"
    records = [json.loads(line) for line in path.read_text().splitlines()]
    for record in records:
        record["contract_version"] = "1.4"
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
    assert validate_skill_run(tmp_path, project_id="legacy", profile="competition", required_skills=["solve-model"]) == []


@pytest.mark.parametrize("skill", ["select-model", "analyze-model-data"])
def test_upstream_skills_do_not_require_future_results_or_figures(tmp_path, skill):
    arguments, outputs = _runner_arguments(tmp_path, skill)
    if skill == "select-model":
        outputs["outputs/decision_contract.json"] = {"questions": [{"id": "q1",
            "result_artifact": "not-solved-yet.json", "validation_artifact": "not-validated-yet.json"}]}
    script = tmp_path / "upstream.py"
    script.write_text(
        "import json\nfrom pathlib import Path\n" + f"outputs={outputs!r}\n"
        "for name, payload in outputs.items():\n"
        " p=Path(name); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload))\n",
        encoding="utf-8",
    )
    assert run_skill([*arguments, "--", sys.executable, str(script)]) == 0
    assert not (tmp_path / "figure-registry.json").exists()
    assert not (tmp_path / "not-solved-yet.json").exists()


@pytest.mark.parametrize("downstream_status", ["RUNNING", "FAIL", "BLOCKED", "STALE_PASS"])
def test_stage_request_ignores_pending_downstream_but_release_rejects_it(tmp_path, downstream_status):
    arguments, outputs = _runner_arguments(tmp_path, "analyze-model-data")
    script = tmp_path / "analyze.py"
    script.write_text(
        "import json\nfrom pathlib import Path\n" + f"outputs={outputs!r}\n"
        "for name, payload in outputs.items():\n"
        " p=Path(name); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload))\n",
        encoding="utf-8",
    )
    assert run_skill([*arguments, "--", sys.executable, str(script)]) == 0
    _put(tmp_path, "later-paper.json", {"version": 1})
    downstream = start_skill_run(tmp_path, "case", "write-model-paper", profile="competition",
                                inputs=[("result_object", "later-paper.json")])
    if downstream_status != "RUNNING":
        finish_skill_run(tmp_path, downstream["run_id"],
                         status="PASS" if downstream_status == "STALE_PASS" else downstream_status)
    _put(tmp_path, "later-paper.json", {"version": 2})
    assert validate_skill_run(tmp_path, project_id="case", profile="competition",
                             required_skills=["analyze-model-data"]) == []
    assert validate_skill_run(tmp_path, project_id="case", profile="competition",
                             required_skills=["analyze-model-data", "write-model-paper"])
    assert validate_skill_run(tmp_path, project_id="case", profile="competition")


def _bound_figure(root):
    source = _put(root, "results/plot-data.json", {"x": [1, 2], "y": [4, 5]})
    stem = root / "figures/chart"
    stem.parent.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for extension in ("pdf", "svg", "png"):
        path = stem.with_suffix("." + extension)
        path.write_bytes(b"format validity is covered by export tests")
        hashes[extension] = hashlib.sha256(path.read_bytes()).hexdigest()
    metadata = {
        "schema_version": 3, "audit": {"passed": True}, "file_audit": {"status": "PASS"},
        "source_files": [{"path": "results/plot-data.json", "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}],
        "environment": {"implementation_hashes": implementation_hashes()}, "output_hashes": hashes,
        "completion_status": "PASS", "visual_review": {"status": "PASS", "reviewer": "test reviewer",
            "output_hashes": hashes, **dict.fromkeys(VISUAL_CHECKS, "PASS")},
    }
    path = _put(root, "figures/chart.figure.json", metadata)
    row = {"figure_id": "F1", "path": "figures/chart.pdf", "sha256": hashes["pdf"],
           "metadata": "figures/chart.figure.json", "inserted_in_body": True}
    _put(root, "figure-registry.json", [row])
    return path, metadata


@pytest.mark.parametrize("key", sorted(VISUAL_CHECKS))
@pytest.mark.parametrize("state", ["FAIL", "NOT_CHECKED"])
def test_formal_gates_read_each_current_visual_check(tmp_path, key, state):
    path, metadata = _bound_figure(tmp_path)
    assert validate_figure_registry(tmp_path, "figure-registry.json") == []
    metadata["visual_review"][key] = state
    path.write_text(json.dumps(metadata), encoding="utf-8")
    errors = validate_gate_payloads(tmp_path, {"figure_registry": {"path": "figure-registry.json"}}, require_figures=True)
    assert any(key in error and state in error for error in errors)
    assert validate_gate_payloads(tmp_path, {}, require_figures=False) == []


@pytest.mark.parametrize("mutation", ["source", "output", "implementation", "missing_metadata"])
def test_formal_figure_bindings_cannot_be_reused_after_changes(tmp_path, mutation):
    path, metadata = _bound_figure(tmp_path)
    if mutation == "source":
        _put(tmp_path, "results/plot-data.json", {"changed": True})
    elif mutation == "output":
        (tmp_path / "figures/chart.svg").write_bytes(b"changed")
    elif mutation == "implementation":
        metadata["environment"]["implementation_hashes"]["figure_export.py"] = "0" * 64
        path.write_text(json.dumps(metadata), encoding="utf-8")
    else:
        path.unlink()
    assert validate_figure_registry(tmp_path, "figure-registry.json")


def test_no_figures_is_explicit_and_not_a_status_placeholder(tmp_path):
    assert validate_gate_payloads(tmp_path, {}, require_figures=True)
    _put(tmp_path, "figure-registry.json", {"status": "PASS"})
    assert validate_gate_payloads(tmp_path, {}, require_figures=True)
    _put(tmp_path, "figure-registry.json", [])
    assert validate_gate_payloads(tmp_path, {}, require_figures=True) == []


def test_registry_cannot_borrow_a_different_figures_successful_review(tmp_path):
    _bound_figure(tmp_path)
    other = tmp_path / "figures/unreviewed.pdf"
    other.write_bytes(b"unreviewed output")
    registry = json.loads((tmp_path / "figure-registry.json").read_text())
    registry[0]["path"] = "figures/unreviewed.pdf"
    registry[0]["sha256"] = hashlib.sha256(other.read_bytes()).hexdigest()
    _put(tmp_path, "figure-registry.json", registry)
    assert any("does not belong" in error for error in validate_figure_registry(tmp_path, "figure-registry.json"))


@pytest.mark.parametrize("extension, content", [
    ("md", "![result](figures/chart.png)"),
    ("tex", r"\includegraphics[width=150mm]{figures/chart.pdf}"),
])
def test_empty_registry_cannot_hide_figures_inserted_in_manuscript(tmp_path, extension, content):
    _bound_figure(tmp_path)
    paper = tmp_path / f"main.{extension}"
    paper.write_text(content, encoding="utf-8")
    records = {"manuscript": {"path": paper.name}}
    assert validate_gate_payloads(tmp_path, records, require_figures=True) == []
    _put(tmp_path, "figure-registry.json", [])
    assert any("unregistered manuscript figure" in error for error in
               validate_gate_payloads(tmp_path, records, require_figures=True))


def test_formal_figure_runner_waits_for_actual_review_but_rapid_can_preview(tmp_path):
    arguments, _ = _runner_arguments(tmp_path, "make-model-figures")
    path, metadata = _bound_figure(tmp_path)
    metadata["visual_review"]["png"] = "NOT_CHECKED"
    path.write_text(json.dumps(metadata), encoding="utf-8")
    registry = json.loads((tmp_path / "figure-registry.json").read_text())
    script = tmp_path / "publish_registry.py"
    script.write_text(
        "import json\nfrom pathlib import Path\n"
        "Path('outputs').mkdir(exist_ok=True)\n"
        f"Path('outputs/figure_registry.json').write_text(json.dumps({registry!r}))\n"
        "review=json.loads(Path('figures/chart.figure.json').read_text())['visual_review']\n"
        "status='PASS' if review['png']=='PASS' else 'NEEDS_VISUAL_REVIEW'\n"
        "Path('outputs/figure_audit_report.json').write_text(json.dumps({'status':status}))\n",
        encoding="utf-8",
    )
    assert run_skill([*arguments, "--", sys.executable, str(script)]) == 1
    assert list_project_skill_runs(tmp_path, "case")[-1]["status"] == "FAIL"
    metadata["visual_review"]["png"] = "PASS"
    path.write_text(json.dumps(metadata), encoding="utf-8")
    assert run_skill([*arguments, "--", sys.executable, str(script)]) == 0
    rapid = ["--project-root", str(tmp_path), "--project-id", "preview", "--skill", "make-model-figures",
             "--skill-path", str(tmp_path), "--profile", "rapid"]
    assert run_skill([*rapid, "--", sys.executable, "-c", "pass"]) == 0


def test_review_release_rejects_changed_figure_then_rewind_requires_fresh_review(tmp_path):
    script = Path(__file__).resolve().parents[2] / "skills/run-modeling-project/scripts/project_state.py"
    spec = importlib.util.spec_from_file_location("recovery_project_state", script)
    state = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(state)
    state.initialize(tmp_path, "case", "run-manifest.json")
    start = state._read_state(tmp_path)
    start["current_stage"] = "writing"
    state._write_state(tmp_path, start)
    metadata_path, metadata = _bound_figure(tmp_path)
    _put(tmp_path, "results/q1.json", {"value": 4})
    _put(tmp_path, "results/validation.json", {"status": "PASS"})
    review_evidence = []
    for role in (*state.gate_requirements(start, "review"), "main_pdf", "latex_compile_report"):
        path = "run-manifest.json" if role == "run_manifest" else f"reports/{role}.json"
        payload = {"status": "PASS"}
        if role == "decision_contract":
            payload = {"questions": [{"id": "q1", "result_artifact": "results/q1.json",
                                      "validation_artifact": "results/validation.json"}]}
        if role == "figure_inventory":
            payload = json.loads((tmp_path / "figure-registry.json").read_text())
        _put(tmp_path, path, payload)
        review_evidence.append(f"{role}={path}")
    reviewed = state.advance(tmp_path, "review", review_evidence, "first actual review")
    release_evidence = []
    for role in state.gate_requirements(reviewed, "release"):
        if role == "run_manifest":
            path = "run-manifest.json"
        else:
            path = f"reports/{role}.json"
            _put(tmp_path, path, {"status": "READY_FOR_SUBMISSION", "all_review_gates_passed": True}
                 if role == "submission_readiness" else {"status": "PASS"})
        release_evidence.append(f"{role}={path}")
    # Only nested metadata changes: the registered inventory hash stays current.
    # Release must consume that metadata rather than trust an old summary PASS.
    metadata["visual_review"]["vector"] = "FAIL"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    assert state.verify_evidence(tmp_path, reviewed) == []
    with pytest.raises(ValueError, match="vector.*FAIL"):
        state.advance(tmp_path, "release", release_evidence, "must not release")
    assert state._read_state(tmp_path)["failed_gates"][-1]["to"] == "release"
    rewound = state.rewind(tmp_path, "writing", "repair failed vector and re-review dependent outputs")
    assert rewound["stale_evidence"] and not rewound["evidence"]
    metadata["visual_review"]["vector"] = "PASS"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    state.advance(tmp_path, "review", review_evidence, "fresh review after repair")
    released = state.advance(tmp_path, "release", release_evidence, "current evidence all passes")
    assert state.handoff(released)["status"] == "complete"
    assert released["failed_gates"] and released["stale_evidence"]
