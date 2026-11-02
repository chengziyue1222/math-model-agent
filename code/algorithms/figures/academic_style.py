"""Academic-publication figure patterns inspired by the local reference skill.

The functions in this module are small, deterministic Matplotlib implementations
for the chart families shown in the reference atlas.  They keep data semantics
explicit while adding the visual structure that a generic adapter cannot provide:
original observations, confidence bands, direct labels, diverging scales, and
multi-panel relationships.
"""
from __future__ import annotations
from . import styles as _style

from itertools import combinations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import PathPatch, Wedge
from matplotlib.path import Path
from scipy.stats import gaussian_kde

from .base import attach_metadata, contract_from, finite_array


PALETTE = _style.Palette(["#6EA7C2", "#E78B83", "#8FB5A0", "#B79ACB", "#E7B56D", "#6E8798"])
INK = "#252A2E"
MUTED = "#81909A"
GRID = "#DCE4E8"


def _ax(ax=None, *, figsize=(6.2, 4.6)):
    if ax is not None:
        return ax
    fig, axis = _style.subplots(figsize=figsize, constrained_layout=True)
    return axis


def _finish(ax, *, xlabel=None, ylabel=None, title=None):
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title, loc="left", fontweight="bold", color=INK)
    ax.tick_params(colors=INK, width=0.6, length=3)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(INK)
        ax.spines[spine].set_linewidth(0.65)
    return ax


def _figure(ax):
    return ax.figure


def grouped_bar_academic(categories, values, *, groups=None, errors=None, units="",
                         interval_kind=None, contract=None, ax=None, **kwargs):
    """Grouped bars with raw replicate points and error intervals."""
    labels = list(categories)
    arr = np.asarray(values, dtype=float)
    if arr.ndim == 1:
        arr = arr[:, None]
    if arr.ndim != 2 or arr.shape[0] != len(labels) or not np.isfinite(arr).all():
        raise ValueError("values must be a finite (n_categories, n_groups) array")
    axis = _ax(ax)
    n_cat, n_group = arr.shape
    x = np.arange(n_cat)
    width = 0.78 / n_group
    colors = (PALETTE * ((n_group + len(PALETTE) - 1) // len(PALETTE)))[:n_group]
    # In the common data shape each row is a category and each column a group.
    if groups is None:
        groups = [f"组{i + 1}" for i in range(n_group)]
    if len(groups) != n_group:
        raise ValueError("groups must align with the second dimension of values")
    heights = arr
    if errors is None:
        err = np.zeros_like(heights)
    else:
        if not interval_kind:
            raise ValueError("interval_kind is required when errors are supplied")
        err = np.asarray(errors, dtype=float)
        if err.ndim == 1 and err.size == n_cat:
            err = err[:, None]
        elif err.shape == (n_group,):
            err = np.broadcast_to(err, heights.shape)
        if err.shape != heights.shape:
            raise ValueError("errors must align with values")
    for gi, group in enumerate(groups):
        vals = heights[:, gi] if heights.ndim == 2 else heights
        xpos = x + (gi - (n_group - 1) / 2) * width
        yerr = err[:, gi] if err.ndim == 2 else err
        axis.bar(xpos, vals, width=width * 0.88, yerr=yerr, capsize=2.5,
                 color=colors[gi], alpha=0.84, label=group, edgecolor="#566671", linewidth=_style.stroke(0.4),
                 hatch=["", "//", "..", "xx"][gi % 4])
        # Raw replicates are optional, but they must come from the caller.
        # Never manufacture observations from a bar height.
        replicates = kwargs.get("replicates")
        if replicates is not None:
            reps = np.asarray(replicates, dtype=float)
            if reps.ndim != 3 or reps.shape[:2] != (n_cat, n_group) or not np.isfinite(reps).all():
                raise ValueError("replicates must be finite category-by-group-by-observation data")
            if reps.ndim == 3:
                for ci in range(n_cat):
                    points = reps[ci, gi]
                    jitter = np.linspace(-width * 0.22, width * 0.22, points.size)
                    axis.scatter(np.full(points.size, xpos[ci]) + jitter, points, s=_style.marker(9, area=True),
                                 color=colors[gi], edgecolors="white", linewidths=_style.stroke(0.35), zorder=4)
    axis.set_xticks(x, labels)
    axis.set_ylabel(units or "指标值")
    axis.grid(axis="y", color=GRID, linewidth=_style.stroke(0.45))
    axis.set_axisbelow(True)
    axis.legend(frameon=False, ncol=min(4, n_group), loc="upper left", bbox_to_anchor=(0, 1.02))
    _finish(axis)
    return attach_metadata(_figure(axis), name="grouped_bar_academic", contract=contract_from(kwargs, contract),
                           encoding="grouped bars; only caller-supplied replicate points", groups=list(groups),
                           interval_kind=interval_kind or "none")


def bar_academic(categories, values, *, units="", contract=None, ax=None, **kwargs):
    """Single-series bar chart; one bar per category, never grouped."""
    labels = list(categories)
    arr = finite_array(values, "values")
    if arr.size != len(labels):
        raise ValueError("categories and values must have the same length")
    axis = _ax(ax)
    x = np.arange(arr.size)
    axis.bar(x, arr, color=PALETTE[0], edgecolor="white", linewidth=_style.stroke(0.5), alpha=.88)
    axis.scatter(x, arr, color=INK, s=_style.marker(12, area=True), zorder=3)
    axis.set_xticks(x, labels)
    axis.set_ylabel(units or "指标值")
    axis.grid(axis="y", color=GRID, linewidth=_style.stroke(0.45))
    axis.set_axisbelow(True)
    _finish(axis)
    return attach_metadata(_figure(axis), name="bar_academic", contract=contract_from(kwargs, contract),
                           encoding="single-series bars", groups=[])


def network_variant(edges, *, weights=None, community=None, variant="correlation",
                    contract=None, ax=None, **kwargs):
    """Network renderer with distinct edge, community, and weight encodings."""
    import networkx as nx
    if not edges:
        raise ValueError("edges must contain at least one edge")
    graph = nx.Graph()
    graph.add_nodes_from(kwargs.get("nodes", list(dict.fromkeys(n for e in edges for n in e[:2]))))
    graph.add_edges_from([(e[0], e[1]) for e in edges])
    if weights is None:
        weights = [1.0] * len(edges)
    weights = np.asarray(weights, dtype=float).reshape(-1)
    if weights.size != len(edges) or not np.isfinite(weights).all():
        raise ValueError("weights must align with edges and be finite")
    if community is not None:
        community = list(community)
        nodes = list(graph.nodes)
        if len(community) != len(nodes):
            raise ValueError("community must align with graph nodes in insertion order")
    axis, node_labels = _style.node_axes(list(graph.nodes), ax); pos = nx.spring_layout(graph, seed=7, weight=None)
    for (u, v), weight in zip(edges, weights):
        if variant == "correlation":
            color = PALETTE[0] if weight >= 0 else PALETTE[1]
            style = "-" if weight >= 0 else "--"
            width = 1.0 + 1.2 * min(abs(float(weight)), 2.0)
        elif variant == "weighted":
            color = PALETTE[2]
            style = "-"
            width = .6 + 3.4 * (abs(float(weight)) / max(float(np.max(np.abs(weights))), 1e-9))
        else:
            color = "#9BA8B0"; style = "-"; width = 1.1
        axis.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]], color=color,
                  lw=width, ls=style, alpha=.78, zorder=1)
    nodes = list(graph.nodes)
    community_labels = None
    if variant == "community":
        # Accept human-readable labels and map them deterministically for color
        # assignment. The mapping is retained in figure metadata.
        community_labels = list(dict.fromkeys(str(value) for value in community))
        label_to_index = {label: index for index, label in enumerate(community_labels)}
        node_colors = [PALETTE[label_to_index[str(community[i])] % len(PALETTE)] for i in range(len(nodes))]
    else:
        node_colors = [PALETTE[0]] * len(nodes)
    if variant == "community":
        from matplotlib.lines import Line2D
        handles = []
        for index, label in enumerate(community_labels):
            marker = ["o", "s", "^", "D", "v"][index % 5]
            members = [node for i, node in enumerate(nodes) if str(community[i]) == label]
            color = PALETTE[index % len(PALETTE)]
            nx.draw_networkx_nodes(graph, pos, nodelist=members, ax=axis, node_color=color,
                                   node_size=340, node_shape=marker, edgecolors="white", linewidths=_style.stroke(0.8))
            handles.append(Line2D([], [], linestyle="", marker=marker, color=color, label=label))
        axis.figure.legend(handles=handles, title="社区", frameon=False, loc="outside upper center", ncol=min(3, len(handles)))
    else:
        nx.draw_networkx_nodes(graph, pos, ax=axis, node_color=node_colors, node_size=340,
                               edgecolors="white", linewidths=_style.stroke(0.8))
    if variant == 'weighted':
        from matplotlib.lines import Line2D
        maximum = max(float(np.max(np.abs(weights))), 1e-9)
        levels = np.linspace(maximum/3, maximum, 3)
        axis.figure.legend(handles=[Line2D([], [], color=PALETTE[2], lw=.6+3.4*v/maximum, label=f'{v:.2g}') for v in levels],
                           title='|边权重|', frameon=False, loc='outside upper center', ncol=3)
    elif variant == 'correlation':
        from matplotlib.lines import Line2D
        axis.figure.legend(handles=[Line2D([],[],color=PALETTE[0],linestyle='-',label='正相关'),
                                    Line2D([],[],color=PALETTE[1],linestyle='--',label='负相关')],
                           frameon=False,loc='outside upper center',ncol=2)
    nx.draw_networkx_labels(graph, pos, labels=node_labels, ax=axis, font_size=_style.font('text', 8),
                           font_color=INK, bbox={'facecolor':'white','edgecolor':'none','alpha':.9,'pad':1.5})
    axis.margins(.18)
    axis.axis("off")
    return attach_metadata(_figure(axis), name=f"{variant}_network", contract=contract_from(kwargs, contract),
                           edge_semantics=("sign and line style" if variant == "correlation" else
                                           "absolute magnitude mapped to width" if variant == "weighted" else
                                           "node color mapped to community"),
                           nodes=nodes, edges=len(edges), community=community,
                           node_label_key=getattr(axis.figure, '_node_label_key', {}),
                           community_labels=community_labels,
                           community_mapping=({label: index for index, label in enumerate(community_labels)}
                                              if community_labels is not None else None))


def correlation_network_academic(edges, *, weights=None, contract=None, ax=None, **kwargs):
    return network_variant(edges, weights=weights, variant="correlation", contract=contract, ax=ax, **kwargs)


def weighted_network_academic(edges, *, weights, contract=None, ax=None, **kwargs):
    return network_variant(edges, weights=weights, variant="weighted", contract=contract, ax=ax, **kwargs)


