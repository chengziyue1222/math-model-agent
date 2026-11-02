"""Behavioral checks for render-time style isolation and truthful new marks."""
import matplotlib.pyplot as plt
from matplotlib.colors import to_hex
import numpy as np
import pytest

from algorithms.figures import get_figure, list_figures
from algorithms.figures.examples import example_data
from algorithms.figure_config import load_figure_config


@pytest.mark.parametrize("name", list_figures())
def test_every_entry_obeys_explicit_physical_size_and_input(name):
    data = example_data(name)
    fig = get_figure(name)(data=data, config={"width_mm": 150, "height_mm": 120}, mode="preview")
    np.testing.assert_allclose(fig.get_size_inches() * 25.4, [150, 120])
    assert fig._figure_config["theme"] == "cumcm-research"
    assert fig._figure_metadata["canonical_key"]
    plt.close(fig)


def test_theme_reaches_marks_and_is_isolated_from_next_render():
    data = {"values": [1, 2, 4, 8]}
    old = get_figure("ecdf")(data=data, config={"theme": "modeling-default"})
    new = get_figure("ecdf")(data=data, config={"theme": "cumcm-research", "width_mm": 75}, width_mm=150)
    assert to_hex(old.axes[0].lines[0].get_color()) != to_hex(new.axes[0].lines[0].get_color())
    np.testing.assert_array_equal(old.axes[0].lines[0].get_xydata(), new.axes[0].lines[0].get_xydata())
    assert new.get_figwidth() * 25.4 == pytest.approx(150)
    custom = get_figure("grouped_bar")(data={"categories": ["甲", "乙"], "groups": ["方案"], "values": [[1], [2]]},
                                      config={"semantic_styles": {"方案": {"color": "#123456"}}})
    assert to_hex(custom.axes[0].patches[0].get_facecolor()) == "#123456"
    plt.close("all")


def test_raincloud_preserves_every_value_and_only_estimates_valid_densities():
    sample = [[1, 2, 3, 7], [4, 4, 4], [6]]
    fig = get_figure("raincloud")(data={"values": sample, "labels": ["甲", "乙", "丙"]})
    from matplotlib.collections import PathCollection, PolyCollection
    clouds = [c for c in fig.axes[0].collections if isinstance(c, PolyCollection)]
    points = [c for c in fig.axes[0].collections if isinstance(c, PathCollection)]
    assert len(clouds) == 1
    assert len(points) == 3
    for points_in_group, values in zip(points, sample):
        np.testing.assert_array_equal(points_in_group.get_offsets()[:, 1], values)
    assert fig._figure_metadata["statistics"][1]["density_estimated"] is False
    plt.close(fig)


def test_matrix_fixed_domain_and_constant_column_is_undefined():
    fig = get_figure("correlation_matrix")(data={"data": [[1, 4, 3], [2, 4, 2], [3, 4, 1]]})
    assert fig.axes[0].images[0].get_clim() == (-1, 1)
    assert fig._figure_metadata["correlation"][1][0] is None
    assert any(t.get_text() == "未定义" for t in fig.axes[0].texts)
    plt.close(fig)


def test_config_rejects_invalid_custom_palette():
    with pytest.raises(ValueError, match="categorical_colors"):
        load_figure_config({"categorical_colors": ["not-a-color"]})


def test_explicit_color_and_cmap_override_the_project_config():
    fig = get_figure("ecdf")(data={"values": [1, 2, 3]}, config={"color": "red"}, color="#123456")
    assert to_hex(fig.axes[0].lines[0].get_color()) == "#123456"
    matrix = get_figure("heatmap")(data={"matrix": [[1, 2], [3, 4]]}, config={"cmap": "Blues"}, cmap="Greens")
    assert matrix.axes[0].images[0].cmap.name == "Greens"
    plt.close("all")


@pytest.mark.parametrize("values", [[1], [2, 2, 2]])
def test_unidentifiable_density_is_not_fabricated(values):
    with pytest.raises(ValueError, match="nonconstant"):
        get_figure("kde")(data={"values": values})
    plt.close("all")


