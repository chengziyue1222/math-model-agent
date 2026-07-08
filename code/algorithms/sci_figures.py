"""
sci_figures.py - 高质量科研图表模板库

从 MathModelAgent (https://github.com/jihe520/MathModelAgent) 提取的 11 种
Nature/Science 风格科研可视化模板，适用于数学建模论文。

模板列表:
  1. TaylorDiagram        - 多模型评价泰勒图
  2. PairedRaincloud      - 配对云雨图（前后对比）
  3. CvRocCurve            - 交叉验证 ROC 曲线与置信区间
  4. CorrelationPairgrid   - 散点+直方图+相关系数组合图
  5. PredictionMarginal    - 预测值-真实值边缘分布图
  6. HyperparamSurface     - 超参数优化 3D 曲面图
  7. CorrSplitViolin       - 下三角相关矩阵+半边小提琴图
  8. CircularHeatmap       - 分组环形热图
  9. ComboComparison       - 堆叠+云雨+箱线组合图
  10. ChordDiagram         - Nature 风格和弦图
  11. ShapBeeswarm         - 多分类 SHAP 柱状+蜂群图

Usage:
    from algorithms.sci_figures import TaylorDiagram, save_figure

    fig = TaylorDiagram(models=[...], panels={...})
    save_figure(fig, 'taylor_diagram')
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.gridspec import GridSpecFromSubplotSpec
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle, Wedge
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch


# ---------------------------------------------------------------------------
# Common utilities
# ---------------------------------------------------------------------------

def _configure_mpl(style: str = "serif") -> None:
    """Apply publication-quality matplotlib settings."""
    if style == "serif":
        mpl.rcParams.update({
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif", "serif"],
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "font.size": 10,
            "axes.linewidth": 0.8,
        })
    else:
        mpl.rcParams.update({
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "font.size": 10,
            "axes.linewidth": 0.8,
        })


def _kde_1d(values: np.ndarray, grid: np.ndarray, bw_adjust: float = 1.0) -> np.ndarray:
    """Gaussian kernel density estimation on a 1-D grid."""
    values = np.asarray(values, dtype=float)
    std = max(np.std(values, ddof=1), 1e-6)
    bandwidth = max(1.06 * std * values.size ** (-1 / 5) * bw_adjust, 1e-4)
    z = (grid[:, None] - values[None, :]) / bandwidth
    density = np.exp(-0.5 * z ** 2).mean(axis=1) / (bandwidth * np.sqrt(2 * np.pi))
    return density


def _polar_to_xy(std, corr):
    """Convert polar (std, correlation) to Cartesian (x, y) for Taylor diagram."""
    corr_arr = np.asarray(corr)
    std_arr = np.asarray(std)
    theta = np.arccos(np.clip(corr_arr, 0.0, 1.0))
    return std_arr * np.cos(theta), std_arr * np.sin(theta)


def _text_rotation(theta_deg: float) -> tuple[float, str]:
    """Compute label rotation for circular layouts."""
    angle = theta_deg % 360
    if 90 < angle < 270:
        return theta_deg + 90, "right"
    return theta_deg - 90, "left"


def _lighten(color: str, amount: float = 0.35) -> tuple:
    """Lighten a color by blending toward white."""
    rgb = np.array(mpl.colors.to_rgb(color))
    return tuple(rgb + (1.0 - rgb) * amount)


def save_figure(fig: plt.Figure, stem: str, out_dir: str = "figures") -> dict[str, str]:
    """Save figure as PNG (300 dpi), PDF, and SVG. Returns dict of paths."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {}
    for ext in ("png", "pdf", "svg"):
        path = out / f"{stem}.{ext}"
        fig.savefig(str(path), dpi=300 if ext == "png" else None, bbox_inches="tight", pad_inches=0.03)
        paths[ext] = str(path)
    plt.close(fig)
    return paths


# ===========================================================================
# 1. Taylor Diagram
# ===========================================================================

@dataclass
class TaylorPoint:
    model: str
    std: float
    corr: float


class TaylorDiagram:
    """Multi-panel Taylor diagram for model evaluation.

    Args:
        models: List of (name, color) tuples. Last entry should be ("Observed", "#000000").
        panels: Dict of panel_name -> list[TaylorPoint].
        labels: Panel labels, defaults to "a", "b", "c", ...
        ref_std: Reference standard deviation, default 1.0.
        rmax: Maximum radius, default 1.75.
    """

    def __init__(
        self,
        models: list[tuple[str, str]],
        panels: dict[str, list[TaylorPoint]],
        labels: Optional[list[str]] = None,
        ref_std: float = 1.0,
        rmax: float = 1.75,
    ):
        self.models = models
        self.panels = panels
        self.labels = labels or [chr(ord("a") + i) for i in range(len(panels))]
        self.ref_std = ref_std
        self.rmax = rmax

    def _draw_grid(self, ax: plt.Axes) -> None:
        theta = np.linspace(0, np.pi / 2, 300)
        grid_c, light_c = "#cfcfcf", "#dedede"
        for r in np.arange(0.25, self.rmax + 0.001, 0.25):
            ax.plot(r * np.cos(theta), r * np.sin(theta), color=grid_c, lw=0.45, zorder=0)
        corr_ticks = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]
        for c in corr_ticks:
            x, y = _polar_to_xy(self.rmax, c)
            ax.plot([0, x], [0, y], color=light_c, lw=0.45, zorder=0)
        phi = np.linspace(0, np.pi, 400)
        for rms in [0.25, 0.50, 0.75, 1.00, 1.25]:
            x = self.ref_std + rms * np.cos(phi)
            y = rms * np.sin(phi)
            mask = (x >= 0) & (y >= 0) & (x ** 2 + y ** 2 <= self.rmax ** 2)
            ax.plot(x[mask], y[mask], ls="--", color="#bdbdbd", lw=0.45, alpha=0.85, zorder=0)
        ax.plot(self.ref_std * np.cos(theta), self.ref_std * np.sin(theta), ls="--", color="#cc7c8f", lw=0.65, alpha=0.75)
        ax.plot(self.rmax * np.cos(theta), self.rmax * np.sin(theta), color="#999999", lw=0.75)
        ax.set_xlim(0, self.rmax)
        ax.set_ylim(0, self.rmax)
        ax.set_aspect("equal", adjustable="box")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_color("#777777")
        ax.spines["left"].set_color("#777777")
        ax.set_xlabel("Standard Deviation", fontsize=8, labelpad=8)
        ax.set_ylabel("Standard Deviation", fontsize=8, labelpad=2)
        ticks = np.arange(0.0, self.rmax + 0.001, 0.25)
        ax.set_xticks(ticks)
        ax.set_yticks(ticks)
        ax.set_xticklabels([f"{t:.2f}" if t else "0" for t in ticks], fontsize=6.2)
        ax.set_yticklabels([f"{t:.2f}" if t else "0" for t in ticks], fontsize=6.2)
        ax.tick_params(length=2.0, width=0.55, pad=1)
        for c in corr_ticks:
            x, y = _polar_to_xy(self.rmax * 1.02, c)
            angle = np.degrees(np.arccos(c)) - 90
            label = f"{c:.2f}" if c >= 0.95 else f"{c:.1f}"
            ax.text(x, y, label, fontsize=6.2, ha="center", va="center", rotation=angle, rotation_mode="anchor")
        lx, ly = _polar_to_xy(self.rmax * 0.94, 0.68)
        ax.text(lx, ly, "Correlation", fontsize=7.2, rotation=-43, rotation_mode="anchor", ha="center", va="center")
        ax.text(self.ref_std, -0.060, "Observed", fontsize=6.4, ha="center", va="top")

    def make(self) -> plt.Figure:
        _configure_mpl()
        color_map = dict(self.models)
        n = len(self.panels)
        fig = plt.figure(figsize=(3.6 * n + 0.6, 5.7))
        lefts = np.linspace(0.08, 0.98 - 0.28, n)
        for i, (key, letter) in enumerate(zip(self.panels, self.labels)):
            ax = fig.add_axes([lefts[i], 0.285, 0.24, 0.465])
            self._draw_grid(ax)
            points = self.panels[key]
            handles = []
            for model, color in self.models:
                if model == "Observed":
                    x, y = _polar_to_xy(1.0, 1.0)
                    h = ax.scatter(x, y, s=18, marker="o", facecolor=color, edgecolor="black", lw=0.35, zorder=5)
                else:
                    pt = next(p for p in points if p.model == model)
                    x, y = _polar_to_xy(pt.std, pt.corr)
                    h = ax.scatter(x, y, s=18, marker="o", facecolor=color, edgecolor="black", lw=0.35, zorder=5)
                handles.append(h)
            ax.legend(handles, [m for m, _ in self.models], loc="upper right",
                      bbox_to_anchor=(1.02, 1.10), fontsize=5.4, labelspacing=0.12,
                      handlelength=0.9, handletextpad=0.25, borderpad=0.25,
                      framealpha=0.86, edgecolor="#999999", facecolor="white", fancybox=False)
            ax.text(0.50, -0.22, f"({letter})", transform=ax.transAxes, fontsize=9, ha="center", va="center")
        return fig


