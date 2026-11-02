"""Optimization, sensitivity, and robustness figures."""
from __future__ import annotations
from . import styles as _style
import numpy as np
from .base import attach_metadata, finite_array, contract_from


def convergence(iterations, objective, *, contract=None, ax=None, **kwargs):
    x,y=finite_array(iterations,"iterations"),finite_array(objective,"objective");
    if x.shape!=y.shape: raise ValueError("iterations and objective must align")
    iteration_label="迭代次数" if np.equal(x,np.rint(x)).all() else "迭代坐标（调用者提供）"
    ax=ax or _style.subplots(constrained_layout=True)[1]; ax.plot(x,y,color=_style.color(0, '#3C6E8F')); ax.set(xlabel=kwargs.get("xlabel",iteration_label),ylabel=kwargs.get("units","目标值")); return attach_metadata(ax.figure,name="convergence",contract=contract_from(kwargs,contract))


def sensitivity(x, response, *, contract=None, ax=None, **kwargs):
    x, response = finite_array(x, "x"), finite_array(response, "response")
    if x.shape != response.shape: raise ValueError("x and response must align")
    ax = ax or _style.subplots(constrained_layout=True)[1]
    order = np.argsort(x); x, response = x[order], response[order]
    ax.plot(x, response, color=_style.color(1, '#D97745'), lw=_style.stroke(1.8), marker="o", ms=_style.marker(3))
    ax.fill_between(x, response.min(), response, color=_style.color(4, '#E7B56D'), alpha=.18)
    ax.set(xlabel=kwargs.get("xlabel", "参数"), ylabel=kwargs.get("ylabel", "响应变化"))
    return attach_metadata(ax.figure, name="sensitivity", contract=contract_from(kwargs, contract), encoding="ordered parameter-response curve")


def pareto(x, y, *, contract=None, ax=None, **kwargs):
    x, y = finite_array(x, "x"), finite_array(y, "y")
    if x.shape != y.shape: raise ValueError("x and y must align")
    ax = ax or _style.subplots(constrained_layout=True)[1]
    points = np.column_stack([x, y])
    minimize = kwargs.get("minimize", [True, True])
    if len(minimize) != 2: raise ValueError("minimize must specify both objective directions")
    objectives = points * np.where(minimize, 1., -1.)
    keep = [i for i, point in enumerate(objectives)
            if not np.any(np.all(objectives <= point, axis=1) & np.any(objectives < point, axis=1))]
    keep = sorted(keep, key=lambda i: x[i])
    ax.scatter(x, y, s=_style.marker(24, area=True), color="#9BA8B0", alpha=.62, edgecolor="white", label="候选解")
    ax.plot(x[keep], y[keep], color=_style.color(1, '#D97745'), lw=_style.stroke(1.8), marker="o", label="帕累托前沿")
    ax.set(xlabel=kwargs.get("xlabel", "目标一"), ylabel=kwargs.get("ylabel", "目标二"))
    ax.legend(frameon=False)
    return attach_metadata(ax.figure, name="pareto", contract=contract_from(kwargs, contract), encoding="candidate cloud + non-dominated frontier", frontier_size=len(keep), frontier_indices=keep, minimize=list(minimize))

