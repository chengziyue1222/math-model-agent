import json
import subprocess
import sys
from pathlib import Path
import pytest

from algorithms.figure_handoff import claim_binding
from algorithms.venue_config import load_venue_config


def test_claim_binding_does_not_prove_manuscript_insertion(tmp_path):
    assert claim_binding(tmp_path, "F1") == ([], False, "NEEDS_CLAIM_BINDING")
    (tmp_path / "paper").mkdir()
    (tmp_path / "paper/claim-registry.json").write_text(json.dumps([
        {"claim_id": "C1", "figure_ids": ["F1"]}]), encoding="utf-8")
    assert claim_binding(tmp_path, "F1") == (["C1"], False, "NEEDS_BODY_INSERTION")
    assert claim_binding(tmp_path, "F2")[1] is False


def test_venue_configuration_uses_generic_default_and_explicit_precedence(tmp_path):
    assert load_venue_config()["venue"] == "generic-research-report"
    assert load_venue_config()["body_page_limit"] is None
    assert load_venue_config(venue="CUMCM")["body_page_limit"] == 30
    assert load_venue_config(venue="journal")["references_style"] == "journal-template"
    path = tmp_path / "venue.yaml"
    path.write_text("venue: journal\noverrides:\n  body_page_limit: 12\n", encoding="utf-8")
    assert load_venue_config(path)["body_page_limit"] == 12
    assert load_venue_config(path, venue="MathorCup")["venue"] == "MathorCup"
    with pytest.raises(ValueError):
        load_venue_config(venue="unknown")


def test_help_has_no_runtime_dependencies_or_side_effects(tmp_path):
    root = Path(__file__).resolve().parents[2]
    for script in ["skills/make-model-figures/scripts/minimal_example.py", "scripts/build_figure_library.py"]:
        result = subprocess.run([sys.executable, "-S", str(root / script), "--help"],
                                cwd=tmp_path, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        assert "usage:" in result.stdout
    assert not list(tmp_path.iterdir())


def test_capability_matrix_is_generated_from_registry(tmp_path):
    from scripts.generate_figure_capability_matrix import generate
    root = Path(__file__).resolve().parents[2]
    actual = generate(tmp_path / "matrix.md").read_text(encoding="utf-8")
    assert actual == (root / "docs/figure-library-capability-matrix.md").read_text(encoding="utf-8")