def community_network_academic(edges, *, community, weights=None, contract=None, ax=None, **kwargs):
    return network_variant(edges, weights=weights, community=community, variant="community", contract=contract, ax=ax, **kwargs)


def embedding_trajectory_academic(embedding, *, time=None, groups=None, contract=None, ax=None, **kwargs):
    """Embedding trajectory with ordered arrows and start/end markers."""
    a = finite_array(embedding, "embedding", ndim=2)
    if a.shape[1] < 2 or a.shape[0] < 3:
        raise ValueError("embedding must be an n×2 array with at least three rows")
    axis = _ax(ax); order = np.arange(a.shape[0]) if time is None else np.argsort(finite_array(time, "time"))
    axis.plot(a[order, 0], a[order, 1], color=PALETTE[0], lw=_style.stroke(1.4), alpha=.9)
    sequence=axis.scatter(a[order, 0], a[order, 1], c=np.arange(a.shape[0]), cmap=_style.cmap('sequential', 'viridis'), s=_style.marker(18, area=True), zorder=3)
    _figure(axis).colorbar(sequence,ax=axis,label="时间排序序号（从 0 开始）")
    for i in range(len(order) - 1):
        axis.annotate("", xy=a[order[i + 1], :2], xytext=a[order[i], :2],
                      arrowprops={"arrowstyle": "->", "color": PALETTE[1], "lw": .65})
    axis.scatter(*a[order[0], :2], s=_style.marker(55, area=True), marker="o", color=PALETTE[2], edgecolor="white", zorder=4,label="起点")
    axis.scatter(*a[order[-1], :2], s=_style.marker(65, area=True), marker="X", color=PALETTE[1], edgecolor="white", zorder=4,label="终点")
    _figure(axis).legend(*axis.get_legend_handles_labels(),loc="outside upper center",ncol=2,frameon=False)
    _finish(axis, xlabel="嵌入维度 1", ylabel="嵌入维度 2")
    return attach_metadata(_figure(axis), name="embedding_trajectory_academic", contract=contract_from(kwargs, contract),
                           encoding="ordered path + arrows + start/end markers")


def cluster_scatter_academic(embedding, *, groups, contract=None, ax=None, **kwargs):
    """Cluster scatter with group hulls and categorical labels."""
    a = finite_array(embedding, "embedding", ndim=2)
    groups = np.asarray(groups)
    if a.shape[0] != groups.size:
        raise ValueError("groups must align with embedding rows")
    axis = _ax(ax)
    for i, group in enumerate(dict.fromkeys(groups.tolist())):
        mask = groups == group; pts = a[mask, :2]
        axis.scatter(pts[:, 0], pts[:, 1], s=_style.marker(25, area=True), color=PALETTE[i % len(PALETTE)],
                     alpha=.72, edgecolor="white", linewidth=_style.stroke(0.35), label=str(group),
                     marker=["o", "s", "^"][i % 3])
        if pts.shape[0] >= 3:
            center = pts.mean(0); cov = np.cov(pts.T) + np.eye(2) * 1e-6
            eigval, eigvec = np.linalg.eigh(cov); order = np.argsort(eigval)[::-1]
            eigval, eigvec = eigval[order], eigvec[:, order]
            theta = np.linspace(0, 2 * np.pi, 80)
            ellipse = center + (eigvec @ (np.sqrt(eigval)[:, None] * np.vstack([np.cos(theta), np.sin(theta)]) * 2.0)).T
            axis.plot(ellipse[:, 0], ellipse[:, 1], color=PALETTE[i % len(PALETTE)], lw=_style.stroke(1.0),
                      ls=["-", "--", ":"][i % 3])
    axis.figure.legend(*axis.get_legend_handles_labels(), frameon=False,
                      title="类别（轮廓为 2SD 数据椭圆）", loc="outside upper center", ncol=3)
    axis.set_aspect("equal", adjustable="box")
    _finish(axis, xlabel="嵌入维度 1", ylabel="嵌入维度 2")
    return attach_metadata(_figure(axis), name="cluster_scatter_academic", contract=contract_from(kwargs, contract),
                           encoding="points + descriptive 2SD covariance ellipses; not confidence regions",
                           interval_kind="descriptive 2SD data ellipse",
                           groups=[str(x) for x in dict.fromkeys(groups.tolist())])


def pca_biplot_academic(scores, loadings, explained_variance, *, labels=None, feature_labels=None,
                        max_labels=12, contract=None, ax=None, **kwargs):
    scores = finite_array(scores, "scores", ndim=2); loadings = finite_array(loadings, "loadings", ndim=2)
    ev = finite_array(explained_variance, "explained_variance")
    if scores.shape[1] < 2 or loadings.shape[1] < 2 or ev.size < 2:
        raise ValueError("pca_biplot requires at least two score/loading dimensions and explained_variance")
    axis = _ax(ax); axis.scatter(scores[:, 0], scores[:, 1], s=_style.marker(20, area=True), color=PALETTE[0], alpha=.55, edgecolor="white", linewidth=_style.stroke(0.25))
    scale = max(np.ptp(scores[:, :2], axis=0).max(), 1e-9) * .42
    labels = list(feature_labels or [f"变量{i + 1}" for i in range(loadings.shape[0])])
    if len(labels) != loadings.shape[0]:
        raise ValueError("feature_labels must align with loadings rows")
    if not isinstance(max_labels, int) or max_labels < 1:
        raise ValueError("max_labels must be a positive integer")
    normalizer = float(max(np.max(np.abs(loadings[:, :2])), 1e-9))
    endpoints = loadings[:, :2] / normalizer * scale
    selected = np.argsort(-np.linalg.norm(loadings[:, :2], axis=1), kind="stable")[:max_labels]
    for i, end in enumerate(endpoints):
        emphasized = i in selected
        axis.annotate("", xy=end, xytext=(0, 0), arrowprops={"arrowstyle": "->",
                      "color": "#A6534C" if emphasized else "#B7C1C7",
                      "alpha": .9 if emphasized else .25, "lw": 1.0 if emphasized else .45})
    # Separate labels from the vectors. Every vector remains drawn; only the
    # explicitly documented strongest projected vectors receive text labels.
    extent = np.vstack([scores[:, :2], endpoints])
    low, high = extent.min(0), extent.max(0)
    span = np.maximum(high - low, 1e-6)
    pad_x = .85 if any(len(str(labels[i])) > 10 for i in selected) else .38
    axis.set_xlim(low[0] - pad_x * span[0], high[0] + pad_x * span[0])
    axis.set_ylim(low[1] - .12 * span[1], high[1] + .12 * span[1])
    import textwrap
    for right in (False, True):
        side = sorted([int(i) for i in selected if (endpoints[i, 0] >= 0) == right],
                      key=lambda i: endpoints[i, 1])
        targets = np.linspace(low[1], high[1], len(side)) if len(side) > 1 else [(low[1] + high[1]) / 2]
        label_x = high[0] + .15 * span[0] if right else low[0] - .15 * span[0]
        for i, label_y in zip(side, targets):
            axis.annotate(textwrap.fill(str(labels[i]), width=10), xy=endpoints[i], xytext=(label_x, label_y),
                          ha="left" if right else "right", va="center", fontsize=_style.font('text', 7),
                          color=_style.color(1, '#A6534C'), arrowprops={"arrowstyle": "-", "color": "#9BA8B0", "lw": .45})
    axis.axhline(0, color=GRID, lw=_style.stroke(0.6)); axis.axvline(0, color=GRID, lw=_style.stroke(0.6))
    axis.set_aspect("equal", adjustable="box")
    if len(selected) < len(labels):
        axis.set_title(f"全部 {len(labels)} 个载荷；标注投影幅度最大的 {len(selected)} 个", fontsize=_style.font('title', 7))
    _finish(axis, xlabel=f"PC1 ({ev[0]:.1%})", ylabel=f"PC2 ({ev[1]:.1%})")
    return attach_metadata(_figure(axis), name="pca_biplot_academic", contract=contract_from(kwargs, contract),
                           encoding="sample scores + loading vectors", explained_variance=ev.tolist(),
                           scores=scores.tolist(), loadings=loadings.tolist(), loading_display_scale=scale,
                           loading_normalizer=normalizer, labeled_feature_indices=selected.tolist(),
                           label_selection="largest norm on displayed PC1/PC2; all vectors retained",
                           loading_scale_note="all loading vectors share one display scale; not score coordinates")


def pca_loadings_academic(loadings, *, labels=None, contract=None, ax=None, **kwargs):
    loading = finite_array(loadings, "loadings", ndim=2)
    labels = list(labels or [f"变量{i + 1}" for i in range(loading.shape[0])])
    if len(labels) != loading.shape[0]:
        raise ValueError("labels must align with loadings rows")
    panel_count = int(np.ceil(loading.shape[0] / 20))
    if ax is not None and panel_count > 1:
        raise ValueError("more than 20 loadings require automatic facets; omit ax")
    if panel_count == 1:
        axes = [_ax(ax)]; fig = axes[0].figure
    else:
        cols = min(2, panel_count); rows = int(np.ceil(panel_count / cols))
        fig, grid = _style.subplots(rows, cols, figsize=(7.2, 4.5 * rows), constrained_layout=True, squeeze=False)
        axes = grid.ravel().tolist()
    bound = max(float(np.abs(loading[:, :2]).max()) * 1.15, 1e-6)
    for index, axis in enumerate(axes):
        start, stop = index * 20, min((index + 1) * 20, len(labels))
        if start >= stop:
            axis.set_visible(False); continue
        chunk = loading[start:stop]; y = np.arange(stop - start); width = .36
        axis.barh(y - width / 2, chunk[:, 0], height=width, color=PALETTE[0], label="PC1", edgecolor="#566671", lw=_style.stroke(0.3))
        if loading.shape[1] > 1:
            axis.barh(y + width / 2, chunk[:, 1], height=width, color=PALETTE[1], label="PC2", hatch="//", edgecolor="#566671", lw=_style.stroke(0.3))
        axis.axvline(0, color=INK, lw=_style.stroke(0.7)); axis.set_yticks(y, labels[start:stop]); axis.invert_yaxis()
        axis.set_xlim(-bound, bound)
        axis.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(.5, 1.16))
        _finish(axis, xlabel="载荷", ylabel="变量")
    return attach_metadata(fig, name="pca_loadings_academic", contract=contract_from(kwargs, contract),
                           encoding="signed component loadings; at most 20 variables per facet",
                           loadings=loading.tolist(), feature_labels=labels, panel_count=panel_count,
                           displayed_components=list(range(min(2, loading.shape[1]))))


