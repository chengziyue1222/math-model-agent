"""Final-layout and independent plotted-value checks, including corrupted proofs."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from figure_acceptance_evidence import artist_evidence
from figure_comparison_invariants import core, equal, verify_change

from algorithms.figures import get_figure
from algorithms.figures.examples import example_data
from algorithms.figures.base import metadata_value


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close('all')


def pair(name, data=None, *, removed=(), config=None):
    data = example_data(name) if data is None else data
    fig = get_figure(name)(data=data, config=config or {}, mode='preview' if data.get('simulated') or 'contract' in data else 'formal')
    fig.canvas.draw()
    current = {'figure_metadata': deepcopy(fig._figure_metadata),
               'numerical_regression': {'artist_evidence': artist_evidence(fig)}}
    prior = {'metadata': deepcopy(current['figure_metadata']),
             'artist_evidence': deepcopy(current['numerical_regression']['artist_evidence'])}
    for key in removed:
        prior['metadata'].pop(key, None)
    source = {k: metadata_value(v) for k, v in data.items() if k != 'contract'}
    return fig, source, prior, current


@pytest.mark.parametrize('width', [75, 150])
@pytest.mark.parametrize('case', ['standard', 'long_labels', 'dense'])
def test_waterfall_complete_cumulative_path_has_margin(case, width):
    data = example_data('waterfall', case=case)
    fig = get_figure('waterfall')(data=data, config={'width_mm': width}, mode='preview')
    fig.canvas.draw()
    axis = fig.axes[0]
    endpoints = np.r_[0., np.cumsum(data['values'])]
    low, high = axis.get_ylim()
    span = np.ptp(endpoints)
    assert low <= endpoints.min()-.07*span
    assert high >= endpoints.max()+.07*span
    np.testing.assert_allclose([p.get_y()+p.get_height() for p in axis.patches], endpoints[1:])
    np.testing.assert_allclose([p.get_height() for p in axis.patches], data['values'])


@pytest.mark.parametrize('width', [75, 150])
def test_dense_weight_sensitivity_legend_does_not_cover_any_curve(width):
    data = example_data('weight_sensitivity', case='dense')
    fig = get_figure('weight_sensitivity')(data=data, config={'width_mm': width}, mode='preview')
    fig.canvas.draw()
    axis = fig.axes[0]
    assert axis.get_legend() is None and len(fig.legends) == 1
    legend = fig.legends[0]
    assert not legend.get_window_extent(fig.canvas.get_renderer()).overlaps(axis.bbox)
    assert [t.get_text() for t in legend.get_texts()] == list(data['schemes'])
    for line, expected in zip(axis.lines, data['scores']):
        np.testing.assert_allclose(line.get_xdata(), data['weights'])
        np.testing.assert_allclose(line.get_ydata(), expected)


def test_long_faceted_heatmap_keeps_complete_row_labels_separate():
    data = example_data('faceted_heatmap', case='long_labels')
    fig = get_figure('faceted_heatmap')(data=data, mode='preview')
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    panels = [axis for axis in fig.axes if axis.images]
    assert len(panels) == len(data['matrices'])
    for axis, expected in zip(panels, data['matrices']):
        labels = axis.get_yticklabels()
        assert [t.get_text().replace('\n', '') for t in labels] == data['row_labels']
        boxes = [t.get_window_extent(renderer) for t in labels]
        assert all(not box.overlaps(other) for i, box in enumerate(boxes) for other in boxes[i+1:])
        np.testing.assert_allclose(axis.images[0].get_array(), expected)


@pytest.mark.parametrize('width', [75, 150])
def test_state_machine_edge_text_does_not_cover_node_names(width):
    fig = get_figure('state_machine')(data=example_data('state_machine'),
                                    config={'width_mm': width}, mode='preview')
    fig.canvas.draw()
    axis = fig.axes[0]
    renderer = fig.canvas.get_renderer()
    nodes = [t.get_bbox_patch().get_window_extent(renderer) for t in axis.texts
             if type(t).__name__ != '_EdgeAnnotation' and t.get_bbox_patch() is not None]
    labels = [t for t in axis.texts if type(t).__name__ == '_EdgeAnnotation']
    assert len(labels) == len(example_data('state_machine')['events'])
    for label in labels:
        assert not any(label.get_window_extent(renderer).overlaps(box) for box in nodes)
    evidence = artist_evidence(fig)
    current = {'figure_metadata': deepcopy(fig._figure_metadata), 'numerical_regression': {'artist_evidence': evidence}}
    source = {k: metadata_value(v) for k, v in example_data('state_machine').items() if k != 'contract'}
    prior = {'metadata': deepcopy(fig._figure_metadata), 'artist_evidence': deepcopy(evidence)}
    assert verify_change('state_machine', source, prior, current)['verification_evidence']['status'] == 'PASS'
    current['figure_metadata']['edge_annotation_layout'][0]['curve_t'] = .95
    assert verify_change('state_machine', source, prior, current)['status'] == 'FAIL'


@pytest.mark.parametrize('variables,width,height,text_pt,constant,long', [
    (3, 150, None, 8.5, False, False), (6, 150, None, 8.5, False, False),
    (12, 150, None, 8.5, False, False), (6, 75, None, 8.5, False, False),
    (6, 150, None, 8.5, False, True), (3, 150, None, 8.5, True, False),
    (6, 150, 90, 12, False, False),
])
def test_final_correlation_annotations_leave_two_point_axis_margin(variables, width, height, text_pt, constant, long):
    rng = np.random.default_rng(271)
    values = rng.normal(size=(60, variables))
    if constant: values[:, 1] = 2
    labels = [f'变量{i+1}的完整中文统计指标名称' if long else f'变量{i+1}' for i in range(variables)]
    config = {'width_mm': width, 'text_pt': text_pt}
    if height: config['height_mm'] = height
    fig = get_figure('correlation_bubble')(data={'data': values, 'labels': labels}, config=config)
    fig.canvas.draw()
    ax = fig.axes[0]; renderer = fig.canvas.get_renderer()
    gap = 2*fig.dpi/72
    assert len(ax.texts) == variables*(variables+1)//2
    assert min(t.get_window_extent(renderer).y0 for t in ax.texts) >= ax.bbox.y0+gap-.3
    for row in range(variables):
        labels_in_row = ax.texts[row*(row+1)//2:(row+1)*(row+2)//2]
        boxes = [label.get_window_extent(renderer) for label in labels_in_row]
        assert all(right.x0-left.x1 >= gap-.3 for left, right in zip(boxes, boxes[1:]))
    assert min(t.get_fontsize() for t in ax.texts) >= text_pt
    assert fig.get_figwidth()*25.4 == pytest.approx(width)
    if height: assert fig.get_figheight()*25.4 == pytest.approx(height)
    with np.errstate(invalid='ignore', divide='ignore'):
        expected = np.corrcoef(values, rowvar=False)
    np.testing.assert_allclose(np.asarray(fig._figure_metadata['correlation'], float), expected, equal_nan=True)


def test_narrow_long_labels_reflow_into_a_complete_nonoverlapping_single_column_key():
    fig = get_figure('correlation_bubble')(data=example_data('correlation_bubble', case='long_labels'), config={'width_mm': 75}, mode='preview')
    fig.canvas.draw(); renderer = fig.canvas.get_renderer()
    axis = next(a for a in fig.axes if getattr(a, '_model_label_key', False))
    boxes = [t.get_window_extent(renderer) for t in axis.texts]
    assert len(boxes) == len(fig._figure_metadata['variables'])
    assert len({t.get_position()[0] for t in axis.texts}) == 1
    for i, box in enumerate(boxes):
        assert box.x0 >= axis.bbox.x0 and box.x1 <= axis.bbox.x1
        assert box.y0 >= axis.bbox.y0 and box.y1 <= axis.bbox.y1
        assert not any(box.overlaps(other) for other in boxes[i+1:])


def test_directed_edge_traversal_order_does_not_change_graph_relationships():
    _, source, prior, current = pair('algorithm_flow', data=example_data('algorithm_flow', case='dense'), removed=('node_label_key',))
    assert verify_change('algorithm_flow', source, prior, current)['verification_evidence']['status'] == 'PASS'


def test_graph_event_or_probability_stays_on_its_actual_edge():
    data = example_data('algorithm_flow')
    data['edge_labels'] = [f'事件{i+1}' for i in range(len(data['edges']))]
    _, source, prior, current = pair('algorithm_flow', data=data, removed=('node_label_key',))
    assert verify_change('algorithm_flow', source, prior, current)['verification_evidence']['status'] == 'PASS'
    text = next(t for t in current['numerical_regression']['artist_evidence'][0]['texts'] if t['text'] == '事件1')
    text['position'][1] += 3
    assert verify_change('algorithm_flow', source, prior, current)['status'] == 'FAIL'


def test_source_changed_but_retained_in_metadata_is_rejected():
    _, source, prior, current = pair('scatter')
    source['x'][0] += 10
    result = verify_change('scatter', source, prior, current)
    assert result['status'] == 'FAIL'
    assert result['invariant_checks']['plotted_input_matches_saved_source'] is False


@pytest.mark.parametrize('corruption', ['partial_fill', 'missing_person', 'caption', 'cropped_domain'])
def test_person_shape_change_requires_actual_counts_area_and_full_labels(corruption):
    _, source, prior, current = pair('pictogram')
    assert verify_change('pictogram', source, prior, current)['verification_evidence']['status'] == 'PASS'
    axis = current['numerical_regression']['artist_evidence'][0]
    if corruption == 'partial_fill':
        # Keep the saved fractions intact while corrupting an actual clip.
        axis['patches'][2]['clip_box'][1][1] -= .3
    elif corruption == 'missing_person':
        del axis['patches'][:4]
    elif corruption == 'caption':
        axis['texts'][0]['text'] = '积极：200'
    else:
        axis['xlim'][1] = .5
    assert verify_change('pictogram', source, prior, current)['status'] == 'FAIL'


def test_domain_only_change_cannot_pass_even_when_artist_arrays_match():
    _, source, prior, current = pair('scatter')
    current['numerical_regression']['artist_evidence'][0]['xlim'][1] /= 2
    result = verify_change('scatter', source, prior, current)
    assert result['status'] == 'NEEDS_REVIEW'
    assert result['verification_evidence']['status'] == 'NOT_CHECKED'


@pytest.mark.parametrize('corruption', ['area', 'coordinate', 'color', 'colorbar'])
def test_correlation_bubble_independent_numeric_and_color_checks(corruption):
    _, source, prior, current = pair('correlation_bubble', removed=('area_scale', 'color_domain', 'correlation', 'size_semantics'))
    assert verify_change('correlation_bubble', source, prior, current)['verification_evidence']['status'] == 'PASS'
    axes = current['numerical_regression']['artist_evidence']
    if corruption == 'area': axes[0]['collections'][0]['sizes'][0] *= .5
    elif corruption == 'coordinate': axes[0]['collections'][0]['offsets'][0][0] += 1
    elif corruption == 'color': axes[0]['collections'][0]['facecolors'][0][0] = .99
    else:
        for collection in axes[1]['collections']:
            if collection.get('array') is not None: collection['color_domain'] = [-.5, .5]
    result = verify_change('correlation_bubble', source, prior, current)
    assert result['status'] == 'FAIL'


def test_bubble_area_offset_cannot_be_accepted_as_cosmetic_marker_change():
    _, source, prior, current = pair('bubble', removed=('area_scale', 'magnitude', 'marker_area_pt2', 'size_semantics'))
    assert verify_change('bubble', source, prior, current)['verification_evidence']['status'] == 'PASS'
    current['numerical_regression']['artist_evidence'][0]['collections'][0]['sizes'][0] += 35
    assert verify_change('bubble', source, prior, current)['status'] == 'FAIL'


@pytest.mark.parametrize('corruption', ['metadata_label', 'actual_label', 'matrix'])
def test_confusion_matrix_added_metadata_is_validated_against_real_marks(corruption):
    _, source, prior, current = pair('confusion_matrix', removed=('matrix', 'labels'))
    assert verify_change('confusion_matrix', source, prior, current)['verification_evidence']['status'] == 'PASS'
    if corruption == 'metadata_label': current['figure_metadata']['labels'][0] = '错误类别'
    elif corruption == 'actual_label': current['numerical_regression']['artist_evidence'][0]['tick_labels']['y'].reverse()
    else: current['figure_metadata']['matrix'][0][0] += 1
    assert verify_change('confusion_matrix', source, prior, current)['status'] == 'FAIL'


def test_polar_origin_angle_is_undefined_but_nonzero_angle_is_checked():
    _, source, prior, current = pair('polar_stacked_bar')
    patch = current['numerical_regression']['artist_evidence'][0]['patches'][0]
    origin = next(p for p in patch['vertices'] if abs(p[1]) < 1e-9)
    origin[0] += 2
    assert verify_change('polar_stacked_bar', source, prior, current)['status'] == 'PASS'
    outer = next(p for p in patch['vertices'] if abs(p[1]) > 1e-9)
    outer[0] += .1
    assert verify_change('polar_stacked_bar', source, prior, current)['status'] == 'FAIL'


def test_wrong_composition_denominator_is_not_a_polar_geometry_exception():
    _, source, prior, current = pair('polar_stacked_bar')
    current['figure_metadata']['denominators'][0] += 1
    assert verify_change('polar_stacked_bar', source, prior, current)['status'] == 'FAIL'


@pytest.mark.parametrize('time', [[2.0], [1., 3., 10.], [1., 2., 3.]])
def test_time_heatmap_checks_actual_nonuniform_and_singleton_edges(time):
    data = {'time': time, 'matrix': [list(range(len(time))), list(range(3, 3+len(time)))], 'row_labels': ['甲', '乙']}
    _, source, prior, current = pair('time_heatmap', data, removed=('time', 'time_edges', 'time_encoding'))
    assert verify_change('time_heatmap', source, prior, current)['verification_evidence']['status'] == 'PASS'
    current['numerical_regression']['artist_evidence'][0]['collections'][0]['mesh_coordinates'][0][0][0] += 1
    assert verify_change('time_heatmap', source, prior, current)['status'] == 'FAIL'


@pytest.mark.parametrize('corruption', ['cell', 'boundary', 'row_key'])
def test_circular_tessellation_does_not_add_or_change_observations(corruption):
    _, source, prior, current = pair('circular_heatmap', removed=('angular_tessellation', 'row_label_key'))
    assert verify_change('circular_heatmap', source, prior, current)['verification_evidence']['status'] == 'PASS'
    cell = current['numerical_regression']['artist_evidence'][0]['patches'][0]
    if corruption == 'cell': cell['facecolor'][0] = 1-cell['facecolor'][0]
    elif corruption == 'boundary': cell['vertices'][2][0] += .02
    else: current['figure_metadata']['row_label_key'] = {'N1': '不存在的行'}
    assert verify_change('circular_heatmap', source, prior, current)['status'] == 'FAIL'


def test_dendrogram_verifies_merge_distances_from_linkage_not_metadata_presence():
    _, source, prior, current = pair('dendrogram', removed=('orientation',))
    assert verify_change('dendrogram', source, prior, current)['verification_evidence']['status'] == 'PASS'
    current['numerical_regression']['artist_evidence'][0]['collections'][0]['paths'][0][1][1] += 1
    assert verify_change('dendrogram', source, prior, current)['status'] == 'FAIL'


@pytest.mark.parametrize('corruption', ['edge', 'edge_anchor', 'node_label'])
def test_graph_layout_approvals_require_all_actual_directed_relationships(corruption):
    _, source, prior, current = pair('algorithm_flow', removed=('node_label_key',))
    assert verify_change('algorithm_flow', source, prior, current)['verification_evidence']['status'] == 'PASS'
    axis = current['numerical_regression']['artist_evidence'][0]
    if corruption == 'edge': axis['patches'].pop(next(i for i, p in enumerate(axis['patches']) if p['type'] == 'FancyArrowPatch'))
    elif corruption == 'edge_anchor':
        next(p for p in axis['patches'] if p['type'] == 'FancyArrowPatch')['endpoint_anchors'][0][0] += 10
    else:
        axis['texts'][0]['text'] = '错误节点名称'
    assert verify_change('algorithm_flow', source, prior, current)['status'] == 'FAIL'


def test_high_dim_density_preserves_every_bin_and_shared_count_domain():
    _, source, prior, current = pair('high_dim_density', removed=('density_color_domain', 'tick_policy'))
    prior['artist_evidence'] = [a for a in prior['artist_evidence'] if a['auxiliary_role'] != 'colorbar']
    result = verify_change('high_dim_density', source, prior, current)
    assert result['verification_evidence']['status'] == 'PASS'
    current['numerical_regression']['artist_evidence'][1]['collections'][0]['array'][0] += 1
    assert verify_change('high_dim_density', source, prior, current)['status'] == 'FAIL'


@pytest.mark.parametrize('name', ['contour', 'contour_density', 'taylor_diagram', 'constraint_boundary'])
def test_contour_label_gap_acceptance_reconstructs_source_isolines(name):
    _, source, prior, current = pair(name)
    # A previous inline-label cut left a different endpoint; the new geometry
    # still has to lie on independently reconstructed source isolines.
    collection = next(c for c in prior['artist_evidence'][0]['collections'] if c['type'] == 'QuadContourSet')
    path = next(p for p in collection['paths'] if len(p) > 1)
    path[0][0] += .01
    result = verify_change(name, source, prior, current)
    assert result['verification_evidence']['status'] == 'PASS'
    actual = next(c for c in current['numerical_regression']['artist_evidence'][0]['collections'] if c['type'] == 'QuadContourSet')
    changed = next(p for p in actual['paths'] if len(p) > 1)
    changed[0][0] += 3
    assert verify_change(name, source, prior, current)['status'] == 'FAIL'


def test_new_auxiliary_metadata_does_not_hide_changed_core_geometry():
    _, _, _, current = pair('scatter')
    evidence = current['numerical_regression']['artist_evidence']
    altered = deepcopy(evidence)
    altered[0]['collections'][0]['offsets'][0][0] += 1
    assert not equal(core(evidence), core(altered))


def test_comparison_writer_binds_actual_values_and_verification_code(tmp_path):
    from compare_research_style_gallery import build
    fig, source, prior, current = pair('confusion_matrix', removed=('matrix', 'labels'))
    before = tmp_path/'before'; gallery = tmp_path/'gallery'; output = tmp_path/'comparison'
    before.mkdir(); (gallery/'standard').mkdir(parents=True)
    stem = gallery/'standard'/'confusion_matrix'
    data = stem.with_suffix('.data.json')
    data.write_text(json.dumps(source, ensure_ascii=False), encoding='utf-8')
    digest = hashlib.sha256(data.read_bytes()).hexdigest()
    prior.update(name='confusion_matrix', case='standard', source_hash=digest)
    (before/'manifest.json').write_text(json.dumps([prior], ensure_ascii=False), encoding='utf-8')
    stem.with_suffix('.figure.json').write_text(json.dumps(current, ensure_ascii=False), encoding='utf-8')
    fig.savefig(stem.with_suffix('.png'))
    (gallery/'manifest.json').write_text(json.dumps([{'name':'confusion_matrix', 'case':'standard'}]), encoding='utf-8')
    build(before, gallery, output)
    result = json.loads(stem.with_suffix('.figure.json').read_text(encoding='utf-8'))
    regression = result['numerical_regression']; evidence = regression['verification_evidence']
    assert regression['status'] == 'DOCUMENTED_METADATA_CHANGE'
    assert evidence['status'] == 'PASS'
    assert evidence['source_sha256'] == digest
    assert evidence['checks_passed'] == evidence['checks_required'] == len(regression['invariant_checks'])
    for key in ('verifier_code', 'artist_capture_code'):
        assert hashlib.sha256(Path(evidence[key]['path']).read_bytes()).hexdigest() == evidence[key]['sha256']
    for key, payload in [('artist_evidence', regression['artist_evidence']), ('figure_metadata', result['figure_metadata'])]:
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
        assert evidence[key+'_sha256'] == hashlib.sha256(encoded).hexdigest()


def test_narrow_unreadable_matrix_fails_instead_of_hiding_values_or_reducing_type():
    values = np.random.default_rng(8).normal(size=(70, 12))
    with pytest.raises(ValueError, match='wider figure or separate matrix panels'):
        get_figure('correlation_bubble')(data={'data': values}, config={'width_mm': 75})


def test_saved_json_contract_roundtrip_and_invalid_fields_allocate_no_figure():
    from algorithms.figures import DataContract
    contract=DataContract(source='saved observations',simulated=True,units={'values':'人'})
    data=json.loads(json.dumps({'categories':['甲','乙'],'values':[13,67],
                               'icon_value':10,'contract':contract.to_dict()}))
    fig=get_figure('pictogram')(data=data,mode='preview')
    assert fig._figure_metadata['data_contract']==contract.to_dict()
    before=plt.get_fignums()
    with pytest.raises(ValueError,match='serialized DataContract'):
        get_figure('pictogram')(data={**data,'contract':{'unknown_field':1}},mode='preview')
    assert plt.get_fignums()==before


@pytest.mark.parametrize('name,case',[('clustered_heatmap','long_labels'),('faceted_heatmap','dense')])
def test_final_matrix_tick_boxes_do_not_intersect(name,case):
    fig=get_figure(name)(data=example_data(name,case=case),mode='preview')
    fig.canvas.draw();renderer=fig.canvas.get_renderer()
    for axis in fig.axes:
        if not axis.images: continue
        boxes=[label.get_window_extent(renderer) for label in axis.get_xticklabels()]
        assert not any(a.overlaps(b) for a,b in zip(boxes,boxes[1:]))
    if name=='faceted_heatmap':
        actual=[axis.get_title() for axis in fig.axes if axis.images]
        assert actual==example_data(name,case=case)['facets']
        assert fig._suptitle.get_text()


def test_negative_hexbin_bins_survive_actual_pdf_render(tmp_path):
    import fitz
    data={'x':[-3,-2,-2.01,-1.98,.9,1,1.1,3],'y':[-3,-2,-2.01,-1.98,.9,1,1.1,3]}
    fig=get_figure('hexbin')(data=data)
    axis=fig.axes[0];collection=axis.collections[0]
    counts=np.asarray(collection.get_array());paths=collection.get_paths()
    assert counts.sum()==len(data['x'])
    centers=np.array([(p.vertices.min(0)+p.vertices.max(0))/2 for p in paths])
    candidates=np.flatnonzero((centers[:,0]<0)&(centers[:,1]<0))
    index=candidates[np.argmax(counts[candidates])]
    target=tmp_path/'negative-bins.pdf';fig.savefig(target)
    xy=axis.transData.transform(centers[index])
    with fitz.open(target) as doc:
        pix=doc[0].get_pixmap(matrix=fitz.Matrix(2,2))
        pixels=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,pix.n)
        px=int(xy[0]/fig.bbox.width*pix.width)
        py=int((1-xy[1]/fig.bbox.height)*pix.height)
        expected=np.asarray(collection.cmap(collection.norm(counts[index]))[:3])
        # A grid stroke may cross the bin center; inspect its small interior,
        # not the overprinted grid pixel. A missing negative bin stays white
        # throughout this neighborhood and cannot satisfy the color check.
        interior=pixels[py-3:py+4,px-3:px+4,:3]/255
        assert np.min(np.max(np.abs(interior-expected),axis=2)) < .04


@pytest.mark.parametrize('corruption',['count','vertices'])
def test_hexbin_vector_workaround_verifies_every_bin(corruption):
    _,source,prior,current=pair('hexbin')
    assert verify_change('hexbin',source,prior,current)['verification_evidence']['status']=='PASS'
    collection=current['numerical_regression']['artist_evidence'][0]['collections'][0]
    if corruption=='count': collection['array'][0]+=1
    else: collection['paths'][0][0][0]+=.2
    assert verify_change('hexbin',source,prior,current)['status']=='FAIL'


@pytest.mark.parametrize('name',['diverging_heatmap','partial_correlation','threshold_heatmap'])
def test_signed_annotations_cannot_disagree_with_saved_cells(name):
    _,source,prior,current=pair(name)
    assert verify_change(name,source,prior,current)['verification_evidence']['status']=='PASS'
    current['numerical_regression']['artist_evidence'][0]['texts'][0]['text']='wrong sign'
    assert verify_change(name,source,prior,current)['status']=='FAIL'


def test_shap_swarm_retains_feature_pairs_and_does_not_invent_rank_diagonals():
    data={'attributions':[[1,2],[1,3],[1,4],[1,5]],'features':[[4,8],[3,7],[2,6],[1,5]],'feature_names':['甲','乙']}
    fig=get_figure('shap_beeswarm')(data=data)
    for row,j in enumerate(fig._figure_metadata['feature_order']):
        points=fig.axes[0].collections[row]
        np.testing.assert_allclose(points.get_offsets()[:,0],np.array(data['attributions'])[:,j])
        expected=np.array(data['features'])[:,j]
        np.testing.assert_allclose(points.get_array(),(expected-expected.min())/np.ptp(expected))
    offsets=fig.axes[0].collections[1].get_offsets()[:,1]
    assert not (np.all(np.diff(offsets)>0) or np.all(np.diff(offsets)<0))


@pytest.mark.parametrize('name',['algorithm_flow','state_machine'])
def test_exported_graph_labels_follow_each_curve_and_keep_full_edge_key(tmp_path,name):
    from algorithms.figure_export import export_bundle
    from algorithms.sci_figures import FigureContract
    data=example_data(name,case='long_labels')
    fig=get_figure(name)(data=data,mode='preview')
    source=tmp_path/'data.json';source.write_text(json.dumps(data,default=str),encoding='utf-8')
    contract=FigureContract('synthetic graph',('saved fixture',),source_paths=(str(source),),
                            width_mm=fig.get_figwidth()*25.4,height_mm=fig.get_figheight()*25.4)
    # Exercise all three export backends, then audit actual canvas geometry.
    export_bundle(fig,tmp_path/'graph',contract,strict=False)
    fig.canvas.draw()
    evidence=artist_evidence(fig)
    current={'figure_metadata':fig._figure_metadata,'numerical_regression':{'artist_evidence':evidence}}
    prior={'metadata':fig._figure_metadata,'artist_evidence':evidence}
    saved={k:metadata_value(v) for k,v in data.items() if k!='contract'}
    result=verify_change(name,saved,prior,current)
    assert result['verification_evidence']['status']=='PASS'
    axis=fig.axes[0]
    for edge in axis.patches:
        if type(edge).__name__!='FancyArrowPatch':continue
        # CLOSEPOLY's dummy vertex is not drawn. Measure the actual Bezier
        # extent, including arrowheads, instead of its control-point envelope.
        extent=edge.get_path().get_extents()
        assert extent.x0>=axis.get_xlim()[0] and extent.x1<=axis.get_xlim()[1]
        assert extent.y0>=axis.get_ylim()[0] and extent.y1<=axis.get_ylim()[1]
    if name=='state_machine':
        evidence[0]['figure_legends'][0][0]='wrong edge identity'
        assert verify_change(name,saved,prior,current)['status']=='FAIL'


@pytest.mark.parametrize('name',['contour','contour_density'])
def test_contour_respects_explicit_colormap(name):
    fig=get_figure(name)(data=example_data(name),config={'cmap':'plasma'},mode='preview')
    assert fig.axes[0].collections[0].cmap.name=='plasma'


@pytest.mark.parametrize('case',['standard','long_labels','dense'])
@pytest.mark.parametrize('width',[75,150])
def test_contour_level_text_survives_at_every_axis_edge(case,width):
    fig=get_figure('contour')(data=example_data('contour',case=case),config={'width_mm':width},mode='preview')
    fig.canvas.draw();renderer=fig.canvas.get_renderer();axis=fig.axes[0]
    for label in axis.collections[0].labelTexts:
        box=label.get_window_extent(renderer)
        assert axis.bbox.x0<=box.x0<=box.x1<=axis.bbox.x1
        assert axis.bbox.y0<=box.y0<=box.y1<=axis.bbox.y1


def test_disjoint_gallery_batches_keep_each_manifest_and_artifact(tmp_path):
    from build_research_style_acceptance import build
    build(tmp_path,names=['bar'],batch_id=0)
    original=(tmp_path/'standard/bar.png').read_bytes()
    build(tmp_path,names=['area'],batch_id=1)
    assert (tmp_path/'standard/bar.png').read_bytes()==original
    for number,name in enumerate(['bar','area']):
        records=json.loads((tmp_path/f'manifest-batch-{number}.json').read_text(encoding='utf-8'))
        assert len(records)==3 and all(r['name']==name and 'error' not in r for r in records)
        assert {(r['case']) for r in records}=={'standard','long_labels','dense'}
        for row in records:
            assert (tmp_path/row['metadata']).is_file()
    assert not (tmp_path/'manifest.json').exists()
