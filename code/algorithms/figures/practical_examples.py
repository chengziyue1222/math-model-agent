"""Explicit synthetic inputs, reusable by previews and behavioral tests."""
import numpy as np


def example(name):
    rows, cols = ["地区甲", "地区乙"], ["时期一", "时期二", "时期三"]
    groups = ["积极", "中性", "消极"]
    if name == "sparkline_matrix":
        result = dict(row_labels=rows, column_labels=cols,
                      series=[[dict(x=[0, 1, 2], y=[1+i+j, 2+i, 4+j], unit="件") for j in range(3)] for i in range(2)], unit="件")
        result["series"][1][2] = None
    elif name == "polar_stacked_bar":
        result = dict(categories=["春", "夏", "秋", "冬"], groups=groups, values=[[2, 3, 1], [4, 1, 2], [3, 2, 4], [1, 2, 1]])
    elif name == "pictogram":
        result = dict(categories=groups, values=[20, 67, 13], icon_value=10)
    elif name in {"calendar_heatmap", "calendar_glyphs"}:
        result = dict(dates=["2023-12-31", "2024-01-01", "2024-02-28", "2024-02-29", "2024-03-01"], values=[0, 2, 6, 4, 8], unit="件")
    elif name in {"correlation_heatmap", "covariance_heatmap"}:
        from .compute import compute_matrix_statistics
        result = compute_matrix_statistics([[1, 3, 2], [2, 5, 2], [3, 4, 2], [4, 7, 2]],
                                           labels=groups, variable_units=["件", "元", "小时"],
                                           kind="correlation" if name == "correlation_heatmap" else "covariance", missing="raise")
    elif name == "matrix_pie":
        result = dict(row_labels=rows, column_labels=cols, groups=groups,
                      values=[[[2, 3, 1], [0, 0, 0], [1, 2, 3]], [[4, 1, 1], [2, 2, 2], [3, 2, 1]]])
    elif name == "regression_curve":
        # An explicitly computed deterministic demonstration, not a trained real model.
        x = np.arange(5.)
        cx = np.linspace(-1, 5, 31)
        result = dict(x=x, y=2*x+1, curve_x=cx, curve_y=2*cx+1,
                      calculation={"method": "synthetic y=2x+1", "simulated": True})
    elif name == "bubble_matrix":
        result = dict(row_labels=rows, column_labels=cols, values=[[0, 2, 8], [1, 3, 4]])
    else:
        raise KeyError(name)
    return {**result, "simulated": True, "source": "explicit synthetic demonstration"}
