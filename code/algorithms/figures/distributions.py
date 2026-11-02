"""Single-variable and distribution plots."""
from __future__ import annotations
from . import styles as _style
import numpy as np
from .base import attach_metadata, finite_array, contract_from


def histogram(values, *, bins=20, label="值", units="", contract=None, ax=None, **kwargs):
    x = finite_array(values, "values")
    ax = ax or _style.subplots(constrained_layout=True)[1]
    ax.hist(x, bins=bins, color=_style.color(0, '#3C6E8F'), alpha=.8, edgecolor="#262626")
    ax.set(xlabel=f"{label} ({units})" if units else label, ylabel="频数")
    return attach_metadata(ax.figure, name="histogram", contract=contract_from(kwargs, contract), n=int(x.size))


def kde(values, *, label="值", units="", contract=None, ax=None, **kwargs):
    x = finite_array(values, "values"); ax = ax or _style.subplots(constrained_layout=True)[1]
    if x.size < 2 or np.ptp(x) == 0:
        raise ValueError("kde needs at least two nonconstant observations; use ECDF or raw points")
    grid = np.linspace(x.min(), x.max(), 200)
    bw = max(np.std(x, ddof=1) * x.size ** (-.2), 1e-6)
    density = np.exp(-.5 * ((grid[:, None] - x[None, :]) / bw) ** 2).mean(1) / (bw * np.sqrt(2*np.pi))
    ax.plot(grid, density, color=_style.color(0, '#3C6E8F')); ax.fill_between(grid, density, color=_style.color(0, '#3C6E8F'), alpha=.18)
    ax.set(xlabel=f"{label} ({units})" if units else label, ylabel="密度")
    return attach_metadata(ax.figure, name="kde", contract=contract_from(kwargs, contract), n=int(x.size))


def ecdf(values, *, label="值", units="", contract=None, ax=None, **kwargs):
    x = np.sort(finite_array(values, "values")); ax = ax or _style.subplots(constrained_layout=True)[1]
    ax.step(x, np.arange(1, x.size+1)/x.size, where="post", color=_style.color(0, '#3C6E8F'))
    ax.set(xlabel=f"{label} ({units})" if units else label, ylabel="经验累积概率", ylim=(0, 1.02))
    return attach_metadata(ax.figure, name="ecdf", contract=contract_from(kwargs, contract), n=int(x.size))


def boxplot(values, *, groups=None, labels=None, contract=None, ax=None, **kwargs):
    data = [finite_array(v, "values") for v in values] if isinstance(values, (list, tuple)) and np.asarray(values).ndim != 1 else [finite_array(values, "values")]
    ax = ax or _style.subplots(constrained_layout=True)[1]; ax.boxplot(data, tick_labels=labels, patch_artist=True)
    return attach_metadata(ax.figure, name="boxplot", contract=contract_from(kwargs, contract), groups=len(data))


def violin(values, *, labels=None, contract=None, ax=None, **kwargs):
    data = [finite_array(v, "values") for v in values] if isinstance(values, (list, tuple)) and any(np.ndim(v) > 0 for v in values) else [finite_array(values, "values")]
    ax = ax or _style.subplots(constrained_layout=True)[1]; ax.violinplot(data, showmedians=True)
    if labels: ax.set_xticks(np.arange(1, len(labels)+1), labels)
    return attach_metadata(ax.figure, name="violin", contract=contract_from(kwargs, contract), groups=len(data))


def qq_plot(values, *, contract=None, ax=None, **kwargs):
    x = np.sort(finite_array(values, "values")); ax = ax or _style.subplots(constrained_layout=True)[1]
    q = (np.arange(x.size)+.5)/x.size
    normal = np.sqrt(2) * np.vectorize(lambda p: __import__('scipy').special.ndtri(p))(q)
    normal = (normal-normal.mean())/max(normal.std(ddof=1), 1e-12)*x.std(ddof=1)+x.mean()
    ax.scatter(normal, x, s=_style.marker(14, area=True), color=_style.color(0, '#3C6E8F')); ax.set(xlabel="理论分位数", ylabel="样本分位数")
    return attach_metadata(ax.figure, name="qq_plot", contract=contract_from(kwargs, contract), n=int(x.size))


def raincloud(values, *, labels=None, contract=None, ax=None, **kwargs):
    """Half densities, quartile boxes and every observation on separate lanes.

    Singleton/constant samples have no estimated density. Deterministic jitter
    changes only the categorical coordinate, never the measured values.
    """
    nested = isinstance(values, (list, tuple)) and any(np.ndim(v) > 0 for v in values)
    data = [finite_array(v, "values") for v in values] if nested else [finite_array(values, "values")]
    if labels is not None and len(labels) != len(data):
        raise ValueError("labels must match the number of groups")
    ax = ax or _style.subplots(constrained_layout=True)[1]
    statistics = []
    for index, sample in enumerate(data, 1):
        shade = _style.color(index - 1)
        if len(sample) > 1 and np.ptp(sample) > 0:
            body = ax.violinplot([sample], positions=[index], widths=.7,
                                 showextrema=False)["bodies"][0]
            for path in body.get_paths():
                path.vertices[:, 0] = np.minimum(path.vertices[:, 0], index)
            body.set_facecolor(shade)
            body.set_edgecolor(shade)
            body.set_alpha(.3)
        box = ax.boxplot([sample], positions=[index + .1], widths=.12,
                         patch_artist=True, showfliers=False,
                         medianprops={"color": "black", "linewidth": 1.1})
        box["boxes"][0].set_facecolor(shade)
        box["boxes"][0].set_alpha(.65)
        jitter = .23 + .09 * ((np.arange(len(sample)) * .61803398875) % 1)
        ax.scatter(index + jitter, sample, s=_style.marker(10, area=True), alpha=.65, color=shade,
                   edgecolors="white", linewidths=_style.stroke(0.25))
        statistics.append({"n": len(sample), "quartiles": np.quantile(sample, [.25, .5, .75]).tolist(),
                           "density_estimated": len(sample) > 1 and np.ptp(sample) > 0})
    ax.set_xticks(np.arange(1, len(data) + 1), labels or [str(i) for i in range(1, len(data) + 1)])
    ax.set_xlim(.5, len(data) + .55)
    ax.set_ylabel(kwargs.get("ylabel", "观测值"))
    ax.grid(axis="x", visible=False)
    return attach_metadata(ax.figure, name="raincloud", contract=contract_from(kwargs, contract),
                           groups=len(data), statistics=statistics, jitter="deterministic; categorical axis only")

