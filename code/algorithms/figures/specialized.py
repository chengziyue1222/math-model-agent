"""Structured renderers for the remaining catalog, without preview fallbacks.

Shared marks are used only where the supplied statistics have the same visual
grammar. Each key declares its own fields and semantic validation.
"""
from __future__ import annotations
from . import styles as _style

import textwrap
import numpy as np
from matplotlib.patches import Polygon, FancyArrowPatch
from matplotlib.path import Path
from matplotlib.text import Text
from scipy.cluster.hierarchy import dendrogram, leaves_list, is_valid_linkage
from scipy.stats import gaussian_kde
import networkx as nx

from .base import attach_metadata, contract_from, finite_array
from .academic_style import PALETTE, _finish

FIELDS = {}


class _EdgeAnnotation(Text):
    """Follow the actual display-space arrow on every export backend."""

    def __init__(self, edge, index, **kwargs):
        super().__init__(**kwargs)
        self._edge = edge
        self._edge_index = index

    def draw(self, renderer):
        vertices = self._edge.get_path().vertices[:3]
        obstacles = []
        for text in self.axes.texts:
            if text is self or not text.get_visible():
                continue
            if isinstance(text, _EdgeAnnotation) and text._edge_index >= self._edge_index:
                continue
            patch = text.get_bbox_patch()
            obstacles.append((patch if patch is not None else text).get_window_extent(renderer))
        best = None
        for t in (.5, .45, .55, .4, .6, .35, .65, .3, .7, .25, .75, .2, .8):
            point = (1-t)**2*vertices[0]+2*(1-t)*t*vertices[1]+t*t*vertices[2]
            self.set_position(point)
            box = self.get_window_extent(renderer).padded(renderer.points_to_pixels(1.5))
            overlap = sum(max(0., min(box.x1, other.x1)-max(box.x0, other.x0))
                          * max(0., min(box.y1, other.y1)-max(box.y0, other.y0)) for other in obstacles)
            score = (overlap, abs(t-.5))
            if best is None or score < best[0]:
                best = (score, t, point)
        _, t, point = best
        self.set_position(point)
        self.figure._figure_metadata['edge_annotation_layout'][self._edge_index].update(position=point.tolist(), curve_t=t)
        super().draw(renderer)


def _contour_ink():
    cfg = _style.current_config()
    return {'cmap': _style.cmap()} if cfg and (cfg.get('cmap') or cfg.get('cmap_definition')) else {'colors': PALETTE[0]}


def _vector_hexbin(axis, x, y, **kwargs):
    """Expand hexagon instances to data paths for reliable vector clipping.

    PDF backends can clip reused hexagon objects at negative offsets. Keeping
    every bin as its explicit polygon preserves the counts and geometry while
    avoiding that backend-specific object/offset interaction.
    """
    from matplotlib.transforms import IdentityTransform
    image = axis.hexbin(x, y, **kwargs)
    shape = image.get_paths()[0].vertices.copy()
    offsets = image.get_offsets().copy()
    image.set_verts([shape+offset for offset in offsets])
    image.set_offsets([[0., 0.]])
    image.set_transform(axis.transData)
    image.set_offset_transform(IdentityTransform())
    return image


def _declare(names, *fields):
    for name in names.split():
        FIELDS[name] = fields


_declare('ranking scenario_ranking', 'categories', 'values', 'direction')
_declare('score_bar', 'categories', 'values', 'score_kind')
_declare('lollipop cleveland_dot diverging_bar', 'categories', 'values')
_declare('ahp_weights topsis_weights feature_importance', 'categories', 'values', 'method')
_declare('effect_size', 'categories', 'estimate', 'lower', 'upper', 'interval_kind', 'effect_kind')
_declare('percent_stacked_bar', 'categories', 'values', 'groups')
_declare('multi_metric_comparison', 'categories', 'metrics', 'values')
_declare('raw_points jitter beeswarm', 'categories', 'samples')
_declare('probability_plot', 'theoretical', 'observed', 'distribution')
_declare('pareto_distribution', 'values')
_declare('area step', 'time', 'values')
_declare('multi_series stacked_area', 'time', 'values', 'groups')
_declare('rolling_mean', 'time', 'center', 'window')
_declare('decomposition', 'time', 'values', 'trend', 'seasonal', 'residual', 'period')
_declare('autocorrelation partial_autocorrelation', 'lag', 'correlation')
_declare('event_timeline', 'time', 'events')
_declare('gantt', 'tasks', 'start', 'end')
_declare('calendar_heatmap', 'dates', 'values')
_declare('time_heatmap', 'time', 'matrix', 'row_labels')
_declare('control_chart', 'time', 'values', 'center', 'lower', 'upper', 'interval_kind')
_declare('threshold_crossing', 'time', 'values', 'threshold')
_declare('adjacency_matrix diverging_heatmap circular_heatmap', 'matrix', 'row_labels', 'column_labels')
_declare('clustered_heatmap', 'matrix', 'row_labels', 'column_labels', 'row_linkage', 'column_linkage')
_declare('dendrogram', 'linkage', 'labels')
_declare('faceted_heatmap', 'matrices', 'facets', 'row_labels', 'column_labels')
_declare('threshold_heatmap', 'matrix', 'row_labels', 'column_labels', 'threshold')
_declare('contour spatial_heatmap', 'x_grid', 'y_grid', 'z')
_declare('spatial_3d', 'x', 'y', 'z')
_declare('spatial_scatter', 'longitude', 'latitude', 'size', 'group')
_declare('contour_density joint_density hexbin', 'x', 'y')
_declare('volcano', 'x', 'y')
_declare('partial_correlation', 'matrix', 'labels', 'control_labels')
_declare('parallel_coordinates high_dim_density', 'data', 'features')
_declare('separation_loadings', 'loadings', 'labels', 'components', 'method')
_declare('shap_summary', 'attributions', 'feature_names')
_declare('shap_beeswarm', 'attributions', 'features', 'feature_names')
_declare('partial_dependence', 'grid', 'response', 'feature_name')
_declare('ice', 'grid', 'curves', 'feature_name')
_declare('taylor_diagram', 'reference_std', 'std', 'correlation', 'labels')
_declare('mantel', 'distance_a', 'distance_b', 'r', 'p', 'permutations', 'seed')
_declare('lift_gain', 'population_fraction', 'gain', 'lift')
_declare('coverage', 'nominal', 'empirical')
_declare('calibration_curve', 'probability', 'observed_rate')
_declare('residual_distribution', 'observed', 'predicted')
_declare('error_by_time', 'time', 'observed', 'predicted')
_declare('cross_validation', 'fold', 'score')
_declare('model_interval', 'center', 'lower', 'upper', 'interval_kind')
_declare('repeated_convergence', 'iterations', 'objectives', 'runs')
_declare('optimum_distribution', 'runs', 'values')
_declare('cluster_stability', 'settings', 'scores', 'runs', 'metric')
_declare('response_1d perturbation', 'x', 'response', 'parameter')
_declare('scenario', 'x', 'responses', 'scenarios')
_declare('state_trajectory', 'time', 'states', 'dimensions')
_declare('response_surface_opt', 'x_grid', 'y_grid', 'z', 'direction')
_declare('parameter_response', 'x_grid', 'y_grid', 'z', 'parameters')
_declare('feasible_region feasible_heatmap', 'x_grid', 'y_grid', 'feasible')
_declare('constraint_boundary', 'x_grid', 'y_grid', 'constraint', 'limit')
_declare('constraint_slack', 'constraints', 'slack')
_declare('global_local', 'parameters', 'local', 'global_values', 'method')
_declare('risk_return', 'risk', 'returns', 'labels')
_declare('weight_sensitivity', 'weights', 'scores', 'schemes')
_declare('contribution_decomposition', 'components', 'values', 'baseline')
_declare('tornado', 'parameters', 'low', 'high')
_declare('adjacency dependency_graph flowchart algorithm_flow technical_route variable_dependency mechanism task_decomposition decision_tree input_model_validation_output', 'nodes', 'edges')
_declare('state_machine', 'nodes', 'edges', 'events')
_declare('state_transition', 'nodes', 'edges', 'probabilities')
_declare('geometry', 'points', 'segments', 'polygons')
_declare('coordinate_system', 'origin', 'basis')
_declare('algorithm_flow', 'nodes', 'edges', 'node_types', 'edge_labels')
_declare('technical_route input_model_validation_output', 'nodes', 'edges', 'stages')
_declare('mechanism', 'nodes', 'edges', 'edge_labels')
_declare('decision_tree', 'nodes', 'edges', 'edge_labels')

GRAPH_KEYS = {'adjacency', 'dependency_graph', 'flowchart', 'algorithm_flow', 'technical_route',
              'variable_dependency', 'mechanism', 'task_decomposition', 'decision_tree',
              'input_model_validation_output', 'state_machine', 'state_transition'}
BAR_KEYS = {'ranking', 'scenario_ranking', 'score_bar', 'lollipop', 'cleveland_dot',
            'diverging_bar', 'ahp_weights', 'topsis_weights', 'feature_importance'}
MARKERS = ['o', 's', '^', 'D', 'v', 'P', 'X']
LINES = ['-', '--', ':', '-.']


def _array(d, field, ndim=1):
    return finite_array(d[field], field, ndim=ndim)


def _labels(d, field, n):
    if isinstance(d[field], (str, bytes)) or n < 1:
        raise ValueError(f'{field} must be a nonempty label sequence')
    labels = list(d[field])
    if len(labels) != n or any(v is None or not str(v).strip() for v in labels):
        raise ValueError(f'{field} must contain {n} nonempty labels')
    return labels


def _aligned(d, *fields):
    arrays = [_array(d, field) for field in fields]
    if len({a.shape for a in arrays}) != 1:
        raise ValueError(f'{fields} must have aligned 1D shapes')
    return arrays


