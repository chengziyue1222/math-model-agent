"""Catalog-wide contract checks and independent numerical/structural examples."""
from collections import Counter
import inspect
import matplotlib.pyplot as plt
import numpy as np
import pytest
from scipy import stats
from matplotlib.patches import Polygon, FancyArrowPatch

from algorithms.figures import get_figure, get_spec, list_figures
from algorithms.figures.examples import example_data
from algorithms.figures import compute


@pytest.mark.parametrize('name', ['violin', 'raincloud'])
def test_distribution_accepts_json_numeric_list(name):
    fig = get_figure(name)(data={'values': [1.0, 2.0, 2.5, 4.0]})
    assert fig._figure_metadata['groups'] == 1
    fig.canvas.draw()
    plt.close(fig)


@pytest.mark.parametrize('case', ['standard', 'dense', 'long_labels'])
@pytest.mark.parametrize('name', list_figures())
def test_all_formal_routes_preserve_evidence(name, case):
    fig = get_figure(name)(data=example_data(name, case=case), mode='formal')
    metadata = fig._figure_metadata
    assert metadata['canonical_key'] == (get_spec(name).to_dict()['alias_of'] or name)
    assert metadata['paper_suitable'] is False
    assert set(get_spec(name).required_fields) <= set(metadata['input_data'])
    assert fig.axes
    plt.close(fig)


@pytest.mark.parametrize('name', list_figures())
def test_every_required_field_is_checked(name):
    data = example_data(name)
    for field in get_spec(name).required_fields:
        missing = dict(data); missing.pop(field)
        with pytest.raises(ValueError, match=field): get_figure(name)(data=missing)


def test_catalog_has_no_placeholder_factories():
    levels = Counter(get_spec(n).implementation_level for n in list_figures())
    assert levels['dedicated'] >= 150 and levels['alias'] == 5
    assert set(levels) == {'dedicated', 'alias'}
    for name in list_figures():
        assert 'academic_catalog_adapter' not in inspect.getsource(get_spec(name).factory)
        assert get_spec(name).to_dict()['formal_supported']


def test_positional_and_keyword_paths_reject_same_bad_dimensions():
    for call in [lambda: get_figure('bar')(['A','B'],[1]),
                 lambda: get_figure('bar')(categories=['A','B'],values=[1]),
                 lambda: get_figure('bar')(data={'categories':['A','B'],'values':[1]}),
                 lambda: get_figure('spatial_3d')([1,2],[1],[2,3])]:
        with pytest.raises(ValueError): call()
    with pytest.raises(ValueError,match='duplicate'): get_figure('bar')(data={'categories':['A'],'values':[1]},values=[2])


def test_rank_ties_direction_and_tornado_reversed_responses():
    fig=get_figure('ranking')(data={'categories':['A','B','C'],'values':[2,2,1],'direction':'max'})
    assert fig._figure_metadata['ranks']==[1,1,3]
    plt.close(fig)
    fig=get_figure('tornado')(data={'parameters':['A','B'],'low':[3,-2],'high':[1,4]})
    assert fig._figure_metadata['low']==[3,-2]
    assert fig._figure_metadata['order']==[1,0]
    plt.close(fig)


def test_spatial_grid_3d_and_real_geometry_structure():
    fig=get_figure('spatial_heatmap')(data=example_data('spatial_heatmap'))
    assert fig._figure_metadata['grid_shape']==[15,15]
    assert any(type(mark).__name__=='QuadMesh' for mark in fig.axes[0].collections)
    plt.close(fig)
    fig=get_figure('spatial_3d')(data=example_data('spatial_3d'))
    assert fig.axes[0].name=='3d'
    plt.close(fig)
    fig=get_figure('geometry')(data=example_data('geometry'))
    assert any(isinstance(p,Polygon) for p in fig.axes[0].patches)
    plt.close(fig)


def test_diagram_branch_tree_and_isolated_nodes():
    data=example_data('algorithm_flow'); fig=get_figure('algorithm_flow')(data=data)
    fig.canvas.draw()
    decision = data['nodes'][data['node_types'].index('decision')]
    label = next(t for t in fig.axes[0].texts if t.get_text().replace('\n','') == decision)
    diamond = label.get_bbox_patch()
    assert len(diamond.get_path().vertices) == 5
    assert diamond.get_window_extent().width/fig.dpi*72 < 75
    assert sum(isinstance(p,FancyArrowPatch) for p in fig.axes[0].patches)==len(data['edges'])
    plt.close(fig)
    data=example_data('dependency_graph'); data['nodes'].append('孤立节点')
    fig=get_figure('dependency_graph')(data=data)
    assert '孤立节点' in fig._figure_metadata['nodes']
    plt.close(fig)
    data=example_data('decision_tree'); data['edges'].append((data['nodes'][1],data['nodes'][2])); data['edge_labels'].append('重复父节点')
    with pytest.raises(ValueError,match='tree'): get_figure('decision_tree')(data=data)


