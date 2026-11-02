import hashlib
import json

import pytest

from algorithms.paper_readiness import review_paper
from algorithms.figure_export import implementation_hashes, VISUAL_CHECKS


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reviewed_metadata(root, number, source):
    # These readiness fixtures test evidence binding; export format inspection
    # is exercised separately against real rendered publication bundles.
    stem = root / "figures" / f"f{number}"
    for extension in ("pdf", "png"):
        stem.with_suffix("." + extension).write_bytes(b"test publication artifact")
    hashes = {extension: _hash(stem.with_suffix("." + extension)) for extension in ("pdf", "svg", "png")}
    metadata = {
        "schema_version": 3, "audit": {"passed": True}, "file_audit": {"status": "PASS"},
        "source_files": [{"path": str(source.relative_to(root)), "sha256": _hash(source)}],
        "environment": {"implementation_hashes": implementation_hashes()}, "output_hashes": hashes,
        "completion_status": "PASS", "visual_review": {"status": "PASS", "reviewer": "test fixture",
            "output_hashes": hashes, **dict.fromkeys(VISUAL_CHECKS, "PASS")},
    }
    stem.with_suffix(".figure.json").write_text(json.dumps(metadata), encoding="utf-8")
    return {"figure_id": f"F{number}", "path": f"figures/f{number}.svg", "inserted_in_body": True,
            "metadata": f"figures/f{number}.figure.json", "sha256": hashes["svg"]}


def _setup(tmp_path, *, paper_extra="", tamper=False, infeasible=False):
    results = tmp_path / "results"; results.mkdir()
    result = results / "metrics.json"; result.write_text(json.dumps({"value": 12.3, "status": "infeasible" if infeasible else "optimal"}), encoding="utf-8")
    (results / "simulation_metrics.json").write_text(json.dumps({"seeds": [1, 2], "aggregate": {"x": {}}}), encoding="utf-8")
    figures = tmp_path / "figures"; figures.mkdir()
    for number in range(1, 9): (figures / f"f{number}.svg").write_text("<svg/>", encoding="utf-8")
    paper = tmp_path / "paper.md"
    sections = ["摘要", "关键词", "问题重述", "问题分析", "模型总体框架", "模型假设", "符号说明", "数据预处理", "模型评价", "最终建议", "参考文献", "附录", "复现说明"]
    body = "\n".join(f"## {s}\n" + "说明。" * 300 for s in sections)
    formulas = "\n".join(f"$$ x_{i}=y_{i} \\tag{{{i}}} $$" for i in range(1, 11))
    images = "\n".join(f"![图{n}](figures/f{n}.svg)" for n in range(1, 9))
    tables = "\n\n".join(f"表 T{n}\n|a|b|\n|---|---|\n|1|2|" for n in range(1, 7))
    refs = "\n".join(f"[{n}] Author. Verified source {n}." for n in range(1, 9))
    paper.write_text(body + "\n目标函数与约束。\n" + formulas + "\n" + images + "\n" + tables + "\n[claim:C1]\n" + refs + paper_extra, encoding="utf-8")
    (tmp_path / "paper-spec.yaml").write_text("title: test\nminimum_body_characters: 9000\nminimum_equations: 10\nminimum_figures: 8\nminimum_tables: 6\nminimum_references: 8\n", encoding="utf-8")
    (results / "decision_contract.json").write_text(json.dumps({"questions": [{"id": "q1", "result_artifact": "results/metrics.json", "validation_artifact": "results/quality_validation.json"}], "requirements": {"baseline_comparison_required": True}}), encoding="utf-8")
    (results / "quality_validation.json").write_text('{"baseline": {"passed": true}}', encoding="utf-8")
    (tmp_path / "evidence-index.json").write_text(json.dumps([{"evidence_id": "E1", "path": "results/metrics.json", "sha256": _hash(result)}]), encoding="utf-8")
    (tmp_path / "claim-registry.json").write_text(json.dumps([{"claim_id": "C1", "evidence_id": "E1", "json_pointer": "/value"}]), encoding="utf-8")
    (tmp_path / "figure-registry.json").write_text(json.dumps([_reviewed_metadata(tmp_path, n, result) for n in range(1, 9)]), encoding="utf-8")
    (tmp_path / "table-registry.json").write_text(json.dumps([{"table_id": f"T{n}", "inserted_in_body": True} for n in range(1, 7)]), encoding="utf-8")
    (tmp_path / "formula-registry.json").write_text(json.dumps([{"formula_id": str(n), "inserted_in_body": True} for n in range(1, 11)]), encoding="utf-8")
    if tamper: result.write_text(json.dumps({"value": 99}), encoding="utf-8")
    return paper