def validate(name, d):
    missing = [field for field in FIELDS[name] if field not in d]
    if missing:
        raise ValueError(f'{name} requires fields: {", ".join(missing)}')
    if name in BAR_KEYS:
        a = _array(d, 'values'); _labels(d, 'categories', len(a))
        if 'direction' in d and d['direction'] not in {'min', 'max'}:
            raise ValueError('direction must be min or max')
        if name in {'ahp_weights', 'topsis_weights'} and (np.any(a < 0) or not np.isclose(a.sum(), 1)):
            raise ValueError('weights must be nonnegative and sum to 1')
        if name == 'feature_importance' and np.any(a < 0):
            raise ValueError('feature_importance must be nonnegative')
        if name == 'score_bar' and not str(d['score_kind']).strip():
            raise ValueError('score_kind must declare the score scale')
    elif name == 'effect_size':
        c, lo, hi = _aligned(d, 'estimate', 'lower', 'upper'); _labels(d, 'categories', len(c))
        if np.any(lo > c) or np.any(c > hi): raise ValueError('interval must bracket estimate')
    elif name in {'percent_stacked_bar', 'multi_metric_comparison'}:
        a = _array(d, 'values', 2); _labels(d, 'categories', len(a))
        _labels(d, 'groups' if name == 'percent_stacked_bar' else 'metrics', a.shape[1])
        if name == 'percent_stacked_bar' and (np.any(a < 0) or np.any(a.sum(1) <= 0)):
            raise ValueError('percent stacks need nonnegative values and nonzero totals')
    elif name in {'raw_points', 'jitter', 'beeswarm'}:
        _labels(d, 'categories', len(d['samples']))
        for sample in d['samples']: finite_array(sample, 'samples')
        if d.get('orientation', 'vertical') not in {'vertical', 'horizontal'}:
            raise ValueError('orientation must be vertical or horizontal')
    elif name == 'probability_plot': _aligned(d, 'theoretical', 'observed')
    elif name == 'pareto_distribution':
        if np.any(_array(d, 'values') <= 0): raise ValueError('Pareto tail values must be positive')
    elif name in {'multi_series', 'stacked_area'}:
        t, a = _array(d, 'time'), _array(d, 'values', 2)
        if len(t) != len(a): raise ValueError('values must be time-by-group')
        _labels(d, 'groups', a.shape[1])
        if name == 'stacked_area' and np.any(a < 0): raise ValueError('stacked_area requires nonnegative values')
    elif name in {'area', 'step', 'threshold_crossing'}:
        _aligned(d, 'time', 'values')
    elif name == 'rolling_mean':
        _aligned(d, 'time', 'center')
        if not isinstance(d['window'], int) or d['window'] < 1: raise ValueError('window must be positive integer')
    elif name == 'decomposition':
        _, y, trend, seasonal, residual = _aligned(d, 'time', 'values', 'trend', 'seasonal', 'residual')
        if not np.allclose(y, trend+seasonal+residual): raise ValueError('decomposition components must sum to values')
        if not isinstance(d['period'], int) or d['period'] < 2: raise ValueError('period must be integer >= 2')
    elif name in {'autocorrelation', 'partial_autocorrelation'}:
        lag, c = _aligned(d, 'lag', 'correlation')
        if np.any(np.abs(c) > 1+1e-9) or np.any(lag < 0) or np.any(lag % 1): raise ValueError('invalid lag/correlation')
    elif name == 'event_timeline': _labels(d, 'events', len(_array(d, 'time')))
    elif name == 'gantt':
        start, end = _aligned(d, 'start', 'end'); _labels(d, 'tasks', len(start))
        if np.any(start > end): raise ValueError('start must not exceed end')
    elif name == 'calendar_heatmap':
        import pandas as pd
        dates = pd.to_datetime(d['dates'], errors='raise')
        if len(dates) != len(_array(d, 'values')) or dates.isna().any() or dates.normalize().duplicated().any():
            raise ValueError('dates must be unique days aligned with values')
    elif name == 'control_chart':
        _, y, c, lo, hi = _aligned(d, 'time', 'values', 'center', 'lower', 'upper')
        if np.any(lo > c) or np.any(c > hi): raise ValueError('control limits must bracket center')
    elif name == 'time_heatmap':
        a = _array(d, 'matrix', 2); _labels(d, 'row_labels', a.shape[0])
        time = _array(d, 'time')
        if a.shape[1] != len(time) or np.any(np.diff(time) <= 0): raise ValueError('matrix columns must align with increasing time')
    elif name in {'adjacency_matrix', 'diverging_heatmap', 'circular_heatmap', 'clustered_heatmap', 'threshold_heatmap'}:
        a = _array(d, 'matrix', 2); _labels(d, 'row_labels', a.shape[0]); _labels(d, 'column_labels', a.shape[1])
        if name == 'adjacency_matrix' and a.shape[0] != a.shape[1]: raise ValueError('adjacency matrix must be square')
        if name == 'clustered_heatmap':
            for field, count in [('row_linkage', a.shape[0]), ('column_linkage', a.shape[1])]:
                z = _array(d, field, 2)
                if z.shape != (count-1, 4) or not is_valid_linkage(z): raise ValueError(f'invalid {field}')
    elif name == 'dendrogram':
        z = _array(d, 'linkage', 2)
        if not is_valid_linkage(z): raise ValueError('invalid linkage')
        _labels(d, 'labels', len(z)+1)
    elif name == 'faceted_heatmap':
        a = _array(d, 'matrices', 3); _labels(d, 'facets', a.shape[0]); _labels(d, 'row_labels', a.shape[1]); _labels(d, 'column_labels', a.shape[2])
    elif name in {'contour', 'spatial_heatmap', 'response_surface_opt', 'parameter_response', 'constraint_boundary', 'feasible_region', 'feasible_heatmap'}:
        x, y = _array(d, 'x_grid'), _array(d, 'y_grid')
        field = 'feasible' if name.startswith('feasible') else 'constraint' if name == 'constraint_boundary' else 'z'
        z = _array(d, field, 2)
        if min(len(x), len(y)) < 2 or not np.all(np.diff(x) > 0) or not np.all(np.diff(y) > 0) or z.shape != (len(y), len(x)):
            raise ValueError('grid axes must increase and grid shape must be (len(y_grid),len(x_grid))')
        if field == 'feasible' and not np.all(np.isin(z, [0, 1])): raise ValueError('feasible must be boolean/0-1')
        if name == 'response_surface_opt' and d['direction'] not in {'min', 'max'}: raise ValueError('direction must be min or max')
        if name == 'parameter_response': _labels(d, 'parameters', 2)
    elif name in {'spatial_3d', 'contour_density', 'joint_density', 'hexbin', 'volcano'}:
        arrays = _aligned(d, *(['x', 'y', 'z'] if name == 'spatial_3d' else ['x', 'y']))
        if name in {'joint_density', 'contour_density'}:
            if len(arrays[0]) < 3 or np.linalg.matrix_rank(np.cov(arrays)) < 2: raise ValueError('density needs nondegenerate paired samples')
        if name == 'volcano' and np.any((arrays[1] <= 0) | (arrays[1] > 1)): raise ValueError('volcano.y must be p values in (0,1]')
    elif name == 'spatial_scatter':
        lon, lat, size = _aligned(d, 'longitude', 'latitude', 'size'); _labels(d, 'group', len(lon))
        if np.any(np.abs(lon) > 180) or np.any(np.abs(lat) > 90) or np.any(size < 0): raise ValueError('invalid longitude, latitude or size')
    elif name == 'partial_correlation':
        a = _array(d, 'matrix', 2); _labels(d, 'labels', len(a))
        if a.shape[0] != a.shape[1] or not np.allclose(a, a.T) or np.any(np.abs(a) > 1+1e-9): raise ValueError('invalid correlation matrix')
        _labels(d, 'control_labels', len(d['control_labels']))
    elif name in {'parallel_coordinates', 'high_dim_density'}:
        a = _array(d, 'data', 2); _labels(d, 'features', a.shape[1])
        if a.shape[1] < 2: raise ValueError('needs at least two variables')
    elif name == 'separation_loadings':
        a = _array(d, 'loadings', 2); _labels(d, 'labels', len(a)); _labels(d, 'components', a.shape[1])
    elif name in {'shap_summary', 'shap_beeswarm'}:
        a = _array(d, 'attributions', 2); _labels(d, 'feature_names', a.shape[1])
        if name == 'shap_beeswarm' and _array(d, 'features', 2).shape != a.shape: raise ValueError('features must align with attributions')
    elif name in {'partial_dependence', 'ice'}:
        g = _array(d, 'grid')
        if not np.all(np.diff(g) > 0): raise ValueError('grid must increase')
        a = _array(d, 'response') if name == 'partial_dependence' else _array(d, 'curves', 2)
        if a.shape[-1] != len(g): raise ValueError('responses must align with feature grid')
    elif name == 'taylor_diagram':
        s, c = _aligned(d, 'std', 'correlation'); _labels(d, 'labels', len(s))
        if not np.isfinite(d['reference_std']) or d['reference_std'] <= 0 or np.any(s < 0) or np.any(np.abs(c) > 1): raise ValueError('invalid Taylor statistics')
    elif name == 'mantel':
        a, b = _aligned(d, 'distance_a', 'distance_b')
        if np.any(a < 0) or np.any(b < 0) or np.std(a) == 0 or np.std(b) == 0: raise ValueError('Mantel needs nonconstant positive distances')
        if not np.isclose(np.corrcoef(a, b)[0, 1], d['r']) or not 0 <= d['p'] <= 1 or not isinstance(d['permutations'], int) or d['permutations'] < 1:
            raise ValueError('invalid Mantel test result')
    elif name == 'lift_gain':
        fraction, gain, lift = _aligned(d, 'population_fraction', 'gain', 'lift')
        if np.any((fraction <= 0) | (fraction > 1)) or not np.all(np.diff(fraction) > 0) or np.any((gain < 0) | (gain > 1)) or not np.allclose(lift, gain/fraction): raise ValueError('invalid lift/gain result')
    elif name == 'coverage':
        a, b = _aligned(d, 'nominal', 'empirical')
        if np.any((a < 0) | (a > 1) | (b < 0) | (b > 1)): raise ValueError('coverage must be in [0,1]')
    elif name == 'calibration_curve':
        a, b = _aligned(d, 'probability', 'observed_rate')
        if np.any((a < 0) | (a > 1) | (b < 0) | (b > 1)): raise ValueError('calibration probabilities and observed rates must lie in [0,1]')
    elif name in {'residual_distribution', 'error_by_time'}:
        a, b = _aligned(d, 'observed', 'predicted')
        if name == 'error_by_time' and len(_array(d, 'time')) != len(a): raise ValueError('time must align with predictions')
    elif name == 'cross_validation': _labels(d, 'fold', len(_array(d, 'score')))
    elif name == 'model_interval':
        c, lo, hi = _aligned(d, 'center', 'lower', 'upper')
        if np.any(lo > c) or np.any(c > hi): raise ValueError('interval must bracket center')
    elif name == 'repeated_convergence':
        a = _array(d, 'objectives', 2); _labels(d, 'runs', len(a))
        if a.shape[1] != len(_array(d, 'iterations')): raise ValueError('objectives must be run-by-iteration')
    elif name == 'optimum_distribution': _labels(d, 'runs', len(_array(d, 'values')))
    elif name == 'cluster_stability':
        a = _array(d, 'scores', 2); _labels(d, 'settings', len(a)); _labels(d, 'runs', a.shape[1])
    elif name in {'response_1d', 'perturbation'}: _aligned(d, 'x', 'response')
    elif name == 'scenario':
        a = _array(d, 'responses', 2); _labels(d, 'scenarios', len(a))
        if a.shape[1] != len(_array(d, 'x')): raise ValueError('responses must be scenario-by-x')
    elif name == 'state_trajectory':
        a = _array(d, 'states', 2); _labels(d, 'dimensions', a.shape[1])
        if a.shape[1] not in {2, 3} or len(a) != len(_array(d, 'time')): raise ValueError('states must be time-by-2/3 dimensions')
    elif name == 'constraint_slack': _labels(d, 'constraints', len(_array(d, 'slack')))
    elif name == 'global_local':
        a, _ = _aligned(d, 'local', 'global_values'); _labels(d, 'parameters', len(a))
    elif name == 'risk_return':
        a, b = _aligned(d, 'risk', 'returns'); _labels(d, 'labels', len(a))
        if np.any(a < 0): raise ValueError('risk cannot be negative')
    elif name == 'weight_sensitivity':
        a = _array(d, 'scores', 2); _labels(d, 'schemes', len(a))
        if a.shape[1] != len(_array(d, 'weights')) or np.any((_array(d, 'weights') < 0) | (_array(d, 'weights') > 1)): raise ValueError('scores must align with weights in [0,1]')
    elif name == 'contribution_decomposition': _labels(d, 'components', len(_array(d, 'values')))
    elif name == 'tornado':
        a, _ = _aligned(d, 'low', 'high'); _labels(d, 'parameters', len(a))
    elif name in GRAPH_KEYS:
        nodes = list(d['nodes']); _labels(d, 'nodes', len(nodes))
        if len(set(nodes)) != len(nodes): raise ValueError('nodes must be unique')
        graph = nx.DiGraph(); graph.add_nodes_from(nodes)
        for edge in d['edges']:
            if len(edge) != 2 or any(v not in nodes for v in edge): raise ValueError('edges must reference declared nodes')
            graph.add_edge(*edge)
        if name in {'decision_tree', 'task_decomposition'} and (not nx.is_directed_acyclic_graph(graph) or any(v > 1 for _, v in graph.in_degree()) or len([v for _, v in graph.in_degree() if v == 0]) != 1): raise ValueError('requires one rooted tree')
        if 'positions' in d and (set(d['positions']) != set(nodes) or any(np.asarray(v).shape != (2,) or not np.isfinite(v).all() for v in d['positions'].values())): raise ValueError('positions must supply finite 2D coordinates for every node')
        if 'edge_labels' in d: _labels(d, 'edge_labels', len(d['edges']))
        if 'stages' in d: _labels(d, 'stages', len(nodes))
        if name == 'algorithm_flow':
            types = _labels(d, 'node_types', len(nodes))
            if any(v not in {'start', 'process', 'decision', 'end'} for v in types): raise ValueError('invalid algorithm node_types')
        if name == 'input_model_validation_output' and not {'输入', '模型', '验证', '输出'}.issubset(set(d['stages'])):
            raise ValueError('pipeline stages must include input/model/validation/output')
        if name == 'state_machine': _labels(d, 'events', len(d['edges']))
        if name == 'state_transition':
            p = _array(d, 'probabilities')
            if len(p) != len(d['edges']) or np.any((p < 0) | (p > 1)): raise ValueError('invalid transition probabilities')
            for node in nodes:
                values = [p[i] for i,e in enumerate(d['edges']) if e[0] == node]
                if values and not np.isclose(sum(values), 1): raise ValueError('outgoing probabilities must sum to one')
    elif name == 'geometry':
        points = _array(d, 'points', 2)
        if points.shape[1] != 2: raise ValueError('geometry.points must be Nx2')
        for field, minimum in [('segments', 2), ('polygons', 3)]:
            for indices in d[field]:
                if len(indices) < minimum or (field == 'segments' and len(indices) != 2) or any(not isinstance(i, (int, np.integer)) or not 0 <= i < len(points) for i in indices): raise ValueError(f'invalid {field} point indices')
    elif name == 'coordinate_system':
        origin, basis = _array(d, 'origin'), _array(d, 'basis', 2)
        if len(origin) not in {2, 3} or basis.shape != (len(origin), len(origin)) or np.linalg.matrix_rank(basis) != len(origin): raise ValueError('basis must be an independent 2D/3D coordinate basis')
    # Scalars and semantic strings are checked even when not used as array axes.
    for field in ('threshold', 'baseline', 'limit'):
        if field in d and (np.ndim(d[field]) != 0 or not np.isfinite(d[field])): raise ValueError(f'{field} must be finite scalar')
    for field in ('method', 'metric', 'effect_kind', 'interval_kind', 'parameter', 'feature_name', 'distribution'):
        if field in d and not str(d[field]).strip(): raise ValueError(f'{field} cannot be empty')
    if 'time' in d and name not in {'event_timeline'}:
        if not np.all(np.diff(_array(d, 'time')) > 0): raise ValueError('time must increase')


