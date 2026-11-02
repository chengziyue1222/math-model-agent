"""Saved-result renderers for matrix, calendar, composition and regression tasks.

Validation runs before any figure is allocated. No renderer fits a model or
invents intervals; empty cells and zero totals are explicit missing states.
"""
from __future__ import annotations
from . import styles as _style

from datetime import date, timedelta
import textwrap

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Patch
from matplotlib.ticker import PercentFormatter
from matplotlib.colors import is_color_like
import numpy as np
import pandas as pd

from .base import attach_metadata, contract_from, finite_array

COLORS = _style.Palette(("#0072B2", "#E69F00", "#009E73", "#CC79A7", "#D55E00", "#56B4E9"))
FIELDS = {
    "sparkline_matrix": ("row_labels", "column_labels", "series"),
    "polar_stacked_bar": ("categories", "groups", "values"),
    "pictogram": ("categories", "values"),
    "calendar_heatmap": ("dates", "values"),
    "correlation_heatmap": ("matrix", "labels"),
    "covariance_heatmap": ("matrix", "labels", "variable_units"),
    "matrix_pie": ("row_labels", "column_labels", "groups", "values"),
    "calendar_glyphs": ("dates", "values"),
    "regression_curve": ("x", "y", "curve_x", "curve_y"),
    "bubble_matrix": ("row_labels", "column_labels", "values"),
}
NAMES = {
    "sparkline_matrix": "矩阵迷你折线图", "polar_stacked_bar": "极坐标堆叠图",
    "pictogram": "人物比例图", "correlation_heatmap": "相关热图",
    "covariance_heatmap": "协方差热图", "matrix_pie": "饼图矩阵",
    "calendar_glyphs": "日历小图", "regression_curve": "拟合曲线图",
    "bubble_matrix": "频次气泡矩阵",
}


def labels(value, n, name):
    if isinstance(value, (str, bytes)) or len(value) != n or n < 1:
        raise ValueError(f"{name} must contain {n} labels")
    if any(v is None or not str(v).strip() for v in value):
        raise ValueError(f"{name} contains an empty label")


def dates_of(values):
    if isinstance(values, (str, bytes)):
        raise ValueError("dates must be a sequence")
    try:
        dates = pd.DatetimeIndex([pd.Timestamp(v) for v in values])
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid dates") from exc
    if dates.empty or dates.isna().any() or dates.tz is not None:
        raise ValueError("dates must be nonempty valid local dates")
    dates = dates.normalize()
    if dates.has_duplicates:
        raise ValueError("duplicate dates: aggregate explicitly before rendering")
    return dates


def nonnegative(value, ndim):
    a = finite_array(value, "values", ndim=ndim)
    if np.any(a < 0):
        raise ValueError("values must be nonnegative")
    if not np.isfinite(a.sum(axis=-1)).all():
        raise ValueError("composition totals overflow; rescale upstream")
    return a