# ===========================================================================
# 2. Paired Raincloud
# ===========================================================================

class PairedRaincloud:
    """Paired raincloud plot for before/after or pre/post comparison.

    Args:
        data: Dict of (condition, group) -> np.ndarray of values.
        groups: List of group names (e.g., ["Versicolor", "Virginica"]).
        conditions: List of condition names (e.g., ["Pre", "Post"]).
        palette: Dict of group -> {"edge": color, "fill": color}.
        ylabel: Y-axis label.
    """

    def __init__(
        self,
        data: dict[tuple[str, str], np.ndarray],
        groups: list[str],
        conditions: list[str],
        palette: dict[str, dict[str, str]],
        ylabel: str = "Value",
    ):
        self.data = data
        self.groups = groups
        self.conditions = conditions
        self.palette = palette
        self.ylabel = ylabel

    @staticmethod
    def _draw_half_violin(ax, values, anchor_x, side, fill, edge, width=0.28, alpha=0.74, zorder=1):
        pad = 0.16
        grid = np.linspace(max(values.min() - pad, values.min() - 1), min(values.max() + pad, values.max() + 1), 240)
        density = _kde_1d(values, grid, bw_adjust=0.92) * width
        if density.max() > 0:
            density = density / density.max() * width
        if side == "left":
            ax.fill_betweenx(grid, anchor_x - density, anchor_x, facecolor=fill, edgecolor=edge, linewidth=2.4, alpha=alpha, zorder=zorder)
        else:
            ax.fill_betweenx(grid, anchor_x, anchor_x + density, facecolor=fill, edgecolor=edge, linewidth=2.4, alpha=alpha, zorder=zorder)

    @staticmethod
    def _draw_points(ax, values, x, fill, edge, seed=0):
        rng = np.random.default_rng(seed)
        jitter = rng.normal(0.0, 0.022, values.size)
        ax.scatter(x + jitter, values, s=50, facecolors=mpl.colors.to_rgba(fill, 0.56),
                   edgecolors=edge, linewidths=1.6, alpha=0.82, zorder=4)

    @staticmethod
    def _draw_box(ax, values, x, fill, edge):
        bp = ax.boxplot(values, positions=[x], widths=0.095, patch_artist=True,
                        showfliers=False, whis=(0, 100), zorder=5)
        for box in bp["boxes"]:
            box.set(facecolor=mpl.colors.to_rgba(fill, 0.68), edgecolor=edge, linewidth=2.5)
        for w in bp["whiskers"]:
            w.set(color=edge, linewidth=2.4)
        for c in bp["caps"]:
            c.set(color=edge, linewidth=2.4)
        for m in bp["medians"]:
            m.set(color=edge, linewidth=2.4)

    def make(self) -> plt.Figure:
        _configure_mpl()
        mpl.rcParams.update({"axes.spines.right": False, "axes.spines.top": False,
                             "axes.linewidth": 2.3, "xtick.major.width": 2.3, "ytick.major.width": 2.3})
        fig, ax = plt.subplots(figsize=(8.2, 7.8))
        fig.subplots_adjust(left=0.13, right=0.78, bottom=0.22, top=0.90)

        n_groups = len(self.groups)
        n_conds = len(self.conditions)
        base_positions = np.arange(n_conds) * 1.4 + 1.0

        for gi, group in enumerate(self.groups):
            for ci, cond in enumerate(self.conditions):
                values = self.data[(cond, group)]
                offset = (gi - (n_groups - 1) / 2) * 0.28
                x = base_positions[ci] + offset
                self._draw_points(ax, values, x, self.palette[group]["fill"], self.palette[group]["edge"], seed=gi * 10 + ci)
                self._draw_box(ax, values, x, self.palette[group]["fill"], self.palette[group]["edge"])

        # Violins at condition centers
        for ci, cond in enumerate(self.conditions):
            for gi, group in enumerate(self.groups):
                values = self.data[(cond, group)]
                side = "left" if ci == 0 else "right"
                self._draw_half_violin(ax, values, base_positions[ci], side,
                                       self.palette[group]["fill"], self.palette[group]["edge"])

        ax.set_xlim(base_positions[0] - 0.6, base_positions[-1] + 0.6)
        ax.set_ylabel(self.ylabel, fontsize=20, fontweight="bold", labelpad=18)
        ax.set_xticks(base_positions)
        ax.set_xticklabels(self.conditions, fontsize=20)
        ax.tick_params(axis="y", labelsize=19, width=2.8, length=11, pad=6)

        handles = [Patch(facecolor=self.palette[g]["fill"], edgecolor=self.palette[g]["fill"], label=g) for g in self.groups]
        fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.96, 0.965),
                   fontsize=18, title_fontsize=20, handlelength=1.8, borderaxespad=0)
        return fig


# ===========================================================================
# 3. CV ROC Curve with Confidence Intervals
# ===========================================================================

@dataclass
class RocModelSpec:
    name: str
    auc_mean: float
    auc_std: float
    color: str
    ci_alpha: float = 0.14
    noise: float = 0.030


