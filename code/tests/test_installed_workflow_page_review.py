"""The workflow must consume current page evidence, not a copied review verdict."""
from copy import deepcopy
import hashlib
import json

import fitz
import pytest

from scripts.verify_modeling_skill_workflow import assert_pending_domain_failure, digest, markdown_review_source, page_review_errors


def _paper(tmp_path):
    path = tmp_path / "paper.pdf"
    with fitz.open() as document:
        for number in range(3):
            page = document.new_page()
            page.insert_text((50, 50), f"Actual result page {number + 1}")
        document.save(path)
    with fitz.open(path) as document:
        rows = [{"page": index + 1, "status": "PASS", "render_sha256": hashlib.sha256(
            page.get_pixmap(dpi=110, alpha=False).samples).hexdigest()} for index, page in enumerate(document)]
    return path, {"visual_review": "PASS", "reviewer": "actual human or agent inspection",
                  "paper_sha256": digest(path), "reviewed_pages": rows}


def test_current_individual_page_attestations_are_consumed(tmp_path):
    path, record = _paper(tmp_path)
    assert page_review_errors(path, record) == []
    record["reviewed_pages"][1]["render_sha256"] = "old raster"
    assert any("page 2" in error for error in page_review_errors(path, record))


def test_duplicate_passes_cannot_replace_an_unviewed_page(tmp_path):
    path, record = _paper(tmp_path)
    record["reviewed_pages"][1] = deepcopy(record["reviewed_pages"][0])
    assert "every page needs exactly one independent conclusion" in page_review_errors(path, record)


def test_old_pdf_and_empty_reviewer_are_rejected(tmp_path):
    path, record = _paper(tmp_path)
    record["paper_sha256"] = "old PDF"
    record["reviewer"] = ""
    errors = page_review_errors(path, record)
    assert any("reviewer" in error for error in errors)
    assert any("current PDF" in error for error in errors)


def test_expected_review_failure_cannot_hide_a_renderer_crash(tmp_path):
    manifests = tmp_path / "manifests"
    manifests.mkdir()
    trace = manifests / "skill-runs.jsonl"
    event = {"event": "finish", "skill": "write-model-paper", "status": "FAIL", "exit_code": 1, "outputs": []}
    trace.write_text(json.dumps(event) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="did not finish rendering successfully"):
        assert_pending_domain_failure(tmp_path, "write-model-paper")
    event.update(exit_code=1, warnings=["command succeeded; output semantic validation failed"],
                 outputs=[{"role": "layout_validation", "path": "pending.json"}])
    trace.write_text(json.dumps(event) + "\n", encoding="utf-8")
    assert_pending_domain_failure(tmp_path, "write-model-paper")


def test_conversion_preserves_body_solver_failures_and_actual_figures():
    converted = ('# Result\nThe actual solver returned infeasible; an optimal claim must fail.\n'
                 '<embed src="../figures/actual.pdf" style="width:150mm" />\n'
                 '# 支撑文件与完整程序\n```python\nsolver_status = "infeasible"\n```')
    manuscript = markdown_review_source(converted)
    assert "actual solver returned infeasible" in manuscript
    assert "![actual](../figures/actual.pdf)" in manuscript
    assert 'solver_status = "infeasible"' not in manuscript
    assert "[论文PDF附录](research/main.pdf)" in manuscript