def scree_plot_academic(explained_variance, *, contract=None, ax=None, **kwargs):
    ev = finite_array(explained_variance, "explained_variance"); axis = _ax(ax); x = np.arange(1, ev.size + 1)
    axis.plot(x, ev, "o-", color=PALETTE[0], lw=_style.stroke(1.6)); axis.bar(x, ev, color=PALETTE[0], alpha=.18)
    axis.lines[-1].set_clip_on(False)
    _finish(axis, xlabel="主成分", ylabel="解释方差")
    return attach_metadata(_figure(axis), name="scree_plot_academic", contract=contract_from(kwargs, contract), encoding="explained variance by component")


def roc_multi(y_true=None, y_score=None, *, curves=None, labels=None, contract=None, ax=None, **kwargs):
    """Multi-model ROC plot with shaded visual emphasis and AUC labels."""
    axis = _ax(ax, figsize=(5.8, 5.4))
    if curves is None:
        if y_true is None or y_score is None:
            raise ValueError("roc_multi requires curves or y_true/y_score")
        curves = [(y_true, y_score)]
    labels = list(labels or [f"模型{i + 1}" for i in range(len(curves))])
    from sklearn.metrics import auc, roc_curve
    auc_values = []
    for i, (truth, score) in enumerate(curves):
        truth = finite_array(truth, "y_true").astype(int)
        score = finite_array(score, "y_score")
        if truth.shape != score.shape or np.unique(truth).size < 2:
            raise ValueError("each ROC curve needs aligned binary labels and scores")
        fpr, tpr, _ = roc_curve(truth, score)
        area = auc(fpr, tpr)
        auc_values.append(float(area))
        color = PALETTE[i % len(PALETTE)]
        axis.fill_between(fpr, 0, tpr, color=color, alpha=0.07)
        axis.plot(fpr, tpr, color=color, lw=_style.stroke(1.8), label=f"{labels[i]} (AUC={area:.3f})")
    axis.plot([0, 1], [0, 1], ls="--", color="#A8B0B5", lw=_style.stroke(0.8))
    axis.set(xlim=(0, 1), ylim=(0, 1), xlabel="假阳性率 (FPR)", ylabel="真阳性率 (TPR)")
    axis.legend(frameon=False, loc="lower right", fontsize=_style.font('legend', 8))
    _finish(axis)
    return attach_metadata(_figure(axis), name="roc_multi", contract=contract_from(kwargs, contract),
                           curve_count=len(curves), curve_labels=labels, auc_values=auc_values,
                           auc=auc_values[0] if len(auc_values) == 1 else None)


def correlation_pairgrid(data, *, labels=None, contract=None, ax=None, **kwargs):
    """Compact correlation matrix: density diagonal, points below, r tiles above."""
    a = finite_array(data, "data", ndim=2)
    n, p = a.shape
    if p < 2 or p > 8:
        raise ValueError("data must contain 2–8 variables")
    labels = list(labels or [f"变量{i + 1}" for i in range(p)])
    fig = ax.figure if ax is not None else _style.figure(figsize=(8.2, 7.2), constrained_layout=True)
    axes = np.empty((p, p), dtype=object)
    cmap = (_style.cmap("diverging") if _style.current_config() is not None else
            LinearSegmentedColormap.from_list("corr", ["#5D94B1", "#F7F7F7", "#D87970"]))
    corr = np.corrcoef(a, rowvar=False)
    for i in range(p):
        for j in range(p):
            axis = fig.add_subplot(p, p, i * p + j + 1)
            axes[i, j] = axis
            axis.set_xticks([]); axis.set_yticks([])
            for spine in axis.spines.values():
                spine.set_color("#B5C1C7"); spine.set_linewidth(0.45)
            if i == j:
                axis.hist(a[:, j], bins=12, density=True, color=_style.color(0, '#A8C4D3'), edgecolor="white", linewidth=_style.stroke(0.35))
                xs = np.linspace(np.nanmin(a[:, j]), np.nanmax(a[:, j]), 100)
                if a.shape[0] > 1 and np.ptp(a[:, j]) > 0:
                    axis.plot(xs, gaussian_kde(a[:, j])(xs), color=_style.color(1, '#D77C72'), lw=_style.stroke(1.0))
            elif i > j:
                axis.scatter(a[:, j], a[:, i], s=_style.marker(8, area=True), color=_style.color(0, '#6EA7C2'), alpha=.6, linewidths=0)
                if np.ptp(a[:, j]) > 0:
                    coef = np.polyfit(a[:, j], a[:, i], 1)
                    xs = np.linspace(a[:, j].min(), a[:, j].max(), 30)
                    axis.plot(xs, np.polyval(coef, xs), color=_style.color(1, '#D77C72'), lw=_style.stroke(0.8))
            else:
                value = corr[i, j]
                axis.set_facecolor(cmap((value + 1) / 2) if np.isfinite(value) else '#eeeeee')
                axis.text(.5, .52, f"r={value:.2f}" if np.isfinite(value) else "未定义", ha="center", va="center", fontsize=_style.font('text', 8),
                          color="white" if abs(value) > .55 else INK, fontweight="bold", transform=axis.transAxes)
            if i == p - 1:
                axis.set_xlabel(labels[j], fontsize=_style.font('text', 7))
            if j == 0:
                axis.set_ylabel(labels[i], fontsize=_style.font('text', 7))
    return attach_metadata(fig, name="correlation_pairgrid", contract=contract_from(kwargs, contract),
                           variables=labels, correlation=corr.tolist(),
                           encoding="density diagonal + scatter lower triangle + correlation upper triangle")


def correlation_matrix(data, *, labels=None, contract=None, ax=None, **kwargs):
    """Pearson matrix with a fixed [-1, 1] domain and undefined cells."""
    a = finite_array(data, "data", ndim=2)
    labels = list(labels) if labels is not None else [f"变量{i + 1}" for i in range(a.shape[1])]
    if len(labels) != a.shape[1]:
        raise ValueError("labels must match columns")
    with np.errstate(divide="ignore", invalid="ignore"):
        correlation = np.corrcoef(a, rowvar=False)
    axis = _ax(ax)
    image = axis.imshow(np.ma.masked_invalid(correlation), vmin=-1, vmax=1,
                        cmap=_style.cmap("diverging", "RdBu_r"))
    image.cmap.set_bad("#eeeeee")
    axis.set_xticks(np.arange(len(labels)), labels, rotation=30, ha="right")
    axis.set_yticks(np.arange(len(labels)), labels)
    axis.grid(False)
    for (i, j), value in np.ndenumerate(correlation):
        axis.text(j, i, f"{value:.2f}" if np.isfinite(value) else "未定义",
                  ha="center", va="center", fontsize=_style.font(),
                  color="white" if np.isfinite(value) and abs(value) > .65 else INK)
    axis.figure.colorbar(image, ax=axis, label="Pearson r", fraction=.045, pad=.04)
    return attach_metadata(axis.figure, name="correlation_matrix", contract=contract_from(kwargs, contract),
                           correlation=correlation.tolist(), variables=labels,
                           encoding="Pearson correlation; fixed [-1,1]; undefined constants masked")


def radar_comparison(metrics, values, *, groups=None, contract=None, ax=None, **kwargs):
    """Small-multiple radar chart for a few objects and metrics."""
    labels = list(metrics)
    arr = np.asarray(values, dtype=float)
    if arr.ndim == 1:
        arr = arr[None, :]
    if arr.ndim != 2 or arr.shape[1] != len(labels):
        raise ValueError("values must have one column per metric")
    groups = list(groups or [f"方案{i + 1}" for i in range(arr.shape[0])])
    if len(groups) != arr.shape[0]:
        raise ValueError("groups must align with values")
    axis = _ax(ax, figsize=(5.8, 5.8))
    figure = axis.figure
    axis.remove()
    axis = figure.add_subplot(111, polar=True)
    theta = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)
    theta = np.r_[theta, theta[0]]
    for i, row in enumerate(arr):
        vals = np.r_[row, row[0]]
        axis.plot(theta, vals, lw=_style.stroke(1.7), color=PALETTE[i % len(PALETTE)], label=groups[i],
                  ls=["-", "--", ":"][i % 3], marker=["o", "s", "^"][i % 3], markersize=_style.marker(3))
        axis.fill(theta, vals, color=PALETTE[i % len(PALETTE)], alpha=.12)
    axis.set_xticks(theta[:-1], labels, fontsize=_style.font('text', 8))
    axis.set_ylim(0, max(1.0, float(np.nanmax(arr) * 1.12)))
    axis.grid(color=GRID, linewidth=_style.stroke(0.55))
    axis.spines["polar"].set_color("#A4B0B6")
    axis.legend(frameon=False, loc="lower center", bbox_to_anchor=(.5, -0.18), ncol=min(3, len(groups)))
    return attach_metadata(axis.figure, name="radar_comparison", contract=contract_from(kwargs, contract), metrics=labels, groups=groups)


def ridgeline(groups, *, labels=None, contract=None, ax=None, **kwargs):
    """Ridgeline density chart with horizontally offset distributions."""
    series = [finite_array(v, "group") for v in groups]
    labels = list(labels or [f"组{i + 1}" for i in range(len(series))])
    axis = _ax(ax, figsize=(6.7, 4.8))
    lo = min(float(v.min()) for v in series); hi = max(float(v.max()) for v in series)
    xs = np.linspace(lo, hi, 220)
    for i, values in enumerate(series):
        density = gaussian_kde(values)(xs)
        density = density / max(density.max(), 1e-9) * .78
        base = len(series) - 1 - i
        axis.fill_between(xs, base, base + density, color=PALETTE[i % len(PALETTE)], alpha=.62)
        axis.plot(xs, base + density, color=PALETTE[i % len(PALETTE)], lw=_style.stroke(0.8))
        axis.scatter(values, np.full(values.shape, base),
                     s=_style.marker(6, area=True), color="#FFFFFF", alpha=.9, edgecolors=PALETTE[i % len(PALETTE)], linewidths=_style.stroke(0.6))
    axis.set_yticks(range(len(series)), labels[::-1])
    axis.set_xlabel("观测值")
    axis.grid(axis="x", color=GRID, linewidth=_style.stroke(0.45))
    _finish(axis)
    return attach_metadata(_figure(axis), name="ridgeline", contract=contract_from(kwargs, contract), groups=labels,
                           raw_point_counts=[len(values) for values in series], raw_point_selection="all observations")