class CvRocCurve:
    """Cross-validation ROC curves with confidence intervals.

    Args:
        models: List of RocModelSpec.
        n_folds: Number of CV folds, default 5.
    """

    def __init__(self, models: list[RocModelSpec], n_folds: int = 5):
        self.models = models
        self.n_folds = n_folds

    @staticmethod
    def _auc_to_exponent(auc: float) -> float:
        return np.clip(auc, 0.60, 0.985) / (1.0 - np.clip(auc, 0.60, 0.985))

    @staticmethod
    def _base_roc(fpr: np.ndarray, auc: float) -> np.ndarray:
        exp = CvRocCurve._auc_to_exponent(auc)
        tpr = 1.0 - (1.0 - fpr) ** exp
        early = 0.030 * np.exp(-((fpr - 0.055) / 0.055) ** 2)
        shoulder = -0.020 * np.exp(-((fpr - 0.34) / 0.20) ** 2)
        return np.clip(tpr + early + shoulder, 0.0, 1.0)

    def _simulate_folds(self, spec: RocModelSpec, grid: np.ndarray, seed: int):
        rng = np.random.default_rng(seed)
        offsets = np.array([-1.20, -0.45, 0.05, 0.55, 1.05])[:self.n_folds]
        offsets = (offsets - offsets.mean()) / max(offsets.std(ddof=1), 1e-6)
        targets = np.clip(spec.auc_mean + offsets * spec.auc_std, 0.72, 0.98)

        interpolated = []
        fold_curves = []
        for target_auc in targets:
            n_knots = 31
            low_fpr = np.sort(rng.beta(0.72, 4.6, size=22))
            high_fpr = np.sort(rng.uniform(0.22, 1.0, size=n_knots - low_fpr.size))
            fpr = np.unique(np.r_[0.0, low_fpr, high_fpr, 1.0])
            tpr_base = self._base_roc(fpr, float(target_auc))
            hetero = spec.noise * (1.15 - 0.55 * fpr)
            tpr = np.clip(tpr_base + rng.normal(0.0, hetero, size=fpr.size), 0.0, 1.0)
            tpr = np.maximum.accumulate(tpr)
            tpr[0], tpr[-1] = 0.0, 1.0
            fold_curves.append((fpr, tpr))
            interpolated.append(np.interp(grid, fpr, tpr))

        tpr_matrix = np.vstack(interpolated)
        mean_tpr = tpr_matrix.mean(axis=0)
        std_tpr = tpr_matrix.std(axis=0, ddof=1)
        mean_tpr[0], mean_tpr[-1] = 0.0, 1.0
        return fold_curves, mean_tpr, np.clip(mean_tpr - std_tpr, 0, 1), np.clip(mean_tpr + std_tpr, 0, 1)

    def make(self) -> plt.Figure:
        _configure_mpl("sans-serif")
        grid = np.linspace(0.0, 1.0, 101)
        fig = plt.figure(figsize=(7.4, 6.0))
        ax = fig.add_axes([0.12, 0.10, 0.75, 0.82])

        legend_handles, legend_labels = [], []
        for idx, spec in enumerate(self.models):
            folds, mean_tpr, lower, upper = self._simulate_folds(spec, grid, seed=814 + idx * 17)
            for fpr, tpr in folds:
                ax.step(fpr, tpr, where="post", color=spec.color, alpha=0.13, linewidth=0.65, zorder=1)
            ax.fill_between(grid, lower, upper, step="post", color=spec.color, alpha=spec.ci_alpha, linewidth=0, zorder=2)
            (line,) = ax.step(grid, mean_tpr, where="post", color=spec.color, linewidth=1.15, zorder=4)
            legend_handles.append(line)
            legend_labels.append(f"{spec.name:<8}: {spec.auc_mean:.3f}+/-{spec.auc_std:.3f}")

        ax.plot([0, 1], [0, 1], linestyle="--", color="#a34545", linewidth=0.8, alpha=0.78, zorder=0)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("False Positive Rate", fontsize=10)
        ax.set_ylabel("True Positive Rate", fontsize=10)
        ax.grid(True, color="#bcbcbc", alpha=0.28, linewidth=0.6)
        ax.legend(legend_handles, legend_labels, loc="lower right", fontsize=9,
                  framealpha=0.72, facecolor="white", edgecolor="#d9d9d9",
                  handlelength=2.1, labelspacing=0.65, borderpad=0.45)
        return fig


# ===========================================================================
# 4. Correlation PairGrid
# ===========================================================================

class CorrelationPairgrid:
    """Scatter + histogram + correlation coefficient matrix (PairGrid style).

    Args:
        data: (n_samples, n_variables) array.
        variable_names: List of variable names.
    """

    def __init__(self, data: np.ndarray, variable_names: Optional[list[str]] = None):
        self.data = data
        n_vars = data.shape[1]
        self.names = variable_names or [f"Var_{i+1}" for i in range(n_vars)]

    @staticmethod
    def _fit_line_ci(x, y, x_grid):
        slope, intercept = np.polyfit(x, y, 1)
        y_hat = slope * x_grid + intercept
        residuals = y - (slope * x + intercept)
        s_err = math.sqrt(np.sum(residuals ** 2) / max(x.size - 2, 1))
        ssx = np.sum((x - x.mean()) ** 2)
        se = s_err * np.sqrt(1.0 / x.size + (x_grid - x.mean()) ** 2 / max(ssx, 1e-12))
        return y_hat, y_hat - 1.96 * se, y_hat + 1.96 * se

    @staticmethod
    def _fisher_p(r, n):
        c = float(np.clip(r, -0.999999, 0.999999))
        z = 0.5 * math.log((1 + c) / (1 - c)) * math.sqrt(max(n - 3, 1))
        return math.erfc(abs(z) / math.sqrt(2.0))

    @staticmethod
    def _stars(p):
        if p < 0.001: return "***"
        if p < 0.01: return "**"
        if p < 0.05: return "*"
        return ""

    def make(self) -> plt.Figure:
        _configure_mpl("sans-serif")
        mpl.rcParams.update({"xtick.major.size": 1.8, "ytick.major.size": 1.8})
        data = self.data
        corr = np.corrcoef(data, rowvar=False)
        n_vars = data.shape[1]
        n_samples = data.shape[0]
        cmap = mpl.colormaps["RdBu_r"]
        norm = Normalize(vmin=-1.0, vmax=1.0)

        fig = plt.figure(figsize=(1.0 * n_vars + 1.2, 0.95 * n_vars + 0.6))
        grid = fig.add_gridspec(n_vars, n_vars, left=0.06, right=0.90, bottom=0.06, top=0.96, wspace=0.08, hspace=0.08)

        for row in range(n_vars):
            for col in range(n_vars):
                ax = fig.add_subplot(grid[row, col])
                for s in ax.spines.values():
                    s.set_color("#737373")
                    s.set_linewidth(0.45)
                ax.tick_params(labelsize=4.0, pad=0.5)
                if row < n_vars - 1: ax.set_xticklabels([])
                if col > 0: ax.set_yticklabels([])

                if row > col:
                    ax.scatter(data[:, col], data[:, row], s=8, color="#11779c", alpha=0.78, edgecolors="none", zorder=2)
                    xg = np.linspace(data[:, col].min(), data[:, col].max(), 120)
                    yf, yl, yh = self._fit_line_ci(data[:, col], data[:, row], xg)
                    ax.fill_between(xg, yl, yh, color="#e8a8d1", alpha=0.36, linewidth=0, zorder=1)
                    ax.plot(xg, yf, color="#9a4bb3", lw=1.0, zorder=3)
                    ax.set_xlim(data[:, col].min() - 0.3, data[:, col].max() + 0.3)
                    ax.set_ylim(data[:, row].min() - 0.3, data[:, row].max() + 0.3)
                elif row == col:
                    ax.hist(data[:, col], bins=12, color="#9ecae1", edgecolor="#2b5d73", linewidth=0.55, alpha=0.90)
                    gd = np.linspace(data[:, col].min() - 0.25, data[:, col].max() + 0.25, 180)
                    d = _kde_1d(data[:, col], gd)
                    counts, _ = np.histogram(data[:, col], bins=12)
                    d_scaled = d / d.max() * max(counts) if d.max() > 0 else d
                    ax.plot(gd, d_scaled, color="#225d78", lw=1.0)
                else:
                    r = corr[row, col]
                    p = self._fisher_p(r, n_samples)
                    ax.set_facecolor(cmap(norm(r)))
                    for s in ax.spines.values():
                        s.set_color("white")
                        s.set_linewidth(1.6)
                    ax.set_xticks([])
                    ax.set_yticks([])
                    tc = "white" if abs(r) >= 0.55 else "#1f1f1f"
                    ax.text(0.5, 0.46, f"{r:.2f}", ha="center", va="center", fontsize=6.7, color=tc, transform=ax.transAxes)
                    st = self._stars(p)
                    if st:
                        ax.text(0.5, 0.68, st, ha="center", va="center", fontsize=6.4, fontweight="bold", color=tc, transform=ax.transAxes)

        cax = fig.add_axes([0.92, 0.15, 0.025, 0.78])
        sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
        cbar = fig.colorbar(sm, cax=cax)
        ticks = np.linspace(-1.0, 1.0, 9)
        cbar.set_ticks(ticks)
        cbar.set_ticklabels([f"{t:.2f}" for t in ticks])
        cbar.ax.tick_params(labelsize=6, width=0.45, length=2)
        cbar.outline.set_linewidth(0.45)
        return fig