def test_custom_colormap_survives_configuration_roundtrip():
    import json
    from matplotlib.colors import ListedColormap
    colormap = ListedColormap(["#123456", "#FEDCBA"], name="user-map").with_extremes(bad="gray")
    cfg = json.loads(json.dumps(load_figure_config({"cmap": colormap})))
    fig = get_figure("heatmap")(data={"matrix": [[0, 1], [1, 0]]}, config=cfg)
    np.testing.assert_allclose(fig.axes[0].images[0].cmap([0.0, 1.0]), colormap([0.0, 1.0]))
    np.testing.assert_allclose(fig.axes[0].images[0].cmap.get_bad(), colormap.get_bad())
    plt.close(fig)


def test_explicit_color_wins_over_project_semantic_binding():
    fig = get_figure("grouped_bar")(
        data={"categories": ["甲", "乙"], "groups": ["方案"], "values": [[1], [2]]},
        config={"semantic_styles": {"方案": {"color": "red"}}}, color="#123456")
    assert to_hex(fig.axes[0].patches[0].get_facecolor()) == "#123456"
    plt.close(fig)


def test_geometry_tuple_indices_preserve_all_segment_endpoints():
    points = np.array([[0, 0], [2, 0], [1, 3]])
    fig = get_figure("geometry")(data={"points": points, "polygons": [(0, 1, 2)],
                                      "segments": [(0, 1), (1, 2)], "labels": ["A", "B", "C"]})
    lines = fig.axes[0].lines
    np.testing.assert_array_equal(lines[0].get_xydata(), points[[0, 1]])
    np.testing.assert_array_equal(lines[1].get_xydata(), points[[1, 2]])
    plt.close(fig)


def test_bubble_area_ratios_and_zero_magnitude_are_truthful():
    fig = get_figure("bubble")(data={"x": [1, 2, 3], "y": [3, 2, 1], "size": [0, 1, 4]})
    areas = fig.axes[0].collections[0].get_sizes()
    assert areas[0] == 0 and areas[2] == pytest.approx(4 * areas[1])
    assert len(fig.axes[0].collections[0].get_offsets()) == 3
    assert len(fig.axes[0].collections[1].get_offsets()) == 1
    assert fig._figure_metadata["magnitude"] == [0, 1, 4]
    with pytest.raises(ValueError, match="nonnegative"):
        get_figure("bubble")(data={"x": [1], "y": [2], "size": [-1]})
    plt.close(fig)


def test_correlation_bubble_uses_one_scale_for_diagonal_color_and_undefined():
    fig = get_figure("correlation_bubble")(data={"data": [[1, 5, 3], [2, 5, 2], [3, 5, 1]]})
    colorbar = fig.axes[1]._colorbar
    np.testing.assert_allclose(fig.axes[0].collections[0].get_facecolors()[0],
                               colorbar.mappable.cmap(colorbar.norm(1)))
    assert colorbar.mappable.get_clim() == (-1, 1)
    assert fig._figure_metadata["correlation"][1][0] is None
    assert sum(text.get_text() == "未定义" for text in fig.axes[0].texts) == 3
    plt.close(fig)


@pytest.mark.parametrize("name", ["confusion_matrix", "confusion_matrix_eval"])
def test_confusion_labels_and_counts_follow_input_order(name):
    fig = get_figure(name)(data={"matrix": [[11, 2], [3, 14]], "labels": ["阳性", "阴性"]})
    assert [text.get_text() for text in fig.axes[0].get_xticklabels()] == ["阳性", "阴性"]
    assert [text.get_text() for text in fig.axes[0].texts] == ["11", "2", "3", "14"]
    np.testing.assert_array_equal(fig.axes[0].images[0].get_array(), [[11, 2], [3, 14]])
    plt.close(fig)


def test_time_matrix_uses_real_unequal_time_boundaries():
    fig = get_figure("time_heatmap")(data={"matrix": [[1, 2, 3]], "row_labels": ["流量"],
                                           "time": [10, 13, 20], "column_labels": ["unused"]})
    coordinates = fig.axes[0].collections[0].get_coordinates()
    np.testing.assert_allclose(coordinates[0, :, 0], [8.5, 11.5, 16.5, 23.5])
    np.testing.assert_array_equal(fig.axes[0].get_xticks(), [10, 13, 20])
    plt.close(fig)