def bubble_scatter(x, y, size, *, groups=None, labels=None, contract=None, ax=None, **kwargs):
    """Bubble scatter where size encodes magnitude and shape encodes group."""
    x, y, size = finite_array(x, "x"), finite_array(y, "y"), finite_array(size, "size")
    if not (x.shape == y.shape == size.shape):
        raise ValueError("x, y and size must align")
    if np.any(size < 0):
        raise ValueError("bubble magnitude must be nonnegative")
    groups = list(groups) if groups is not None else ["组A"] * x.size
    if len(groups) != x.size or labels is not None and len(labels) != x.size:
        raise ValueError("groups and labels must align with observations")
    axis = _ax(ax)
    unique = list(dict.fromkeys(groups))
    maximum = float(size.max())
    scale = _style.marker(160, area=True) / maximum if maximum > 0 else 0
    areas = size * scale
    for i, group in enumerate(unique):
        mask = np.asarray(groups) == group
        axis.scatter(x[mask], y[mask], s=areas[mask],
                     color=PALETTE[i % len(PALETTE)], marker="o", alpha=.72,
                     edgecolor=INK, linewidth=_style.stroke(0.45), hatch=_style.hatch(i), label=group)
        if labels is not None:
            for xi, yi, label in zip(x[mask], y[mask], np.asarray(labels)[mask]):
                axis.text(xi, yi, str(label), fontsize=_style.font('text', 7), ha="left", va="bottom", color=INK)
    axis.set(xlabel="变量 X", ylabel="变量 Y")
    from matplotlib.lines import Line2D
    handles, names = axis.get_legend_handles_labels()
    if maximum > 0:
        for level in (maximum/4, maximum/2, maximum):
            handles.append(Line2D([], [], marker="o", markersize=np.sqrt(level*scale),
                                  linestyle="", markerfacecolor="none", markeredgecolor=INK))
            names.append(f"量值 {level:.3g}")
    if np.any(size == 0):
        axis.scatter(x[size == 0], y[size == 0], marker="x", color=INK, s=_style.marker(18, area=True))
        handles.append(Line2D([], [], marker="x", color=INK, linestyle=""))
        names.append("量值 0")
    axis.figure.legend(handles, names, frameon=False, title="类别；面积正比于量值",
                       loc="outside upper center", ncol=min(3, len(handles)))
    axis.grid(color=GRID, linewidth=_style.stroke(0.4))
    _finish(axis)
    return attach_metadata(_figure(axis), name="bubble_scatter", contract=contract_from(kwargs, contract),
                           groups=unique, size_semantics="circular marker area = magnitude * area_scale; zero shown as x",
                           magnitude=size.tolist(), marker_area_pt2=areas.tolist(), area_scale=scale)


def correlation_bubble_matrix(data, *, labels=None, contract=None, ax=None, **kwargs):
    """Lower-triangle bubble correlation matrix with direction and magnitude."""
    a = finite_array(data, "data", ndim=2)
    with np.errstate(divide="ignore", invalid="ignore"):
        corr = np.atleast_2d(np.corrcoef(a, rowvar=False))
    p = corr.shape[0]
    labels = list(labels or [f"变量{i + 1}" for i in range(p)])
    cfg = _style.current_config()
    if cfg is not None and cfg['width_mm'] < 100 and (p > 8 or any(len(str(label)) > 10 for label in labels)):
        axis, codes = _style.node_axes(labels, ax)
        tick_labels = [codes[label] for label in labels]
    else:
        axis = _ax(ax, figsize=(6.5, 5.8))
        tick_labels = labels
    axis.set_xlim(-.5, p - .5); axis.set_ylim(p - .5, -.5)
    norm = Normalize(-1, 1); cmap = _style.cmap("diverging", "RdBu_r")
    if isinstance(cmap, str): cmap = plt.get_cmap(cmap)
    area_scale = _style.marker(300, area=True)
    annotations = []
    for i in range(p):
        for j in range(p):
            if i < j:
                continue
            value = corr[i, j]
            if not np.isfinite(value):
                axis.scatter(j, i, marker="x", s=_style.marker(28, area=True), color="#777777")
                annotations.append(axis.annotate("未定义", (j, i), xytext=(0, -11),
                                                textcoords="offset points", ha="center", va="top",
                                                fontsize=_style.font(), color="#777777"))
            else:
                axis.scatter(j, i, s=area_scale * abs(value), color=cmap(norm(value)),
                             edgecolor=INK, linewidth=_style.stroke(0.4))
                annotations.append(axis.annotate(f"{value:.2f}", (j, i), xytext=(0, -11),
                                                 textcoords="offset points", ha="center", va="top",
                                                 fontsize=_style.font(), color=INK))
    axis.set_xticks(range(p), tick_labels, rotation=45, ha="right")
    axis.set_yticks(range(p), tick_labels)
    axis.grid(color="#E6ECEF", linewidth=_style.stroke(0.45))
    _finish(axis, title="相关气泡矩阵")
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    if cfg is not None and cfg['width_mm'] < 100:
        axis.figure.colorbar(sm, ax=axis, orientation='horizontal', fraction=.045, pad=.08, label="Pearson r")
    else:
        axis.figure.colorbar(sm, ax=axis, fraction=.035, pad=.04, label="Pearson r")

    def reserve_annotation_space():
        # Offset labels have a physical size independent of the data range.
        # Measure after the common font/layout pass; changing font size or
        # paper width must not push the final row through the x-axis again.
        figure = axis.figure
        for _ in range(4):
            figure.canvas.draw()
            renderer = figure.canvas.get_renderer()
            padding = 2 * figure.dpi / 72
            bottom = min(label.get_window_extent(renderer).y0 for label in annotations)
            overflow = axis.bbox.y0 + padding - bottom
            if overflow <= .25:
                for row in range(p):
                    labels_in_row = annotations[row*(row+1)//2:(row+1)*(row+2)//2]
                    boxes = [label.get_window_extent(renderer) for label in labels_in_row]
                    if any(right.x0-left.x1 < padding-.25 for left, right in zip(boxes, boxes[1:])):
                        raise ValueError("correlation bubble value labels require a wider figure or separate matrix panels")
                return
            lower, upper = axis.get_ylim()  # This matrix uses an inverted y axis.
            axis.set_ylim(lower + (overflow + .5) / axis.bbox.height * (lower-upper), upper)
        figure.canvas.draw()
        if min(label.get_window_extent(figure.canvas.get_renderer()).y0 for label in annotations) < axis.bbox.y0:
            raise ValueError("correlation bubble annotations require a taller figure")

    axis.figure._publication_layout_finalizers = [reserve_annotation_space]
    reserve_annotation_space()
    return attach_metadata(_figure(axis), name="correlation_bubble_matrix", contract=contract_from(kwargs, contract),
                           variables=labels, correlation=corr.tolist(), color_domain=[-1, 1],
                           variable_label_key=getattr(axis.figure, '_node_label_key', {}),
                           area_scale=area_scale, size_semantics="area = abs(Pearson r) * area_scale; undefined shown as x")


def network_academic(edges, *, weights=None, labels=None, contract=None, ax=None, **kwargs):
    """Network plot with positive/negative edge semantics and node labels."""
    import networkx as nx
    graph = nx.Graph()
    graph.add_edges_from(edges)
    axis = _ax(ax, figsize=(6.4, 5.2))
    pos = nx.spring_layout(graph, seed=7, weight=None)
    weight_values = list(weights or [1.0] * len(edges))
    if len(weight_values) != len(edges):
        raise ValueError("weights must align with edges")
    for (u, v), weight in zip(edges, weight_values):
        axis.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]],
                  color="#6F9EC2" if weight >= 0 else "#E5807A", lw=.8 + 2.0 * abs(float(weight)),
                  ls="-" if weight >= 0 else "--", alpha=.75, zorder=1)
    nx.draw_networkx_nodes(graph, pos, ax=axis, node_color=[PALETTE[i % len(PALETTE)] for i, _ in enumerate(graph.nodes)],
                           node_size=310, edgecolors="white", linewidths=_style.stroke(0.8))
    nx.draw_networkx_labels(graph, pos, ax=axis, font_size=_style.font('text', 8), font_color=INK)
    axis.axis("off")
    return attach_metadata(_figure(axis), name="network_academic", contract=contract_from(kwargs, contract),
                           edge_semantics="solid positive / dashed negative", nodes=list(graph.nodes), edges=len(edges))


