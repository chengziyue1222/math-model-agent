"""Low-level helpers for figure functions."""
from __future__ import annotations
from . import styles as _style

from typing import Any, Mapping
from collections.abc import Sequence
import matplotlib.pyplot as plt
import numpy as np

from .contracts import DataContract


def finite_array(value: Any, name: str, *, ndim: int = 1) -> np.ndarray:
    arr = np.asarray(value, dtype=float)
    if arr.ndim != ndim or arr.size == 0 or not np.isfinite(arr).all():
        raise ValueError(f"{name} must be a non-empty finite {ndim}D array")
    return arr


def attach_metadata(fig: plt.Figure, *, name: str, contract: DataContract | None = None,
                    **metadata: Any) -> plt.Figure:
    fig._figure_type = name
    fig._figure_metadata = metadata_value({"figure_type": name, **metadata})
    if contract is not None:
        fig._figure_metadata["data_contract"] = contract.to_dict()
    return fig


def metadata_value(value):
    """Preserve numerical evidence in JSON-compatible form without flattening."""
    if isinstance(value, np.ndarray):
        return metadata_value(value.tolist())
    if isinstance(value, np.generic):
        return metadata_value(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, Mapping):
        return {str(k): metadata_value(v) for k, v in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [metadata_value(v) for v in value]
    return value


def new_figure(*, width: float = 6.0, height: float = 4.0):
    return _style.subplots(figsize=(width, height), constrained_layout=True)


def contract_from(data: Mapping[str, Any], contract: DataContract | None) -> DataContract:
    if contract is not None:
        return contract
    return DataContract(source=str(data.get("source", "caller supplied; provenance unspecified")),
                        simulated=bool(data.get("simulated", False)),
                        independent_unit=str(data.get("independent_unit", "observation")),
                        units=data.get("units") if isinstance(data.get("units"), dict) else {},
                        interval_kind=data.get("interval_kind"))