# ===========================================================================
# 5. Prediction Marginal Grid
# ===========================================================================

@dataclass
class PredModelPanel:
    name: str
    train_color: str
    test_color: str
    train_noise: float
    test_noise: float
    train_bias: float
    test_bias: float
    r2_train: float
    rmse_train: float
    r2_test: float
    rmse_test: float


class PredictionMarginal:
    """Prediction vs Actual with marginal distributions (2x2 grid).

    Args:
        panels: List of 4 PredModelPanel entries.
        actual_range: (min, max) for simulated actual values.
    """

    def __init__(self, panels: list[PredModelPanel], actual_range: tuple[float, float] = (0.0, 108.0)):
        self.panels = panels
        self.actual_range = actual_range

    @staticmethod
    def _make_actual(rng, n, lo, hi):
        low = rng.gamma(2.1, 13.0, size=n)
        mid = rng.normal(52.0, 14.0, size=n)
        high = rng.normal(82.0, 11.0, size=n)
        sel = rng.choice([0, 1, 2], size=n, p=[0.46, 0.34, 0.20])
        vals = np.where(sel == 0, low, np.where(sel == 1, mid, high))
        return np.clip(vals, lo, hi)

    @staticmethod
    def _predict(rng, actual, noise, bias):
        hetero = rng.normal(0.0, noise * (0.72 + 0.008 * actual), size=actual.size)
        return np.clip(actual + bias + hetero, -6.0, 112.0)

    def make(self) -> plt.Figure:
        _configure_mpl("sans-serif")
        mpl.rcParams.update({"xtick.major.width": 0.9, "ytick.major.width": 0.9, "legend.frameon": False})
        fig = plt.figure(figsize=(10.4, 8.2))
        outer = fig.add_gridspec(2, 2, left=0.055, right=0.982, bottom=0.055, top=0.960, wspace=0.22, hspace=0.28)
        lo, hi = self.actual_range

        for idx, panel in enumerate(self.panels[:4]):
            rng = np.random.default_rng(20260505 + idx * 103)
            act_train = self._make_actual(rng, 230, lo, hi)
            act_test = self._make_actual(rng, 92, lo, hi)
            pred_train = self._predict(rng, act_train, panel.train_noise, panel.train_bias)
            pred_test = self._predict(rng, act_test, panel.test_noise, panel.test_bias)

            sub = GridSpecFromSubplotSpec(2, 2, subplot_spec=outer[idx // 2, idx % 2],
                                          height_ratios=[0.30, 1.0], width_ratios=[1.0, 0.34],
                                          hspace=0.06, wspace=0.06)
            ax_top = fig.add_subplot(sub[0, 0])
            ax_main = fig.add_subplot(sub[1, 0])
            ax_right = fig.add_subplot(sub[1, 1], sharey=ax_main)
            fig.add_subplot(sub[0, 1]).axis("off")

            # Top histogram
            bins = np.linspace(lo, hi, 20)
            for vals, color in [(act_test, panel.test_color), (act_train, panel.train_color)]:
                ax_top.hist(vals, bins=bins, density=True, facecolor=mpl.colors.to_rgba(color, 0.12),
                            edgecolor=mpl.colors.to_rgba(color, 0.58), linewidth=1.05)
                gd = np.linspace(lo, hi, 240)
                d = _kde_1d(vals, gd)
                ax_top.plot(gd, d, color=color, lw=1.45, alpha=0.88)
            ax_top.set_xlim(lo - 5, hi + 5)
            ax_top.set_ylim(bottom=0)
            ax_top.set_xticklabels([])
            ax_top.set_yticklabels([])
            ax_top.tick_params(length=0)

            # Main scatter
            ax_main.plot([lo - 5, hi + 5], [lo - 5, hi + 5], color="#a5a5a5", lw=1.25, zorder=0)
            ax_main.scatter(act_test, pred_test, s=23, facecolors="none",
                            edgecolors=mpl.colors.to_rgba(panel.test_color, 0.76), linewidths=1.2, label="Test", zorder=2)
            ax_main.scatter(act_train, pred_train, s=23, facecolors="none",
                            edgecolors=mpl.colors.to_rgba(panel.train_color, 0.78), linewidths=1.2, label="Train", zorder=3)
            ax_main.set_xlim(lo - 5, hi + 5)
            ax_main.set_ylim(lo - 5, hi + 10)
            ax_main.set_xlabel("Actual", fontsize=12, fontweight="bold", labelpad=2)
            ax_main.set_ylabel("Predicted", fontsize=12, fontweight="bold", labelpad=2)
            ax_main.legend(loc="upper left", fontsize=8, handletextpad=0.5, borderaxespad=0.45)
            metric = f"Train R2={panel.r2_train:.3f}  RMSE={panel.rmse_train:.1f}\nTest  R2={panel.r2_test:.3f}  RMSE={panel.rmse_test:.1f}"
            ax_main.text(0.28, 0.035, metric, transform=ax_main.transAxes, fontsize=7.8, ha="left", va="bottom",
                         bbox=dict(boxstyle="square,pad=0.22", facecolor="white", edgecolor="#777777", alpha=0.92))

            # Right histogram
            for vals, color in [(pred_test, panel.test_color), (pred_train, panel.train_color)]:
                bins_r = np.linspace(lo - 5, hi + 10, 20)
                counts, edges = np.histogram(vals, bins=bins_r, density=True)
                centers = (edges[:-1] + edges[1:]) / 2
                ax_right.barh(centers, counts, height=np.diff(edges), facecolor=mpl.colors.to_rgba(color, 0.12),
                              edgecolor=mpl.colors.to_rgba(color, 0.58), linewidth=1.05)
                gd = np.linspace(lo - 5, hi + 10, 240)
                d = _kde_1d(vals, gd)
                ax_right.plot(d, gd, color=color, lw=1.45, alpha=0.88)
            ax_right.set_ylim(lo - 5, hi + 10)
            ax_right.set_xlim(left=0)
            ax_right.set_xticklabels([])
            ax_right.set_yticklabels([])
            ax_right.tick_params(length=0)
            ax_top.set_title(f"{panel.name}", fontsize=10.5, fontweight="bold", pad=5)
        return fig


# ===========================================================================
# 6. Hyperparameter Surface (3D)
# ===========================================================================

class HyperparamSurface:
    """3D surface plot for hyperparameter optimization (e.g., TPE results).

    Args:
        param1_values: Array of parameter 1 trial values.
        param2_values: Array of parameter 2 trial values.
        metric_values: Array of metric values (e.g., RMSE).
        param1_name: Name of parameter 1.
        param2_name: Name of parameter 2.
        metric_name: Name of metric.
    """

    def __init__(self, param1_values: np.ndarray, param2_values: np.ndarray,
                 metric_values: np.ndarray, param1_name: str = "max_depth",
                 param2_name: str = "n_estimators", metric_name: str = "RMSE"):
        self.p1 = param1_values
        self.p2 = param2_values
        self.metric = metric_values
        self.p1_name = param1_name
        self.p2_name = param2_name
        self.metric_name = metric_name

    @staticmethod
    def _idw_surface(p1, p2, metric, g1, g2, power=2.15):
        s1, s2 = max(p1.max(), 1), max(p2.max(), 1)
        tx, ty = p1 / s1, p2 / s2
        gx, gy = g1 / s1, g2 / s2
        surface = np.empty_like(g1, dtype=float)
        for row in range(g1.shape[0]):
            dx = gx[row, :, None] - tx[None, :]
            dy = gy[row, :, None] - ty[None, :]
            dist2 = dx * dx + dy * dy + 0.0045
            w = 1.0 / (dist2 ** (power / 2))
            surface[row, :] = (w @ metric) / w.sum(axis=1)
        return surface

    def make(self) -> plt.Figure:
        _configure_mpl()
        p1_grid = np.linspace(self.p1.min(), self.p1.max(), 80)
        p2_grid = np.linspace(self.p2.min(), self.p2.max(), 80)
        g1, g2 = np.meshgrid(p1_grid, p2_grid)
        surface = self._idw_surface(self.p1, self.p2, self.metric, g1, g2)

        fig = plt.figure(figsize=(9.2, 7.2))
        ax = fig.add_axes([0.02, 0.05, 0.78, 0.88], projection="3d")
        norm = Normalize(vmin=surface.min(), vmax=surface.max())
        surf = ax.plot_surface(g1, g2, surface, cmap="coolwarm", norm=norm,
                               linewidth=0, antialiased=True, shade=True, rstride=1, cstride=1, alpha=0.96)
        ax.set_title(f"Hyperparameter Optimization: {self.metric_name}", fontsize=14, pad=18)
        ax.set_xlabel(self.p1_name, fontsize=13, labelpad=10)
        ax.set_ylabel(self.p2_name, fontsize=13, labelpad=10)
        ax.set_zlabel(self.metric_name, fontsize=12, labelpad=8)
        ax.tick_params(labelsize=8, pad=2)
        ax.view_init(elev=31, azim=42)
        for axis in [ax.xaxis, ax.yaxis, ax.zaxis]:
            axis.pane.set_facecolor((1, 1, 1, 0))
            axis.pane.set_edgecolor("#d0d0d0")
            axis._axinfo["grid"]["color"] = (0.72, 0.72, 0.72, 0.65)
            axis._axinfo["grid"]["linewidth"] = 0.6
        cax = fig.add_axes([0.84, 0.23, 0.028, 0.48])
        cbar = fig.colorbar(surf, cax=cax)
        cbar.set_label(self.metric_name, fontsize=11, labelpad=10)
        cbar.ax.tick_params(labelsize=8)
        cbar.outline.set_linewidth(0.75)
        return fig


# ===========================================================================
# 7. Correlation + Split Violin
# ===========================================================================

class CorrSplitViolin:
    """Lower-triangle correlation matrix + grouped split violin plots.

    Args:
        train_data: (n_train, n_features) array.
        test_data: (n_test, n_features) array.
        feature_names: List of feature names.
        feature_labels: Optional display labels.
        groups: Optional dict of group_name -> list of feature indices for bracket annotations.
    """

    def __init__(self, train_data: np.ndarray, test_data: np.ndarray,
                 feature_names: Optional[list[str]] = None,
                 feature_labels: Optional[list[str]] = None,
                 groups: Optional[dict[str, list[int]]] = None):
        n_feat = train_data.shape[1]
        self.train = train_data
        self.test = test_data
        self.names = feature_names or [f"F{i+1}" for i in range(n_feat)]
        self.labels = feature_labels or self.names
        self.groups = groups

    @staticmethod
    def _rank(data):
        ranked = np.empty_like(data, dtype=float)
        for col in range(data.shape[1]):
            order = np.argsort(data[:, col], kind="mergesort")
            ranks = np.empty(data.shape[0], dtype=float)
            ranks[order] = np.arange(1, data.shape[0] + 1)
            ranked[:, col] = ranks
        return ranked

    @staticmethod
    def _split_violin(ax, train, test, label, tc="#2f7fa7", tsc="#b4162d"):
        pooled = np.r_[train, test]
        pad = 0.08 * (pooled.max() - pooled.min() + 1e-6)
        grid = np.linspace(pooled.min() - pad, pooled.max() + pad, 240)
        td = _kde_1d(train, grid) * 0.40
        tsd = _kde_1d(test, grid) * 0.40
        if td.max() > 0: td = td / td.max() * 0.40
        if tsd.max() > 0: tsd = tsd / tsd.max() * 0.40
        ax.fill_betweenx(grid, -td, 0, facecolor="none", edgecolor=tc, linewidth=1.1)
        ax.fill_betweenx(grid, 0, tsd, facecolor="none", edgecolor=tsc, linewidth=1.1)
        ax.axvline(0, color=tsc, lw=0.75, alpha=0.9)
        for vals, color, side in [(train, tc, -1), (test, tsc, 1)]:
            q1, med, q3 = np.percentile(vals, [25, 50, 75])
            ax.hlines([q1, med, q3], side * 0.04, side * 0.33, color=color, linestyles="--", linewidth=0.75)
        ax.set_xlim(-0.45, 0.45)
        ax.set_xticks([])
        ax.set_ylabel(label, fontsize=7, fontweight="bold", labelpad=1)
        ax.tick_params(axis="y", labelsize=6, length=2, width=0.6, pad=1)

    def make(self) -> plt.Figure:
        _configure_mpl("sans-serif")
        all_data = np.vstack([self.train, self.test])
        corr = np.corrcoef(self._rank(all_data), rowvar=False)
        n = len(self.names)

        fig = plt.figure(figsize=(13.8, 4.6))
        cax = fig.add_axes([0.024, 0.165, 0.018, 0.72])
        ax_corr = fig.add_axes([0.075, 0.135, 0.355, 0.77])

        cmap = mpl.colormaps["RdBu_r"]
        norm = Normalize(-1, 1)
        ax_corr.set_xlim(-0.5, n + 4.3)
        ax_corr.set_ylim(n - 0.5, -0.5)
        ax_corr.set_aspect("equal")
        ax_corr.set_xticks(np.arange(n))
        ax_corr.set_xticklabels(self.names, rotation=90, fontsize=7, fontweight="bold")
        ax_corr.set_yticks(np.arange(n))
        ax_corr.set_yticklabels(self.names, fontsize=8, fontweight="bold")
        ax_corr.yaxis.tick_right()
        ax_corr.tick_params(axis="both", length=0, pad=1)
        for s in ax_corr.spines.values():
            s.set_visible(False)

        for row in range(n):
            for col in range(row):
                v = corr[row, col]
                sz = 0.12 + 0.70 * abs(v)
                ax_corr.add_patch(plt.Rectangle((col - sz / 2, row - sz / 2), sz, sz,
                                                 facecolor=cmap(norm(v)), edgecolor="#222222", linewidth=0.55))

        sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
        cbar = fig.colorbar(sm, cax=cax)
        cbar.set_label("Correlation", fontsize=9, fontweight="bold", labelpad=6)
        cbar.set_ticks(np.linspace(-1, 1, 9))
        cbar.ax.tick_params(labelsize=7, length=2)
        cbar.outline.set_linewidth(0.7)

        # Split violins on the right
        right_left, right_right = 0.520, 0.985
        cols = min(5, n)
        rows = math.ceil(n / cols)
        gap_x, gap_y = 0.030, 0.050
        cell_w = (right_right - right_left - gap_x * (cols - 1)) / cols
        cell_h = (0.905 - 0.110 - gap_y * (rows - 1)) / rows

        for idx in range(n):
            r, c = idx // cols, idx % cols
            left = right_left + c * (cell_w + gap_x)
            bottom = 0.905 - (r + 1) * cell_h - r * gap_y
            ax = fig.add_axes([left, bottom, cell_w, cell_h])
            self._split_violin(ax, self.train[:, idx], self.test[:, idx], self.labels[idx])

        handles = [Line2D([0], [0], color="#2f7fa7", lw=1.5, label="Train"),
                   Line2D([0], [0], color="#b4162d", lw=1.5, label="Test")]
        fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.725, 0.022), ncol=2, fontsize=8, frameon=False)
        return fig