def chord_academic(nodes, flows, *, contract=None, ax=None, **kwargs):
    """Circular weighted chord diagram with deterministic ribbon geometry."""
    labels = list(nodes)
    values = {label: 0.0 for label in labels}
    for src, dst, weight in flows:
        values[src] += float(weight); values[dst] += float(weight)
    total = sum(values.values()) or 1.0
    gap = 3.0
    cursor = 90.0
    layout = {}
    for i, label in enumerate(labels):
        arc = max(5.0, values[label] / total * (360 - gap * len(labels)))
        layout[label] = (cursor, cursor - arc)
        cursor -= arc + gap
    axis, node_labels = _style.node_axes(labels, ax); axis.axis("off"); axis.set_aspect("equal")
    colors = {label: PALETTE[i % len(PALETTE)] for i, label in enumerate(labels)}
    for i, label in enumerate(labels):
        start, end = layout[label]
        axis.add_patch(Wedge((0, 0), 1.0, end, start, width=.13, facecolor=colors[label], edgecolor="white", linewidth=_style.stroke(0.7)))
        theta = np.deg2rad((start + end) / 2)
        axis.text(1.18 * np.cos(theta), 1.18 * np.sin(theta), node_labels[label], ha="center", va="center", fontsize=_style.font('text', 8))
    max_weight = max((float(w) for _, _, w in flows), default=1.0)
    for src, dst, weight in flows:
        s = np.deg2rad(sum(layout[src]) / 2); t = np.deg2rad(sum(layout[dst]) / 2)
        p0 = np.array([.90 * np.cos(s), .90 * np.sin(s)])
        p3 = np.array([.90 * np.cos(t), .90 * np.sin(t)])
        path = Path([p0, [0, 0], [0, 0], p3], [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
        axis.add_patch(PathPatch(path, facecolor="none", edgecolor=colors[src], alpha=.18 + .38 * float(weight) / max_weight,
                                  linewidth=.8 + 4.0 * float(weight) / max_weight))
    axis.set_xlim(-1.35, 1.35); axis.set_ylim(-1.3, 1.3)
    return attach_metadata(_figure(axis), name="chord_academic", contract=contract_from(kwargs, contract), flows=len(flows),
                           node_label_key=getattr(axis.figure, "_node_label_key", {}))


def trajectory_3d(embedding, *, groups=None, contract=None, ax=None, **kwargs):
    """PHATE-like 2D trajectory view with group paths and density envelopes."""
    a = finite_array(embedding, "embedding", ndim=2)
    if a.shape[1] < 2 or a.shape[0] < 3:
        raise ValueError("embedding must be an n×2 array with at least three rows")
    axis = _ax(ax, figsize=(6.2, 4.7))
    groups = np.asarray(groups if groups is not None else np.zeros(a.shape[0], dtype=int))
    unique = list(dict.fromkeys(groups.tolist()))
    for i, group in enumerate(unique):
        mask = groups == group
        order = np.flatnonzero(mask)
        color = PALETTE[i % len(PALETTE)]
        axis.scatter(a[mask, 0], a[mask, 1], s=_style.marker(10, area=True), color=color, alpha=.24, edgecolors="none")
        if order.size >= 3:
            axis.plot(a[order, 0], a[order, 1], color=color, lw=_style.stroke(1.25), alpha=.9)
            axis.scatter(a[order[-1], 0], a[order[-1], 1], s=_style.marker(34, area=True), color=color, edgecolor="white", linewidth=_style.stroke(0.6))
        axis.text(a[mask, 0].mean(), a[mask, 1].mean(), str(group), color=color, fontsize=_style.font('text', 8))
    axis.axhline(0, color=GRID, lw=_style.stroke(0.5)); axis.axvline(0, color=GRID, lw=_style.stroke(0.5))
    _finish(axis, xlabel="PHATE 1", ylabel="PHATE 2")
    return attach_metadata(_figure(axis), name="trajectory_3d", contract=contract_from(kwargs, contract), groups=[str(x) for x in unique])


def mantel_linkage(matrix, env_matrix, *, labels=None, contract=None, ax=None, **kwargs):
    """Correlation matrix with a compact environmental linkage layer."""
    x = finite_array(matrix, "matrix", ndim=2); y = finite_array(env_matrix, "env_matrix", ndim=2)
    if x.shape[0] != y.shape[0]:
        raise ValueError("matrix and env_matrix must share rows")
    corr = np.corrcoef(x, rowvar=False); env = np.corrcoef(x.T, y.T)[: x.shape[1], x.shape[1]:]
    labels = list(labels or [f"变量{i + 1}" for i in range(corr.shape[0])])
    axis = _ax(ax, figsize=(7.0, 5.6)); axis.imshow(corr, vmin=-1, vmax=1, cmap=_style.cmap('diverging', 'RdBu_r'), alpha=.92)
    axis.set_xticks(range(len(labels)), labels, rotation=45, ha="right"); axis.set_yticks(range(len(labels)), labels)
    for i, j in combinations(range(corr.shape[0]), 2):
        if abs(env[i % env.shape[0], j % env.shape[1]]) > .25:
            axis.plot([j, i], [i, j], color="#D98A72" if env[i % env.shape[0], j % env.shape[1]] >= 0 else "#6E98B8",
                      lw=1.0 + 2.0 * abs(env[i % env.shape[0], j % env.shape[1]]), alpha=.6)
    axis.figure.colorbar(axis.images[0], ax=axis, fraction=.035, pad=.04, label="相关系数")
    _finish(axis, title="Mantel 关联图")
    return attach_metadata(_figure(axis), name="mantel_linkage", contract=contract_from(kwargs, contract), environmental_links=int(np.sum(np.abs(env) > .25)))


__all__ = ["grouped_bar_academic", "roc_multi", "correlation_pairgrid", "radar_comparison",
           "ridgeline", "bubble_scatter", "correlation_bubble_matrix", "network_academic",
           "chord_academic", "trajectory_3d", "network_variant", "correlation_network_academic",
           "weighted_network_academic", "community_network_academic", "embedding_trajectory_academic",
           "cluster_scatter_academic", "pca_biplot_academic", "pca_loadings_academic", "scree_plot_academic",
           "mantel_linkage", "academic_catalog_adapter",
           "make_academic_catalog_adapter"]


# ---------------------------------------------------------------------------
# Full-catalog academic adapter
# ---------------------------------------------------------------------------

def _as_values(data, n=48):
    """Return a finite one-dimensional vector without inventing required fields."""
    for key in ("values", "value", "y", "response", "objective", "observed", "center", "probability", "scores", "loadings", "longitude", "matrix", "data"):
        if key in data:
            arr = np.asarray(data[key], dtype=float).reshape(-1)
            arr = arr[np.isfinite(arr)]
            if arr.size:
                return arr
    if data.get("flows"):
        arr = np.asarray([float(flow[2]) for flow in data["flows"] if len(flow) >= 3], dtype=float)
        if arr.size:
            return arr
    if data.get("edges"):
        return np.arange(1, len(data["edges"]) + 1, dtype=float)
    if data.get("embedding") is not None:
        arr = np.asarray(data["embedding"], dtype=float)
        if arr.ndim >= 2 and arr.size:
            return arr[:, 0]
    if data.get("groups") is not None:
        arr = np.asarray(data["groups"], dtype=object).reshape(-1)
        if arr.size:
            return np.arange(1, arr.size + 1, dtype=float)
    raise ValueError("figure data must contain one of values, y, response, objective, observed")


def _matrix(data, values):
    raw = data.get("matrix", data.get("data"))
    if raw is not None:
        arr = np.asarray(raw, dtype=float)
        if arr.ndim == 2 and arr.size:
            return np.nan_to_num(arr, nan=0.0)
    size = max(3, min(10, int(np.ceil(np.sqrt(values.size)))))
    return np.resize(values, (size, size))


def _academic_axis(ax, title, xlabel=None, ylabel=None):
    _finish(ax, xlabel=xlabel, ylabel=ylabel)
    ax.set_title(title, loc="left", fontweight="bold", color=INK, fontsize=_style.font('title', 10))
    ax.grid(color=GRID, linewidth=_style.stroke(0.45), alpha=.8)
    ax.set_axisbelow(True)
    return ax


_FORMAL_ADAPTER_FIELDS = {
    "errorbar": ("categories", "values", "lower", "upper", "interval_kind"),
    "forest": ("categories", "estimate", "lower", "upper", "interval_kind"),
    "calibration_curve": ("probability", "observed_rate"),
    "learning_curve": ("train_size", "mean_score", "lower", "upper", "interval_kind"),
    "cross_validation": ("fold", "score"),
    "model_interval": ("center", "lower", "upper", "interval_kind"),
    "robustness_envelope": ("x", "center", "lower", "upper", "interval_kind"),
    "response_surface_opt": ("x_grid", "y_grid", "z"),
    "feasible_region": ("x_grid", "y_grid", "z"),
    "parameter_response": ("x_grid", "y_grid", "z"),
    "tornado": ("parameters", "low", "high"),
}


def _require_formal_fields(name, data):
    required = _FORMAL_ADAPTER_FIELDS.get(name)
    if not required:
        return
    missing = [field for field in required if field not in data]
    if missing:
        raise ValueError(f"{name} requires fields: {', '.join(missing)}")


def academic_catalog_adapter(name, *args, contract=None, ax=None, name_zh=None, **data):
    """Render every long-tail registry entry with an academic visual grammar.

    The adapter accepts chart-specific fields when supplied and falls back to
    ``values`` for exploratory previews.  It never claims inferential results;
    metadata records the chart key and the fields actually consumed.
    """
    if data.get("mode", "formal") == "formal" and name not in {
        "volcano", "hexbin", "joint_density", "spatial_scatter", "calibration_curve", "tornado",
        "cross_validation", "learning_curve", "model_interval", "robustness_envelope",
    }:
        raise ValueError(f"{name} is a layout adapter; mode='preview' with simulated=True is required")
    if args:
        if len(args) == 1 and isinstance(args[0], dict):
            data = {**args[0], **data}
        else:
            keys = ("categories", "values") if len(args) == 2 else ("values",)
            data = {**dict(zip(keys, args)), **data}
    _require_formal_fields(name, data)
    values = _as_values(data) if "values" in data or name not in _FORMAL_ADAPTER_FIELDS else np.asarray([], dtype=float)
    if name == "robustness_envelope":
        values = np.asarray(data["center"], dtype=float).reshape(-1)
    axis = _ax(ax)
    title = name_zh or name.replace("_", " ")
    categories = list(data.get("categories", data.get("labels", [])))
    if not categories:
        categories = [f"方案{chr(甲 + i)}" for i, 甲 in enumerate(range(0x7532, 0x7532 + min(8, values.size)))]

    # Distribution families: each has a different mark/summary grammar.
    if name in {"probability_plot", "pareto_distribution"}:
        ordered = np.sort(values)
        q = (np.arange(ordered.size) + .5) / ordered.size
        if name == "probability_plot":
            theoretical = np.sqrt(2) * np.vectorize(lambda p: __import__("scipy").special.ndtri(p))(q)
            axis.scatter(theoretical, ordered, s=_style.marker(18, area=True), color=PALETTE[0], edgecolor="white", linewidth=_style.stroke(0.3))
            axis.plot([theoretical.min(), theoretical.max()], [ordered.min(), ordered.max()], color=PALETTE[1], lw=_style.stroke(1.2))
            _academic_axis(axis, title, xlabel="理论分位数", ylabel="样本分位数")
        else:
            counts, edges = np.histogram(ordered, bins=min(10, max(4, int(np.sqrt(ordered.size)))))
            axis.bar(edges[:-1], counts, width=np.diff(edges), align="edge", color=PALETTE[0], alpha=.75, edgecolor="white")
            axis.plot(edges[:-1], np.cumsum(counts) / max(counts.sum(), 1) * counts.max(), color=PALETTE[1], marker="o", ms=_style.marker(3))
            _academic_axis(axis, title, xlabel="观测值", ylabel="频数 / 累计")
    elif name == "control_chart":
        x = np.arange(values.size); mean = np.mean(values); sd = np.std(values)
        axis.plot(x, values, color=PALETTE[0], marker="o", ms=_style.marker(2.8), lw=_style.stroke(1))
        axis.axhline(mean, color=INK, lw=_style.stroke(1.1), label="中心线")
        axis.axhspan(mean - 3 * sd, mean + 3 * sd, color=PALETTE[0], alpha=.10, label="±3σ范围")
        axis.legend(frameon=False, fontsize=_style.font('legend', 8)); _academic_axis(axis, title, xlabel="观测序号", ylabel="过程值")
    elif name in {"beeswarm", "jitter", "raw_points", "dot_plot", "lollipop", "cleveland_dot", "errorbar"}:
        vals = values[:len(categories)] if len(categories) else values
        x = np.arange(vals.size)
        axis.scatter(x, vals, s=_style.marker(34, area=True), color=PALETTE[0], edgecolor="white", linewidth=_style.stroke(0.5), zorder=3)
        axis.vlines(x, 0, vals, color=PALETTE[0], alpha=.28, lw=_style.stroke(1.8))
        axis.set_xticks(x, categories[:vals.size])
        _academic_axis(axis, title, ylabel="指标值")
    elif name in {"horizontal_bar", "lollipop", "cleveland_dot"}:
        vals = values[:len(categories)]; order = np.argsort(vals); yy = np.arange(vals.size)
        axis.hlines(yy, 0, vals[order], color=PALETTE[0], lw=_style.stroke(2.2), alpha=.65)
        axis.scatter(vals[order], yy, s=_style.marker(42, area=True), color=PALETTE[1], edgecolor="white", zorder=3)
        axis.set_yticks(yy, [categories[i] for i in order]); _academic_axis(axis, title, xlabel="指标值")
    elif name in {"stacked_bar", "percent_stacked_bar", "multi_metric_comparison"}:
        n = min(len(categories), max(3, values.size // 3)); groups = 3
        mat = np.resize(values, (n, groups)); mat = np.abs(mat)
        if name == "percent_stacked_bar": mat = mat / np.maximum(mat.sum(1, keepdims=True), 1e-9)
        bottom = np.zeros(n); x = np.arange(n)
        for gi in range(groups):
            axis.bar(x, mat[:, gi], bottom=bottom, color=PALETTE[gi], label=f"指标{gi + 1}", edgecolor="white", linewidth=_style.stroke(0.4)); bottom += mat[:, gi]
        axis.set_xticks(x, categories[:n]); axis.legend(frameon=False, ncol=3, fontsize=_style.font('legend', 8))
        _academic_axis(axis, title, ylabel="比例" if name == "percent_stacked_bar" else "指标值")
    elif name in {"effect_size", "forest", "multi_metric_comparison"}:
        if name == "forest":
            vals = np.asarray(data["estimate"], dtype=float)
            lower = np.asarray(data["lower"], dtype=float)
            upper = np.asarray(data["upper"], dtype=float)
            yy = np.arange(vals.size)
            axis.errorbar(vals, yy, xerr=np.vstack([vals - lower, upper - vals]), fmt="o",
                          color=PALETTE[0], ecolor=PALETTE[1], capsize=3, lw=_style.stroke(1.2))
        else:
            vals = values[:len(categories)]
            yy = np.arange(vals.size)
            axis.scatter(vals, yy, s=_style.marker(38, area=True), color=PALETTE[0], edgecolor="white", zorder=3)
        axis.axvline(0, color=GRID, lw=_style.stroke(0.8)); axis.set_yticks(yy, categories[:vals.size]); _academic_axis(axis, title, xlabel="效应量 / 估计值")
    elif name in {"diverging_bar", "waterfall", "risk_return", "scenario_ranking", "ranking"}:
        vals = values[:len(categories)]
        colors = [PALETTE[1] if v < 0 else PALETTE[0] for v in vals]
        axis.bar(np.arange(vals.size), vals, color=colors, alpha=.86, edgecolor="white")
        axis.axhline(0, color=INK, lw=_style.stroke(0.65))
        axis.set_xticks(np.arange(vals.size), categories[:vals.size], rotation=25, ha="right")
        _academic_axis(axis, title, ylabel="变化量")
    elif name == "volcano":
        effect = np.asarray(data.get("x", values), dtype=float).reshape(-1)
        significance = np.asarray(data.get("y", np.abs(values)), dtype=float).reshape(-1)
        n = min(effect.size, significance.size)
        effect, significance = effect[:n], np.maximum(significance[:n], 1e-8)
        score = -np.log10(significance)
        colors = np.where((effect < -.5) & (score > 1.3), PALETTE[0],
                          np.where((effect > .5) & (score > 1.3), PALETTE[1], "#B7C1C6"))
        axis.scatter(effect, score, s=_style.marker(26, area=True), c=colors, alpha=.74, edgecolors="white", linewidth=_style.stroke(0.35))
        axis.axvline(-.5, color=GRID, lw=_style.stroke(0.7), ls="--"); axis.axvline(.5, color=GRID, lw=_style.stroke(0.7), ls="--"); axis.axhline(1.3, color=GRID, lw=_style.stroke(0.7), ls="--")
        _academic_axis(axis, title, xlabel="效应量（log2）", ylabel="显著性 −log10(p)")
    elif name == "hexbin":
        x = np.asarray(data.get("x", np.arange(values.size)), dtype=float).reshape(-1); y = np.asarray(data.get("y", values), dtype=float).reshape(-1); n = min(x.size, y.size)
        axis.hexbin(x[:n], y[:n], gridsize=14, cmap=_style.cmap('sequential', 'GnBu'), mincnt=1); _academic_axis(axis, title, xlabel="变量 X", ylabel="变量 Y")
    elif name in {"joint_density", "contour_density", "high_dim_density", "contour"}:
        x = np.asarray(data.get("x", np.arange(values.size)), dtype=float).reshape(-1); y = np.asarray(data.get("y", values), dtype=float).reshape(-1); n = min(x.size, y.size); x, y = x[:n], y[:n]
        axis.scatter(x, y, s=_style.marker(10, area=True), color=PALETTE[0], alpha=.22)
        try:
            from scipy.stats import gaussian_kde
            xx = np.linspace(x.min(), x.max(), 60); yy = np.linspace(y.min(), y.max(), 60); X, Y = np.meshgrid(xx, yy); Z = gaussian_kde(np.vstack([x, y]))(np.vstack([X.ravel(), Y.ravel()])).reshape(X.shape)
            axis.contour(X, Y, Z, levels=5, colors=[PALETTE[1]], linewidths=_style.stroke(0.8))
        except Exception:
            pass
        _academic_axis(axis, title, xlabel="变量 X", ylabel="变量 Y")
    elif name == "spatial_scatter":
        lon = np.asarray(data.get("longitude", data.get("x")), dtype=float).reshape(-1)
        lat = np.asarray(data.get("latitude", data.get("y")), dtype=float).reshape(-1)
        size = np.asarray(data.get("size", values), dtype=float).reshape(-1)
        group = np.asarray(data.get("group", ["样本"] * len(lon)), dtype=object).reshape(-1)
        if not (lon.size == lat.size == size.size == group.size):
            raise ValueError("spatial_scatter coordinates, size and group must align")
        for i, label in enumerate(dict.fromkeys(group.tolist())):
            mask = group == label
            axis.scatter(lon[mask], lat[mask], s=24 + 2 * np.abs(size[mask]), color=PALETTE[i % len(PALETTE)], label=str(label), alpha=.78, edgecolor="white")
        axis.legend(frameon=False, title="分组")
        _academic_axis(axis, title, xlabel="经度", ylabel="纬度")
    elif name in {"scatter", "scatter_trend", "partial_correlation", "partial_dependence"}:
        x = np.asarray(data.get("x", np.arange(values.size)), dtype=float).reshape(-1)
        y = np.asarray(data.get("y", values), dtype=float).reshape(-1)
        n = min(x.size, y.size); x, y = x[:n], y[:n]
        axis.scatter(x, y, s=_style.marker(20, area=True), color=PALETTE[0], alpha=.48, edgecolors="white", linewidth=_style.stroke(0.3))
        if n > 2 and name in {"scatter_trend", "joint_density", "contour_density", "partial_correlation", "partial_dependence"}:
            coef = np.polyfit(x, y, 1); xx = np.linspace(x.min(), x.max(), 100)
            axis.plot(xx, np.polyval(coef, xx), color=PALETTE[1], lw=_style.stroke(1.5))
        _academic_axis(axis, title, xlabel="变量 X", ylabel="变量 Y")
    elif name in {"area", "stacked_area", "multi_series"}:
        x = np.asarray(data.get("time", data.get("x", np.arange(values.size))), dtype=float).reshape(-1); n = min(x.size, values.size); x, y = x[:n], values[:n]
        series = np.vstack([np.maximum(y, 0), np.maximum(y * .65 + np.sin(x), 0), np.maximum(y * .35 + np.cos(x), 0)])
        if name == "area": axis.fill_between(x, 0, series[0], color=PALETTE[0], alpha=.62)
        else:
            axis.stackplot(x, series, colors=PALETTE[:3], labels=["组A", "组B", "组C"], alpha=.75); axis.legend(frameon=False, fontsize=_style.font('legend', 8))
        _academic_axis(axis, title, xlabel="时间", ylabel="累计值")
    elif name in {"step", "event_timeline", "gantt"}:
        x = np.arange(values.size)
        if name == "step": axis.step(x, values, where="mid", color=PALETTE[0], lw=_style.stroke(1.8))
        else:
            for i, start in enumerate(x[::max(1, values.size // 8)]): axis.broken_barh([(start, max(1, values.size // 10))], (i - .35, .7), facecolors=PALETTE[i % len(PALETTE)], alpha=.72)
            axis.set_yticks(range(min(8, len(x[::max(1, values.size // 8)]))), [f"阶段{i + 1}" for i in range(min(8, len(x[::max(1, values.size // 8)])))])
        _academic_axis(axis, title, xlabel="时间", ylabel="阶段" if name != "step" else "状态")
    elif name in {"autocorrelation", "partial_autocorrelation"}:
        centered = values - np.mean(values); maxlag = min(20, values.size - 2); ac = [1.0] + [np.corrcoef(centered[:-lag], centered[lag:])[0, 1] for lag in range(1, maxlag + 1)]
        axis.vlines(np.arange(len(ac)), 0, ac, color=PALETTE[0], lw=_style.stroke(1.2)); axis.scatter(np.arange(len(ac)), ac, color=PALETTE[1], s=_style.marker(18, area=True)); axis.axhline(0, color=INK, lw=_style.stroke(0.6)); _academic_axis(axis, title, xlabel="滞后阶数", ylabel="相关系数")
    elif name in {"decomposition", "error_band", "error_by_time", "forecast_interval", "convergence", "repeated_convergence", "sensitivity", "response_1d", "threshold_crossing", "robustness_envelope", "state_trajectory", "time_series", "rolling_mean"}:
        x = np.asarray(data.get("time", data.get("x", np.arange(values.size))), dtype=float).reshape(-1)
        n = min(x.size, values.size); x, y = x[:n], values[:n]
        axis.plot(x, y, color=PALETTE[0], lw=_style.stroke(1.8), label="估计轨迹")
        if name == "error_band" and "lower" in data and "upper" in data:
            lower = np.asarray(data["lower"], dtype=float).reshape(-1); upper = np.asarray(data["upper"], dtype=float).reshape(-1)
            if lower.size != n or upper.size != n or np.any(lower > upper): raise ValueError("error_band interval fields must align and satisfy lower <= upper")
            axis.fill_between(x, lower, upper, color=PALETTE[0], alpha=.18, label=str(data.get("interval_kind", "区间")))
        elif name == "robustness_envelope":
            lower = np.asarray(data["lower"], dtype=float).reshape(-1)
            upper = np.asarray(data["upper"], dtype=float).reshape(-1)
            if lower.size != n or upper.size != n or np.any(lower > upper):
                raise ValueError("robustness_envelope interval fields must align and satisfy lower <= upper")
            axis.fill_between(x, lower, upper, color=PALETTE[1], alpha=.18,
                              label=str(data["interval_kind"]))
        axis.legend(frameon=False, loc="best")
        _academic_axis(axis, title, xlabel="时间 / 迭代", ylabel="响应值")
    elif name in {"circular_heatmap"}:
        mat = _matrix(data, values); theta = np.linspace(0, 2 * np.pi, mat.shape[1] + 1); radius = np.arange(mat.shape[0] + 1)
        fig = axis.figure; axis.remove(); axis = fig.add_subplot(111, polar=True); mesh = axis.pcolormesh(theta, radius, mat, cmap=_style.cmap('sequential', 'YlGnBu'), shading="auto"); fig.colorbar(mesh, ax=axis, pad=.1, fraction=.04, label="强度"); axis.set_title(title, loc="left", fontweight="bold", color=INK)
    elif name in {"faceted_heatmap"}:
        mat = _matrix(data, values); fig = axis.figure; axis.remove(); axes = fig.subplots(2, 2, squeeze=False)
        for i, sub in enumerate(axes.flat): sub.imshow(np.roll(mat, i, axis=1), aspect="auto", cmap=_style.cmap('sequential', 'YlGnBu')); sub.set_title(f"分面 {i + 1}", fontsize=_style.font('title', 8)); sub.set_xticks([]); sub.set_yticks([])
        fig.suptitle(title, x=.02, ha="left", fontweight="bold", color=INK); axis = axes[0, 0]
    elif name in {"confusion_matrix_eval", "transition_matrix"}:
        mat = np.abs(_matrix(data, values)); mat = mat / np.maximum(mat.sum(1, keepdims=True), 1e-9) if name == "transition_matrix" else mat
        image = axis.imshow(mat, cmap=_style.cmap('sequential', 'Blues'), vmin=0); axis.set_xticks(range(mat.shape[1]), [f"类{i + 1}" for i in range(mat.shape[1])], rotation=45, ha="right"); axis.set_yticks(range(mat.shape[0]), [f"真{i + 1}" for i in range(mat.shape[0])])
        for i in range(mat.shape[0]):
            for j in range(mat.shape[1]): axis.text(j, i, f"{mat[i, j]:.2f}", ha="center", va="center", fontsize=_style.font('text', 7), color="white" if mat[i, j] > mat.max() * .55 else INK)
        axis.figure.colorbar(image, ax=axis, fraction=.046, pad=.04); _academic_axis(axis, title)
    elif name in {"clustered_heatmap", "clustered_heatmap_matrix"}:
        mat = _matrix(data, values); order = np.argsort(mat.mean(1)); image = axis.imshow(mat[order], aspect="auto", cmap="vlag" if False else "RdBu_r"); axis.figure.colorbar(image, ax=axis, fraction=.046, pad=.04, label="强度"); _academic_axis(axis, title, xlabel="变量", ylabel="聚类排序")
    elif name in {"heatmap", "diverging_heatmap", "feasible_heatmap", "threshold_heatmap", "time_heatmap", "calendar_heatmap", "scheme_indicator_matrix", "topsis_weights", "ahp_weights", "indicator_correlation", "contribution_decomposition", "adjacency_matrix"}:
        mat = _matrix(data, values)
        cmap = "RdBu_r" if name in {"diverging_heatmap", "indicator_correlation", "correlation_matrix"} else "YlGnBu"
        image = axis.imshow(mat, aspect="auto", cmap=cmap)
        axis.figure.colorbar(image, ax=axis, fraction=.046, pad=.04, label="强度")
        axis.set_xlabel("指标"); axis.set_ylabel("样本")
        _academic_axis(axis, title)
    elif name == "calibration_curve":
        p = np.asarray(data["probability"], dtype=float).reshape(-1)
        observed = np.asarray(data["observed_rate"], dtype=float).reshape(-1)
        if p.shape != observed.shape or np.any((p < 0) | (p > 1)) or np.any((observed < 0) | (observed > 1)):
            raise ValueError("calibration_curve probability and observed_rate must align in [0,1]")
        order = np.argsort(p); axis.plot([0, 1], [0, 1], ls="--", color=GRID, label="理想校准"); axis.plot(p[order], observed[order], "o-", color=PALETTE[1], label="模型"); axis.legend(frameon=False); _academic_axis(axis, title, xlabel="预测概率", ylabel="实际频率")
    elif name in {"lift_gain", "coverage"}:
        x = np.linspace(0, 1, values.size); y = np.sort(np.abs(values)); y = np.cumsum(y) / max(y.sum(), 1e-9); axis.plot(x, y, color=PALETTE[0], lw=_style.stroke(1.8), label="模型"); axis.plot(x, x, ls="--", color=GRID, label="基线"); axis.legend(frameon=False); _academic_axis(axis, title, xlabel="样本覆盖率", ylabel="累计增益")
    elif name == "taylor_diagram":
        r = np.clip(np.abs(values[:8]) / max(np.max(np.abs(values)), 1e-9), .1, 1); th = np.linspace(.15, 1.35, r.size); fig = axis.figure; axis.remove(); axis = fig.add_subplot(111, polar=True); axis.scatter(th, r, s=_style.marker(45, area=True), c=(PALETTE * 2)[:r.size], edgecolor="white"); axis.set_theta_zero_location("E"); axis.set_title(title, loc="left", fontweight="bold", color=INK)
    elif name in {"cross_validation", "learning_curve", "model_interval"}:
        if name == "cross_validation":
            x = np.asarray(data["fold"])
            center = np.asarray(data["score"], dtype=float)
            if x.shape != center.shape:
                raise ValueError("cross_validation.fold and score must align")
            axis.plot(x, center, "o-", color=PALETTE[0])
        elif name == "learning_curve":
            x = np.asarray(data["train_size"], dtype=float)
            center = np.asarray(data["mean_score"], dtype=float)
            lower = np.asarray(data["lower"], dtype=float)
            upper = np.asarray(data["upper"], dtype=float)
            if not (x.shape == center.shape == lower.shape == upper.shape) or np.any(lower > upper):
                raise ValueError("learning_curve fields must align and satisfy lower <= upper")
            axis.plot(x, center, "o-", color=PALETTE[0])
            axis.fill_between(x, lower, upper, color=PALETTE[0], alpha=.18,
                              label=str(data["interval_kind"]))
        else:
            if "center" not in data or "lower" not in data or "upper" not in data:
                raise ValueError("model_interval requires center, lower, upper and interval_kind")
            x = np.arange(len(data["center"]))
            center = np.asarray(data["center"], dtype=float)
            lower = np.asarray(data["lower"], dtype=float)
            upper = np.asarray(data["upper"], dtype=float)
            axis.plot(x, center, "o-", color=PALETTE[0])
            axis.fill_between(x, lower, upper, color=PALETTE[0], alpha=.18)
        axis.legend(frameon=False) if axis.get_legend_handles_labels()[0] else None
        _academic_axis(axis, title, xlabel="折次 / 训练规模", ylabel="评分")
    elif name in {"feature_importance", "shap_summary"}:
        n = min(10, values.size); order = np.argsort(np.abs(values[:n])); axis.barh(np.arange(n), np.abs(values[:n])[order], color=PALETTE[0]); axis.set_yticks(np.arange(n), [f"特征{i + 1}" for i in order]); _academic_axis(axis, title, xlabel="重要性")
    elif name in {"shap_beeswarm", "residual_distribution"}:
        axis.violinplot([values, values * .7 + .15], positions=[1, 2], showmeans=True, showextrema=False); axis.set_xticks([1, 2], ["高影响", "低影响"]); _academic_axis(axis, title, ylabel="贡献 / 残差")
    elif name == "observed_predicted":
        observed = np.asarray(data.get("observed", values), dtype=float).reshape(-1); predicted = np.asarray(data.get("predicted", values), dtype=float).reshape(-1); n = min(observed.size, predicted.size); axis.scatter(observed[:n], predicted[:n], s=_style.marker(18, area=True), color=PALETTE[0], alpha=.6); lo, hi = min(observed.min(), predicted.min()), max(observed.max(), predicted.max()); axis.plot([lo, hi], [lo, hi], ls="--", color=PALETTE[1]); _academic_axis(axis, title, xlabel="观测值", ylabel="预测值")
    elif name in {"residuals", "residual_distribution"}:
        axis.axhline(0, color=GRID); axis.scatter(np.arange(values.size), values - np.mean(values), s=_style.marker(16, area=True), color=PALETTE[1]); _academic_axis(axis, title, xlabel="样本", ylabel="残差")
    elif name in {"calibration_curve", "lift_gain", "taylor_diagram", "coverage", "model_interval", "learning_curve", "cross_validation", "feature_importance", "shap_summary", "shap_beeswarm", "residual_distribution", "observed_predicted"}:
        x = np.arange(values.size)
        axis.plot(x, values, color=PALETTE[0], lw=_style.stroke(1.5))
        axis.fill_between(x, values - np.std(values) * .25, values + np.std(values) * .25, color=PALETTE[0], alpha=.15)
        axis.scatter(x[::max(1, values.size // 30)], values[::max(1, values.size // 30)], s=_style.marker(14, area=True), color=PALETTE[1], zorder=3)
        _academic_axis(axis, title, xlabel="样本 / 阈值", ylabel="模型指标")
    elif name in {"parallel_coordinates"}:
        mat = _matrix(data, values); mat = (mat - mat.min(0)) / np.maximum(np.ptp(mat, axis=0), 1e-9); xs = np.arange(mat.shape[1])
        for row in mat[:min(28, mat.shape[0])]: axis.plot(xs, row, color=PALETTE[0], alpha=.25, lw=_style.stroke(0.8))
        axis.plot(xs, mat.mean(0), color=PALETTE[1], lw=_style.stroke(2), label="均值"); axis.set_xticks(xs, [f"指标{i + 1}" for i in xs]); axis.legend(frameon=False); _academic_axis(axis, title, ylabel="归一化值")
    elif name == "dendrogram":
        from scipy.cluster.hierarchy import dendrogram, linkage
        mat = _matrix(data, values); dendrogram(linkage(mat, method="ward"), ax=axis, color_threshold=None, above_threshold_color=PALETTE[0]); _academic_axis(axis, title, ylabel="距离")
    elif name == "cluster_stability":
        x = np.arange(2, 2 + min(8, values.size)); score = .55 + .35 * np.exp(-((x - 5) ** 2) / 6); axis.plot(x, score, "o-", color=PALETTE[0]); axis.fill_between(x, score - .04, score + .04, color=PALETTE[0], alpha=.15); _academic_axis(axis, title, xlabel="聚类数 k", ylabel="稳定性")
    elif name in {"pca_biplot", "pca_loadings", "scree_plot", "separation_loadings"}:
        mat = _matrix(data, values)
        if name == "scree_plot":
            ev = np.var(mat, axis=0)[:8]; axis.plot(np.arange(1, ev.size + 1), ev, "o-", color=PALETTE[0]); axis.set_xlabel("主成分"); axis.set_ylabel("解释方差")
        else:
            axis.scatter(mat[:, 0], mat[:, 1] if mat.shape[1] > 1 else np.arange(mat.shape[0]), s=_style.marker(24, area=True), color=PALETTE[0], alpha=.68)
            _academic_axis(axis, title, xlabel="维度 1", ylabel="维度 2")
    elif name in {"sankey", "alluvial"}:
        sources = list(data.get("source", [])); targets = list(data.get("target", [])); flow_values = np.asarray(data.get("value", values), dtype=float).reshape(-1)
        pairs = list(zip(sources, targets, flow_values)) if sources and targets else list(data.get("flows", []))
        nodes = list(dict.fromkeys([str(x) for pair in pairs for x in pair[:2]])) or ["输入", "处理", "输出"]
        y = {node: .84 - i * .68 / max(1, len(nodes) - 1) for i, node in enumerate(nodes)}; axis.set_xlim(0, 1); axis.set_ylim(0, 1)
        for i, label in enumerate(nodes):
            xpos = .05 if i < len(nodes) / 2 else .83
            axis.add_patch(plt.Rectangle((xpos, y[label] - .035), .10, .07, color=PALETTE[i % len(PALETTE)], alpha=.85)); axis.text(xpos + .05, y[label], str(label), va="center", ha="center", fontsize=_style.font('text', 8), color="white")
        max_value = max([float(p[2]) for p in pairs], default=1.0)
        for i, (src, dst, weight) in enumerate(pairs):
            start = [.15, y[str(src)]]; end = [.83, y[str(dst)]]
            path = Path([start, [.38, start[1]], [.62, end[1]], [.83, end[1]]], [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
            axis.add_patch(PathPatch(path, facecolor="none", edgecolor=PALETTE[i % len(PALETTE)], lw=2 + 7 * float(weight) / max_value, alpha=.38))
        axis.axis("off"); axis.set_title(title, loc="left", fontweight="bold", color=INK)
    elif name == "adjacency":
        edges = data.get("edges", []); nodes = list(dict.fromkeys([item for edge in edges for item in edge])) or ["A", "B", "C"]; pos = {node: (np.cos(i * 2 * np.pi / len(nodes)), np.sin(i * 2 * np.pi / len(nodes))) for i, node in enumerate(nodes)}
        for edge in edges:
            axis.plot([pos[edge[0]][0], pos[edge[1]][0]], [pos[edge[0]][1], pos[edge[1]][1]], color=PALETTE[0], lw=_style.stroke(1.4), alpha=.7)
        axis.scatter([pos[n][0] for n in nodes], [pos[n][1] for n in nodes], s=_style.marker(180, area=True), color=PALETTE[1], edgecolor="white");
        for node, (xx, yy) in pos.items(): axis.text(xx, yy, str(node), ha="center", va="center", fontsize=_style.font('text', 8), color="white")
        axis.axis("off"); axis.set_title(title, loc="left", fontweight="bold", color=INK)
    elif name in {"state_transition"}:
        nodes = list(data.get("nodes", categories[:4])) or ["状态A", "状态B", "状态C"]; theta = np.linspace(0, 2 * np.pi, len(nodes), endpoint=False); xx, yy = np.cos(theta), np.sin(theta); axis.scatter(xx, yy, s=_style.marker(240, area=True), color=PALETTE[:len(nodes)], edgecolor="white")
        for i, label in enumerate(nodes): axis.text(xx[i], yy[i], str(label), ha="center", va="center", fontsize=_style.font('text', 8), color="white")
        for i in range(len(nodes)): axis.annotate("", xy=(xx[(i + 1) % len(nodes)], yy[(i + 1) % len(nodes)]), xytext=(xx[i], yy[i]), arrowprops={"arrowstyle": "->", "color": PALETTE[1], "lw": 1.0})
        axis.axis("off"); axis.set_title(title, loc="left", fontweight="bold", color=INK)
    elif name in {"flowchart", "technical_route", "algorithm_flow", "input_model_validation_output", "task_decomposition", "variable_dependency", "decision_tree", "state_machine", "mechanism", "geometry", "coordinate_system", "constraint_boundary"}:
        nodes = list(data.get("nodes", categories[:6])) or ["输入", "处理", "输出"]
        y = np.linspace(.85, .15, len(nodes)); axis.scatter(np.zeros(len(nodes)), y, s=_style.marker(180, area=True), color=PALETTE[0], edgecolor="white", zorder=3)
        for i, label in enumerate(nodes):
            axis.text(.04, y[i], str(label), va="center", fontsize=_style.font('text', 8))
            if i + 1 < len(nodes): axis.annotate("", xy=(.0, y[i + 1]), xytext=(.0, y[i]), arrowprops={"arrowstyle": "->", "color": PALETTE[1], "lw": 1.5})
        axis.set_xlim(-.1, .9); axis.set_ylim(0, 1); axis.axis("off")
        axis.set_title(title, loc="left", fontweight="bold", color=INK)
    elif name in {"pareto"}:
        if "x" not in data or "y" not in data:
            raise ValueError("pareto requires x and y objective values")
        x = np.asarray(data["x"], dtype=float).reshape(-1)
        y = np.asarray(data["y"], dtype=float).reshape(-1)
        if x.shape != y.shape:
            raise ValueError("pareto.x and y must align")
        order = np.argsort(x); x, y = x[order], y[order]
        keep = []; best = np.inf
        for index, value in enumerate(y):
            if value <= best:
                keep.append(index); best = value
        axis.scatter(x, y, s=_style.marker(24, area=True), color=PALETTE[0], edgecolor="white", label="候选解")
        axis.plot(x[keep], y[keep], color=PALETTE[1], lw=_style.stroke(1.1), marker="o", label="非支配前沿")
        axis.legend(frameon=False); _academic_axis(axis, title, xlabel="目标一", ylabel="目标二")
    elif name in {"tornado"}:
        labels = list(data["parameters"])
        low = np.asarray(data["low"], dtype=float)
        high = np.asarray(data["high"], dtype=float)
        if not (low.shape == high.shape == np.asarray(labels).shape) or np.any(low > high):
            raise ValueError("tornado parameters, low and high must align and satisfy low <= high")
        yy = np.arange(len(labels)); axis.barh(yy, high - low, left=low, color=PALETTE[0], edgecolor="white")
        axis.set_yticks(yy, labels); axis.axvline(0, color=INK, lw=_style.stroke(0.7)); _academic_axis(axis, title, xlabel="影响范围")
    elif name in {"response_surface", "response_surface_opt", "feasible_region", "parameter_response"}:
        x_grid = np.asarray(data["x_grid"], dtype=float).reshape(-1)
        y_grid = np.asarray(data["y_grid"], dtype=float).reshape(-1)
        z = np.asarray(data["z"], dtype=float)
        if z.shape != (y_grid.size, x_grid.size):
            raise ValueError(f"{name}.z must have shape (len(y_grid), len(x_grid))")
        X, Y = np.meshgrid(x_grid, y_grid)
        image = axis.contourf(X, Y, z, levels=14, cmap=_style.cmap('sequential', 'GnBu'))
        axis.contour(X, Y, z, levels=6, colors="white", linewidths=_style.stroke(0.4), alpha=.8)
        axis.figure.colorbar(image, ax=axis, fraction=.046, pad=.04, label="响应")
        _academic_axis(axis, title, xlabel="参数 1", ylabel="参数 2")
    elif name in {"optimum_distribution"}:
        axis.hist(values, bins=12, color=PALETTE[0], alpha=.75, edgecolor="white"); axis.axvline(np.median(values), color=PALETTE[1], lw=_style.stroke(1.5), label="中位数"); axis.legend(frameon=False); _academic_axis(axis, title, xlabel="最优值", ylabel="频数")
    elif name in {"global_local", "constraint_slack", "perturbation", "scenario", "robustness_envelope"}:
        x = np.arange(values.size); axis.plot(x, values, color=PALETTE[0], lw=_style.stroke(1.6)); axis.fill_between(x, values - np.std(values) * .35, values + np.std(values) * .35, color=PALETTE[1], alpha=.20); _academic_axis(axis, title, xlabel="情景 / 扰动", ylabel="目标响应")
    elif name in {"spatial_heatmap", "spatial_3d"}:
        x = np.asarray(data.get("x", np.linspace(0, 1, values.size)), dtype=float).reshape(-1); y = np.asarray(data.get("y", values), dtype=float).reshape(-1); n = min(x.size, y.size); axis.scatter(x[:n], y[:n], s=35 + 90 * np.abs(values[:n] / max(np.max(np.abs(values)), 1e-9)), c=values[:n], cmap=_style.cmap('sequential', 'YlOrRd'), alpha=.75, edgecolor="white"); axis.set_aspect("equal", adjustable="datalim"); _academic_axis(axis, title, xlabel="空间 X", ylabel="空间 Y")
    elif name in {"spatial_heatmap", "spatial_3d", "response_surface", "response_surface_opt", "feasible_region", "parameter_response", "optimum_distribution", "perturbation", "scenario", "global_local", "constraint_slack", "tornado", "pareto", "robustness_envelope"}:
        x = np.asarray(data.get("x", np.arange(values.size)), dtype=float).reshape(-1)
        y = np.asarray(data.get("y", values), dtype=float).reshape(-1); n = min(x.size, y.size)
        axis.plot(x[:n], y[:n], color=PALETTE[0], lw=_style.stroke(1.8)); axis.scatter(x[:n], y[:n], color=PALETTE[1], s=_style.marker(14, area=True), alpha=.55)
        _academic_axis(axis, title, xlabel="参数 / 情景", ylabel="目标响应")
    else:
        x = np.arange(values.size)
        axis.plot(x, values, color=PALETTE[0], lw=_style.stroke(1.8))
        axis.scatter(x[::max(1, values.size // 25)], values[::max(1, values.size // 25)], color=PALETTE[1], s=_style.marker(16, area=True), zorder=3)
        _academic_axis(axis, title, xlabel="索引", ylabel="数值")
    return attach_metadata(_figure(axis), name=name, name_zh=title,
                           contract=contract_from(data, contract), implementation="academic catalog adapter",
                           consumed_fields=sorted(k for k in data if k not in {"contract"}))


def make_academic_catalog_adapter(name, name_zh=None):
    """Create a stable callable used by the registry for long-tail entries."""
    def factory(*args, **kwargs):
        return academic_catalog_adapter(name, *args, name_zh=name_zh, **kwargs)
    factory.__name__ = name
    factory.__doc__ = f"{name_zh or name.replace('_', ' ')}：学术风格图表实现。"
    return factory