def test_long_node_key_and_ridgeline_retain_complete_input():
    data = example_data("algorithm_flow", case="long_labels")
    fig = get_figure("algorithm_flow")(data=data)
    assert set(fig._figure_metadata["node_label_key"].values()) == set(data["nodes"])
    assert fig._figure_metadata["edges"] == [list(edge) for edge in data["edges"]]
    values = [np.linspace(1, 2, 80), np.linspace(3, 5, 95)]
    ridge = get_figure("ridgeline")(data={"groups": values, "labels": ["甲", "乙"]})
    from matplotlib.collections import PathCollection
    points = [collection for collection in ridge.axes[0].collections if isinstance(collection, PathCollection)]
    for collection, group in zip(points, values):
        np.testing.assert_array_equal(collection.get_offsets()[:, 0], group)
    plt.close("all")


@pytest.mark.parametrize("name", ["adjacency_matrix", "diverging_heatmap", "clustered_heatmap", "partial_correlation", "threshold_heatmap"])
def test_specialized_matrix_honors_explicit_colormap(name):
    fig = get_figure(name)(data=example_data(name), config={"cmap": "Greens"})
    assert any(image.cmap.name == "Greens" for axis in fig.axes for image in axis.images)
    plt.close(fig)


def test_3d_text_audit_uses_drawn_projection_and_still_rejects_real_overflow(tmp_path):
    from algorithms.sci_figures import FigureContract, audit_publication_figure
    source=tmp_path/'basis.json';source.write_text('{}',encoding='utf-8')
    fig=get_figure('coordinate_system')(data=example_data('coordinate_system',case='dense'))
    contract=FigureContract('Coordinate basis',('supplied basis vectors',),source_paths=(str(source),),width_mm=150)
    report=audit_publication_figure(fig,contract)
    assert not any('outside canvas' in error for error in report.errors)
    fig.axes[0].text2D(2,2,'actual overflow',transform=fig.axes[0].transAxes)
    assert any('actual overflow' in error for error in audit_publication_figure(fig,contract).errors)
    plt.close(fig)


def test_source_renderer_or_failed_visual_review_cannot_reuse_pass(tmp_path, monkeypatch):
    import json
    from algorithms import figure_export
    from algorithms.sci_figures import FigureContract
    source = tmp_path / "source.json"
    source.write_text('[1, 2, 3]', encoding="utf-8")
    fig = get_figure("ecdf")(data={"values": [1, 2, 3]})
    contract = FigureContract("Three observations", ("all observations",),
                              source_paths=(str(source),), width_mm=150)
    paths = figure_export.export_bundle(fig, tmp_path / "review", contract)
    checks = dict.fromkeys(["png", "vector", "physical_proof", "grayscale", "source_values"], "PASS")
    source.write_text('[1, 2, 99]', encoding="utf-8")
    with pytest.raises(ValueError, match="source changed"):
        figure_export.record_visual_review(paths["metadata"], reviewer="test", checks=checks, notes="test")
    source.write_text('[1, 2, 3]', encoding="utf-8")
    hashes = figure_export.implementation_hashes()
    assert "figures/styles.py" in hashes and "figures/distributions.py" in hashes
    changed = {**hashes, "figures/styles.py": "0" * 64}
    with monkeypatch.context() as context:
        context.setattr(figure_export, "implementation_hashes", lambda: changed)
        with pytest.raises(ValueError, match="implementation changed"):
            figure_export.record_visual_review(paths["metadata"], reviewer="test", checks=checks, notes="test")
    checks["grayscale"] = "FAIL"
    figure_export.record_visual_review(paths["metadata"], reviewer="test", checks=checks, notes="unreadable")
    metadata = json.loads((tmp_path / "review.figure.json").read_text(encoding="utf-8"))
    assert metadata["completion_status"] == metadata["visual_review"]["status"] == "FAIL"
    plt.close(fig)