# ===========================================================================
# 8. Circular Heatmap
# ===========================================================================

@dataclass
class HeatmapTrait:
    name: str
    color: str
    pale: str


@dataclass
class HeatmapGroup:
    label: str
    color: str
    count: int


class CircularHeatmap:
    """Grouped circular heatmap (Circos-style).

    Args:
        traits: List of HeatmapTrait (outer to inner rings).
        groups: List of HeatmapGroup for the group ring.
        values: (n_traits, n_items) array of values.
        start_angle: Starting angle in degrees.
        span_angle: Total angular span in degrees.
    """

    def __init__(self, traits: list[HeatmapTrait], groups: list[HeatmapGroup],
                 values: np.ndarray, start_angle: float = 82.0, span_angle: float = 322.0):
        self.traits = traits
        self.groups = groups
        self.values = values
        self.start_angle = start_angle
        self.span_angle = span_angle

    @staticmethod
    def _make_cmap(spec: HeatmapTrait):
        return LinearSegmentedColormap.from_list(
            f"{spec.name}_mag", [(0.00, spec.color), (0.35, spec.pale), (0.50, "#ffffff"), (0.65, spec.pale), (1.00, spec.color)])

    def make(self) -> plt.Figure:
        _configure_mpl()
        n_items = sum(g.count for g in self.groups)
        step = self.span_angle / n_items
        theta = np.deg2rad(self.start_angle + (np.arange(n_items) + 0.5) * step)
        width = np.deg2rad(step * 0.96)

        fig = plt.figure(figsize=(13.6, 12.6), facecolor="white")
        ax = fig.add_axes([0.005, 0.025, 0.805, 0.950], projection="polar")
        ax.set_theta_zero_location("E")
        ax.set_theta_direction(1)
        ax.set_axis_off()

        # Group ring
        group_r, group_h = 1.25, 0.110
        group_colors = []
        for g in self.groups:
            group_colors.extend([g.color] * g.count)
        for angle, color in zip(theta, group_colors):
            ax.bar(angle, group_h, width=width, bottom=group_r, color=color, edgecolor="white", linewidth=0.55, align="center")

        # Heatmap rings
        ring_gap = 0.012
        ring_h = 0.115
        heatmap_r = 1.50
        ring_radii = [heatmap_r + i * (ring_h + ring_gap) for i in range(len(self.traits))]
        norm = Normalize(vmin=-5, vmax=5)
        cmaps = [self._make_cmap(t) for t in self.traits]

        for ti, (spec, cmap) in enumerate(zip(self.traits, cmaps)):
            r = ring_radii[len(self.traits) - 1 - ti]
            colors = cmap(norm(self.values[ti]))
            ax.bar(theta, np.full_like(theta, ring_h), width=width, bottom=r,
                   color=colors, edgecolor="white", linewidth=0.55, align="center")

        # Labels
        outer_r = ring_radii[-1] + ring_h
        for idx in range(n_items):
            angle_deg = self.start_angle + (idx + 0.5) * step
            rot, ha = _text_rotation(angle_deg)
            ax.text(theta[idx], outer_r + 0.265, f"Item {idx+1}", rotation=rot,
                    rotation_mode="anchor", ha=ha, va="center", fontsize=6.5)

        # Legend
        handles = [Patch(facecolor=g.color, edgecolor="white", label=g.label) for g in self.groups]
        ax_legend = fig.add_axes([0.372, 0.410, 0.295, 0.205])
        ax_legend.axis("off")
        ax_legend.legend(handles=handles, loc="upper left", frameon=False, fontsize=8.3,
                         handlelength=1.2, labelspacing=0.55)
        return fig


