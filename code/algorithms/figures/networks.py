"""Network and flow figures."""
from __future__ import annotations
from . import styles as _style
import networkx as nx
from .base import attach_metadata, contract_from


def network(edges, *, directed=False, contract=None, ax=None, **kwargs):
    graph=nx.DiGraph() if directed else nx.Graph()
    graph.add_nodes_from(kwargs.get("nodes", [])); graph.add_edges_from(edges)
    ax, labels=_style.node_axes(list(graph.nodes), ax)
    pos=nx.spring_layout(graph,seed=0)
    nx.draw_networkx(graph,pos,labels=labels,ax=ax,node_color=_style.color(0, '#3C6E8F'),
                     node_size=500,font_size=_style.font('text', 8),arrows=directed,
                     bbox={"facecolor":"white","edgecolor":"none","alpha":.9,"pad":1.5})
    ax.margins(.18); ax.axis("off")
    return attach_metadata(ax.figure,name="network",contract=contract_from(kwargs,contract),
                           directed=directed,nodes=graph.number_of_nodes(),edges=graph.number_of_edges(),
                           node_label_key=getattr(ax.figure, "_node_label_key", {}))


def dependency(edges, **kwargs): return network(edges,directed=True,**kwargs)