def _axis(ax=None, projection=None):
    return ax if ax is not None else _style.subplots(subplot_kw={'projection': projection} if projection else {}, constrained_layout=True)[1]


def _ticks(axis, labels, horizontal=False):
    wrapped = [textwrap.fill(str(v), 10) for v in labels]
    if horizontal: axis.set_yticks(range(len(labels)), wrapped)
    else: axis.set_xticks(range(len(labels)), wrapped, rotation=25 if len(labels) > 4 else 0, ha='right' if len(labels) > 4 else 'center')


def _curves(axis, x, curves, labels):
    for i, (row, label) in enumerate(zip(curves, labels)):
        axis.plot(x, row, color=PALETTE[i % len(PALETTE)], ls=LINES[i % 4], label=str(label), lw=_style.stroke(1.4))
    if len(labels) > 4:
        config = _style.current_config()
        columns = 2 if config and config['width_mm'] < 100 else 3
        axis.figure.legend(*axis.get_legend_handles_labels(), frameon=False,
                           loc='outside upper center', ncol=columns)
    else:
        axis.legend(frameon=False)


def render(name, *, title=None, ax=None, contract=None, **d):
    validate(name, d)
    metadata = {'semantic_key': name, 'input_fields': list(FIELDS[name]), 'calculation': d.get('calculation', {}), 'interval_kind': d.get('interval_kind', 'none')}
    axis = None
    if name in BAR_KEYS:
        values = _array(d, 'values'); labels = list(d['categories']); order = np.arange(len(values))
        if name in {'ranking', 'scenario_ranking'}:
            order = np.argsort(values if d['direction'] == 'min' else -values, kind='stable')
            from scipy.stats import rankdata
            metadata['ranks'] = rankdata(values if d['direction'] == 'min' else -values, method='min').astype(int).tolist()
        if name == 'feature_importance': order = np.argsort(-values, kind='stable')
        axis = _axis(ax); horizontal = name != 'score_bar'
        if name in {'lollipop', 'cleveland_dot'}:
            if name == 'lollipop': axis.hlines(range(len(values)), 0, values, color=PALETTE[0])
            axis.scatter(values, range(len(values)), marker='D' if name == 'cleveland_dot' else 'o', color=PALETTE[0])
        elif horizontal:
            axis.barh(range(len(values)), values[order], color=[PALETTE[0] if v >= 0 else PALETTE[1] for v in values[order]], edgecolor='#44515b', linewidth=_style.stroke(0.4))
            axis.axvline(0, color='#555555', lw=_style.stroke(0.7))
        else: axis.bar(range(len(values)), values, color=PALETTE[0], edgecolor='#44515b', hatch='//')
        _ticks(axis, [labels[i] for i in order], horizontal); metadata.update(values=values.tolist(), order=order.tolist())
        if horizontal: axis.invert_yaxis()
        axis.set(xlabel=d.get('method', d.get('score_kind', '数值')) if horizontal else '对象', ylabel='对象' if horizontal else d.get('score_kind', '得分'))
    elif name == 'effect_size':
        from .comparisons import forest
        fig = forest(d['categories'], d['estimate'], d['lower'], d['upper'], interval_kind=d['interval_kind'], contract=contract, ax=ax)
        axis = fig.axes[0]; axis.set_xlabel(f"{d['effect_kind']} ({d['interval_kind']})")
    elif name == 'percent_stacked_bar':
        from .validated import stacked_bar
        values = _array(d, 'values', 2); percentage = values / values.sum(1, keepdims=True)*100
        fig = stacked_bar(d['categories'], percentage, d['groups'], contract=contract, ax=ax)
        axis = fig.axes[0]; axis.set_ylabel('占比 (%)'); metadata['normalized_values'] = percentage.tolist()
    elif name == 'multi_metric_comparison':
        axis = _axis(ax); values = _array(d, 'values', 2)
        for i, row in enumerate(values): axis.plot(range(values.shape[1]), row, marker=MARKERS[i % 7], ls=LINES[i % 4], label=d['categories'][i], color=PALETTE[i % len(PALETTE)])
        _ticks(axis, d['metrics']); axis.figure.legend(*axis.get_legend_handles_labels(),frameon=False,loc='outside upper center',ncol=3); axis.set(xlabel='指标', ylabel='指标值（须可比尺度）')
    elif name in {'raw_points', 'jitter', 'beeswarm'}:
        axis = _axis(ax); rng = np.random.default_rng(d.get('seed', 0)); count = 0
        for i, sample in enumerate(d['samples']):
            y = np.asarray(sample); offset = np.zeros(len(y))
            if name == 'jitter': offset = rng.uniform(-.18, .18, len(y))
            if name == 'beeswarm':
                # Deterministic local bins spread coincident observations; never drop points.
                bins = np.round((y-y.min()) / max(np.ptp(y), 1e-9)*20).astype(int)
                for b in np.unique(bins):
                    ids = np.where(bins == b)[0]; offset[ids] = (np.arange(len(ids))-(len(ids)-1)/2)*min(.07, .35/max(len(ids), 1))
            horizontal = d.get('orientation', 'vertical') == 'horizontal'
            axis.scatter(y if horizontal else i+offset, i+offset if horizontal else y, s=_style.marker(14, area=True), marker=MARKERS[i % 7], color=PALETTE[i % len(PALETTE)], alpha=.8); count += len(y)
        if d.get('orientation', 'vertical') == 'horizontal':
            axis.set_yticks(range(len(d['categories'])), d['categories'])
            axis.set(xlabel='观测值', ylabel='类别')
        else:
            _ticks(axis, d['categories']); axis.set(xlabel='类别', ylabel='观测值')
        metadata.update(observation_count=count, display_jitter=name, seed=d.get('seed', 0), orientation=d.get('orientation', 'vertical'))
    elif name == 'probability_plot':
        axis = _axis(ax); axis.scatter(d['theoretical'], d['observed'], s=_style.marker(18, area=True), color=PALETTE[0]); axis.set(xlabel=f"理论分位数 ({d['distribution']})", ylabel='观测分位数')
    elif name == 'pareto_distribution':
        axis = _axis(ax); y = np.sort(d['values']); survival = (len(y)-np.arange(len(y))) / len(y)
        axis.step(y, survival, where='post', color=PALETTE[0]); axis.set(xscale='log', yscale='log', xlabel='正值观测（对数）', ylabel='经验尾概率（对数）'); metadata['survival'] = survival.tolist()
    elif name in {'area', 'step', 'multi_series', 'stacked_area', 'rolling_mean', 'threshold_crossing', 'control_chart'}:
        axis = _axis(ax); t = _array(d, 'time')
        if name == 'area': axis.fill_between(t, 0, d['values'], color=PALETTE[0], alpha=.6)
        elif name == 'step': axis.step(t, d['values'], where='post', color=PALETTE[0])
        elif name == 'multi_series': _curves(axis, t, _array(d, 'values', 2).T, d['groups'])
        elif name == 'stacked_area':
            stacks = axis.stackplot(t, _array(d, 'values', 2).T, labels=d['groups'], colors=PALETTE)
            for i, stack in enumerate(stacks): stack.set_hatch(['', '//', '..', 'xx'][i % 4])
            axis.legend(frameon=False)
        elif name == 'rolling_mean': axis.plot(t, d['center'], color=PALETTE[0], label=f"窗口={d['window']}"); axis.legend(frameon=False)
        elif name == 'threshold_crossing':
            y = _array(d, 'values'); axis.plot(t, y, color=PALETTE[0]); axis.axhline(d['threshold'], color=PALETTE[1], ls='--', label='阈值')
            cross = np.where((y[:-1]-d['threshold'])*(y[1:]-d['threshold']) < 0)[0]; axis.scatter(t[cross+1], y[cross+1], marker='X', color=PALETTE[1]); metadata['crossing_indices'] = (cross+1).tolist(); axis.legend(frameon=False)
        else:
            _curves(axis, t, [d['values'], d['center'], d['lower'], d['upper']], ['观测', '中心', '下控制限', '上控制限'])
            outside = (np.asarray(d['values']) < d['lower']) | (np.asarray(d['values']) > d['upper'])
            axis.scatter(t[outside], np.asarray(d['values'])[outside], marker='X', color=PALETTE[1],label='超出控制限')
            axis.get_legend().remove()
            config=_style.current_config()
            columns=2 if config and config['width_mm'] < 100 else 3
            if config and config['width_mm'] < 100:
                from matplotlib.ticker import MaxNLocator
                axis.xaxis.set_major_locator(MaxNLocator(nbins=4,min_n_ticks=3))
            axis.figure.legend(*axis.get_legend_handles_labels(),frameon=False,loc='outside upper center',ncol=columns)
            metadata['out_of_control'] = np.where(outside)[0].tolist()
        axis.set(xlabel='时间', ylabel='数值')
    elif name == 'decomposition':
        if ax is not None: raise ValueError('decomposition requires its own four panels')
        fig, axes = _style.subplots(4, 1, sharex=True, figsize=(6, 6), constrained_layout=True)
        for a, field, label in zip(axes, ['values', 'trend', 'seasonal', 'residual'], ['观测', '趋势', '季节', '残差']): a.plot(d['time'], d[field], color=PALETTE[0]); a.set_ylabel(label)
        axes[-1].set_xlabel('时间'); axis = axes[0]
    elif name in {'autocorrelation', 'partial_autocorrelation'}:
        axis = _axis(ax); axis.vlines(d['lag'], 0, d['correlation'], color=PALETTE[0]); axis.scatter(d['lag'], d['correlation'], s=_style.marker(18, area=True), color=PALETTE[0]); axis.axhline(0, color='#555555', lw=_style.stroke(0.7)); axis.set(xlabel='滞后', ylabel='ACF' if name == 'autocorrelation' else 'PACF')
    elif name in {'event_timeline', 'gantt'}:
        axis = _axis(ax)
        if name == 'gantt': axis.barh(range(len(d['tasks'])), _array(d, 'end')-_array(d, 'start'), left=d['start'], color=PALETTE[0], hatch='//'); _ticks(axis, d['tasks'], True); axis.set_ylabel('任务')
        else:
            axis.hlines(0, min(d['time']), max(d['time']), color='#555555')
            for i, (t, event) in enumerate(zip(d['time'], d['events'])): axis.vlines(t, 0, 1 if i % 2 else -1, color=PALETTE[0]); axis.text(t, 1.15 if i % 2 else -1.15, textwrap.fill(str(event), 10), ha='center', va='bottom' if i % 2 else 'top', fontsize=_style.font('text', 7))
            axis.set_ylim(-2, 2); axis.set_yticks([]); axis.set_ylabel('事件')
        axis.set_xlabel('时间')
    elif name == 'calendar_heatmap':
        import pandas as pd
        dates = pd.DatetimeIndex(pd.to_datetime(d['dates'])); years = sorted(set(dates.year)); grid = np.full((7*len(years), 54), np.nan)
        for date, value in zip(dates, d['values']):
            offset = pd.Timestamp(date.year, 1, 1).weekday(); week = (date.dayofyear-1+offset)//7
            grid[years.index(date.year)*7+date.weekday(), week] = value
        axis = _axis(ax); image = axis.imshow(np.ma.masked_invalid(grid), aspect='auto', cmap=_style.cmap('sequential', 'viridis')); axis.figure.colorbar(image, ax=axis, label='观测值'); axis.set_yticks([i*7+3 for i in range(len(years))], years); axis.set(xlabel='年内周（周一开始）', ylabel='年份 / 星期')
    elif name in {'adjacency_matrix', 'diverging_heatmap', 'circular_heatmap', 'clustered_heatmap', 'threshold_heatmap', 'partial_correlation', 'time_heatmap'}:
        a = _array(d, 'matrix', 2); rows = list(d.get('row_labels', d.get('labels', range(a.shape[0])))); cols = list(d.get('column_labels', d.get('labels', range(a.shape[1]))))
        if name == 'clustered_heatmap':
            if ax is not None: raise ValueError('clustered_heatmap needs its own dendrogram panels')
            fig = _style.figure(figsize=(6, 5), constrained_layout=True); gs = fig.add_gridspec(2, 2, width_ratios=[1, 4], height_ratios=[1, 4])
            dendrogram(d['row_linkage'], ax=fig.add_subplot(gs[1, 0]), orientation='left', no_labels=True, color_threshold=0, above_threshold_color='#555555')
            dendrogram(d['column_linkage'], ax=fig.add_subplot(gs[0, 1]), no_labels=True, color_threshold=0, above_threshold_color='#555555')
            ri, ci = leaves_list(d['row_linkage']), leaves_list(d['column_linkage']); a = a[np.ix_(ri, ci)]; rows = [rows[i] for i in ri]; cols = [cols[i] for i in ci]; axis = fig.add_subplot(gs[1, 1]); metadata.update(row_order=ri.tolist(), column_order=ci.tolist())
        elif name == 'circular_heatmap':
            axis,row_codes = _style.node_axes(rows, ax)
            if axis.name != 'polar':
                if ax is not None: raise ValueError('circular_heatmap requires polar ax or automatic layout')
                fig = axis.figure; spec = axis.get_subplotspec(); axis.remove(); axis = fig.add_subplot(spec, projection='polar')
            metadata['row_label_key'] = getattr(axis.figure, '_node_label_key', {})
            if metadata['row_label_key']:
                for key_axis in axis.figure.axes:
                    if getattr(key_axis, '_model_label_key', False):
                        for text in key_axis.texts:
                            text.set_text(text.get_text().replace('N', '圈', 1))
                metadata['row_label_key'] = {code.replace('N', '圈', 1): value for code, value in metadata['row_label_key'].items()}
        else: axis = _axis(ax)
        if name == 'circular_heatmap':
            from matplotlib.cm import ScalarMappable
            from matplotlib.colors import Normalize
            norm = Normalize(vmin=a.min(), vmax=a.max() if a.max() != a.min() else a.min()+1)
            image = ScalarMappable(norm=norm, cmap=_style.cmap('sequential', 'viridis'))
            for i, j in np.ndindex(a.shape):
                axis.bar(j*2*np.pi/a.shape[1], 1, bottom=i, width=2*np.pi/a.shape[1],
                         align='edge', color=image.to_rgba(a[i,j]), linewidth=0, edgecolor='none')
            axis.set_ylim(0, a.shape[0])
            axis.set_xticks((np.arange(a.shape[1])+.5)*2*np.pi/a.shape[1], cols)
            axis.tick_params(axis='x', pad=12)
            axis.set_yticks([])
            if not metadata['row_label_key']:
                from matplotlib.lines import Line2D
                axis.figure.legend(handles=[Line2D([], [], linestyle='', label=f'第{i+1}圈：{row}') for i, row in enumerate(rows)],
                                   loc='outside lower center', ncol=2, frameon=False)
            metadata['angular_tessellation'] = {'subdivisions_per_cell': 1, 'meaning': 'one true polar arc per source cell; no artificial radial subdivisions'}
        elif name == 'time_heatmap':
            time = _array(d, 'time')
            edges = np.r_[time[0]-.5, time[0]+.5] if len(time)==1 else np.r_[time[0]-(time[1]-time[0])/2, (time[:-1]+time[1:])/2, time[-1]+(time[-1]-time[-2])/2]
            image = axis.pcolormesh(edges, np.arange(a.shape[0]+1)-.5, a,
                                    cmap=_style.cmap('sequential', 'viridis'), shading='flat')
            axis.set_yticks(range(len(rows)), rows); axis.invert_yaxis()
            shown = np.unique(np.linspace(0, len(time)-1, min(6, len(time)), dtype=int))
            axis.set_xticks(time[shown], [f'{value:g}' for value in time[shown]])
            metadata.update(time=time.tolist(), time_edges=edges.tolist(), time_encoding='actual time centers with midpoint cell boundaries')
        else:
            diverging = name in {'diverging_heatmap', 'partial_correlation', 'threshold_heatmap'}
            cmap = _style.cmap('diverging' if diverging else 'sequential', 'coolwarm' if diverging else 'viridis')
            limit = 1 if name == 'partial_correlation' else max(abs(a.min()), abs(a.max()), 1e-12)
            kwargs = {'vmin': -limit, 'vmax': limit} if diverging else {}
            image = axis.imshow(a, cmap=cmap, aspect='auto', **kwargs); axis.set_yticks(range(len(rows)), rows); axis.set_xticks(range(len(cols)), cols, rotation=35, ha='right')
            if name in {'diverging_heatmap', 'partial_correlation', 'threshold_heatmap'}:
                for i, j in np.ndindex(a.shape):
                    value = a[i,j]
                    label = f'{value:+.2f}' if max(a.shape) <= 6 else '+' if value > 0 else '−' if value < 0 else '0'
                    if name == 'threshold_heatmap' and value >= d['threshold']: label += '×'
                    rgb = image.cmap(image.norm(value))[:3]
                    ink = 'white' if np.dot(rgb, [.2126,.7152,.0722]) < .5 else '#111111'
                    axis.text(j, i, label, ha='center', va='center', color=ink, fontsize=_style.font('tick', 8))
        color_label = f"矩阵值；× 表示 ≥ {d['threshold']:g}" if name == 'threshold_heatmap' else '矩阵值'
        axis.figure.colorbar(image, ax=axis, label=color_label); axis.set(xlabel='时间' if name == 'time_heatmap' else '列变量（圈次由内向外递增）' if name == 'circular_heatmap' else '列变量', ylabel='' if name == 'circular_heatmap' else '行变量'); metadata['matrix'] = a.tolist()
    elif name == 'faceted_heatmap':
        if ax is not None: raise ValueError('faceted_heatmap needs separate panels')
        a = _array(d, 'matrices', 3)
        long = any(len(str(label)) > 12 for label in (*d['row_labels'], *d['column_labels']))
        cfg = _style.current_config()
        vertical = long or (cfg is not None and cfg['width_mm'] < 100)
        columns = 1 if vertical or a.shape[2] > 6 else min(2, len(a))
        rows_count = int(np.ceil(len(a)/columns))
        fig, axes = _style.subplots(rows_count, columns, squeeze=False, figsize=(max(6, 3*columns), 4*rows_count), constrained_layout=True)
        for i, a_i in enumerate(a):
            panel = axes.ravel()[i]; image = panel.imshow(a_i, vmin=a.min(), vmax=a.max(), cmap=_style.cmap('sequential', 'viridis'), aspect='auto'); panel.set_title(d['facets'][i]); panel.set_xticks(range(a.shape[2]), d['column_labels'], rotation=30); panel.set_yticks(range(a.shape[1]), d['row_labels']); panel.set(xlabel='列', ylabel='行')
        for unused in axes.ravel()[len(a):]: unused.set_visible(False)
        fig.colorbar(image, ax=list(axes.ravel()[:len(a)]), label='共享数值'); axis = axes[0,0]
    elif name == 'dendrogram':
        axis = _axis(ax)
        horizontal = len(d['labels']) > 8 or any(len(str(label)) > 10 for label in d['labels'])
        result = dendrogram(d['linkage'], labels=d['labels'], ax=axis,
                            orientation='right' if horizontal else 'bottom', leaf_rotation=0,
                            leaf_font_size=_style.font('tick', 8), color_threshold=0, above_threshold_color=PALETTE[0])
        axis.set(xlabel='链接距离' if horizontal else '对象', ylabel='对象' if horizontal else '链接距离')
        metadata.update(leaf_order=result['leaves'], orientation='right' if horizontal else 'bottom')
    elif name in {'contour', 'spatial_heatmap', 'response_surface_opt', 'parameter_response', 'feasible_region', 'feasible_heatmap', 'constraint_boundary'}:
        axis = _axis(ax); x, y = d['x_grid'], d['y_grid']; field = 'feasible' if name.startswith('feasible') else 'constraint' if name == 'constraint_boundary' else 'z'; z = _array(d, field, 2)
        if name == 'contour':
            image = axis.contour(x,y,z, levels=9, **_contour_ink(), linewidths=_style.stroke(1))
            axis.clabel(image, fontsize=_style.font('text', 7), colors='#222222')
            axis.use_sticky_edges = False
            axis.margins(.08)
        elif name == 'spatial_heatmap': image = axis.pcolormesh(x,y,z,cmap=_style.cmap('sequential', 'viridis'),shading='auto'); axis.figure.colorbar(image,ax=axis,label='空间网格值'); axis.set_aspect('equal')
        elif name in {'feasible_region', 'feasible_heatmap'}:
            image = axis.pcolormesh(x,y,z,cmap=_style.cmap('sequential', 'Greys'),vmin=0,vmax=1,shading='auto')
            if name == 'feasible_region': axis.contourf(x,y,z,levels=[.5,1.5],colors='none',hatches=['//'])
            axis.figure.colorbar(image,ax=axis,ticks=[0,1],label='可行性（0/1）')
        elif name == 'constraint_boundary':
            image = axis.contour(x,y,z,levels=[d['limit']],colors=PALETTE[1]); axis.clabel(image,fontsize=_style.font('text', 7)); axis.contourf(x,y,z,levels=[z.min()-1, d['limit']],colors=[PALETTE[0]],alpha=.25)
        else:
            image = axis.contourf(x,y,z,levels=12,cmap=_style.cmap('sequential', 'viridis')); axis.figure.colorbar(image,ax=axis,label='响应值')
            if name == 'response_surface_opt':
                index = np.unravel_index(np.argmin(z) if d['direction'] == 'min' else np.argmax(z), z.shape); axis.scatter([x[index[1]]],[y[index[0]]],marker='*',s=_style.marker(100, area=True),color='#111111',edgecolor='white',label='网格最优'); axis.legend(frameon=False); metadata['optimum'] = [float(x[index[1]]), float(y[index[0]]), float(z[index])]
        axis.set(xlabel=d.get('parameters', ['空间 / 参数 X', '空间 / 参数 Y'])[0], ylabel=d.get('parameters', ['空间 / 参数 X', '空间 / 参数 Y'])[1]); metadata['grid_shape'] = list(z.shape)
    elif name == 'spatial_3d':
        axis = _axis(ax, '3d'); axis.scatter(d['x'],d['y'],d['z'],color=PALETTE[0],marker='o',s=_style.marker(20, area=True)); axis.set(xlabel='空间 X',ylabel='空间 Y',zlabel='空间 Z'); metadata['dimensions'] = 3
        # 3D axes retain out-of-range tick artists that are not actually drawn.
        # Use only ticks inside the data limits so export audits inspect real text.
        for dim in ('x', 'y', 'z'):
            bounds = getattr(axis, f'get_{dim}lim')()
            ticks = getattr(axis, f'get_{dim}ticks')()
            getattr(axis, f'set_{dim}ticks')([t for t in ticks if min(bounds) <= t <= max(bounds)])
    elif name == 'spatial_scatter':
        axis = _axis(ax); groups = list(dict.fromkeys(d['group']))
        for i,g in enumerate(groups):
            keep = np.asarray(d['group']) == g; axis.scatter(np.asarray(d['longitude'])[keep], np.asarray(d['latitude'])[keep], s=np.asarray(d['size'])[keep]*5, marker=MARKERS[i % 7], color=PALETTE[i % len(PALETTE)], label=str(g), edgecolor='#44515b',linewidths=_style.stroke(0.4))
        axis.figure.legend(*axis.get_legend_handles_labels(),frameon=False,loc='outside upper center',ncol=3); axis.set(xlabel='经度 (°)',ylabel='纬度 (°)')
    elif name in {'joint_density', 'contour_density', 'hexbin', 'volcano'}:
        axis = _axis(ax); x,y = _array(d,'x'),_array(d,'y')
        if name == 'hexbin': image = _vector_hexbin(axis,x,y,gridsize=d.get('gridsize',22),cmap=_style.cmap('sequential', 'viridis'),mincnt=1); axis.figure.colorbar(image,ax=axis,label='观测数')
        elif name == 'volcano':
            effect_cut = float(d.get('effect_threshold',1)); p_cut = float(d.get('p_threshold',.05)); keep = (np.abs(x) >= effect_cut) & (y <= p_cut)
            axis.scatter(x[~keep],-np.log10(y[~keep]),s=_style.marker(16, area=True),color='#707b83',marker='o'); axis.scatter(x[keep],-np.log10(y[keep]),s=_style.marker(22, area=True),color=PALETTE[1],marker='^',label='达到声明阈值'); axis.axhline(-np.log10(p_cut),ls='--',color='#555555'); axis.axvline(-effect_cut,ls=':',color='#555555'); axis.axvline(effect_cut,ls=':',color='#555555'); axis.legend(frameon=False); axis.set(xlabel='效应（调用者声明尺度）',ylabel='−log10(p)'); metadata['significant_indices'] = np.where(keep)[0].tolist()
        else:
            xx, yy = np.meshgrid(np.linspace(x.min(),x.max(),70), np.linspace(y.min(),y.max(),70)); density = gaussian_kde(np.vstack([x,y]))(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)
            if name == 'joint_density': axis.contourf(xx,yy,density,levels=7,cmap=_style.cmap('sequential', 'Blues'),alpha=.75); axis.scatter(x,y,s=_style.marker(9, area=True),color=_style.color(0, '#405b70'),alpha=.45)
            else:
                contours = axis.contour(xx,yy,density,levels=7,**_contour_ink(),linewidths=_style.stroke(1))
                axis.clabel(contours,fontsize=_style.font('text', 6),colors='#222222')
            axis.margins(.08)
            metadata['density_method'] = 'Gaussian KDE (Scott bandwidth)'
        if name != 'volcano': axis.set(xlabel='变量 X',ylabel='变量 Y')
    elif name in {'parallel_coordinates', 'high_dim_density'}:
        a = _array(d,'data',2)
        if name == 'parallel_coordinates':
            axis = _axis(ax); minimum, span = a.min(0), np.ptp(a,axis=0); scaled = (a-minimum)/np.where(span==0,1,span)
            for row in scaled: axis.plot(range(a.shape[1]),row,color=PALETTE[0],alpha=.4,lw=_style.stroke(0.7))
            _ticks(axis,d['features']); axis.set(xlabel='特征（列内归一化）',ylabel='列内相对位置'); metadata.update(normalization_min=minimum.tolist(),normalization_span=span.tolist(),observation_count=len(a))
        else:
            if ax is not None: raise ValueError('high_dim_density needs pairwise panels')
            n=a.shape[1]; fig,axes=_style.subplots(n,n,figsize=(max(6,1.6*n),max(6,1.6*n)),constrained_layout=True,squeeze=False)
            densities = []
            for i in range(n):
                for j in range(n):
                    panel=axes[i,j]
                    if i==j: panel.hist(a[:,j],bins=15,color=PALETTE[0])
                    else: densities.append(_vector_hexbin(panel,a[:,j],a[:,i],gridsize=12,mincnt=1,cmap=_style.cmap('sequential', 'Blues')))
                    panel.set_xlim(a[:,j].min(),a[:,j].max())
                    panel.set_xticks([a[:,j].min(),a[:,j].max()])
                    if i != j:
                        panel.set_ylim(a[:,i].min(),a[:,i].max())
                        panel.set_yticks([a[:,i].min(),a[:,i].max()])
                    panel.tick_params(labelbottom=i==n-1,labelleft=j==0)
                    from matplotlib.ticker import FormatStrFormatter
                    panel.xaxis.set_major_formatter(FormatStrFormatter('%.1f'))
                    panel.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
                    if i==n-1: panel.set_xlabel(d['features'][j])
                    if j==0: panel.set_ylabel('频数' if i==j else d['features'][i])
            if densities:
                from matplotlib.colors import Normalize
                maximum = max(float(collection.get_array().max()) for collection in densities)
                for collection in densities: collection.set_norm(Normalize(0,maximum))
                fig.colorbar(densities[0],ax=axes.ravel().tolist(),fraction=.025,pad=.015,label='共同观测数')
            axis=axes[0,0]; metadata.update(observation_count=len(a),dimensions=n,
                                          tick_policy='outer axes; actual range endpoints',density_color_domain=[0,maximum] if densities else None)
    elif name == 'separation_loadings':
        a=_array(d,'loadings',2); panels=int(np.ceil(len(a)/20))
        if ax is not None and panels>1: raise ValueError('dense loadings require separate panels')
        if panels>1: fig,axes=_style.subplots(panels,1,figsize=(6,panels*4),constrained_layout=True,squeeze=False); axes=axes.ravel()
        else: axes=[_axis(ax)]
        for i,panel in enumerate(axes):
            start=i*20; stop=min(len(a),start+20); width=.8/a.shape[1]
            for j in range(a.shape[1]): panel.barh(np.arange(stop-start)+(j-(a.shape[1]-1)/2)*width,a[start:stop,j],height=width,label=d['components'][j],hatch=['','//','..','xx'][j%4],color=PALETTE[j%len(PALETTE)])
            _ticks(panel,d['labels'][start:stop],True); panel.set_xlabel(f"载荷 ({d['method']})"); panel.legend(frameon=False); panel.invert_yaxis()
        axis=axes[0]; metadata['loadings']=a.tolist()
    elif name in {'shap_summary','shap_beeswarm'}:
        axis=_axis(ax); a=_array(d,'attributions',2); mean_abs=np.abs(a).mean(0); order=np.argsort(-mean_abs,kind='stable')
        if name=='shap_summary': axis.barh(range(len(order)),mean_abs[order],color=PALETTE[0],hatch='//'); axis.set_xlabel('平均 |SHAP 归因|')
        else:
            features=_array(d,'features',2)
            for row,j in enumerate(order):
                bins = np.floor((a[:,j]-a[:,j].min())/max(np.ptp(a[:,j]),1e-12)*40).astype(int)
                maximum = max(np.bincount(bins))
                step = min(.09, .65/max(maximum, 1))
                offset = np.zeros(len(a))
                for bucket in np.unique(bins):
                    ids = np.flatnonzero(bins == bucket)
                    ranks = np.arange(len(ids))
                    offset[ids] = np.where(ranks % 2, (ranks+1)//2, -ranks//2)*step
                color_value=(features[:,j]-features[:,j].min())/max(np.ptp(features[:,j]),1e-12)
                image=axis.scatter(a[:,j],row+offset,c=color_value,cmap=_style.cmap('sequential', 'viridis'),vmin=0,vmax=1,s=_style.marker(10, area=True),alpha=.9)
            axis.figure.colorbar(image,ax=axis,label='特征内相对值（低 → 高）'); axis.axvline(0,color='#555555',lw=_style.stroke(0.7)); axis.set_xlabel('SHAP 归因')
            metadata['feature_color_min']=features.min(0).tolist(); metadata['feature_color_max']=features.max(0).tolist()
        _ticks(axis,[d['feature_names'][j] for j in order],True); axis.invert_yaxis(); metadata.update(mean_absolute_attribution=mean_abs.tolist(),feature_order=order.tolist(),observation_count=len(a))
    elif name in {'partial_dependence','ice'}:
        axis=_axis(ax)
        if name=='partial_dependence': axis.plot(d['grid'],d['response'],color=PALETTE[0],lw=_style.stroke(1.8))
        else:
            for curve in d['curves']: axis.plot(d['grid'],curve,color=PALETTE[0],alpha=.3,lw=_style.stroke(0.7))
            axis.plot(d['grid'],np.mean(d['curves'],axis=0),color='#111111',ls='--',label='样本均值'); axis.legend(frameon=False)
        axis.set(xlabel=d['feature_name'],ylabel='模型响应')
    elif name=='taylor_diagram':
        axis=_axis(ax,'polar'); std=_array(d,'std'); corr=_array(d,'correlation'); reference=d['reference_std']
        maximum=max(reference,std.max())*1.25; theta=np.linspace(0,np.pi,120); radii=np.linspace(0,maximum,100); th,rr=np.meshgrid(theta,radii)
        centered=np.sqrt(reference**2+rr**2-2*reference*rr*np.cos(th)); contours=axis.contour(th,rr,centered,levels=5,colors='#8b959d',linewidths=_style.stroke(0.7)); axis.clabel(contours,fontsize=_style.font('text', 6))
        for label in contours.labelTexts: label.set_clip_on(False)
        for i,(s,c,label) in enumerate(zip(std,corr,d['labels'])): axis.scatter(np.arccos(c),s,marker=MARKERS[i%7],color=PALETTE[i%len(PALETTE)],label=label,clip_on=False)
        axis.scatter(0,reference,marker='*',s=_style.marker(90, area=True),color='#111111',label='参考',clip_on=False); axis.set_thetamin(0); axis.set_thetamax(180); ticks=np.array([-1,-.5,0,.5,1]); axis.set_xticks(np.arccos(ticks),[str(v) for v in ticks]); axis.set_ylim(0,maximum); axis.set_yticks(np.linspace(maximum/3,maximum,3)); axis.set_rlabel_position(90); axis.set_xlabel('相关系数（角度） / 标准差（半径）'); axis.figure.legend(*axis.get_legend_handles_labels(),frameon=False,loc='outside upper center',ncol=3); metadata.update(std=std.tolist(),correlation=corr.tolist())
    elif name=='mantel':
        axis=_axis(ax); axis.scatter(d['distance_a'],d['distance_b'],color=PALETTE[0],s=_style.marker(18, area=True),alpha=.8); axis.set(xlabel='距离矩阵 A（上三角）',ylabel='距离矩阵 B（上三角）'); axis.text(.03,.97,f"Mantel r={d['r']:.3f}\np={d['p']:.4f}; {d['permutations']} 次置换",transform=axis.transAxes,va='top',fontsize=_style.font('text', 7)); metadata.update(r=d['r'],p=d['p'],permutations=d['permutations'],seed=d['seed'])
    elif name=='lift_gain':
        if ax is not None: raise ValueError('lift_gain requires two panels')
        fig,axes=_style.subplots(1,2,figsize=(7,3.5),constrained_layout=True); axes[0].plot(d['population_fraction'],d['gain'],color=PALETTE[0]); axes[0].plot([0,1],[0,1],ls='--',color='#555555'); axes[1].plot(d['population_fraction'],d['lift'],color=PALETTE[1]); axes[1].axhline(1,ls='--',color='#555555'); axes[0].set(xlabel='样本比例',ylabel='累计增益'); axes[1].set(xlabel='样本比例',ylabel='提升'); axis=axes[0]
    elif name=='coverage':
        axis=_axis(ax); axis.plot(d['nominal'],d['empirical'],marker='s',color=PALETTE[0]); axis.plot([0,1],[0,1],ls='--',color='#555555'); axis.set(xlim=(0,1),ylim=(0,1),xlabel='名义覆盖率',ylabel='实际覆盖率')
    elif name=='calibration_curve':
        axis=_axis(ax); order=np.argsort(d['probability'],kind='stable'); axis.plot(_array(d,'probability')[order],_array(d,'observed_rate')[order],marker='s',color=PALETTE[0],label='实际分箱结果',clip_on=False,zorder=3); axis.plot([0,1],[0,1],ls='--',color='#555555',label='理想校准'); axis.set(xlim=(0,1),ylim=(0,1),xlabel='分箱平均预测概率',ylabel='分箱实际发生率'); axis.legend(frameon=False); metadata['order']=order.tolist()
    elif name in {'residual_distribution','error_by_time','cross_validation','model_interval'}:
        axis=_axis(ax)
        if name in {'residual_distribution','error_by_time'}:
            residual=_array(d,'observed')-_array(d,'predicted'); metadata['residuals']=residual.tolist()
            if name=='residual_distribution': axis.hist(residual,bins='auto',color=PALETTE[0],edgecolor='white'); axis.set(xlabel='观测 − 预测',ylabel='观测数')
            else: axis.plot(d['time'],residual,color=PALETTE[0]); axis.axhline(0,color='#555555',ls='--'); axis.set(xlabel='时间',ylabel='观测 − 预测')
        elif name=='cross_validation': axis.scatter(range(len(d['score'])),d['score'],marker='s',color=PALETTE[0]); _ticks(axis,d['fold']); axis.set(xlabel='实际折',ylabel='折内得分')
        else: axis.errorbar(range(len(d['center'])),d['center'],yerr=[_array(d,'center')-_array(d,'lower'),_array(d,'upper')-_array(d,'center')],fmt='o',color=PALETTE[0],capsize=3,label=d['interval_kind']); axis.legend(frameon=False); axis.set(xlabel='观测 / 模型编号',ylabel='估计值')
    elif name in {'repeated_convergence','scenario','weight_sensitivity'}:
        axis=_axis(ax); x=d['iterations'] if name=='repeated_convergence' else d['weights'] if name=='weight_sensitivity' else d['x']; curves=d['objectives'] if name=='repeated_convergence' else d['scores'] if name=='weight_sensitivity' else d['responses']; labels=d['runs'] if name=='repeated_convergence' else d['schemes'] if name=='weight_sensitivity' else d['scenarios']; _curves(axis,x,curves,labels); axis.set(xlabel='迭代' if name=='repeated_convergence' else '权重' if name=='weight_sensitivity' else '自变量',ylabel='目标值 / 响应')
    elif name=='cluster_stability':
        axis=_axis(ax); a=_array(d,'scores',2); axis.boxplot(list(a),tick_labels=d['settings'],showfliers=False)
        for i,row in enumerate(a): axis.scatter(np.full(len(row),i+1),row,color=PALETTE[i%len(PALETTE)],marker=MARKERS[i%7],s=_style.marker(12, area=True))
        axis.set(xlabel='聚类设置',ylabel=d['metric']); metadata['repetition_count']=a.shape[1]
    elif name=='optimum_distribution':
        axis=_axis(ax); axis.hist(d['values'],bins='auto',color=PALETTE[0]); axis.set(xlabel='各次运行最优目标值',ylabel='运行数'); metadata['run_count']=len(d['runs'])
    elif name in {'response_1d','perturbation'}:
        axis=_axis(ax); axis.plot(d['x'],d['response'],marker='o' if name=='perturbation' else None,color=PALETTE[0]); axis.set(xlabel=d['parameter'],ylabel='扰动响应' if name=='perturbation' else '响应')
    elif name=='state_trajectory':
        states=_array(d,'states',2); axis=_axis(ax,'3d' if states.shape[1]==3 else None); axis.plot(*states.T,color=PALETTE[0]); axis.scatter(*states[[0]].T,marker='o',color='#111111',label='起点'); axis.scatter(*states[[-1]].T,marker='X',color=PALETTE[1],label='终点'); axis.set(xlabel=d['dimensions'][0],ylabel=d['dimensions'][1]); axis.legend(frameon=False)
        if states.shape[1]==3: axis.set_zlabel(d['dimensions'][2])
        metadata['time']=list(d['time'])
    elif name=='constraint_slack':
        axis=_axis(ax); axis.barh(range(len(d['slack'])),d['slack'],color=[PALETTE[0] if v>=0 else PALETTE[1] for v in d['slack']]); _ticks(axis,d['constraints'],True); axis.axvline(0,color='#111111'); axis.set(xlabel='约束余量（负值表示违反）',ylabel='约束')
    elif name=='global_local':
        axis=_axis(ax); y=np.arange(len(d['parameters'])); axis.barh(y-.18,d['local'],height=.35,color=PALETTE[0],label='局部'); axis.barh(y+.18,d['global_values'],height=.35,color=PALETTE[1],hatch='//',label='全局'); _ticks(axis,d['parameters'],True); axis.set(xlabel=d['method'],ylabel='参数'); axis.legend(frameon=False)
    elif name=='risk_return':
        axis=_axis(ax); axis.scatter(d['risk'],d['returns'],color=PALETTE[0],s=_style.marker(30, area=True))
        x,y=_array(d,'risk'),_array(d,'returns')
        span_x=max(float(np.ptp(x)),1e-6); span_y=max(float(np.ptp(y)),1e-6)
        label_x=float(x.max())+.16*span_x
        target_y=np.linspace(y.min(),y.max(),len(y))
        for index,label_y in zip(np.argsort(y,kind='stable'),target_y):
            axis.annotate(textwrap.fill(str(d['labels'][index]),12),(x[index],y[index]),xytext=(label_x,label_y),
                          ha='left',va='center',fontsize=_style.font('text', 7),
                          arrowprops={'arrowstyle':'-','color':'#6B7280','lw':.5})
        axis.set_xlim(x.min()-.08*span_x,x.max()+.75*span_x); axis.set_ylim(y.min()-.08*span_y,y.max()+.08*span_y)
        metadata['label_layout']='ordered side labels with leaders; all point coordinates retained'
        axis.set(xlabel='风险',ylabel='收益')
    elif name=='contribution_decomposition':
        axis=_axis(ax); values=_array(d,'values'); prior=d['baseline']+np.r_[0,np.cumsum(values[:-1])]; axis.bar(range(len(values)),values,bottom=prior,color=[PALETTE[0] if v>=0 else PALETTE[1] for v in values]); _ticks(axis,d['components']); axis.axhline(d['baseline'],ls='--',color='#555555'); axis.set(xlabel='贡献项',ylabel='累计结果'); metadata['total']=float(d['baseline']+values.sum())
    elif name=='tornado':
        axis=_axis(ax); low,high=_aligned(d,'low','high'); order=np.argsort(-np.abs(high-low),kind='stable'); baseline=float(d.get('baseline',0)); y=np.arange(len(low)); axis.barh(y,np.minimum(low,high)[order]-baseline,left=baseline,color=PALETTE[0],height=.5); axis.barh(y,np.maximum(low,high)[order]-baseline,left=baseline,color=PALETTE[1],height=.5,hatch='//'); axis.scatter(low[order],y,marker='o',color='#111111',label='参数低水平'); axis.scatter(high[order],y,marker='s',facecolor='white',edgecolor='#111111',label='参数高水平'); _ticks(axis,[d['parameters'][i] for i in order],True); axis.invert_yaxis(); axis.axvline(baseline,color='#555555'); axis.legend(frameon=False); axis.set(xlabel='参数两端的目标响应',ylabel='参数'); metadata.update(low=low.tolist(),high=high.tolist(),order=order.tolist())
    elif name in GRAPH_KEYS:
        axis,node_labels=_style.node_axes(d['nodes'],ax); graph=nx.Graph() if name=='adjacency' else nx.DiGraph(); graph.add_nodes_from(d['nodes']); graph.add_edges_from(d['edges'])
        if 'positions' in d: pos=d['positions']
        elif 'stages' in d:
            stage_order=list(dict.fromkeys(d['stages'])); pos={}
            vertical = len(stage_order) > 5
            for i,stage in enumerate(stage_order):
                members=[node for node,s in zip(d['nodes'],d['stages']) if s==stage]
                for j,node in enumerate(members): pos[node]=(j,-i) if vertical else (i,-j)
        elif name in {'state_machine','state_transition','adjacency'}: pos=nx.circular_layout(graph)
        elif nx.is_directed_acyclic_graph(graph):
            pos={}
            levels = list(nx.topological_generations(graph))
            vertical = len(levels) > 5 or name in {'decision_tree','task_decomposition'}
            for i,members in enumerate(levels):
                for j,node in enumerate(members): pos[node]=((j-(len(members)-1)/2,-i) if vertical else (i,-j+(len(members)-1)/2))
        else: pos=nx.spring_layout(graph,seed=0)
        node_boxes = {}
        def diamond(x0, y0, width, height, mutation_size):
            pad = .25*mutation_size
            cx, cy = x0+width/2, y0+height/2
            rx, ry = width+pad, height+pad
            return Path([(cx-rx,cy),(cx,cy+ry),(cx+rx,cy),(cx,cy-ry),(cx-rx,cy)],
                        [Path.MOVETO,Path.LINETO,Path.LINETO,Path.LINETO,Path.CLOSEPOLY])
        for i,node in enumerate(d['nodes']):
            x,y=pos[node]
            if name == 'algorithm_flow' and d['node_types'][i] == 'decision':
                text = axis.text(x,y,textwrap.fill(node_labels[node],8),ha='center',va='center',fontsize=_style.font('text', 7),zorder=3,
                                 bbox={'boxstyle':diamond,'facecolor':'white','edgecolor':PALETTE[1]})
            else:
                boxstyle='round,pad=.45' if name != 'algorithm_flow' or d['node_types'][i] in {'start','end'} else 'square,pad=.45'
                text = axis.text(x,y,textwrap.fill(node_labels[node],10),ha='center',va='center',fontsize=_style.font('text', 7),bbox={'boxstyle':boxstyle,'facecolor':'white','edgecolor':PALETTE[i%len(PALETTE)]},zorder=3)
            node_boxes[node] = text.get_bbox_patch()
        if 'stages' in d:
            for stage in dict.fromkeys(d['stages']):
                members=[pos[node] for node,s in zip(d['nodes'],d['stages']) if s==stage]
                if len(set(d['stages'])) > 5:
                    axis.text(min(v[0] for v in members)-.55,np.mean([v[1] for v in members]),str(stage),ha='right',va='center',fontsize=_style.font('text', 8),fontweight='bold')
                else:
                    axis.text(np.mean([v[0] for v in members]),max(v[1] for v in members)+.55,str(stage),ha='center',fontsize=_style.font('text', 8),fontweight='bold')
        labels=d.get('events',d.get('probabilities',d.get('edge_labels',[])))
        keyed_edges = any(len(str(value)) > 10 for value in labels)
        edge_labels = []
        edge_anchors = []
        edge_texts = []
        for i,(u,v) in enumerate(d['edges']):
            a,b=np.asarray(pos[u]),np.asarray(pos[v])
            distance = np.linalg.norm(b-a)
            # A cross-stage edge must clear the intermediate node. Circular
            # layouts need their gentler curve so their outer arcs stay inside.
            direction = b-a
            blocked = any(0 < np.dot(np.asarray(point)-a, direction)/max(distance**2,1e-12) < 1
                          and np.linalg.norm(np.asarray(point)-a-direction*np.dot(np.asarray(point)-a,direction)/max(distance**2,1e-12)) < .05*distance
                          for node,point in pos.items() if node not in {u,v})
            radius = .95 if blocked else .12 if distance < 1.5 else .35
            edge = FancyArrowPatch(a,b,patchA=node_boxes[u],patchB=node_boxes[v],
                                   arrowstyle='-|>' if graph.is_directed() else '-', mutation_scale=10,
                                   shrinkA=2,shrinkB=2,connectionstyle=f'arc3,rad={radius}',color='#555555',zorder=1)
            axis.add_patch(edge)
            if len(labels):
                midpoint=(a+b)/2+radius*.5*np.array([b[1]-a[1],a[0]-b[0]])
                label = f'E{i+1}' if keyed_edges else str(labels[i])
                annotation = _EdgeAnnotation(edge, len(edge_texts), x=midpoint[0], y=midpoint[1], text=label, fontsize=_style.font('text', 6),ha='center',va='center',bbox={'facecolor':'white','edgecolor':'none','pad':1},zorder=4)
                axis.add_artist(annotation)
                edge_texts.append((edge, annotation))
                edge_anchors.append(dict(edge=[u,v],value=labels[i],label=label,position=midpoint.tolist()))
                edge_labels.append(f'{label}：{node_labels[u]} → {node_labels[v]}；{labels[i]}')
        if keyed_edges:
            from matplotlib.lines import Line2D
            axis.figure.legend(handles=[Line2D([],[],linestyle='',label=textwrap.fill(label,26)) for label in edge_labels],
                               loc='outside lower center',frameon=False,ncol=1)
        metadata['edge_annotation_layout'] = edge_anchors
        def place_edge_annotations():
            # Each annotation draws against the final backend's arrow curve
            # and actual text boxes; do not replace its chosen curve parameter.
            axis.figure.canvas.draw()
        axis.figure._publication_layout_finalizers = [*getattr(axis.figure, '_publication_layout_finalizers', []),place_edge_annotations]
        xy=np.asarray(list(pos.values())); axis.set_xlim(xy[:,0].min()-.8,xy[:,0].max()+.8); axis.set_ylim(xy[:,1].min()-.8,xy[:,1].max()+.8); axis.axis('off'); metadata.update(nodes=list(d['nodes']),edges=[list(e) for e in d['edges']],positions={str(k):list(v) for k,v in pos.items()},node_label_key=getattr(axis.figure,'_node_label_key',{}))
    elif name=='geometry':
        axis=_axis(ax); points=_array(d,'points',2)
        for polygon in d['polygons']: axis.add_patch(Polygon(points[list(polygon)],facecolor=PALETTE[0],alpha=.25,edgecolor='#111111',hatch='//'))
        for segment in d['segments']: axis.plot(*points[list(segment)].T,color='#111111',lw=_style.stroke(1.2))
        axis.scatter(*points.T,color=PALETTE[1],s=_style.marker(25, area=True))
        for i,(x,y) in enumerate(points): axis.annotate(str(d.get('labels',list(range(len(points))))[i]),(x,y),xytext=(4,4),textcoords='offset points',fontsize=_style.font('text', 7))
        axis.set_aspect('equal'); axis.set(xlabel='坐标 X',ylabel='坐标 Y'); metadata.update(points=points.tolist(),segments=d['segments'],polygons=d['polygons'])
    elif name=='coordinate_system':
        origin=_array(d,'origin'); basis=_array(d,'basis',2); axis=_axis(ax,'3d' if len(origin)==3 else None)
        for i,vector in enumerate(basis):
            if len(origin)==3: axis.quiver(*origin,*vector,color=PALETTE[i])
            else: axis.annotate('',xy=origin+vector,xytext=origin,arrowprops={'arrowstyle':'->','color':PALETTE[i]})
            axis.text(*(origin+vector),f'e{i+1}',fontsize=_style.font('text', 8))
        points=np.vstack([origin,origin+basis]); axis.set_xlim(points[:,0].min()-1,points[:,0].max()+1); axis.set_ylim(points[:,1].min()-1,points[:,1].max()+1); axis.set(xlabel='X',ylabel='Y')
        if len(origin)==3: axis.set_zlim(points[:,2].min()-1,points[:,2].max()+1); axis.set_zlabel('Z')
        else: axis.set_aspect('equal')
        metadata['basis']=basis.tolist()
    else:
        raise ValueError(f'no dedicated renderer for {name}')
    fig=axis.figure
    for panel in fig.axes:
        if panel.name not in {'3d','polar'} and panel.axison: _finish(panel)
        if panel.images or name in {'circular_heatmap','time_heatmap'}: panel.grid(False, which='both')
    if title:
        if name == 'faceted_heatmap': fig.suptitle(title, fontsize=_style.font('title',9))
        else: axis.set_title(title,fontsize=_style.font('title', 9),pad=10)
    # Keep exact supplied numerical evidence, not a flattened surrogate vector.
    metadata['input_data']={field: d[field] for field in FIELDS[name]}
    return attach_metadata(fig,name=name,contract=contract_from(d,contract),**metadata)


def factory(name, title):
    def draw(**data):
        return render(name,title=title,**data)
    draw.__name__=name
    draw.positional_fields=FIELDS[name]
    return draw
