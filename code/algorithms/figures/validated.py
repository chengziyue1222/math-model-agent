"""Render supplied statistics without manufacturing observations or intervals."""
from __future__ import annotations
from . import styles as _style

import numpy as np
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Rectangle

from .academic_style import PALETTE, _finish
from .base import attach_metadata, contract_from, finite_array


def interval_arrays(center, lower, upper, interval_kind):
    c, lo, hi = [finite_array(v, k) for v, k in
                 [(center, "center"), (lower, "lower"), (upper, "upper")]]
    if not (c.shape == lo.shape == hi.shape) or np.any(lo > c) or np.any(c > hi):
        raise ValueError("lower <= center <= upper must hold with equal 1D shapes")
    if not interval_kind or not str(interval_kind).strip():
        raise ValueError("interval_kind must be non-empty")
    return c, lo, hi


def errorbar(categories, values, lower, upper, interval_kind, *, contract=None, ax=None, **kwargs):
    c, lo, hi = interval_arrays(values, lower, upper, interval_kind)
    if len(categories) != c.size:
        raise ValueError("categories must align with values")
    ax = ax or _style.subplots(constrained_layout=True)[1]
    ax.errorbar(np.arange(c.size), c, yerr=[c-lo, hi-c], fmt="o", capsize=3,
                color=PALETTE[0], label=str(interval_kind))
    ax.set_xticks(np.arange(c.size), categories)
    ax.legend(frameon=False)
    _finish(ax, ylabel=kwargs.get("units", "估计值"))
    return attach_metadata(ax.figure, name="errorbar", contract=contract_from(kwargs, contract),
                           estimate=c.tolist(), lower=lo.tolist(), upper=hi.tolist(), interval_kind=interval_kind)


def interval_band(x, center, lower, upper, interval_kind, *, contract=None, ax=None, name="robustness_envelope", **kwargs):
    c, lo, hi = interval_arrays(center, lower, upper, interval_kind)
    x = finite_array(x, "x")
    if x.shape != c.shape:
        raise ValueError("x must align with center")
    ax = ax or _style.subplots(constrained_layout=True)[1]
    ax.plot(x, c, color=PALETTE[0], label="中心值")
    ax.fill_between(x, lo, hi, color=PALETTE[0], alpha=.2, label=str(interval_kind))
    ax.legend(frameon=False)
    _finish(ax, xlabel=kwargs.get("xlabel", "参数 / 时间"), ylabel=kwargs.get("units", "响应值"))
    return attach_metadata(ax.figure, name=name, contract=contract_from(kwargs, contract),
                           center=c.tolist(), lower=lo.tolist(), upper=hi.tolist(), interval_kind=interval_kind)


def error_band(time, center, lower, upper, interval_kind, **kwargs):
    return interval_band(time, center, lower, upper, interval_kind, name="error_band", **kwargs)


def learning_curve(train_size, mean_score, lower, upper, interval_kind, **kwargs):
    return interval_band(train_size, mean_score, lower, upper, interval_kind,
                         name="learning_curve", xlabel="训练样本量", **kwargs)


def robustness_envelope(x, center, lower, upper, interval_kind, **kwargs):
    return interval_band(x, center, lower, upper, interval_kind, name="robustness_envelope", **kwargs)


def stacked_bar(categories, values, groups, *, contract=None, ax=None, **kwargs):
    a = finite_array(values, "values", ndim=2)
    if a.shape != (len(categories), len(groups)):
        raise ValueError("values must have shape (len(categories), len(groups))")
    if np.any(a < 0):
        raise ValueError("stacked_bar.values must be non-negative")
    ax = ax or _style.subplots(constrained_layout=True)[1]
    bottom = np.zeros(len(categories))
    hatches = ["", "//", "..", "xx", "\\\\", "++"]
    for i, label in enumerate(groups):
        ax.bar(np.arange(len(categories)), a[:, i], bottom=bottom, label=label,
               color=PALETTE[i % len(PALETTE)], hatch=hatches[i % len(hatches)], edgecolor="white")
        bottom += a[:, i]
    ax.set_xticks(np.arange(len(categories)), categories)
    ax.figure.legend(*ax.get_legend_handles_labels(), frameon=False,
                     loc="outside upper center", ncol=min(4, len(groups)))
    _finish(ax, ylabel=kwargs.get("units", "组成值"))
    return attach_metadata(ax.figure, name="stacked_bar", contract=contract_from(kwargs, contract),
                           values=a.tolist(), groups=list(groups))


