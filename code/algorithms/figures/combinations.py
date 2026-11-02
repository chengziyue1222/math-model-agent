"""Composition percentages and a separately supplied quantity on shared categories."""
from __future__ import annotations
from . import styles as _style

import math
import textwrap

from matplotlib.colors import is_color_like
from matplotlib.ticker import MaxNLocator, PercentFormatter
import numpy as np

from .base import attach_metadata, contract_from, finite_array


STACK_COLORS = _style.Palette(("#59B99C", "#A9D54E", "#B3B3B3", "#E69F00", "#0072B2", "#CC79A7"))
LINE_COLOR = "#167C9A"


def validate_percent_stacked_bar_line(categories, values, groups, line_values):
    """Reject undefined compositions and quantities that do not align with the bars."""
    matrix = finite_array(values, "values", ndim=2)
    quantity = finite_array(line_values, "line_values")
    for field, labels, size in (
        ("categories", categories, matrix.shape[0]),
        ("groups", groups, matrix.shape[1]),
    ):
        if isinstance(labels, (str, bytes)):
            raise ValueError(f"{field} must be a nonempty label sequence")
        labels = np.asarray(labels, dtype=object)
        if labels.shape != (size,) or any(v is None or not str(v).strip() for v in labels):
            raise ValueError(f"{field} must contain {size} nonempty labels")
    if np.any(matrix < 0) or np.any(matrix.max(axis=1) <= 0):
        raise ValueError("values must be nonnegative with a positive total in every category")
    if quantity.shape != (matrix.shape[0],) or np.any(quantity < 0):
        raise ValueError("line_values must be nonnegative and align with categories")
    return matrix, quantity


def percent_stacked_bar_line(
    categories, values, groups, line_values, *, contract=None, ax=None,
    title="百分比堆叠柱折线图", xlabel="类别", ylabel="占比 (%)",
    right_ylabel="数量", line_label="数量", group_colors=None,
    line_color=None, bar_width=0.5, annotate=True, **kwargs,
):
    """Draw 100% stacked bars (left axis) and quantity with labels (right axis).

    ``values`` is category-by-group; counts, fractions and percentages are
    normalized per row. ``line_values`` is independent, explicitly supplied
    data, never inferred from the composition. Both axes start at zero.
    Optional labels, colors, bar width and quantity annotations are configurable.
    """
    matrix, quantity = validate_percent_stacked_bar_line(categories, values, groups, line_values)
    line_color = _style.color(1, LINE_COLOR) if line_color is None else line_color
    colors = list(group_colors) if group_colors is not None else [
        STACK_COLORS[i % len(STACK_COLORS)] for i in range(matrix.shape[1])
    ]
    if len(colors) != matrix.shape[1] or not all(is_color_like(c) for c in colors):
        raise ValueError("group_colors must contain one valid color per group")
    if not is_color_like(line_color):
        raise ValueError("line_color must be a valid color")
    if np.ndim(bar_width) != 0 or not np.isfinite(bar_width) or not 0 < bar_width <= 1:
        raise ValueError("bar_width must be in (0, 1]")

    # Scaling first avoids overflowing row sums for otherwise finite inputs.
    scaled = matrix / matrix.max(axis=1, keepdims=True)
    percentages = scaled / scaled.sum(axis=1, keepdims=True) * 100
    axis = ax if ax is not None else _style.subplots(figsize=(7, 4.5), constrained_layout=True)[1]
    x = np.arange(len(categories))
    bottom = np.zeros(len(categories))
    bars = []
    for i, label in enumerate(groups):
        bars.append(axis.bar(x, percentages[:, i], bottom=bottom, width=bar_width,
                             color=colors[i], edgecolor="#555555", linewidth=_style.stroke(0.4),
                             hatch=_style.hatch(i), label=str(label)))
        bottom += percentages[:, i]
    axis.set_xticks(x, [textwrap.fill(str(label), 12) for label in categories])
    axis.set(xlabel=xlabel, ylabel=ylabel, ylim=(0, 100), xlim=(-0.5, len(categories) - 0.5))
    axis.yaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
    axis.set_axisbelow(True)
    axis.grid(False)
    axis.grid(axis="y", color="#E4E4E4", linewidth=_style.stroke(0.5))
    axis.spines[["top", "right"]].set_visible(False)

    right = axis.twinx()
    right.patch.set_visible(False)
    line, = right.plot(x, quantity, color=line_color, marker="D", markersize=_style.marker(4),
                       linewidth=_style.stroke(1.6), label=line_label)
    right.set(ylabel=right_ylabel, ylim=(0, max(float(quantity.max()) * 1.18, 1)))
    right.yaxis.set_major_locator(MaxNLocator(nbins=6, min_n_ticks=3))
    right.grid(False)
    right.spines[["top", "left", "bottom"]].set_visible(False)
    right.spines["right"].set_visible(True)
    if annotate:
        for position, number in zip(x, quantity):
            label = str(int(number)) if number.is_integer() else np.format_float_positional(number, trim="-")
            right.annotate(label, (position, number), xytext=(0, 7),
                           textcoords="offset points", ha="center", va="bottom", fontsize=_style.font('text', 7),
                           color="#222222", bbox={"facecolor": "white", "edgecolor": "none",
                                                 "alpha": 0.8, "pad": 1.5})

    # Reserve space above the data for one legend covering both axes.
    columns = min(len(groups) + 1, 4)
    legend_rows = math.ceil((len(groups) + 1) / columns)
    axis.legend(handles=[*bars, line], labels=[*(str(g) for g in groups), line_label],
                loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=columns,
                frameon=False, fontsize=_style.font('legend', 7), borderaxespad=0.5)
    axis.set_title(title, fontsize=_style.font('title', 9), pad=18 + 13 * legend_rows)
    return attach_metadata(
        axis.figure, name="percent_stacked_bar_line", contract=contract_from(kwargs, contract),
        values=matrix, normalized_values=percentages, line_values=quantity,
        categories=list(categories), groups=list(groups),
        transformations=["normalize each category's group values to 100%; keep line_values unchanged"],
        axis_mapping={"left": "normalized_values (%)", "right": "line_values"},
        axis_labels={"left": ylabel, "right": right_ylabel},
        palette={"groups": colors, "line": line_color},
        line_label=line_label, annotations=bool(annotate),
    )
