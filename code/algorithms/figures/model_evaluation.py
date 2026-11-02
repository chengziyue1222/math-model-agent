"""Model evaluation plots. Real ROC/PR data are required by default."""
from __future__ import annotations
from . import styles as _style
import numpy as np
from sklearn.metrics import roc_curve, precision_recall_curve, auc, average_precision_score
from .base import attach_metadata, finite_array, contract_from


def roc_curve_plot(y_true, y_score, *, contract=None, ax=None, **kwargs):
    y=finite_array(y_true,"y_true").astype(int); s=finite_array(y_score,"y_score")
    if y.shape!=s.shape or np.unique(y).size<2: raise ValueError("real ROC requires aligned binary labels with both classes")
    fpr,tpr,_=roc_curve(y,s); ax=ax or _style.subplots(constrained_layout=True)[1]; ax.plot(fpr,tpr,label=f"AUC={auc(fpr,tpr):.3f}"); ax.plot([0,1],[0,1],"--",color="#6B6B6B"); ax.set(xlabel="假阳性率",ylabel="真阳性率"); ax.legend(); return attach_metadata(ax.figure,name="roc_curve",contract=contract_from(kwargs,contract),auc=float(auc(fpr,tpr)),real_data=True)


def pr_curve(y_true, y_score, *, contract=None, ax=None, **kwargs):
    y=finite_array(y_true,"y_true").astype(int); s=finite_array(y_score,"y_score")
    if y.shape!=s.shape or np.unique(y).size<2: raise ValueError("real PR requires aligned binary labels with both classes")
    precision,recall,_=precision_recall_curve(y,s); ax=ax or _style.subplots(constrained_layout=True)[1]; ax.plot(recall,precision); ax.set(xlabel="召回率",ylabel="精确率"); return attach_metadata(ax.figure,name="pr_curve",contract=contract_from(kwargs,contract),real_data=True,precision=precision.tolist(),recall=recall.tolist(),average_precision=float(average_precision_score(y,s)))


def observed_predicted(observed, predicted, *, contract=None, ax=None, **kwargs):
    o,p=finite_array(observed,"observed"),finite_array(predicted,"predicted");
    if o.shape!=p.shape: raise ValueError("observed and predicted must align")
    ax=ax or _style.subplots(constrained_layout=True)[1]; ax.scatter(o,p,s=_style.marker(16, area=True),color=_style.color(0, '#3C6E8F')); lo,hi=min(o.min(),p.min()),max(o.max(),p.max()); ax.plot([lo,hi],[lo,hi],"--",color="#6B6B6B"); ax.set(xlabel="观测",ylabel="预测"); return attach_metadata(ax.figure,name="observed_predicted",contract=contract_from(kwargs,contract),n=int(o.size))


def residuals(observed, predicted, *, contract=None, ax=None, **kwargs):
    o,p=finite_array(observed,"observed"),finite_array(predicted,"predicted")
    if o.shape != p.shape: raise ValueError("observed and predicted must align")
    r = o - p
    ax = ax or _style.subplots(constrained_layout=True)[1]
    ax.scatter(p, r, s=_style.marker(18, area=True), color=_style.color(0, '#3C6E8F'), alpha=.7)
    ax.axhline(0, color="#6B6B6B", ls="--")
    ax.set(xlabel="预测值", ylabel="残差（观测 − 预测）")
    return attach_metadata(ax.figure, name="residuals", contract=contract_from(kwargs,contract), residuals=r.tolist())