def test_shap_values_and_pdp_ice_use_actual_model_responses():
    data={'attributions':[[1,-2],[3,0]],'feature_names':['A','B']}
    fig=get_figure('shap_summary')(data=data)
    np.testing.assert_allclose(fig._figure_metadata['mean_absolute_attribution'],[2,1])
    plt.close(fig)
    computed=compute.compute_dependence(lambda a:2*a[:,0]+a[:,1], [[1,1],[2,3]],0,[0,1,2])
    np.testing.assert_allclose(computed['response'],[2,4,6])
    np.testing.assert_allclose(computed['curves'],[[1,3,5],[3,5,7]])


def test_mantel_matches_observed_distance_correlation_and_is_seeded():
    a=np.array([[0,1,3,4],[1,0,2,5],[3,2,0,6],[4,5,6,0]],float)
    b=np.array([[0,2,4,3],[2,0,1,6],[4,1,0,5],[3,6,5,0]],float)
    result=compute.compute_mantel(a,b,permutations=99,seed=5)
    mask=np.triu_indices(4,1)
    assert result['r']==pytest.approx(stats.pearsonr(a[mask],b[mask]).statistic)
    assert result['p']==compute.compute_mantel(a,b,permutations=99,seed=5)['p']
    assert .01 <= result['p'] <= 1
    with pytest.raises(ValueError,match='symmetric'): compute.compute_mantel(a+np.eye(4),b)


def test_taylor_partial_correlation_coverage_and_ahp():
    result=compute.compute_taylor([1,2,3,4],[[1,2],[2,4],[3,6],[4,8]])
    np.testing.assert_allclose(result['correlation'],[1,1]); np.testing.assert_allclose(result['std'],[np.sqrt(5/3),2*np.sqrt(5/3)])
    coverage=compute.compute_coverage([1,2,3],[[0],[1],[3.5]],[[2],[2.5],[4]],[.8])
    assert coverage['empirical'][0]==pytest.approx(2/3)
    weights=compute.compute_ahp([[1,2,4],[.5,1,2],[.25,.5,1]])
    np.testing.assert_allclose(weights['values'],np.array([4,2,1])/7)
    assert abs(weights['consistency_ratio']) < 1e-10
    rng=np.random.default_rng(4); z=rng.normal(size=(20,1)); x=np.column_stack([z[:,0]+rng.normal(size=20),z[:,0]+rng.normal(size=20)])
    out=compute.compute_partial_correlation(x,z)
    design=np.column_stack([np.ones(20),z]); residual=x-design@np.linalg.pinv(design)@x
    np.testing.assert_allclose(out['matrix'],np.corrcoef(residual,rowvar=False))


def test_timeseries_components_gain_and_percent_stack():
    out=compute.compute_timeseries(np.arange(12),np.arange(12)+np.sin(np.arange(12)),window=3,period=3,max_lag=3)
    np.testing.assert_allclose(out['trend']+out['seasonal']+out['residual'],out['values'])
    result=compute.compute_lift_gain([1,0,1,0],[.9,.8,.7,.6])
    np.testing.assert_allclose(result['gain'],[.5,.5,1,1]); np.testing.assert_allclose(result['lift'],[2,1,4/3,1])
    fig=get_figure('percent_stacked_bar')(data={'categories':['A','B'],'values':[[1,3],[2,2]],'groups':['G1','G2']})
    np.testing.assert_allclose(fig._figure_metadata['normalized_values'],[[25,75],[50,50]])
    plt.close(fig)


@pytest.mark.parametrize('name,field', [('spatial_3d','x'),('shap_summary','attributions'),('ranking','values'),('response_surface_opt','z'),('weight_sensitivity','scores')])
def test_nan_and_wrong_dimensions_are_value_errors(name,field):
    data=example_data(name); a=np.asarray(data[field],dtype=float); bad=a.copy(); bad.flat[0]=np.nan; data[field]=bad
    with pytest.raises(ValueError): get_figure(name)(data=data)
    data[field]=np.expand_dims(a,0)
    with pytest.raises(ValueError): get_figure(name)(data=data)
