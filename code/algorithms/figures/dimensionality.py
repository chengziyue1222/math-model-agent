"""Dimension reduction and embedding views with algorithm names preserved."""
from __future__ import annotations
from . import styles as _style
from .base import attach_metadata, finite_array, contract_from


def embedding(embedding, *, algorithm="embedding", labels=None, contract=None, ax=None, **kwargs):
    x=finite_array(embedding,"embedding",ndim=2)
    if x.shape[1] < 2: raise ValueError("embedding requires at least two columns")
    ax=ax or _style.subplots(constrained_layout=True)[1]; ax.scatter(x[:,0],x[:,1],s=_style.marker(18, area=True),color=_style.color(0, '#3C6E8F')); ax.set(xlabel=f"{algorithm} 1",ylabel=f"{algorithm} 2"); return attach_metadata(ax.figure,name="embedding",contract=contract_from(kwargs,contract),algorithm=algorithm,n=int(x.shape[0]))


def pca_scores(scores, **kwargs): return embedding(scores, algorithm="PCA", **kwargs)


def tsne(embedding, **kwargs): return globals()["embedding"](embedding, algorithm="t-SNE", **kwargs)


def umap(embedding, **kwargs): return globals()["embedding"](embedding, algorithm="UMAP", **kwargs)