def validate(name, d):
    missing = [f for f in FIELDS[name] if f not in d]
    if missing:
        raise ValueError(f"{name} requires {', '.join(missing)}")
    if "group_colors" in d:
        count = len(d.get("groups", d.get("categories", COLORS)))
        if len(d["group_colors"]) != count or not all(is_color_like(c) for c in d["group_colors"]):
            raise ValueError("group_colors must match the categories/groups and contain valid colors")
    if name == "sparkline_matrix":
        nr, nc = len(d["row_labels"]), len(d["column_labels"])
        labels(d["row_labels"], nr, "row_labels")
        labels(d["column_labels"], nc, "column_labels")
        if len(d["series"]) != nr or any(len(row) != nc for row in d["series"]):
            raise ValueError("series must match row/column dimensions")
        if d.get("scale", "shared") not in {"shared", "independent"}:
            raise ValueError("scale must be shared or independent")
        for row in d["series"]:
            for cell in row:
                if cell is not None:
                    if not isinstance(cell, dict) or not {"x", "y"}.issubset(cell):
                        raise ValueError("each series cell needs x and y, or None")
                    x, y = finite_array(cell["x"], "x"), finite_array(cell["y"], "y")
                    if x.shape != y.shape or np.any(np.diff(x) <= 0):
                        raise ValueError("cell x/y must align; x must increase")
        units = [c.get("unit", d.get("unit", "")) for row in d["series"] for c in row if c]
        if d.get("scale", "shared") == "shared" and len(set(units)) > 1:
            raise ValueError("shared scale requires consistent units")
    elif name in {"polar_stacked_bar", "pictogram"}:
        a = nonnegative(d["values"], 2 if name == "polar_stacked_bar" else 1)
        labels(d["categories"], len(a), "categories")
        if name == "polar_stacked_bar":
            labels(d["groups"], a.shape[1], "groups")
            if d.get("orientation", "radial") not in {"radial", "angular"}:
                raise ValueError("orientation must be radial or angular")
        else:
            if d.get("pictogram_mode", "array") not in {"array", "silhouette"}:
                raise ValueError("pictogram mode must be array or silhouette")
            q = d.get("icon_value", 1)
            if not np.isscalar(q) or not np.isfinite(q) or q <= 0:
                raise ValueError("icon_value must be finite and positive")
            if d.get("pictogram_mode", "array") == "array" and np.ceil(a / q).sum() > 1000:
                raise ValueError("too many icons; increase icon_value")
            if d.get("array_layout", "grouped") not in {"grouped", "waffle"}:
                raise ValueError("array_layout must be grouped or waffle")
            if d.get("array_layout") == "waffle" and np.any(a/q != np.floor(a/q)):
                raise ValueError("waffle requires whole icon counts; do not round cases")
            columns = d.get("columns", 10)
            if not isinstance(columns, int) or isinstance(columns, bool) or columns < 1:
                raise ValueError("columns must be a positive integer")
    elif name in {"calendar_heatmap", "calendar_glyphs"}:
        dates = dates_of(d["dates"])
        kind = d.get("glyph", "bubble")
        if name == "calendar_glyphs" and kind not in {"bubble", "pie"}:
            raise ValueError("glyph must be bubble or pie")
        a = (nonnegative(d["values"], 2 if kind == "pie" else 1) if name == "calendar_glyphs"
             else finite_array(d["values"], "values"))
        if len(dates) != len(a):
            raise ValueError("dates and values must align")
        if name == "calendar_glyphs" and kind == "pie":
            labels(d.get("groups", []), a.shape[1], "groups")
        if d.get("layout", "horizontal") not in {"horizontal", "vertical"}:
            raise ValueError("layout must be horizontal or vertical")
    elif name in {"correlation_heatmap", "covariance_heatmap"}:
        a = np.asarray(d["matrix"], dtype=float)
        if a.ndim != 2 or a.shape[0] != a.shape[1] or not a.size or np.isinf(a).any():
            raise ValueError("matrix must be square; NaN denotes undefined, infinity is invalid")
        if not np.allclose(a, a.T, equal_nan=True):
            raise ValueError("matrix must be symmetric")
        labels(d["labels"], len(a), "labels")
        if name == "correlation_heatmap" and np.any(np.abs(a[np.isfinite(a)]) > 1 + 1e-10):
            raise ValueError("correlations must be in [-1, 1]")
        if name == "covariance_heatmap":
            labels(d["variable_units"], len(a), "variable_units")
            if np.any(np.diag(a)[np.isfinite(np.diag(a))] < 0):
                raise ValueError("variance must be nonnegative")
    elif name in {"matrix_pie", "bubble_matrix"}:
        a = nonnegative(d["values"], 3 if name == "matrix_pie" else 2)
        labels(d["row_labels"], a.shape[0], "row_labels")
        labels(d["column_labels"], a.shape[1], "column_labels")
        if name == "matrix_pie":
            labels(d["groups"], a.shape[2], "groups")
    elif name == "regression_curve":
        x, y, cx, cy = [finite_array(d[f], f) for f in FIELDS[name]]
        if x.shape != y.shape or cx.shape != cy.shape or np.any(np.diff(cx) <= 0):
            raise ValueError("observations/curve must align; curve_x must increase")
        if ("lower" in d) != ("upper" in d):
            raise ValueError("lower and upper must be supplied together")
        if "lower" in d:
            lo, hi = finite_array(d["lower"], "lower"), finite_array(d["upper"], "upper")
            if lo.shape != cx.shape or hi.shape != cx.shape or np.any(lo > cy) or np.any(hi < cy):
                raise ValueError("interval must align and bracket curve_y")
            if not str(d.get("interval_kind", "")).strip():
                raise ValueError("interval_kind required")
    if name in {"bubble_matrix", "calendar_glyphs"}:
        default_max = 8 if name == "calendar_glyphs" else 180
        for f, default in (("max_area", default_max), ("min_area", 0)):
            v = d.get(f, default)
            if not np.isscalar(v) or not np.isfinite(v) or v < 0 or (f == "max_area" and v == 0):
                raise ValueError(f"{f} must be finite and nonnegative (max_area positive)")
        if d.get("min_area", 0) > d.get("max_area", default_max):
            raise ValueError("min_area must not exceed max_area")


