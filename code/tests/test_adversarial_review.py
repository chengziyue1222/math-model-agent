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


def test_declared_decision_quality_requirements_fail_closed(tmp_path):
    paper_dir = tmp_path / "paper"
    paper_dir.mkdir()
    (paper_dir / "main.md").write_text("# paper", encoding="utf-8")
    (tmp_path / "decision_contract.json").write_text(
        json.dumps({
            "questions": [{
                "id": "planning",
                "result_artifact": "results/plan.csv",
                "validation_artifact": "reports/validation.json",
                "requires_dynamic_state": True,
                "requires_uncertainty": True,
                "requires_tradeoff": True,
                "requires_baseline": True,
            }]
        }),
        encoding="utf-8",
    )
    (tmp_path / "model_specification.json").write_text(json.dumps({"variables": ["x"]}), encoding="utf-8")
    (tmp_path / "quality_validation.json").write_text(json.dumps({"uncertainty": {"mode": "deterministic"}}), encoding="utf-8")

    codes = {issue["code"] for issue in semantic_issues(tmp_path, paper_dir / "main.md")}

    assert {"multi_period_state_missing", "uncertainty_evidence_missing", "tradeoff_evidence_missing", "baseline_comparison_missing"} <= codes


def test_declared_decision_quality_requirements_accept_complete_evidence(tmp_path):
    paper_dir = tmp_path / "paper"
    paper_dir.mkdir()
    (paper_dir / "main.md").write_text("# paper", encoding="utf-8")
    (tmp_path / "decision_contract.json").write_text(
        json.dumps({
            "questions": [{
                "id": "planning",
                "result_artifact": "results/plan.csv",
                "validation_artifact": "reports/validation.json",
                "requires_dynamic_state": True,
                "requires_uncertainty": True,
                "requires_tradeoff": True,
                "requires_baseline": True,
            }]
        }),
        encoding="utf-8",
    )
    (tmp_path / "model_specification.json").write_text(json.dumps({"state_variables": ["inventory"], "balance_constraints": ["I[t+1]=I[t]+in-out"]}), encoding="utf-8")
    (tmp_path / "quality_validation.json").write_text(
        json.dumps({
            "uncertainty": {"mode": "scenario", "scenario_source": "held-out history", "holdout_or_stress_evidence": "reports/stress.json"},
            "multiobjective": {"strategy": "epsilon_constraint", "tradeoff_evidence": "results/frontier.csv"},
            "baseline_comparison": {"shared_inputs": True, "metrics": {"cost": 1.0}},
        }),
        encoding="utf-8",
    )

    codes = {issue["code"] for issue in semantic_issues(tmp_path, paper_dir / "main.md")}

    assert not {"multi_period_state_missing", "uncertainty_evidence_missing", "tradeoff_evidence_missing", "baseline_comparison_missing"} & codes