def test_complete_competition_paper_passes(tmp_path):
    assert review_paper(tmp_path, _setup(tmp_path)).overall_status == "PASS"


@pytest.mark.parametrize("mutator, expected", [
    (lambda root, paper: paper.write_text("# 短文", encoding="utf-8"), "paper_too_short"),
    (lambda root, paper: (root / "figure-registry.json").write_text("[]", encoding="utf-8"), "insufficient_figure_registry"),
    (lambda root, paper: paper.write_text(paper.read_text(encoding="utf-8").replace("C1", "UNKNOWN"), encoding="utf-8"), "claim_not_registered"),
    (lambda root, paper: (root / "formula-registry.json").write_text("[]", encoding="utf-8"), "formula_registry_incomplete"),
    (lambda root, paper: (root / "results" / "quality_validation.json").write_text("{}", encoding="utf-8"), "validation_evidence_failed"),
    (lambda root, paper: paper.write_text(paper.read_text(encoding="utf-8").replace("[8]", ""), encoding="utf-8"), "insufficient_citations"),
    (lambda root, paper: (root / "figure-registry.json").write_text(json.dumps([{"figure_id": "F1", "path": "figures/f1.svg", "inserted_in_body": False}]), encoding="utf-8"), "figure_not_inserted"),
    (lambda root, paper: (root / "claim-registry.json").write_text(json.dumps([{"claim_id": "C1", "evidence_id": "E1", "json_pointer": "/missing"}]), encoding="utf-8"), "claim_pointer_invalid"),
])
def test_required_fail_closed_gates(tmp_path, mutator, expected):
    paper = _setup(tmp_path); mutator(tmp_path, paper)
    review = review_paper(tmp_path, paper, profile="audit")
    assert review.overall_status == "FAIL"
    assert expected in {issue.code for issue in review.issues}


def test_tampered_evidence_fails(tmp_path):
    review = review_paper(tmp_path, _setup(tmp_path, tamper=True))
    assert review.overall_status == "FAIL" and review.stale_evidence == ["E1"]


def test_infeasible_claim_fails(tmp_path):
    review = review_paper(tmp_path, _setup(tmp_path, infeasible=True, paper_extra="\n最优方案 optimal"))
    assert review.overall_status == "FAIL"
    assert any(issue.code == "invalid_solver_claim" for issue in review.issues)


def test_teaching_example_uses_lower_presentation_thresholds(tmp_path):
    (tmp_path / "figure.svg").write_text("<svg/>", encoding="utf-8")
    paper = tmp_path / "short.md"; paper.write_text("## 教学\n$$ x=y $$\n![图](figure.svg)\n|a|b|\n|---|---|\n|1|2|", encoding="utf-8")
    assert review_paper(tmp_path, paper, mode="teaching_example").overall_status == "PASS"


def test_competition_thresholds_can_be_declared_in_paper_spec(tmp_path):
    paper = _setup(tmp_path)
    paper.write_text("\n".join(line for line in paper.read_text(encoding="utf-8").splitlines()
                                if not line.startswith("![图") or line.startswith("![图1]")), encoding="utf-8")
    (tmp_path / "paper-spec.yaml").write_text(
        "\n".join(
            (
                "title: test",
                "minimum_body_characters: 100",
                "minimum_equations: 1",
                "minimum_figures: 1",
                "minimum_tables: 1",
                "minimum_references: 1",
            )
        ),
        encoding="utf-8",
    )
    (tmp_path / "figure-registry.json").write_text(
        json.dumps([_reviewed_metadata(tmp_path, 1, tmp_path / "results/metrics.json")]),
        encoding="utf-8",
    )
    (tmp_path / "table-registry.json").write_text(
        json.dumps([{"table_id": "T1", "inserted_in_body": True}]),
        encoding="utf-8",
    )
    (tmp_path / "formula-registry.json").write_text(
        json.dumps([{"formula_id": "1", "inserted_in_body": True}]),
        encoding="utf-8",
    )
    assert review_paper(tmp_path, paper).overall_status == "PASS"