def calendar_positions(dates, year):
    """Monday-based week/day coordinates from real dates, including leap days."""
    start = date(year, 1, 1)
    monday = start - timedelta(days=start.weekday())
    return [(int((t.date() - monday).days // 7), t.weekday()) for t in dates]


def _grid(rows, columns, d):
    fig, axes = _style.subplots(rows, columns, squeeze=False, constrained_layout=True,
                             figsize=d.get("figsize", (max(4, columns * 2), max(2.8, rows * 1.5))))
    if d.get("title"):
        fig.suptitle(d["title"])
    return fig, axes


def _legend(fig, groups, colors=COLORS):
    fig.legend(handles=[Patch(facecolor=colors[i % len(colors)], edgecolor="#555555", hatch=_style.hatch(i), label=str(g)) for i, g in enumerate(groups)],
               loc="outside lower center", ncol=min(len(groups), 4), frameon=False)


def _areas(values, d):
    maximum = float(np.max(values))
    if maximum == 0:
        return np.zeros_like(values), maximum
    return np.where(values > 0, d.get("min_area", 0) +
                    (d.get("max_area", 180) - d.get("min_area", 0)) * values / maximum, 0), maximum


def _size_legend(ax, maximum, d):
    if maximum > 0:
        levels = np.array([maximum / 4, maximum / 2, maximum])
        sizes, _ = _areas(levels, d)
        handles = [ax.scatter([], [], s=s, color=COLORS[0], label=f"{v:g}") for s, v in zip(sizes, levels)]
        ax.legend(handles=handles, title="数量（面积）" if d.get("min_area", 0) == 0 else "数量（面积含最小偏移）",
                  loc="upper left", bbox_to_anchor=(1.02, 1), frameon=False, labelspacing=1.4)


def _person_body():
    """Symmetric standing silhouette, with rounded shoulders, hands and feet.

    Sample the smooth outline into one simple, editable polygon. The head is
    separate and the legs share one body, so the visible-area integral never
    double-counts intersecting limbs or seams.
    """
    right = [np.array([.5, .805])]
    curves = [
        ((.52, .805), (.54, .805), (.555, .801)),
        ((.61, .794), (.651, .773), (.674, .732)),
        ((.699, .687), (.726, .593), (.764, .487)),
        ((.777, .452), (.760, .430), (.740, .430)),
        ((.721, .430), (.709, .440), (.701, .461)),
        ((.678, .518), (.657, .580), (.640, .622)),
        ((.637, .566), (.630, .493), (.630, .438)),
        ((.630, .329), (.619, .169), (.614, .049)),
        ((.613, .020), (.600, .006), (.576, .006)),
        ((.552, .006), (.537, .019), (.536, .043)),
        ((.531, .142), (.521, .273), (.511, .373)),
        ((.509, .394), (.506, .403), (.5, .403)),
    ]
    t = np.linspace(0, 1, 13)[1:, None]
    for c1, c2, end in curves:
        start = right[-1]
        points = ((1-t)**3*start + 3*(1-t)**2*t*np.array(c1)
                  + 3*(1-t)*t**2*np.array(c2) + t**3*np.array(end))
        right.extend(points)
    right = np.asarray(right)
    return np.vstack([right, right[-2:0:-1]*[-1, 1]+[1, 0]])


_PERSON = [np.column_stack([.5+.081*np.cos(np.linspace(0, 2*np.pi, 96, endpoint=False)),
                            .919+.081*np.sin(np.linspace(0, 2*np.pi, 96, endpoint=False))]),
           _person_body()]


def person_fraction_height(fraction):
    """Invert the exact polygon visible-area integral (array remainder)."""
    if not 0 <= fraction <= 1:
        raise ValueError("fraction must be in [0,1]")
    if fraction in {0, 1}:
        return float(fraction)
    target = fraction * person_visible_area(1)
    low, high = 0., 1.
    for _ in range(50):
        middle = (low+high)/2
        if person_visible_area(middle) < target:
            low = middle
        else:
            high = middle
    return (low+high)/2


def person_visible_area(height):
    """Shoelace area of each polygon clipped against y <= height."""
    area = 0.
    for polygon in _PERSON:
        clipped = []
        for p, q in zip(polygon, np.roll(polygon, -1, axis=0)):
            if p[1] <= height:
                clipped.append(p)
            if (p[1] <= height) != (q[1] <= height):
                clipped.append(p+(q-p)*(height-p[1])/(q[1]-p[1]))
        if len(clipped) >= 3:
            xy = np.asarray(clipped)
            area += abs(np.dot(xy[:, 0], np.roll(xy[:, 1], 1)) - np.dot(xy[:, 1], np.roll(xy[:, 0], 1)))/2
    return area


def _person(ax, left, bottom, width, height, color, lower=0, upper=1, hatch=None):
    for polygon in _PERSON:
        patch = Polygon(polygon * [width, height] + [left, bottom], facecolor=color, edgecolor="#555555", linewidth=0, hatch=hatch)
        # Fine print texture distinguishes categories without hiding the small
        # head, hands or the boundary of a partly filled person.
        if hasattr(patch, "set_hatch_linewidth"):
            patch.set_hatch_linewidth(.28)
        ax.add_patch(patch)
        patch.set_clip_path(Rectangle((left, bottom+height*lower), width, height*(upper-lower), transform=ax.transData))


def render(name, d):
    validate(name, d)
    info = {}
    colors = d.get("group_colors", COLORS)
    if name == "sparkline_matrix":
        fig, axes = _grid(len(d["row_labels"]), len(d["column_labels"]), d)
        ys = [np.asarray(c["y"]) for row in d["series"] for c in row if c]
        limits = None
        if ys:
            low, high = min(y.min() for y in ys), max(y.max() for y in ys)
            pad = max((high-low)*.08, abs(high)*.02, .01)
            limits = (low-pad, high+pad)
        for i, row in enumerate(d["series"]):
            for j, cell in enumerate(row):
                ax = axes[i, j]
                if cell is None:
                    ax.text(.5, .5, "缺失", ha="center", transform=ax.transAxes, color="gray")
                else:
                    ax.plot(cell["x"], cell["y"], color=COLORS[i % len(COLORS)], lw=_style.stroke(1.2))
                if d.get("scale", "shared") == "shared" and limits:
                    ax.set_ylim(*limits)
                if i == 0:
                    ax.set_title(str(d["column_labels"][j]))
                if j == 0:
                    ax.set_ylabel(str(d["row_labels"][i]))
                if cell and d.get("scale") == "independent":
                    ax.set_title(f"{d['column_labels'][j]} · 独立尺度 ({cell.get('unit', d.get('unit', ''))})")
                ax.spines[["top", "right"]].set_visible(False)
        info = dict(scale=d.get("scale", "shared"), shared_ylim=limits)
    elif name == "polar_stacked_bar":
        a = np.asarray(d["values"], float)
        totals = a.sum(1)
        shown = np.divide(a, totals[:, None], out=np.zeros_like(a), where=totals[:, None] > 0)*100 if d.get("percent", False) else a.copy()
        orientation = d.get("orientation", "radial")
        fig, ax = _style.subplots(subplot_kw={"projection": "polar"}, figsize=(6, 4.5), constrained_layout=True)
        if orientation == "radial":
            theta = np.arange(len(a))*2*np.pi/len(a)
            bottom = np.zeros(len(a))
            for k, g in enumerate(d["groups"]):
                ax.bar(theta, shown[:, k], bottom=bottom, width=2*np.pi/len(a)*.75, color=colors[k % len(colors)], label=str(g), hatch=_style.hatch(k), edgecolor="#555555", linewidth=_style.stroke(0.35))
                bottom += shown[:, k]
            ax.set_xticks(theta, d["categories"])
            ax.set_ylim(0, max(shown.sum(1).max()*1.1, 1))
            if d.get("percent", False):
                ax.yaxis.set_major_formatter(PercentFormatter(100))
        else:
            maximum = max(shown.sum(1).max(), 1)
            for i, row in enumerate(shown):
                start = 0
                for k, value in enumerate(row):
                    angle = value/maximum*2*np.pi
                    ax.bar(start, .7, bottom=i+1, width=angle, align="edge", color=colors[k % len(colors)], hatch=_style.hatch(k), edgecolor="#555555", linewidth=_style.stroke(0.35))
                    start += angle
            ax.set_yticks(np.arange(len(a))+1.35, d["categories"])
            theta = np.linspace(0, 2*np.pi, 5, endpoint=False)
            ax.set_xticks(theta, [f"{t/2/np.pi*maximum:g}{'%' if d.get('percent') else ''}" for t in theta])
        _legend(fig, d["groups"], colors)
        ax.set_title(d.get("title", "极坐标组成（径向长度）" if orientation == "radial" else "极坐标组成（角度）"))
        for i in np.flatnonzero(totals == 0):
            ax.text(0, i+1.35 if orientation == "angular" else .1, f"{d['categories'][i]}：无组成")
        info = dict(orientation=orientation, displayed_values=shown, denominators=totals, percent=bool(d.get("percent", False)), encoding="radial length" if orientation == "radial" else "angle")
    elif name == "pictogram":
        a = np.asarray(d["values"], float)
        fig, ax = _style.subplots(figsize=(6, 4), constrained_layout=True)
        mode = d.get("pictogram_mode", "array")
        if mode == "array" and d.get("array_layout") == "waffle":
            q = d.get("icon_value", 1)
            counts = (a/q).astype(int)
            columns = d.get("columns", 10)
            rows = max(1, int(np.ceil(counts.sum()/columns)))
            cursor = 0
            for i, count in enumerate(counts):
                for k in range(cursor, cursor+count):
                    _person(ax, k % columns, rows-1-k//columns, .75, .9, colors[i % len(colors)], hatch=_style.hatch(i))
                cursor += count
            ax.set(xlim=(-.2, columns), ylim=(-.2, rows+.2), title=d.get("title", f"每个人物图标代表 {q:g}；总量 {a.sum():g}"))
            total = a.sum()
            _legend(fig, [f"{c}：{v:g} ({v/total:.1%})" if total else f"{c}：0（无组成）" for c, v in zip(d["categories"], a)], colors)
            info = dict(icon_value=q, category_icon_counts=counts, layout="waffle", encoding="whole icons, no rounding")
        elif mode == "array":
            q = d.get("icon_value", 1)
            columns = _style.pictogram_columns(d)
            pitch = .72
            used_columns = max(1, min(columns, int(np.ceil(a/q).max())))
            row_offset = 0
            fractions = []
            for i, value in enumerate(a):
                number = value/q
                count = int(np.ceil(number))
                rows = max(1, int(np.ceil(count/columns)))
                caption = f"{d['categories'][i]}：{value:g}"
                cfg = _style.current_config()
                wrap_width = 7 if cfg is not None and cfg["width_mm"] < 100 else 12
                lines = textwrap.fill(caption, wrap_width).splitlines()
                for j in range(1, len(lines)):
                    if lines[j][0] in "），。；：、】》" and len(lines[j-1]) > 2:
                        lines[j] = lines[j-1][-2:]+lines[j]
                        lines[j-1] = lines[j-1][:-2]
                ax.text(-.12, -row_offset-.55, "\n".join(lines), ha="right", va="center")
                for k in range(count):
                    fraction = min(1, number-k)
                    left, bottom = (k % columns)*pitch, -row_offset-k//columns-1
                    _person(ax, left, bottom, .8, .85, "#e4e4e4")
                    _person(ax, left, bottom, .8, .85, colors[i % len(colors)], upper=person_fraction_height(fraction), hatch=_style.hatch(i))
                    fractions.append(fraction)
                row_offset += rows + .4
            ax.set(xlim=(-.18, (used_columns-1)*pitch+.8), ylim=(-row_offset+.15, .1),
                   title=d.get("title", f"每个人形代表 {q:g}\n余量按实际填色面积折算"))
            info = dict(icon_value=q, fractions=fractions, encoding="visible polygon area",
                        category_icon_counts=np.ceil(a/q).astype(int), layout="grouped", columns=columns)
        else:
            total = a.sum()
            start = 0
            _person(ax, 0, 0, 1, 1, "#e4e4e4")
            for i, value in enumerate(a):
                proportion = value/total if total else 0
                _person(ax, 0, 0, 1, 1, colors[i % len(colors)], lower=start, upper=start+proportion, hatch=_style.hatch(i))
                start += proportion
                ax.text(1.15, .9-i*.15, f"{d['categories'][i]}：{value:g} ({proportion:.1%})", color=colors[i % len(colors)])
            ax.set(xlim=(-.2, 3), ylim=(-.1, 1.1), title=d.get("title", "轮廓分段按高度比例" if total else "零总量：无组成"))
            info = dict(denominator=float(total), encoding="height proportion")
        ax.set_aspect("equal")
        ax.axis("off")
        info['icon_geometry'] = 'rounded-standing-person-v2'
    elif name in {"calendar_heatmap", "calendar_glyphs"}:
        dates = dates_of(d["dates"])
        years = sorted(set(dates.year))
        vertical = d.get("layout", "horizontal") == "vertical"
        fig, axes = _grid(1 if vertical else len(years), len(years) if vertical else 1, {**d, "figsize": d.get("figsize", (8, 2.2*len(years)) if not vertical else (3*len(years), 7))})
        a = np.asarray(d["values"], float)
        positions = []
        for year, ax in zip(years, axes.flat):
            all_dates = pd.date_range(f"{year}-01-01", f"{year}-12-31")
            bg = np.array(calendar_positions(all_dates, year))
            ax.scatter(bg[:, int(vertical)], bg[:, int(not vertical)], s=_style.marker(8, area=True), marker="s", color="#eeeeee")
            selected = np.flatnonzero(dates.year == year)
            locs = np.array(calendar_positions(dates[selected], year))
            x, y = locs[:, int(vertical)], locs[:, int(not vertical)]
            positions.extend([dict(date=str(dates[k].date()), year=year, week=int(w), weekday=int(day)) for k, (w, day) in zip(selected, locs)])
            if name == "calendar_heatmap":
                image = ax.scatter(x, y, c=a[selected], marker="s", s=_style.marker(28, area=True), cmap=d.get("cmap", _style.cmap("sequential", "YlOrRd")), vmin=a.min(), vmax=a.max() if a.max() != a.min() else a.min()+1)
                if year == years[-1]:
                    fig.colorbar(image, ax=list(axes.flat), label=d.get("unit", "数值"), shrink=.7)
            elif d.get("glyph", "bubble") == "bubble":
                glyph_style = {**d, "max_area": d.get("max_area", 8)}
                sizes, maximum = _areas(a, glyph_style)
                ax.scatter(x, y, s=sizes[selected], color=COLORS[0], alpha=.8)
                if year == years[-1]:
                    _size_legend(ax, maximum, glyph_style)
            else:
                for idx, px, py in zip(selected, x, y):
                    if a[idx].sum() > 0:
                        wedges, _ = ax.pie(a[idx], center=(px, py), radius=.42, colors=[colors[k % len(colors)] for k in range(a.shape[1])], normalize=True, wedgeprops={"edgecolor": "#555555", "linewidth": .25})
                        for k, wedge in enumerate(wedges):
                            wedge.set_hatch(_style.hatch(k))
            if name == "calendar_glyphs":
                zeros = np.sum(a[selected], axis=1) == 0 if a.ndim == 2 else a[selected] == 0
                ax.scatter(x[zeros], y[zeros], marker="s", s=_style.marker(20, area=True), facecolors="none", edgecolors="#444444", linewidths=_style.stroke(0.8))
            month_coords = calendar_positions(pd.to_datetime([f"{year}-{m:02}-01" for m in range(1, 13)]), year)
            ticks = [w for w, _ in month_coords]
            if vertical:
                ax.set(xticks=range(7), xticklabels=["一", "二", "三", "四", "五", "六", "日"], yticks=ticks, yticklabels=[f"{m}月" for m in range(1, 13)], xlim=(-.6, 6.6), ylim=(53.6, -.6))
                ax.tick_params(axis="x", labelsize=6, pad=1)
                plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
            else:
                ax.set(yticks=range(7), yticklabels=["一", "二", "三", "四", "五", "六", "日"], xticks=ticks, xticklabels=[f"{m}月" for m in range(1, 13)], xlim=(-.6, 53.6), ylim=(6.6, -.6))
            ax.set_aspect("equal")
            ax.set_title(str(year))
            ax.grid(False)
        if name == "calendar_glyphs" and d.get("glyph") == "pie":
            _legend(fig, d["groups"], colors)
        axes.flat[0].text(0, 1.18, "灰底：缺失日期；空框：已观测零值" if name == "calendar_glyphs" else "灰底：缺失日期；有色格：观测值（含零）", transform=axes.flat[0].transAxes, fontsize=_style.font('text', 7))
        info = dict(positions=positions, layout=d.get("layout", "horizontal"), missing_encoding="gray background", zero_dates=[str(t.date()) for t, value in zip(dates, a) if np.sum(value) == 0])
    elif name in {"correlation_heatmap", "covariance_heatmap"}:
        a = np.asarray(d["matrix"], float)
        fig, ax = _style.subplots(figsize=(5, 4), constrained_layout=True)
        cmap = plt.get_cmap(d.get("cmap", _style.cmap("diverging", "RdBu_r"))).with_extremes(bad="#dddddd")
        bound = 1 if name == "correlation_heatmap" else max(np.max(np.abs(a[np.isfinite(a)]), initial=0), 1e-10)
        image = ax.imshow(np.ma.masked_invalid(a), cmap=cmap, vmin=-bound, vmax=bound)
        ticklabels = d["labels"] if name == "correlation_heatmap" else [f"{label} ({unit})" for label, unit in zip(d["labels"], d["variable_units"])]
        ax.set(xticks=range(len(a)), yticks=range(len(a)), xticklabels=ticklabels, yticklabels=ticklabels)
        plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
        if len(a) <= 8:
            for (i, j), value in np.ndenumerate(a):
                ax.text(j, i, "未定义" if np.isnan(value) else f"{value:.2g}", ha="center", va="center", fontsize=_style.font('text', 7), color="white" if np.isfinite(value) and abs(value)/bound > .6 else "black")
        fig.colorbar(image, ax=ax, label="相关系数" if name == "correlation_heatmap" else "协方差（行单位×列单位）")
        ax.set_title(d.get("title", "相关热图" if name == "correlation_heatmap" else "协方差热图"))
        info = dict(color_limits=[-bound, bound], undefined_cells=np.argwhere(np.isnan(a)))
    elif name == "matrix_pie":
        a = np.asarray(d["values"], float)
        fig, axes = _grid(a.shape[0], a.shape[1], d)
        for (i, j), ax in np.ndenumerate(axes):
            if a[i, j].sum() > 0:
                wedges, _ = ax.pie(a[i, j], colors=[colors[k % len(colors)] for k in range(a.shape[2])], normalize=True,
                                   wedgeprops={"edgecolor": "#555555", "linewidth": .35})
                for k, wedge in enumerate(wedges):
                    wedge.set_hatch(_style.hatch(k))
            else:
                ax.text(0, 0, "无组成", ha="center")
                ax.set(xlim=(-1.1, 1.1), ylim=(-1.1, 1.1))
                ax.axis("off")
            if d.get("show_total", True):
                ax.text(0, -1.38, f"总量 {a[i,j].sum():g}", ha="center", fontsize=_style.font('text', 7))
                ax.set_ylim(-1.6,1.25)
            ax.set_title(f"{d['row_labels'][i]} · {d['column_labels'][j]}")
        _legend(fig, d["groups"], colors)
        info = dict(totals=a.sum(2), encoding="fixed radius, composition angle")
    elif name == "regression_curve":
        x, y, cx, cy = [np.asarray(d[f], float) for f in FIELDS[name]]
        fig, ax = _style.subplots(constrained_layout=True)
        ax.scatter(x, y, color=COLORS[0], s=_style.marker(18, area=True), label="观测")
        inside = (cx >= x.min()) & (cx <= x.max())
        # Separate line segments so an external section is never styled as interpolation.
        for mask, style, label in ((inside, "-", "保存拟合"), (cx < x.min(), "--", "外推"), (cx > x.max(), "--", "外推")):
            if mask.any():
                selected = np.flatnonzero(mask)
                if style == "--" and inside.any():
                    boundary = np.flatnonzero(inside)[0 if cx[selected[0]] < x.min() else -1]
                    selected = np.sort(np.append(selected, boundary))
                ax.plot(cx[selected], cy[selected], style, color=COLORS[1], label=label)
        if "lower" in d:
            ax.fill_between(cx, d["lower"], d["upper"], color=COLORS[1], alpha=.18, label=d["interval_kind"])
        handles, labs = ax.get_legend_handles_labels()
        unique = dict(zip(labs, handles))
        ax.legend(unique.values(), unique.keys(), frameon=False)
        ax.set(xlabel=d.get("xlabel", "自变量"), ylabel=d.get("ylabel", "响应"), title=d.get("title", "保存拟合曲线"))
        info = dict(extrapolation_mask=~inside, interval_kind=d.get("interval_kind"), fit_performed=False)
    else:  # bubble_matrix
        a = np.asarray(d["values"], float)
        fig, ax = _style.subplots(figsize=(6, 4), constrained_layout=True)
        sizes, maximum = _areas(a, d)
        y, x = np.indices(a.shape)
        ax.scatter(x.ravel(), y.ravel(), s=sizes.ravel(), color=COLORS[0])
        ax.set(xticks=range(a.shape[1]), yticks=range(a.shape[0]), xticklabels=d["column_labels"], yticklabels=d["row_labels"], xlim=(-.5, a.shape[1]-.5), ylim=(a.shape[0]-.5, -.5), title=d.get("title", "频次气泡矩阵"))
        _size_legend(ax, maximum, d)
        info = dict(areas=sizes, min_area=d.get("min_area", 0), encoding="area proportional to value" if d.get("min_area", 0) == 0 else "area with declared minimum offset")
    for axis in fig.axes:
        if axis.images:
            axis.grid(False, which='both')
    return attach_metadata(fig, name=name, contract=contract_from(d, d.get("contract")), palette=list(colors), **info)


def factory(name):
    def draw(**data):
        return render(name, data)
    draw.__name__ = name
    draw.positional_fields = FIELDS[name]
    return draw
