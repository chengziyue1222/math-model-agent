import json

from algorithms.adversarial_review import semantic_issues


def test_required_supplier_list_and_registry_completeness_are_enforced(tmp_path):
    paper_dir = tmp_path / "paper"
    paper_dir.mkdir()
    (paper_dir / "main.md").write_text("# result\nS001\n", encoding="utf-8")
    (paper_dir / "paper-spec.yaml").write_text("required_supplier_count: 50\n", encoding="utf-8")
    (paper_dir / "formula-registry.json").write_text(json.dumps([{"latex": "x"}]), encoding="utf-8")
    (paper_dir / "table-registry.json").write_text(json.dumps([{"data_file": "x"}]), encoding="utf-8")

    codes = {issue["code"] for issue in semantic_issues(tmp_path, paper_dir / "main.md")}

    assert "required_list_incomplete" in codes
    assert "formula_registry_incomplete" in codes
    assert "table_registry_incomplete" in codes


def test_decomposition_cannot_be_described_as_integrated_robust(tmp_path):
    paper_dir = tmp_path / "paper"
    paper_dir.mkdir()
    (paper_dir / "main.md").write_text("一体化鲁棒优化模型", encoding="utf-8")
    (tmp_path / "model_specification.json").write_text(json.dumps({"method": "decomposition"}), encoding="utf-8")

    codes = {issue["code"] for issue in semantic_issues(tmp_path, paper_dir / "main.md")}

    assert "model_claim_code_mismatch" in codes
