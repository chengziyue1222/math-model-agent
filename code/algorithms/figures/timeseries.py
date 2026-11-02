"""Time-series and forecast figures."""
from __future__ import annotations
from . import styles as _style
import numpy as np
from .base import attach_metadata, finite_array, contract_from


def line(time, values, *, label="观测", lower=None, upper=None, interval_kind=None, contract=None, ax=None, **kwargs):
    t,y=finite_array(time,"time"),finite_array(values,"values")
    if t.shape!=y.shape or np.any(np.diff(t)<=0): raise ValueError("time and values must align and time must increase")
    ax=ax or _style.subplots(constrained_layout=True)[1]; ax.plot(t,y,label=label,color=_style.color(0, '#3C6E8F'))
    if lower is not None or upper is not None:
        if lower is None or upper is None or not interval_kind: raise ValueError("lower, upper and interval_kind are required together")
        lo,hi=finite_array(lower,"lower"),finite_array(upper,"upper");
        if lo.shape!=y.shape or hi.shape!=y.shape or np.any(lo>y) or np.any(hi<y): raise ValueError("interval must bracket values")
        ax.fill_between(t,lo,hi,color=_style.color(0, '#3C6E8F'),alpha=.18,label=interval_kind)
    ax.set(xlabel="时间",ylabel=kwargs.get("units", "值")); return attach_metadata(ax.figure,name="time_series",contract=contract_from(kwargs,contract),interval_kind=interval_kind or "none")


def forecast_interval(time, observed, predicted, lower, upper, *, interval_kind, contract=None, **kwargs):
    t, o, p = finite_array(time, "time"), finite_array(observed, "observed"), finite_array(predicted, "predicted")
    if t.shape != o.shape or t.shape != p.shape:
        raise ValueError("forecast_interval.time, observed and predicted must align")
    fig = line(t,p,lower=lower,upper=upper,interval_kind=interval_kind,contract=contract,label="预测",**kwargs)
    fig.axes[0].plot(t, o, color=_style.color(1, '#A6534C'), ls="--", label="观测")
    fig.axes[0].legend(frameon=False)
    fig._figure_metadata.update(name="forecast_interval", observed=o.tolist(), predicted=p.tolist())
    return fig

