"""Modular figure library for mathematical-modeling papers.

Legacy classes remain available from :mod:`algorithms.sci_figures`; this
package supplies contracts, registry metadata, and small composable chart
functions for new code.
"""
from .contracts import DataContract
from .registry import FigureSpec, display_name, get_figure, get_spec, list_figures, register
from .export import export_publication_figure, audit_publication_figure

__all__ = ["DataContract", "FigureSpec", "register", "display_name", "get_figure", "get_spec", "list_figures", "export_publication_figure", "audit_publication_figure"]