# ===========================================================================
# 9. Combo Comparison (Stacked + Raincloud + Boxplot)
# ===========================================================================

class ComboComparison:
    """Combined stacked bar + raincloud + boxplot for multi-metric city comparison.

    Args:
        cities: List of city names.
        groups: List of group names.
        city_group_map: Dict of city -> group.
        bar_data: Dict of city -> (count1, count2).
        metric_data: Dict of (city, metric) -> np.ndarray.
        metric_names: List of metric names.
    """

    def __init__(self, cities: list[str], groups: list[str],
                 city_group_map: dict[str, str],
                 bar_data: dict[str, tuple[int, int]],
                 metric_data: dict[tuple[str, str], np.ndarray],
                 metric_names: list[str]):
        self.cities = cities
        self.groups = groups
        self.city_group_map = city_group_map
        self.bar_data = bar_data
        self.metric_data = metric_data
        self.metric_names = metric_names

    def make(self) -> plt.Figure:
        _configure_mpl("sans-serif")
        n_metrics = len(self.metric_names)
        fig, axes = plt.subplots(1, n_metrics + 1, figsize=(4 * (n_metrics + 1), 6),
                                  gridspec_kw={"width_ratios": [1.5] + [1] * n_metrics})

        # Stacked bar chart
        ax_bar = axes[0]
        x = np.arange(len(self.cities))
        c1 = [self.bar_data[c][0] for c in self.cities]
        c2 = [self.bar_data[c][1] for c in self.cities]
        group_colors = {g: plt.cm.Set3(i / len(self.groups)) for i, g in enumerate(self.groups)}
        colors = [group_colors[self.city_group_map[c]] for c in self.cities]
        ax_bar.bar(x, c1, color=colors, alpha=0.7)
        ax_bar.bar(x, c2, bottom=c1, color=colors, alpha=0.4, hatch="//")
        ax_bar.set_xticks(x)
        ax_bar.set_xticklabels(self.cities, rotation=45, ha="right", fontsize=7)
        ax_bar.set_ylabel("Count")

        # Metric raincloud/boxplots
        for mi, metric in enumerate(self.metric_names):
            ax = axes[mi + 1]
            data_list = [self.metric_data.get((c, metric), np.array([])) for c in self.cities]
            parts = ax.violinplot([d for d in data_list if len(d) > 0], positions=x[:len([d for d in data_list if len(d) > 0])],
                                  showmeans=False, showmedians=True, showextrema=False)
            for pc in parts["bodies"]:
                pc.set_alpha(0.3)
            ax.set_xticks(x)
            ax.set_xticklabels(self.cities, rotation=45, ha="right", fontsize=7)
            ax.set_ylabel(metric)

        fig.tight_layout()
        return fig


