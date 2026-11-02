"""Relationship, correlation, and agreement plots."""
from __future__ import annotations
from . import styles as _style
import numpy as np
from .base import attach_metadata, finite_array, contract_from


def scatter(x, y, *, trend=False, contract=None, ax=None, **kwargs):
    x,y=finite_array(x,"x"),finite_array(y,"y")
    if x.shape != y.shape: raise ValueError("x and y must align")
    ax=ax or _style.subplots(constrained_layout=True)[1]; ax.scatter(x,y,s=_style.marker(18, area=True),color=_style.color(0, '#3C6E8F'),alpha=.75)
    ax.set(xlabel=kwargs.get("xlabel", "变量 X"), ylabel=kwargs.get("ylabel", "变量 Y"))
    if trend:
        if x.size < 3 or np.ptp(x) == 0:
            raise ValueError("scatter_trend regression requires at least 3 observations and nonconstant x")
        from scipy.stats import t
        coef=np.polyfit(x,y,1); grid=np.linspace(x.min(),x.max(),100); fitted=np.polyval(coef,grid)
        ax.plot(grid,fitted,color=_style.color(1, '#A6534C'), label="线性回归")
        residual = y - np.polyval(coef, x)
        se = np.sqrt(np.sum(residual**2)/(x.size-2) * (1/x.size + (grid-x.mean())**2/np.sum((x-x.mean())**2)))
        delta = t.ppf(.975, x.size-2) * se
        ax.fill_between(grid, fitted-delta, fitted+delta, color=_style.color(1, '#A6534C'), alpha=.15, label="95% 均值置信带")
        ax.legend(frameon=False)
    return attach_metadata(ax.figure,name="scatter",contract=contract_from(kwargs,contract),n=int(x.size),trend=trend)


def correlation_matrix(data, *, labels=None, method="pearson", contract=None, ax=None, **kwargs):
    a=finite_array(data,"data",ndim=2); corr=np.corrcoef(a,rowvar=False) if method=="pearson" else np.corrcoef(a,rowvar=False)
    ax=ax or _style.subplots(constrained_layout=True)[1]; im=ax.imshow(corr,vmin=-1,vmax=1,cmap=_style.cmap('diverging', 'RdBu_r')); ax.figure.colorbar(im,ax=ax,label="相关系数");
    if labels: ax.set_xticks(range(len(labels)),labels,rotation=45,ha="right"); ax.set_yticks(range(len(labels)),labels)
    return attach_metadata(ax.figure,name="correlation_matrix",contract=contract_from(kwargs,contract),method=method,n=int(a.shape[0]))


def bland_altman(reference, comparison, *, contract=None, ax=None, **kwargs):
    ref,comp=finite_array(reference,"reference"),finite_array(comparison,"comparison")
    if ref.shape!=comp.shape: raise ValueError("reference and comparison must align")
    if ref.size < 2:
        raise ValueError("Bland-Altman sample standard deviation requires at least two pairs")
    mean=(ref+comp)/2; diff=comp-ref
    ax=ax or _style.subplots(constrained_layout=True)[1]
    md=float(diff.mean()); sd=float(diff.std(ddof=1))
    lower,upper=md-1.96*sd,md+1.96*sd
    ax.scatter(mean,diff,s=_style.marker(16, area=True),color=_style.color(0, '#3C6E8F'))
    ax.axhline(md,color=_style.color(1, '#A6534C'),label=f"平均偏差\n{md:.3g}")
    ax.axhline(upper,color="#6B6B6B",ls="--",label=f"一致性上限\n均差 + 1.96s\n{upper:.3g}")
    ax.axhline(lower,color="#6B6B6B",ls=":",label=f"一致性下限\n均差 − 1.96s\n{lower:.3g}")
    ax.set(xlabel="均值",ylabel="差值（比较 − 参考）")
    columns=3 if ax.figure.get_figwidth()*25.4 >= 120 else 1
    ax.figure.legend(*ax.get_legend_handles_labels(),loc="outside upper center",ncol=columns,frameon=False,
                     title="一致性限：s 为差值的样本标准差")
    return attach_metadata(ax.figure,name="bland_altman",contract=contract_from(kwargs,contract),limits_of_agreement=[lower,upper])

