import numpy as np
import pytest

from algorithms.research_validation import (
    identifiability_diagnostics, moving_block_mean_interval, scenario_policy_metrics,
)


def test_identifiability_detects_equivalent_parameters_and_bad_scaling():
    x = np.linspace(0, 1, 30)
    result = identifiability_diagnostics(np.column_stack([x, 2*x]))
    assert result['rank'] == 1
    assert result['condition_number'] is None
    scaled = identifiability_diagnostics(np.diag([1e8, 1]), parameter_scales=[1e-8, 1])
    assert scaled['locally_full_rank']
    assert scaled['condition_number'] == pytest.approx(1)
    assert not scaled['global_identifiability_proven']


def test_block_bootstrap_keeps_dependence_and_is_reproducible():
    rng = np.random.default_rng(42)
    noise = rng.normal(size=400)
    series = np.zeros(400)
    for i in range(1, 400):
        series[i] = .9*series[i-1] + noise[i]
    dependent = moving_block_mean_interval(series, block_length=20, seed=12)
    iid = moving_block_mean_interval(series, block_length=1, seed=12)
    assert dependent == moving_block_mean_interval(series, block_length=20, seed=12)
    assert dependent['upper'] - dependent['lower'] > 2*(iid['upper'] - iid['lower'])
    assert dependent['observations'] == len(series)


def test_tail_risk_uses_partial_mass_and_counts_failure():
    result = scenario_policy_metrics([[0, 10, 100]], probabilities=[.7, .25, .05],
                                    feasible=[[True, True, False]], tail_probability=.1)[0]
    assert result['expected_cost'] == pytest.approx(7.5)
    assert result['upper_tail_mean_cost'] == pytest.approx(55)
    assert result['feasible_probability_mass'] == pytest.approx(.95)
    assert result['infeasible_scenario_count'] == 1


def test_zero_probability_does_not_affect_worst_risk():
    result = scenario_policy_metrics([[5, 100]], probabilities=[1, 0])[0]
    assert result['worst_cost'] == 5
    assert result['upper_tail_mean_cost'] == pytest.approx(5)


@pytest.mark.parametrize('value', [[], [1, np.nan], [[1, 2]]])
def test_bootstrap_rejects_invalid_data(value):
    with pytest.raises(ValueError):
        moving_block_mean_interval(value, block_length=1)


def test_diagnostics_and_scenarios_reject_invalid_definitions():
    with pytest.raises(ValueError):
        identifiability_diagnostics([[1, 2]], parameter_scales=[1, -1])
    with pytest.raises(ValueError):
        scenario_policy_metrics([[1, 2]], probabilities=[.2, .3])
    with pytest.raises(ValueError):
        scenario_policy_metrics([[1, 2]], feasible=[[1, 0]])
