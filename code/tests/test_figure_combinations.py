"""Verify composition normalization and independent right-axis quantity semantics."""
import matplotlib.pyplot as plt
import numpy as np
import pytest

from algorithms.figures import get_figure, get_spec
from algorithms.figures.examples import example_data


def data():
    return dict(categories=["主题1", "主题2"], values=[[1, 3, 6], [5, 0, 5]],
                groups=["中性", "消极", "积极"], line_values=[2817, 368])


def test_combo_preserves_quantity_and_normalizes_bar_heights():
    original = data()
    fig = get_figure("percent_stacked_bar_line")(data=original)
    try:
        left, right = fig.axes
        heights = np.array([[patch.get_height() for patch in bar] for bar in left.containers]).T
        np.testing.assert_allclose(heights, [[10, 30, 60], [50, 0, 50]])
        np.testing.assert_allclose(heights.sum(axis=1), [100, 100])
        np.testing.assert_array_equal(right.lines[0].get_ydata(), original["line_values"])
        np.testing.assert_array_equal(right.lines[0].get_xdata(), [0, 1])
        assert left.get_ylim() == (0, 100)
        assert right.get_ylim()[0] == 0 and right.get_ylim()[1] > 2817
        assert [text.get_text() for text in right.texts] == ["2817", "368"]
        assert right.spines["right"].get_visible()
        np.testing.assert_allclose(fig._figure_metadata["normalized_values"], heights)
        assert fig._figure_metadata["input_data"] == original
        assert fig._figure_metadata["axis_mapping"]["right"] == "line_values"
        assert original["values"] == [[1, 3, 6], [5, 0, 5]]
        fig.canvas.draw()
        legend_box = left.get_legend().get_window_extent(fig.canvas.get_renderer())
        assert legend_box.y0 >= left.get_window_extent().y1
    finally:
        plt.close(fig)


@pytest.mark.parametrize("updates,match", [
    ({"values": [[0, 0, 0], [1, 2, 3]]}, "positive total"),
    ({"values": [[-1, 2, 3], [1, 2, 3]]}, "nonnegative"),
    ({"values": [1, 2]}, "2D"),
    ({"values": [[1, np.nan, 3], [1, 2, 3]]}, "finite"),
    ({"values": [[1, np.inf, 3], [1, 2, 3]]}, "finite"),
    ({"categories": ["A"]}, "categories"),
    ({"categories": "AB"}, "categories"),
    ({"groups": ["A", "B"]}, "groups"),
    ({"groups": ["A", "", "C"]}, "groups"),
    ({"line_values": [1]}, "align"),
    ({"line_values": [1, -2]}, "nonnegative"),
    ({"line_values": [1, np.nan]}, "finite"),
    ({"group_colors": ["red"]}, "group_colors"),
    ({"line_color": "invalid"}, "line_color"),
    ({"bar_width": 0}, "bar_width"),
])
def test_combo_rejects_invalid_data_before_allocating_figure(updates, match):
    figures_before = plt.get_fignums()
    with pytest.raises(ValueError, match=match):
        get_figure("percent_stacked_bar_line")(data={**data(), **updates})
    assert plt.get_fignums() == figures_before


def test_combo_requires_explicit_line_values():
    supplied = data()
    del supplied["line_values"]
    with pytest.raises(ValueError, match="line_values"):
        get_figure("percent_stacked_bar_line")(data=supplied)


def test_combo_chinese_alias_and_supplied_axis():
    assert get_spec("百分比堆叠柱折线图").name == "percent_stacked_bar_line"
    assert get_spec("percent_stacked_bar_line").implementation_level == "dedicated"
    fig, axis = plt.subplots(constrained_layout=True)
    try:
        result = get_figure("百分比堆叠柱折线图")(
            **data(), ax=axis, title="主题比较", right_ylabel="文本数量 (条)",
            line_label="文本数量", group_colors=["green", "gold", "gray"], annotate=False,
        )
        assert result is fig and fig.axes[0] is axis and len(fig.axes) == 2
        assert fig.axes[1].get_ylabel() == "文本数量 (条)"
        assert len(fig.axes[1].texts) == 0
        assert axis.get_title() == "主题比较"
        assert [t.get_text() for t in axis.get_legend().get_texts()] == ["中性", "消极", "积极", "文本数量"]
    finally:
        plt.close(fig)


def test_combo_handles_zero_quantity_and_finite_large_composition():
    fig = get_figure("percent_stacked_bar_line")(
        data={**data(), "values": [[1e308, 1e308, 0], [0, 1, 0]], "line_values": [0, 0]},
    )
    try:
        np.testing.assert_allclose(fig._figure_metadata["normalized_values"], [[50, 50, 0], [0, 100, 0]])
        assert fig.axes[1].get_ylim() == (0, 1)
        assert [t.get_text() for t in fig.axes[1].texts] == ["0", "0"]
    finally:
        plt.close(fig)


def test_combo_registered_example_and_positional_arguments():
    supplied = example_data("percent_stacked_bar_line")
    fig = get_figure("percent_stacked_bar_line")(data=supplied, mode="preview")
    assert fig._figure_metadata["simulated"]
    plt.close(fig)
    supplied = data()
    fig = get_figure("percent_stacked_bar_line")(
        *(supplied[field] for field in get_spec("percent_stacked_bar_line").required_fields),
    )
    plt.close(fig)