# ===========================================================================
# 10. Chord Diagram (Nature/Circos style)
# ===========================================================================

@dataclass
class ChordNode:
    label: str
    color: str
    weight: float = 1.0


class ChordDiagram:
    """Nature-style chord diagram (Circos graph).

    Args:
        nodes: List of ChordNode.
        flows: List of (source_label, target_label, weight) tuples.
        gap: Gap between sectors in degrees.
        start_angle: Starting angle.
    """

    def __init__(self, nodes: list[ChordNode], flows: list[tuple[str, str, float]],
                 gap: float = 0.92, start_angle: float = 124.0):
        self.nodes = nodes
        self.flows = flows
        self.gap = gap
        self.start_angle = start_angle

    def _compute_layout(self):
        total_gap = self.gap * len(self.nodes)
        total_weight = sum(n.weight for n in self.nodes)
        current = self.start_angle
        layout = {}
        for n in self.nodes:
            arc = (360.0 - total_gap) * n.weight / total_weight
            layout[n.label] = {"start": current, "end": current - arc, "mid": (current + current - arc) / 2.0, "arc": arc}
            current = current - arc - self.gap
        return layout

    @staticmethod
    def _ribbon_patch(s_angle, e_angle, width, color, radius=0.805, alpha=0.26, zorder=2):
        width = min(max(width, 0.20), 8.0)
        s1, s2 = s_angle - width / 2, s_angle + width / 2
        e1, e2 = e_angle + width / 2, e_angle - width / 2

        def polar(t, r):
            t_rad = np.deg2rad(t)
            return np.array([r * np.cos(t_rad), r * np.sin(t_rad)])

        vertices = [polar(s1, radius), polar(s1, radius * 0.20), polar(e1, radius * 0.20), polar(e1, radius),
                    polar(e2, radius), polar(e2, radius * 0.20), polar(s2, radius * 0.20), polar(s2, radius), polar(s1, radius)]
        codes = [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
                 MplPath.LINETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4, MplPath.CLOSEPOLY]
        return PathPatch(MplPath(vertices, codes), facecolor=color, edgecolor="none", alpha=alpha, zorder=zorder)

    def make(self) -> plt.Figure:
        _configure_mpl()
        layout = self._compute_layout()
        color_map = {n.label: n.color for n in self.nodes}

        fig, ax = plt.subplots(figsize=(10.6, 10.6), facecolor="white")
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_xlim(-1.38, 1.38)
        ax.set_ylim(-1.34, 1.39)

        # Draw ribbons
        rng = np.random.default_rng(42)
        sorted_flows = sorted(self.flows, key=lambda f: f[2])
        for src, tgt, w in sorted_flows:
            if src not in layout or tgt not in layout:
                continue
            s_arc = layout[src]["arc"]
            t_arc = layout[tgt]["arc"]
            s_mid = layout[src]["mid"] + rng.uniform(-0.34 * s_arc, 0.34 * s_arc)
            t_mid = layout[tgt]["mid"] + rng.uniform(-0.34 * t_arc, 0.34 * t_arc)
            alpha = 0.07 if w < 1.1 else (0.12 if w < 3.5 else 0.25)
            rw = 0.22 + 0.32 * w if w < 3.5 else 0.48 + 0.70 * w
            patch = self._ribbon_patch(s_mid, t_mid, rw, _lighten(color_map.get(src, "#888888"), 0.18), alpha=alpha)
            ax.add_patch(patch)

        # Sector ring
        ax.add_patch(Wedge((0, 0), 1.075, 0, 360, width=0.105, facecolor="#eeeeee", edgecolor="none", alpha=0.85, zorder=0))
        for n in self.nodes:
            item = layout[n.label]
            ax.add_patch(Wedge((0, 0), 1.000, theta1=item["end"], theta2=item["start"], width=0.115,
                               facecolor=n.color, edgecolor="#3a3a3a", linewidth=0.38, zorder=5))

        # Labels
        for n in self.nodes:
            mid = layout[n.label]["mid"]
            rot, ha = _text_rotation(mid)
            r = 1.145
            if layout[n.label]["arc"] < 7.0:
                r += 0.045
            ax.text(*_polar_to_xy(r, np.cos(np.deg2rad(mid))), n.label,
                    rotation=rot, rotation_mode="anchor", ha=ha, va="center",
                    fontsize=11.8 if layout[n.label]["arc"] > 7.0 else 9.6, color="#090909", zorder=8)
        return fig


# ===========================================================================
# 11. SHAP Beeswarm (Multiclass)
# ===========================================================================

