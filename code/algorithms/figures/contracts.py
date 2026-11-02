"""Data contracts shared by the modular figure library.

The contracts intentionally describe provenance and statistical meaning.  They
do not infer sample size, units, or uncertainty from arrays or filenames.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Mapping


@dataclass(frozen=True)
class DataContract:
    """Traceability information required by a reusable figure.

    ``independent_unit`` is the unit used for statistical inference (for
    example ``participant`` rather than the number of repeated rows).
    """

    source: str = "synthetic"
    fields: Mapping[str, str] = field(default_factory=dict)
    units: Mapping[str, str] = field(default_factory=dict)
    independent_unit: str = "observation"
    repeated_measurement: str | None = None
    split: str | None = None
    random_seed: int | None = None
    interval_kind: str | None = None
    deterministic: bool = True
    simulated: bool = False
    transformations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not str(self.source).strip():
            raise ValueError("source must be non-empty")
        if not str(self.independent_unit).strip():
            raise ValueError("independent_unit must be non-empty")
        if self.random_seed is not None and not isinstance(self.random_seed, int):
            raise ValueError("random_seed must be an integer or None")
        if any(not str(x).strip() for x in self.transformations):
            raise ValueError("transformations must contain non-empty strings")

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["fields"] = dict(self.fields)
        value["units"] = dict(self.units)
        value["transformations"] = list(self.transformations)
        return value


def require_fields(data: Mapping[str, Any], required: tuple[str, ...] | list[str]) -> None:
    missing = [name for name in required if name not in data]
    if missing:
        raise ValueError(f"missing required fields: {missing}")

