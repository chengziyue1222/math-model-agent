import hashlib
import json

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest
from PIL import Image

from algorithms.figure_config import load_figure_config, semantic_style
from algorithms.figure_templates import render_template, TEMPLATES
from algorithms.sci_figures import (
    FigureContract, PairedRaincloud, audit_publication_figure,
    export_publication_figure, paper_figure_rc_params, publication_size,
)


def contract(tmp_path, **kw):
    source = tmp_path / "data.json"
    source.write_text('[1, 2, 3]')
    return FigureContract("Test observations increase", ("three observations",),
                          source_paths=(str(source),), width_mm=150, **kw)


def simple():
    with mpl.rc_context(paper_figure_rc_params()):
        fig, ax = plt.subplots(figsize=publication_size(width_mm=150), constrained_layout=True)
        ax.plot([1, 2, 3], [1, 2, 3], label="测试")
        ax.set(xlabel="时间 (s)", ylabel="响应 (m)")
    return fig, ax


def test_config_precedence_and_fallback(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert load_figure_config({})["sources"] == ["builtin:algorithms.figure_config.DEFAULTS"]
    (tmp_path / "config").mkdir()
    (tmp_path / "config/paper_style.yaml").write_text("figures:\n  default_width_mm: 132\n  minimum_text_pt: 6\n")
    cfg = load_figure_config(width_mm=150)
    assert cfg["width_mm"] == 150
    assert load_figure_config()["width_mm"] == 132
    assert publication_size(None, None, config=cfg)[0]*25.4 == pytest.approx(150)
    assert publication_size("double")[0]*25.4 == pytest.approx(183)
    assert cfg["sources"][1]["sha256"]
    cfg["semantic_styles"]["model"] = {"color": "black"}
    assert "model" not in load_figure_config({})["semantic_styles"]


def test_formal_export_ignores_external_tight(tmp_path):
    fig, _ = simple()
    with mpl.rc_context({"savefig.bbox": "tight"}):
        paths = export_publication_figure(fig, tmp_path / "成图", contract(tmp_path))
        assert mpl.rcParams["savefig.bbox"] == "tight"
    with Image.open(paths["png"]) as image:
        assert image.mode == "RGB"
        assert abs(image.width - 150/25.4*450) <= 1
        assert image.info["dpi"] == pytest.approx((450,450), abs=.02)
    metadata = json.loads(open(paths["metadata"], encoding="utf-8").read())
    assert metadata["visual_review"]["status"] == "NOT_CHECKED"
    assert metadata["configuration"]["height_mm"] == pytest.approx(fig.get_figheight()*25.4)
    assert metadata["completion_status"] == "NEEDS_VISUAL_REVIEW"
    assert metadata["file_audit"]["pdf_fonts"]
    assert all(f["embedded"] for f in metadata["file_audit"]["pdf_fonts"])
    plt.close(fig)


def test_failed_export_preserves_previous_bundle(tmp_path, monkeypatch):
    from algorithms import figure_export
    fig, _ = simple()
    c = contract(tmp_path)
    paths = export_publication_figure(fig, tmp_path / "bundle", c)
    before = {k: hashlib.sha256(open(v, "rb").read()).hexdigest() for k,v in paths.items()}
    def fail(*args, **kwargs):
        raise RuntimeError("injected rendering failure")
    monkeypatch.setattr(figure_export, "inspect_exports", fail)
    with pytest.raises(RuntimeError):
        export_publication_figure(fig, tmp_path / "bundle", c)
    assert before == {k: hashlib.sha256(open(v, "rb").read()).hexdigest() for k,v in paths.items()}
    plt.close(fig)


def test_source_missing_and_hash_changed(tmp_path):
    fig, _ = simple()
    c = contract(tmp_path, source_hashes={str(tmp_path / "data.json"): "0"*64})
    assert any("hash changed" in e for e in audit_publication_figure(fig,c).errors)
    (tmp_path / "data.json").unlink()
    assert any("missing" in e for e in audit_publication_figure(fig,c).errors)
    plt.close(fig)


@pytest.mark.parametrize("element", ["tick", "legend", "figure_legend", "colorbar"])
def test_canvas_overflow_including_ticks_and_legends(tmp_path, element):
    fig, ax = simple()
    fig.set_layout_engine(None)
    if element == "tick":
        ax.set_xticks([2], ["中文长标签"*30])
    elif element == "legend":
        ax.legend(bbox_to_anchor=(4,1))
    elif element == "figure_legend":
        fig.legend(bbox_to_anchor=(4,1))
    else:
        image = ax.imshow([[1,2],[3,4]])
        cb = fig.colorbar(image, ax=ax)
        cb.set_label("色条标签"*40)
    assert any("outside canvas" in e for e in audit_publication_figure(fig,contract(tmp_path)).errors)
    plt.close(fig)


def test_colorbar_is_not_a_data_panel(tmp_path):
    fig, ax = simple()
    fig.colorbar(ax.imshow([[1,2],[3,4]], cmap="viridis"), ax=ax)
    report = audit_publication_figure(fig,contract(tmp_path))
    assert report.metrics["data_axes_count"] == 1
    assert not any("multi-panel" in w for w in report.warnings)
    plt.close(fig)


def test_missing_glyph_and_valid_chinese(tmp_path):
    fig, ax = simple()
    assert not any("missing glyph" in e for e in audit_publication_figure(fig,contract(tmp_path)).errors)
    ax.set_title("中文", fontfamily="DejaVu Sans")
    assert any("missing glyph" in e for e in audit_publication_figure(fig,contract(tmp_path)).errors)
    plt.close(fig)


def test_comparison_sort_values_styles_and_long_labels():
    names = ["很长的中文模型名称用于验证标签自动换行", "基线", "方案乙"]
    data = dict(names=names, values=[3,1,2], metric="MAE", direction="min", split="same test", units="m")
    before = dict(mpl.rcParams)
    fig = render_template("comparison", data)
    assert dict(mpl.rcParams) == before
    assert fig._comparison_order == [names[1],names[2],names[0]]
    assert [line.get_xdata()[0] for line in fig.axes[0].lines] == [1,2,3]
    assert any("\n" in label.get_text() for label in fig.axes[0].get_yticklabels())
    first = {n: semantic_style(n) for n in names}
    assert first == {n: semantic_style(n) for n in reversed(names)}
    data["split"] = ["test", "train", "test"]
    with pytest.raises(ValueError, match="split"):
        render_template("comparison",data)
    plt.close("all")


def test_real_input_templates_do_not_invent_evidence():
    prediction = dict(x=[1,2,3], observed=[1,3,4], predicted=[1,2,5], forecast_start=2, units="m", residuals=True)
    fig = render_template("prediction", prediction)
    np.testing.assert_array_equal(fig.axes[1].lines[0].get_ydata(), [0,1,-1])
    assert len(fig.axes[0].collections) == 0
    assert fig.axes[0].lines[2].get_xdata() == [2,2]
    with pytest.raises(ValueError, match="interval"):
        render_template("prediction", dict(prediction, lower=[0,0,0]))
    fig = render_template("optimization",dict(iterations=[1,2],objective=[3,2],units="s"))
    assert len(fig.axes)==1
    assert "No repeated runs" in fig._template_metadata["omitted_panels"][0]
    with pytest.raises(ValueError, match="midpoint_meaning"):
        render_template("sensitivity", dict(x=[1,2],y=[1,2], response=[[-1,0],[1,2]], units="m",midpoint=0))
    assert set(TEMPLATES)=={"prediction","comparison","optimization","sensitivity","robustness","mechanism"}
    plt.close("all")


def test_specialized_legacy_recipe_restores_rcparams():
    before = dict(mpl.rcParams)
    # Its recipe still returns the legacy exploratory canvas size.
    fig = PairedRaincloud({("Pre", "A"): np.array([1,2,3]), ("Post", "A"): np.array([2,3,4])}, ["A"], ["Pre", "Post"], {"A": {"edge": "#333333", "fill": "#8899AA"}}).make()
    assert dict(mpl.rcParams)==before
    plt.close(fig)