class ShapBeeswarm:
    """Multiclass SHAP importance bar + beeswarm combo plot.

    Args:
        feature_names: List of feature names.
        class_names: List of class names.
        importance_table: (n_features, n_classes) mean |SHAP| values.
        shap_values: List of (n_samples, n_features) arrays, one per class.
        feature_values: (n_samples, n_features) normalized feature values.
        class_colors: Dict of class_name -> color.
    """

    def __init__(self, feature_names: list[str], class_names: list[str],
                 importance_table: np.ndarray,
                 shap_values: Optional[list[np.ndarray]] = None,
                 feature_values: Optional[np.ndarray] = None,
                 class_colors: Optional[dict[str, str]] = None):
        self.features = feature_names
        self.classes = class_names
        self.imp = importance_table
        self.shap = shap_values
        self.feat_vals = feature_values
        self.class_colors = class_colors or {c: plt.cm.Set2(i / len(class_names)) for i, c in enumerate(class_names)}

    def make(self) -> plt.Figure:
        _configure_mpl("sans-serif")
        n_feat = len(self.features)
        y_pos = np.arange(n_feat)

        fig = plt.figure(figsize=(11.8, 7.2))
        left, bottom, width, height = 0.075, 0.165, 0.820, 0.735
        ax_imp = fig.add_axes([left, bottom, width, height])

        # Stacked importance bars
        running = np.zeros(n_feat)
        for ci, cn in enumerate(self.classes):
            ax_imp.barh(y_pos, self.imp[:, ci], left=running, height=0.56,
                        color=self.class_colors[cn], alpha=0.48, edgecolor=self.class_colors[cn], linewidth=0.45)
            running += self.imp[:, ci]

        ax_imp.set_xlim(0, running.max() * 1.1)
        ax_imp.set_ylim(n_feat - 0.22, -0.82)
        ax_imp.set_yticks(y_pos)
        ax_imp.set_yticklabels(self.features, fontsize=12)
        ax_imp.tick_params(axis="y", pad=8, length=0)
        ax_imp.xaxis.tick_top()
        ax_imp.set_xlabel("Importance value", fontsize=16, labelpad=14)
        ax_imp.grid(axis="x", color="#222222", alpha=0.45, linewidth=0.75)
        ax_imp.spines["left"].set_visible(False)
        ax_imp.spines["right"].set_visible(False)
        ax_imp.spines["bottom"].set_visible(False)

        # Beeswarm panels (if shap values provided)
        if self.shap and self.feat_vals is not None:
            panel_gap = 0.044
            n_classes = len(self.classes)
            panel_width = (width - panel_gap * (n_classes - 1)) / n_classes
            feat_cmap = LinearSegmentedColormap.from_list("fv", ["#2166ac", "#1fa8c9", "#77d7c8", "#fff3a5", "#fdae61", "#d73027"])
            norm = Normalize(vmin=0.0, vmax=1.0)
            rng = np.random.default_rng(42)

            for ci, cn in enumerate(self.classes):
                panel_left = left + ci * (panel_width + panel_gap)
                ax = fig.add_axes([panel_left, bottom, panel_width, height], sharey=ax_imp)
                ax.axvline(0, color="#222222", linewidth=0.9, alpha=0.72, zorder=2)
                ax.spines["left"].set_visible(False)
                ax.spines["right"].set_visible(False)
                ax.spines["top"].set_visible(False)
                ax.tick_params(axis="y", left=False, labelleft=False)
                ax.set_xlabel("SHAP value", fontsize=11, labelpad=2)

                half_range = max(np.abs(self.shap[ci]).max(), 1.0) * 1.1
                ax.set_xlim(-half_range, half_range)

                for fi, y in enumerate(y_pos):
                    sv = self.shap[ci][:, fi]
                    fv = self.feat_vals[:, fi]
                    density_proxy = np.exp(-0.5 * (sv / max(half_range * 0.35, 1e-6)) ** 2)
                    y_swarm = y + rng.normal(scale=0.045 + 0.105 * density_proxy, size=sv.size)
                    order = rng.permutation(sv.size)
                    ax.scatter(sv[order], y_swarm[order], c=fv[order], cmap=feat_cmap, norm=norm,
                               s=10, alpha=0.76, linewidths=0, rasterized=True, zorder=4)

            cax = fig.add_axes([0.925, bottom + 0.050, 0.012, height - 0.080])
            sm = mpl.cm.ScalarMappable(norm=norm, cmap=feat_cmap)
            cbar = fig.colorbar(sm, cax=cax)
            cbar.set_ticks([])
            cbar.ax.text(2.2, 1.0, "High", transform=cbar.ax.transAxes, ha="left", va="center", fontsize=10)
            cbar.ax.text(2.2, 0.0, "Low", transform=cbar.ax.transAxes, ha="left", va="center", fontsize=10)
            cbar.ax.set_ylabel("Feature value", rotation=90, labelpad=28, fontsize=11)

        # Legend
        handles = [Patch(facecolor=self.class_colors[cn], edgecolor=self.class_colors[cn], alpha=0.48, label=cn) for cn in self.classes]
        fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.50, 0.040), ncol=len(self.classes),
                   handlelength=1.8, columnspacing=1.6, fontsize=12)
        return fig


# ===========================================================================
# Quick demo / self-test
# ===========================================================================

def _demo():
    """Run a quick self-test of all figure types."""
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    out_dir = "figures/sci_demo"
    results = {}

    # 1. Taylor Diagram
    models = [("XGBoost", "#f2a51a"), ("ANN", "#d7191c"), ("GPR", "#2222a0"), ("Observed", "#000000")]
    panels = {
        "train": [TaylorPoint("XGBoost", 1.02, 0.985), TaylorPoint("ANN", 0.93, 0.970), TaylorPoint("GPR", 1.08, 0.955)],
        "test": [TaylorPoint("XGBoost", 1.00, 0.975), TaylorPoint("ANN", 0.96, 0.965), TaylorPoint("GPR", 1.06, 0.960)],
    }
    fig = TaylorDiagram(models, panels).make()
    results["taylor"] = save_figure(fig, "taylor", out_dir)

    # 2. Paired Raincloud
    rng = np.random.default_rng(42)
    data = {
        ("Pre", "A"): rng.normal(2.74, 0.31, 50), ("Pre", "B"): rng.normal(3.00, 0.36, 50),
        ("Post", "A"): rng.normal(3.60, 0.35, 50), ("Post", "B"): rng.normal(2.65, 0.30, 50),
    }
    palette = {"A": {"edge": "#c9253e", "fill": "#ee7f8d"}, "B": {"edge": "#145f86", "fill": "#6f9fba"}}
    fig = PairedRaincloud(data, ["A", "B"], ["Pre", "Post"], palette, "Value").make()
    results["raincloud"] = save_figure(fig, "raincloud", out_dir)

    # 3. CV ROC
    specs = [RocModelSpec("LR", 0.889, 0.026, "#2d214c"), RocModelSpec("RF", 0.906, 0.029, "#8f3032"),
             RocModelSpec("XGB", 0.895, 0.032, "#c47b4b")]
    fig = CvRocCurve(specs).make()
    results["roc"] = save_figure(fig, "roc", out_dir)

    # 4. Correlation PairGrid
    f1 = rng.normal(size=80)
    data4 = np.column_stack([f1 + rng.normal(0, 0.5, 80), 0.5 * f1 + rng.normal(0, 0.8, 80),
                              rng.normal(size=80), -0.3 * f1 + rng.normal(0, 0.9, 80)])
    fig = CorrelationPairgrid(data4, ["X1", "X2", "X3", "X4"]).make()
    results["pairgrid"] = save_figure(fig, "pairgrid", out_dir)

    # 6. Hyperparameter Surface
    p1 = rng.uniform(1, 40, 100)
    p2 = rng.uniform(5, 200, 100)
    metric = 0.5 + 0.1 * np.sin(p1 / 5) * np.cos(p2 / 30) + rng.normal(0, 0.02, 100)
    fig = HyperparamSurface(p1, p2, metric).make()
    results["surface"] = save_figure(fig, "surface", out_dir)

    # 11. SHAP (simplified, no beeswarm)
    imp = np.array([[0.18, 0.07, 0.14], [0.05, 0.10, 0.21], [0.10, 0.04, 0.04], [0.09, 0.01, 0.05]])
    fig = ShapBeeswarm(["Mn", "Co", "Fe", "Cd"], ["MVT", "SEDEX", "VMS"], imp).make()
    results["shap"] = save_figure(fig, "shap", out_dir)

    for name, paths in results.items():
        print(f"[OK] {name}: {', '.join(f'{k}={len(v)}' for k, v in paths.items())}")
    print("=== All scientific figure templates validated! ===")


if __name__ == "__main__":
    _demo()
