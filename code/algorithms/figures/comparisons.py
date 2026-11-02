"""Category comparison plots with explicit error interval semantics."""
from __future__ import annotations
from . import styles as _style
import numpy as np
from .base import attach_metadata, finite_array, contract_from


def _categories(categories, values):
    labels = list(categories); y = finite_array(values, "values")
    if len(labels) != len(y): raise ValueError("categories and values must align")
    return labels, y


def grouped_bar(categories, values, *, groups=None, errors=None, interval_kind=None, units="", contract=None, ax=None, **kwargs):
    labels, y = _categories(categories, values); ax = ax or _style.subplots(constrained_layout=True)[1]
    if errors is not None:
        e = finite_array(errors, "errors");
        if e.shape != y.shape: raise ValueError("errors must align with values")
    else: e = None
    ax.bar(np.arange(len(y)), y, yerr=e, color=_style.color(0, '#3C6E8F'), capsize=3)
    ax.set_xticks(np.arange(len(y)), labels, rotation=30, ha="right"); ax.set_ylabel(units)
    if e is not None and not interval_kind: raise ValueError("interval_kind is required when errors are supplied")
    return attach_metadata(ax.figure, name="grouped_bar", contract=contract_from(kwargs, contract), interval_kind=interval_kind or "none")


def bar(categories, values, **kwargs): return grouped_bar(categories, values, **kwargs)
def horizontal_bar(categories, values, *, contract=None, ax=None, **kwargs):
    labels, y = _categories(categories, values); ax = ax or _style.subplots(constrained_layout=True)[1]
    ax.barh(np.arange(len(y)), y, color=_style.color(0, '#3C6E8F')); ax.set_yticks(np.arange(len(y)), labels); return attach_metadata(ax.figure, name="horizontal_bar", contract=contract_from(kwargs, contract))


def dot_plot(categories, values, *, contract=None, ax=None, **kwargs):
    labels, y = _categories(categories, values); ax = ax or _style.subplots(constrained_layout=True)[1]
    order = np.argsort(y); ax.plot(y[order], np.arange(len(y)), "o", color=_style.color(0, '#3C6E8F')); ax.set_yticks(np.arange(len(y)), [labels[i] for i in order]); return attach_metadata(ax.figure, name="dot_plot", contract=contract_from(kwargs, contract))


def forest(categories, values=None, lower=None, upper=None, *, estimate=None, interval_kind=None, contract=None, ax=None, **kwargs):
    if values is None:
        values = estimate
    if lower is None or upper is None: raise ValueError("forest requires lower and upper bounds")
    labels, y = _categories(categories, values); lo, hi = finite_array(lower,"lower"), finite_array(upper,"upper")
    if lo.shape != y.shape or hi.shape != y.shape or np.any(lo > y) or np.any(hi < y): raise ValueError("interval must bracket values")
    if not interval_kind: raise ValueError("interval_kind is required")
    ax = ax or _style.subplots(constrained_layout=True)[1]; pos=np.arange(len(y)); ax.errorbar(y,pos,xerr=[y-lo,hi-y],fmt="o",color=_style.color(0, '#3C6E8F')); ax.set_yticks(pos,labels)
    ax.set_xlabel(kwargs.get("xlabel", f"估计值（{interval_kind}）"))
    ax.set_ylabel("对象")
    return attach_metadata(ax.figure, name="forest", contract=contract_from(kwargs, contract), interval_kind=interval_kind)


def waterfall(values, *, labels=None, contract=None, ax=None, **kwargs):
    y=finite_array(values,"values")
    if labels is None or len(labels) != len(y): raise ValueError('waterfall.labels must align with values')
    ax=ax or _style.subplots(constrained_layout=True)[1]
    prior = np.r_[0, np.cumsum(y[:-1])]
    bars=ax.bar(np.arange(len(y)),y,bottom=prior,color=np.where(y>=0,_style.color(0,"#5B8C6A"),_style.color(1,"#A6534C")),
                edgecolor="#44515b",linewidth=_style.stroke(.4))
    for bar,value in zip(bars,y):
        if value < 0: bar.set_hatch("///")
    for i in range(len(y)-1): ax.plot([i+.4,i+.6],[prior[i]+y[i]]*2,color='#555555',lw=_style.stroke(0.7))
    ax.axhline(0,color="#262626",lw=_style.stroke(0.7))
    # Floating-bar sticky edges suppress autoscale margins at every cumulative
    # endpoint. Reserve space around the complete path, including negative runs.
    ax.use_sticky_edges = False
    ax.margins(y=.08)
    ax.set(xlabel='变化项',ylabel='累计值')
    if labels: ax.set_xticks(np.arange(len(y)),labels,rotation=30,ha="right")
    return attach_metadata(ax.figure,name="waterfall",contract=contract_from(kwargs,contract), cumulative=np.cumsum(y).tolist())