def transition_matrix(matrix, *, contract=None, ax=None, **kwargs):
    a = finite_array(matrix, "matrix", ndim=2)
    if a.shape[0] != a.shape[1] or np.any(a < 0) or not np.allclose(a.sum(axis=1), 1):
        raise ValueError("transition_matrix.matrix must be square, non-negative with row sums of 1")
    ax = ax or _style.subplots(constrained_layout=True)[1]
    im = ax.imshow(a, cmap=_style.cmap('sequential', 'Blues'), vmin=0, vmax=1)
    ax.figure.colorbar(im, ax=ax, label="转移概率")
    for i, j in np.ndindex(a.shape):
        ax.text(j, i, f"{a[i,j]:.2f}", ha="center", va="center", color="white" if a[i,j] > .5 else "black")
    _finish(ax, xlabel="下一状态", ylabel="当前状态")
    ax.set_xticks(range(len(a)))
    ax.set_yticks(range(len(a)))
    ax.grid(False, which='both')
    return attach_metadata(ax.figure, name="transition_matrix", contract=contract_from(kwargs, contract), matrix=a.tolist())


def flow_diagram(source, target, value, *, source_stage=None, target_stage=None,
                 name="sankey", contract=None, ax=None, **kwargs):
    """Allocate node and ribbon thickness in the same units, preserving flows."""
    import networkx as nx
    vals = finite_array(value, "value")
    if len(source) != len(target) or len(source) != vals.size or np.any(vals < 0) or vals.sum() <= 0:
        raise ValueError("source, target, value must align; value must be non-negative with positive total")
    if name == "alluvial":
        if source_stage is None or target_stage is None:
            raise ValueError("alluvial requires source_stage and target_stage for state transitions")
        ss, ts = finite_array(source_stage, "source_stage"), finite_array(target_stage, "target_stage")
        if ss.shape != vals.shape or ts.shape != vals.shape or np.any(ss >= ts):
            raise ValueError("alluvial stages must align and satisfy source_stage < target_stage")
        src = [(float(stage), str(label)) for stage, label in zip(ss, source)]
        dst = [(float(stage), str(label)) for stage, label in zip(ts, target)]
        stages = {node: node[0] for node in src + dst}
    else:
        src, dst = list(map(str, source)), list(map(str, target))
        graph = nx.DiGraph(list(zip(src, dst)))
        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError("sankey requires an acyclic source/target graph")
        stages = {node: level for level, nodes in enumerate(nx.topological_generations(graph)) for node in nodes}
    nodes = list(dict.fromkeys(src + dst))
    inbound = {n: 0. for n in nodes}; outbound = {n: 0. for n in nodes}
    for s, t, v in zip(src, dst, vals):
        outbound[s] += v; inbound[t] += v
    levels = sorted(set(stages.values()))
    totals = [sum(max(inbound[n], outbound[n]) for n in nodes if stages[n] == level) for level in levels]
    scale = .7 / max(totals)
    positions = {}
    colors = {n: PALETTE[i % len(PALETTE)] for i,n in enumerate(nodes)}
    ax, node_labels = _style.node_axes(nodes, ax)
    for column, level in enumerate(levels):
        layer = [n for n in nodes if stages[n] == level]
        cursor = .92; gap = .10 / max(len(layer), 1)
        for n in layer:
            height = max(inbound[n], outbound[n]) * scale
            xpos = .08 + .78 * column / max(len(levels)-1, 1)
            positions[n] = (xpos, cursor-height, height)
            ax.add_patch(Rectangle((xpos, cursor-height), .025, height, color=colors[n]))
            label = node_labels[n]
            ax.text(xpos + .035, cursor-height/2, label, fontsize=_style.font('text', 7), va="center")
            cursor -= height + gap
    out_cursor = {n: positions[n][1] for n in nodes}; in_cursor = dict(out_cursor)
    for s, t, v in zip(src, dst, vals):
        x0 = positions[s][0] + .025; x1 = positions[t][0]
        y0, y1, thickness = out_cursor[s], in_cursor[t], v*scale
        mid = (x0+x1)/2
        vertices = [(x0,y0), (mid,y0), (mid,y1), (x1,y1), (x1,y1+thickness),
                    (mid,y1+thickness), (mid,y0+thickness), (x0,y0+thickness), (x0,y0)]
        codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.LINETO,
                 Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(vertices, codes), facecolor=colors[s], edgecolor="none", alpha=.35))
        out_cursor[s] += thickness; in_cursor[t] += thickness
    ax.set(xlim=(0, 1.08), ylim=(0,1)); ax.axis("off")
    ax.set_title("冲积图" if name == "alluvial" else "桑基图", loc="left")
    return attach_metadata(ax.figure, name=name, contract=contract_from(kwargs, contract),
                           source=list(source), target=list(target), value=vals.tolist(),
                           flow_count=vals.size, flow_semantics="state transitions" if name == "alluvial" else "directed flow",
                           node_label_key=getattr(ax.figure, "_node_label_key", {}),
                           source_stage=list(source_stage) if source_stage is not None else None,
                           target_stage=list(target_stage) if target_stage is not None else None)


def sankey(source, target, value, **kwargs):
    return flow_diagram(source, target, value, name="sankey", **kwargs)


def alluvial(source, target, value, source_stage, target_stage, **kwargs):
    return flow_diagram(source, target, value, source_stage=source_stage, target_stage=target_stage,
                        name="alluvial", **kwargs)
