"""Small, auditable checks for inverse models, dependent data and decisions.

These routines report evidence; they do not declare a scientific model valid.
"""
from __future__ import annotations

import numpy as np


def identifiability_diagnostics(jacobian, *, parameter_scales=None, rtol=1e-8):
    """Inspect local sensitivity after explicit parameter scaling.

    A full column rank is only a local numerical property, not a proof of global
    identifiability. Scales must use the same units as their parameters.
    """
    matrix = np.asarray(jacobian, dtype=float)
    if matrix.ndim != 2 or min(matrix.shape) < 1 or not np.isfinite(matrix).all():
        raise ValueError("jacobian must be a finite nonempty two-dimensional array")
    if not np.isfinite(rtol) or not 0 < rtol < 1:
        raise ValueError("rtol must lie between zero and one")
    scales = np.ones(matrix.shape[1]) if parameter_scales is None else np.asarray(parameter_scales, float)
    if scales.shape != (matrix.shape[1],) or not np.isfinite(scales).all() or np.any(scales <= 0):
        raise ValueError("parameter scales must be finite, positive and match the columns")
    values = np.linalg.svd(matrix * scales, compute_uv=False)
    threshold = rtol * values[0]
    rank = int(np.count_nonzero(values > threshold))
    full_rank = rank == matrix.shape[1]
    condition = float(values[0] / values[-1]) if full_rank else None
    return {"rank": rank, "parameter_count": matrix.shape[1], "locally_full_rank": full_rank,
            "scaled_singular_values": values.tolist(), "condition_number": condition,
            "relative_tolerance": float(rtol), "global_identifiability_proven": False}


def moving_block_mean_interval(values, *, block_length, confidence=0.95, repetitions=2000, seed=0):
    """Circular moving-block bootstrap interval for an ordered scalar series.

    Resamples overlapping *blocks*, retaining order within each block. The
    caller must justify weak stationarity, block length and sampling unit.
    """
    x = np.asarray(values, float)
    if x.ndim != 1 or len(x) < 2 or not np.isfinite(x).all():
        raise ValueError("values must be a finite series with at least two observations")
    if isinstance(block_length, bool) or int(block_length) != block_length or not 1 <= block_length < len(x):
        raise ValueError("block_length must be a positive integer smaller than the series")
    if isinstance(repetitions, bool) or int(repetitions) != repetitions or repetitions < 100:
        raise ValueError("repetitions must be an integer of at least 100")
    if not np.isfinite(confidence) or not 0 < confidence < 1:
        raise ValueError("confidence must lie between zero and one")
    rng = np.random.default_rng(seed)
    blocks = int(np.ceil(len(x) / block_length))
    starts = rng.integers(0, len(x), (int(repetitions), blocks, 1))
    indices = ((starts + np.arange(block_length)) % len(x)).reshape(int(repetitions), -1)[:, :len(x)]
    means = np.mean(x[indices], axis=1)
    tail = (1 - confidence) / 2
    lower, upper = np.quantile(means, [tail, 1 - tail])
    return {"mean": float(x.mean()), "lower": float(lower), "upper": float(upper),
            "confidence": float(confidence), "interval_type": "circular-moving-block-bootstrap-percentile",
            "block_length": int(block_length), "observations": len(x), "repetitions": int(repetitions),
            "seed": seed, "assumption": "weakly stationary ordered analysis units"}


def scenario_policy_metrics(costs, *, probabilities=None, feasible=None, tail_probability=0.1):
    """Evaluate fixed policies on a shared policy-by-scenario matrix.

    Upper-tail expected cost uses exact probability mass, including the partial
    mass at the tail boundary. This is a finite-scenario risk measure, not a
    population confidence bound. Infeasible scenarios remain in the denominator.
    """
    values = np.asarray(costs, float)
    if values.ndim != 2 or min(values.shape) < 1 or not np.isfinite(values).all():
        raise ValueError("costs must be a finite policy-by-scenario matrix")
    p = np.full(values.shape[1], 1 / values.shape[1]) if probabilities is None else np.asarray(probabilities, float)
    if p.shape != (values.shape[1],) or not np.isfinite(p).all() or np.any(p < 0) or not np.isclose(p.sum(), 1):
        raise ValueError("probabilities must be nonnegative, finite and sum to one")
    p = p / p.sum()
    if not np.isfinite(tail_probability) or not 0 < tail_probability <= 1:
        raise ValueError("tail_probability must lie in (0, 1]")
    ok = np.ones(values.shape, dtype=bool) if feasible is None else np.asarray(feasible)
    if ok.shape != values.shape or ok.dtype.kind != 'b':
        raise ValueError("feasible must be a boolean matrix matching costs")
    reports = []
    for row, flags in zip(values, ok):
        order = np.argsort(-row, kind="stable")
        mass_before = np.r_[0.0, np.cumsum(p[order])[:-1]]
        tail_mass = np.minimum(p[order], np.maximum(0, tail_probability - mass_before))
        reports.append({"expected_cost": float(row @ p), "worst_cost": float(np.max(row[p > 0])),
                        "upper_tail_mean_cost": float(row[order] @ tail_mass / tail_probability),
                        "feasible_probability_mass": float(flags @ p),
                        "infeasible_scenario_count": int(np.count_nonzero(~flags)),
                        "scenario_count": values.shape[1], "tail_probability": float(tail_probability)})
    return reports
