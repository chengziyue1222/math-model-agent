"""A formal consumer must recheck the delivered bundle, not a cached PASS."""
import json
import hashlib
from pathlib import Path

import pytest

from algorithms.figure_export import export_bundle, record_visual_review, validate_figure_review
from algorithms.figures import get_figure
from algorithms.sci_figures import FigureContract


@pytest.fixture
def bundle(tmp_path):
    source = tmp_path / "observations.json"
    source.write_text('[1, 2, 3, 4]', encoding="utf-8")
    fig = get_figure("ecdf")(data={"values": [1, 2, 3, 4]})
    paths = export_bundle(fig, tmp_path / "ecdf", FigureContract(
        "All four observations", ("the saved sample",), source_paths=(str(source),),
        width_mm=150), close=True)
    metadata = Path(paths["metadata"])
    record_visual_review(metadata, reviewer="unit-test fixture", notes="Synthetic review fixture",
                         checks=dict.fromkeys(("png", "vector", "physical_proof", "grayscale", "source_values"), "PASS"))
    return metadata, source


def update(metadata, operation):
    payload = json.loads(metadata.read_text(encoding="utf-8"))
    operation(payload)
    metadata.write_text(json.dumps(payload), encoding="utf-8")


def test_current_bundle_passes_and_source_change_invalidates_it(bundle):
    metadata, source = bundle
    assert validate_figure_review(metadata) == []
    source.write_text('[1, 2, 3, 99]', encoding="utf-8")
    assert any("source changed" in error for error in validate_figure_review(metadata))


def test_portable_sources_are_resolved_from_explicit_root(bundle, tmp_path, monkeypatch):
    metadata, source = bundle
    update(metadata, lambda p: p["source_files"][0].update(resolved_path=source.name))
    elsewhere = tmp_path / "another-caller"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert validate_figure_review(metadata, source_root=tmp_path) == []
    assert any("source changed" in error for error in validate_figure_review(metadata))


@pytest.mark.parametrize("check", ["png", "vector", "physical_proof", "grayscale", "source_values"])
def test_a_top_level_pass_cannot_hide_an_unchecked_dimension(bundle, check):
    metadata, _ = bundle
    update(metadata, lambda p: p["visual_review"].update({check: "NOT_CHECKED"}))
    assert any(check in error for error in validate_figure_review(metadata))


def test_changed_export_or_incomplete_bindings_cannot_reuse_review(bundle):
    metadata, _ = bundle
    png = metadata.with_name("ecdf.png")
    png.write_bytes(png.read_bytes() + b"changed")
    assert any("export changed" in error for error in validate_figure_review(metadata))
    update(metadata, lambda p: p["environment"]["implementation_hashes"].pop("figures/styles.py"))
    assert any("module inventory" in error for error in validate_figure_review(metadata))


@pytest.mark.parametrize("regression", [
    {"status": "NEEDS_REVIEW"},
    {"status": "DOCUMENTED_DISPLAY_CHANGE", "documented_change": "layout only"},
    {"status": "PASS", "invariant_checks": {"same_values": False}, "verification_evidence": {"status": "PASS"}},
])
def test_numerical_comparison_needs_actual_passing_invariants(bundle, regression):
    metadata, _ = bundle
    update(metadata, lambda p: p.update(numerical_regression=regression))
    assert any("numerical comparison" in error for error in validate_figure_review(metadata))


def test_verified_display_change_is_accepted_without_claiming_identical_geometry(bundle):
    metadata, source = bundle
    verifier = source.with_name('verifier.py')
    verifier.write_text('# invariant verifier fixture\n', encoding='utf-8')
    code = {'path': str(verifier), 'sha256': hashlib.sha256(verifier.read_bytes()).hexdigest()}
    def bind(payload):
        def canonical(value):
            return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                             separators=(',', ':')).encode('utf-8')).hexdigest()
        payload['numerical_regression'] = {
            'status': 'DOCUMENTED_DISPLAY_CHANGE', 'invariant_checks': {'same_source_and_statistics': True},
            'artist_evidence': [], 'comparison_code': code,
            'verification_evidence': {'status': 'PASS', 'method': 'saved-input-and-plotted-artists',
                                      'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                                      'verifier_code': code, 'artist_capture_code': code,
                                      'artist_evidence_sha256': canonical([]),
                                      'figure_metadata_sha256': canonical(payload['figure_metadata'])}}
    update(metadata, bind)
    assert validate_figure_review(metadata) == []
    update(metadata, lambda p: p['figure_metadata'].update(changed_denominator=999))
    assert any('figure_metadata' in error for error in validate_figure_review(metadata))
    verifier.write_text('# changed verifier\n', encoding='utf-8')
    assert any('comparison code changed' in error for error in validate_figure_review(metadata))


def test_missing_legacy_review_is_readable_but_not_formally_complete(bundle):
    metadata, _ = bundle
    update(metadata, lambda p: p.pop("visual_review"))
    assert any("NOT_CHECKED" in error for error in validate_figure_review(metadata))
