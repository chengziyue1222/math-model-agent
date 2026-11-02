"""Mechanism and workflow diagrams."""
from __future__ import annotations
from . import styles as _style
from .base import attach_metadata, contract_from


def flowchart(nodes, edges, *, contract=None, ax=None, **kwargs):
    ax=ax or _style.subplots(constrained_layout=True)[1]; labels=list(nodes); positions={n:(i,0) for i,n in enumerate(labels)}
    for a,b in edges: ax.annotate("",xy=positions[b],xytext=positions[a],arrowprops={"arrowstyle":"->","color":"#6B6B6B"})
    for n,(x,y) in positions.items(): ax.text(x,y,n,ha="center",va="center",bbox={"boxstyle":"round,pad=.35","facecolor":"white","edgecolor":"#3C6E8F"})
    ax.set_xlim(-1,len(labels)); ax.set_ylim(-1,1); ax.axis("off"); return attach_metadata(ax.figure,name="flowchart",contract=contract_from(kwargs,contract),nodes=labels)

