"""Executable numerical checks for declared figure display/semantic repairs.

These checks are embedded in the existing per-figure numerical_regression record.
An entry name selects a verifier, never an unconditional approval.
"""
from __future__ import annotations

from copy import deepcopy
import numpy as np


AXIS_KEYS = {'projection', 'xscale', 'yscale', 'xlim', 'ylim', 'lines', 'collections', 'patches', 'images'}
COLLECTION_KEYS = {'type', 'offsets', 'array', 'sizes', 'paths'}


def equal(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    if isinstance(a, (float, int, np.number)) and isinstance(b, (float, int, np.number)):
        return bool(np.isclose(a, b, rtol=1e-8, atol=1e-8, equal_nan=True))
    return a == b


def core(axes, *, domains=True):
    result = []
    for original in axes:
        axis = {k: deepcopy(v) for k, v in original.items() if k in AXIS_KEYS}
        if not domains:
            axis.pop('xlim', None); axis.pop('ylim', None)
        axis['collections'] = [{k: deepcopy(v) for k, v in c.items() if k in COLLECTION_KEYS}
                               for c in axis.get('collections', [])]
        axis['patches'] = [{k: deepcopy(v) for k, v in p.items() if k in {'type', 'vertices'}}
                           for p in axis.get('patches', [])]
        if axis.get('projection') == 'polar':
            for patch in axis.get('patches', []):
                for point in patch['vertices']:
                    if point[0] is not None and point[1] is not None:
                        # The angle at r=0 is undefined. Inverse transforms can
                        # return any angle there after a physical resize.
                        angle = point[0] % (2*np.pi)
                        point[0] = 0. if abs(point[1]) <= 1e-9 or np.isclose(angle, 2*np.pi, rtol=0, atol=1e-9) else angle
        result.append(axis)
    return result


def numerical_metadata(value):
    ignored = {'colors', 'palette', 'group_colors', 'positions', 'data_contract', 'font_size', 'input_data'}
    if isinstance(value, dict):
        return {k: numerical_metadata(v) for k, v in value.items() if k not in ignored}
    if isinstance(value, list):
        return [numerical_metadata(v) for v in value]
    return value if isinstance(value, (float, int, bool)) or value is None else None


def _points(axis):
    return [c for c in axis.get('collections', []) if c['type'] == 'PathCollection']


def _no_crop(before, after):
    for old, new in zip(before, after):
        for key in ('xlim', 'ylim'):
            lo, hi = sorted(old[key]); nlo, nhi = sorted(new[key])
            if nlo > lo+1e-8 or nhi < hi-1e-8 or np.sign(np.diff(old[key])) != np.sign(np.diff(new[key])):
                return False
    return True


def _key_matches(metadata, labels):
    key = metadata.get('node_label_key', metadata.get('row_label_key', metadata.get('variable_label_key', {})))
    return not key or (len(key) == len(labels) and sorted(key.values()) == sorted(map(str, labels)))


def _rendered_key_matches(metadata, axes):
    key = metadata.get('node_label_key', metadata.get('row_label_key', metadata.get('variable_label_key', {})))
    if not key: return True
    rendered = [t['text'] for axis in axes if axis.get('auxiliary_role') == 'label_key' for t in axis.get('texts', [])]
    normalize = lambda value: ''.join(value.split())
    return sorted(map(normalize, rendered)) == sorted(normalize(f'{code} {name}') for code, name in key.items())


def _strip_key_axes(axes):
    return [a for a in axes if a.get('auxiliary_role') != 'label_key']


def _multiset_equal(actual, expected):
    remaining = list(actual)
    for item in expected:
        found = next((i for i, candidate in enumerate(remaining) if equal(item, candidate)), None)
        if found is None: return False
        remaining.pop(found)
    return not remaining


def _only_metadata_added(before, after, allowed):
    before = numerical_metadata(before); after = numerical_metadata(after)
    return set(after)-set(before) <= set(allowed) and equal(before, {k: after[k] for k in before if k in after})


def _polygon_area(vertices):
    points = np.asarray(vertices, dtype=float)
    if len(points) < 3:
        return 0.
    return abs(np.sum(points[:, 0]*np.roll(points[:, 1], -1)
                      - points[:, 1]*np.roll(points[:, 0], -1)))/2


def _hexbin_core(axes):
    result = core(axes, domains=False)
    for axis in result:
        for collection in axis['collections']:
            if collection['type'] != 'PolyCollection' or collection.get('array') is None:
                continue
            paths = collection['paths']; offsets = collection['offsets']
            count = len(collection['array'])
            if len(paths) == 1 and len(offsets) == count:
                paths = [(np.asarray(paths[0])+offset).tolist() for offset in offsets]
            elif len(paths) == count and len(offsets) == 1:
                paths = [(np.asarray(path)+offsets[0]).tolist() for path in paths]
            else:
                raise ValueError('hexbin paths and bins do not align')
            for path in paths:
                while len(path) > 1 and equal(path[0],path[-1]):
                    path.pop()
            collection['paths'] = paths
            collection['offsets'] = [[0.,0.]]
    return result


def _clipped_polygon_area(vertices, box):
    """Independent four-sided polygon clipping, including concave bodies."""
    polygon = list(np.asarray(vertices, dtype=float))
    for dimension, boundary, sign in ((0, box[0][0], 1), (0, box[1][0], -1),
                                      (1, box[0][1], 1), (1, box[1][1], -1)):
        output = []
        for previous, current in zip(polygon[-1:]+polygon[:-1], polygon):
            previous_in = sign*(previous[dimension]-boundary) >= -1e-12
            current_in = sign*(current[dimension]-boundary) >= -1e-12
            if previous_in != current_in:
                position = (boundary-previous[dimension])/(current[dimension]-previous[dimension])
                output.append(previous+position*(current-previous))
            if current_in:
                output.append(current)
        polygon = output
        if not polygon:
            return 0.
    return _polygon_area(polygon)


def _person_array_checks(source, axes):
    """Read actual clip rectangles, shapes and captions, rather than claims."""
    groups = {}
    valid = len(axes) == 1
    for patch in axes[0]['patches']:
        box = patch.get('clip_box')
        if box is None or patch['type'] != 'Polygon':
            valid = False
            continue
        key = tuple(np.round([*box[0], box[1][0]], 8))
        groups.setdefault(key, []).append(patch)
    fractions = []
    for key in sorted(groups, key=lambda item: (-item[1], item[0])):
        patches = groups[key]
        unique = []
        for patch in patches:
            if not any(equal(patch['vertices'], points) for points in unique):
                unique.append(patch['vertices'])
        area = sum(_polygon_area(points) for points in unique)
        valid &= area > 0 and all(sum(equal(p['vertices'], points) for p in patches) == 2 for points in unique)
        visible = sum(_clipped_polygon_area(p['vertices'], p['clip_box']) for p in patches)
        fractions.append(visible/area-1 if area > 0 else np.nan)
    values = np.asarray(source['values'], dtype=float)/source.get('icon_value', 1)
    expected = [min(1., value-i) for value in values for i in range(int(np.ceil(value)))]
    captions = [t['text'].replace('\n', '') for t in axes[0].get('texts', [])]
    bounds = sorted(axes[0]['xlim']), sorted(axes[0]['ylim'])
    inside = all(all(bounds[0][0]-1e-8 <= x <= bounds[0][1]+1e-8
                     and bounds[1][0]-1e-8 <= y <= bounds[1][1]+1e-8
                     for x, y in patch['vertices']) for patch in axes[0]['patches'])
    return dict(actual_icon_layers_complete=valid,
                exact_icon_count_and_visible_area=equal(fractions, expected),
                full_category_names_values_and_order=captions == [f'{label}：{value:g}' for label, value in zip(source['categories'], source['values'])],
                all_icon_geometry_inside_displayed_domain=inside,
                linear_untransformed_coordinates=axes[0]['xscale'] == axes[0]['yscale'] == 'linear')


def _contour_geometry(source, name, old, new):
    """Verify inline-label gaps against independently reconstructed isolines."""
    from contourpy import contour_generator
    from scipy.stats import gaussian_kde
    if name == 'taylor_diagram':
        reference = source['reference_std']; maximum = max(reference, max(source['std']))*1.25
        x = np.linspace(0, np.pi, 120); y = np.linspace(0, maximum, 100)
        xx, yy = np.meshgrid(x, y)
        z = np.sqrt(reference**2+yy**2-2*reference*yy*np.cos(xx))
    elif name == 'contour_density':
        x = np.linspace(min(source['x']), max(source['x']), 70)
        y = np.linspace(min(source['y']), max(source['y']), 70)
        xx, yy = np.meshgrid(x, y)
        z = gaussian_kde(np.vstack([source['x'], source['y']]))(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)
    else:
        x, y = source['x_grid'], source['y_grid']
        z = source['constraint'] if name == 'constraint_boundary' else source['z']
    generator = contour_generator(x=x, y=y, z=z, name='serial')
    checked = 0
    for before, after in zip(old['collections'], new['collections']):
        if before['type'] != 'QuadContourSet' or equal(before['paths'], after['paths']):
            continue
        levels = after.get('contour_levels')
        # A uniform contour ink changes the ScalarMappable array to color
        # indices. The contour levels, not those indices, encode the statistic.
        same_levels = equal(before.get('contour_levels'), levels) if before.get('contour_levels') is not None else equal(before['array'], levels) or equal(before['array'], after['array'])
        if levels is None or not same_levels or len(levels) != len(after['paths']):
            return False
        for path_index, (level, vertices) in enumerate(zip(levels, after['paths'])):
            chunks = generator.lines(float(level))
            points = np.asarray(vertices, dtype=float).reshape(-1, 2)
            points = points[np.isfinite(points).all(1)]
            if not len(points):
                if any(len(chunk) for chunk in chunks): return False
                continue
            if not chunks: return False
            starts = np.concatenate([c[:-1] for c in chunks if len(c)>1])
            ends = np.concatenate([c[1:] for c in chunks if len(c)>1])
            vectors = ends-starts; lengths = (vectors*vectors).sum(1)
            codes = after.get('path_codes', [None]*len(levels))[path_index]
            if codes is None: return False
            codes = np.asarray(codes)
            segments = (codes[1:] != 1) & (codes[1:] != 79)
            midpoints = (points[:-1]+points[1:])/2
            points = np.vstack([points, midpoints[segments]])
            # Bounded batches keep the dense-case checker independent of RAM.
            tolerance = 1e-7*max(float(np.ptp(x)), float(np.ptp(y)), 1)
            for start in range(0, len(points), 64):
                delta = points[start:start+64, None, :]-starts
                fraction = np.clip((delta*vectors).sum(2)/np.maximum(lengths, 1e-30), 0, 1)
                distance = np.linalg.norm(delta-fraction[..., None]*vectors, axis=2).min(1)
                if np.any(distance > tolerance): return False
        checked += 1
    return checked > 0


def verify_change(name, source, prior, current):
    """Return a classified result only after concrete invariants succeed."""
    before = prior['artist_evidence']; after = current['numerical_regression']['artist_evidence']
    old_meta = prior.get('metadata') or {}; meta = current.get('figure_metadata') or {}
    checks = {
        'saved_input_fields_unchanged': equal(old_meta.get('input_data'), meta.get('input_data')),
        'plotted_input_matches_saved_source': all(k in source and equal(v, source[k]) for k, v in meta.get('input_data', {}).items()),
    }
    if not meta.get('input_data'): checks['plotted_input_matches_saved_source'] = False
    status = 'NEEDS_REVIEW'; note = 'Unclassified numerical or domain difference.'

    def classify(kind, text, **conditions):
        nonlocal status, note
        status, note = kind, text
        checks.update({k: bool(v) for k, v in conditions.items()})

    a, b = core(before), core(after)
    if name == 'pictogram' and source.get('pictogram_mode', 'array') == 'array' and source.get('array_layout', 'grouped') == 'grouped':
        classify('DOCUMENTED_DISPLAY_CHANGE', 'Rounded person outline, finer texture and reflowed spacing; actual clipped polygon areas preserve all quantities.',
                 **_person_array_checks(source, after),
                 original_icon_value_preserved=equal(meta.get('icon_value'), old_meta.get('icon_value')),
                 original_fraction_encoding_preserved=equal(meta.get('fractions'), old_meta.get('fractions')))
    elif name in {'diverging_heatmap','partial_correlation','threshold_heatmap'}:
        matrix = np.asarray(source['matrix'])
        texts = {(round(t['position'][1]),round(t['position'][0])):t['text'] for t in after[0]['texts']}
        expected = {(i,j): f'{matrix[i,j]:+.2f}' if max(matrix.shape) <= 6 else '+' if matrix[i,j] > 0 else '−' if matrix[i,j] < 0 else '0' for i,j in np.ndindex(matrix.shape)}
        if name == 'threshold_heatmap': expected = {key:value+('×' if matrix[key] >= source['threshold'] else '') for key,value in expected.items()}
        classify('DOCUMENTED_DISPLAY_CHANGE','Signed cell annotations make the unchanged matrix readable in grayscale.',
                 exact_matrix_marks_and_domains=equal(a,b), every_actual_sign_annotation_matches_source=texts == expected,
                 existing_numeric_metadata_unchanged=equal(numerical_metadata(old_meta),numerical_metadata(meta)))
    elif name == 'hexbin':
        classify('DOCUMENTED_DISPLAY_CHANGE','PDF hexagon instances expanded into explicit vector polygons to prevent lost negative-offset bins.',
                 all_bin_counts_and_translated_hexagons_exact=equal(_hexbin_core(before),_hexbin_core(after)),
                 numeric_metadata_unchanged=equal(numerical_metadata(old_meta),numerical_metadata(meta)),
                 original_domains_preserved=equal([[v['xlim'],v['ylim']] for v in before],[[v['xlim'],v['ylim']] for v in after]))
    elif name == 'shap_beeswarm':
        values=np.asarray(source['attributions']);features=np.asarray(source['features'])
        order=np.argsort(-np.abs(values).mean(0),kind='stable');points=_points(after[0])
        preserved=len(points)==len(order)
        for row,j in enumerate(order):
            if row >= len(points): preserved=False;continue
            point=points[row];offset=np.asarray(point['offsets'])
            normalized=(features[:,j]-features[:,j].min())/max(np.ptp(features[:,j]),1e-12)
            preserved &= equal(offset[:,0].tolist(),values[:,j].tolist()) and np.all(np.abs(offset[:,1]-row) <= .35) and equal(point['array'],normalized.tolist()) and equal(point['color_domain'],[0,1])
        classify('DOCUMENTED_DISPLAY_CHANGE','Within-attribution-bin spreading replaces artificial rank diagonals; every SHAP/feature pair is retained.',
                 every_paired_attribution_and_feature_value_retained=preserved,
                 exact_mean_absolute_ranking=equal(meta['feature_order'],order.tolist()) and equal(meta['mean_absolute_attribution'],np.abs(values).mean(0).tolist()),
                 full_feature_order_labels=equal([s.replace('\n','') for s in after[0]['tick_labels']['y']],[source['feature_names'][j] for j in order]),
                 linear_coordinates=after[0]['xscale']==after[0]['yscale']=='linear')
    elif name in {'contour','contour_density'}:
        classify('DOCUMENTED_DISPLAY_CHANGE','Contour strokes and label margins clarified; every isoline is checked against the original grid or density.',
                 independently_reconstructed_isolines=_contour_geometry(source,name,before[0],after[0]),
                 axis_domain_only_expanded=_no_crop(before,after),
                 numeric_metadata_unchanged=equal(numerical_metadata(old_meta),numerical_metadata(meta)))
    elif equal(a, b) and equal(numerical_metadata(old_meta), numerical_metadata(meta)) and not ({'nodes','edges'} <= source.keys() and 'edge_annotation_layout' in meta):
        classify('PASS', 'All saved numerical marks, metadata, domains and transformations are unchanged.',
                 numerical_artists_metadata_and_domains_identical=True)
    elif name in {'confusion_matrix', 'confusion_matrix_eval'}:
        labels = source.get('labels') or [f'类别{i+1}' for i in range(len(source['matrix']))]
        classify('DOCUMENTED_METADATA_CHANGE', 'Matrix and category names are now retained explicitly in metadata.',
                 existing_marks_and_domains_unchanged=equal(a, b),
                 matrix_matches_source=equal(meta.get('matrix'), source['matrix']),
                 labels_match_source=equal(meta.get('labels'), labels),
                 actual_category_order=all(equal([t.replace('\n', '') for t in after[0].get('tick_labels', {}).get(axis, [])], [str(v).replace('\n', '') for v in labels]) for axis in ('x', 'y')),
                 only_expected_metadata_added=_only_metadata_added(old_meta, meta, {'matrix', 'labels'}))
    elif name in {'adjacency', 'community_network', 'correlation_network', 'weighted_network', 'chord', 'sankey', 'alluvial'} and 'edge_annotation_layout' not in meta:
        clean = _strip_key_axes(after)
        nodes = source.get('nodes')
        if name == 'alluvial':
            nodes = list(dict.fromkeys((float(t), str(n)) for t, n in zip(source['source_stage']+source['target_stage'], source['source']+source['target'])))
        elif nodes is None: nodes = list(dict.fromkeys(source['source']+source['target']))
        classify('DOCUMENTED_LAYOUT_CHANGE', 'Full-name key and/or outer margins changed; primary numerical geometry is preserved.',
                 primary_marks_unchanged=equal(core(before, domains=False), core(clean, domains=False)),
                 domain_only_expanded=_no_crop(before, clean),
                 complete_node_key=_key_matches(meta, nodes),
                 full_name_key_is_actually_rendered=_rendered_key_matches(meta, after),
                 only_expected_metadata_added=_only_metadata_added(old_meta, meta, {'node_label_key'}))
    elif name == 'circular_heatmap':
        clean = _strip_key_axes(after); matrix = np.asarray(source['matrix'])
        if clean[0]['patches']:
            patches=clean[0]['patches']; expected=[]
            for i,j in np.ndindex(matrix.shape):
                start,end=j*2*np.pi/matrix.shape[1],(j+1)*2*np.pi/matrix.shape[1]
                vertices=[[start,i],[end,i],[end,i+1],[start,i+1],[start,i]]
                for point in vertices:
                    point[0]=0. if point[1]==0 or np.isclose(point[0]%(2*np.pi),2*np.pi,atol=1e-9) else point[0]%(2*np.pi)
                expected.append(vertices)
            colorbars=[c for axis in after if axis.get('auxiliary_role')=='colorbar' for c in axis['collections'] if c.get('array') is not None]
            colors=bool(colorbars)
            if colors:
                lut=colorbars[0]['colormap_lut']; lo,hi=colorbars[0]['color_domain']
                wanted=[lut[min(len(lut)-1,int((v-lo)/(hi-lo)*len(lut)))] for v in matrix.flat]
                colors=equal([p.get('facecolor') for p in patches],wanted)
            classify('DOCUMENTED_DISPLAY_CHANGE','One true polar arc per source cell removes tessellation seams without altering values.',
                     exact_source_matrix=equal(meta['matrix'],matrix.tolist()),
                     one_exact_angular_radial_cell_per_value=equal([p['vertices'] for p in core(clean)[0]['patches']],expected),
                     actual_cell_colors_match_source_and_shared_scale=colors,
                     full_row_key=_key_matches(meta,source['row_labels']) and _rendered_key_matches(meta,after))
            if not all(checks.values()): status='FAIL'
            return {'status':status,'documented_change':note,'invariant_checks':checks,
                    'verification_evidence':{'status':'PASS' if status!='FAIL' else 'FAIL','method':'actual polar cells, source matrix and scalar-map lookup'}}
        subdivision = meta.get('angular_tessellation', {}).get('subdivisions_per_cell', 0)
        collection = clean[0]['collections'][0]
        mesh = np.asarray(collection['array']); coordinates = collection.get('mesh_coordinates')
        classify('DOCUMENTED_DISPLAY_CHANGE', 'Angular cells are tessellated into arcs without adding observations.',
                 source_matrix_unchanged=equal(meta.get('matrix'), matrix.tolist()),
                 repeated_mesh_values_exact=subdivision > 0 and equal(mesh.tolist(), np.repeat(matrix, subdivision, axis=1).tolist()),
                 exact_angular_radial_boundaries=coordinates is not None and equal(np.asarray(coordinates)[0, :, 0].tolist(), np.linspace(0, 2*np.pi, matrix.shape[1]*subdivision+1).tolist()) and equal(np.asarray(coordinates)[:, 0, 1].tolist(), list(range(matrix.shape[0]+1))),
                 full_row_key=_key_matches(meta, source['row_labels']),
                 full_row_key_is_actually_rendered=_rendered_key_matches(meta, after),
                 original_domains_preserved=equal([[v['xlim'], v['ylim']] for v in before], [[v['xlim'], v['ylim']] for v in clean]),
                 only_expected_metadata_added=_only_metadata_added(old_meta, meta, {'angular_tessellation', 'row_label_key'}))
    elif {'nodes', 'edges'} <= source.keys() and 'positions' in meta:
        positions = meta['positions']; clean = _strip_key_axes(after)
        key = meta.get('node_label_key', {}); reverse_key = {value: code for code, value in key.items()}
        nodes_ok = set(positions) == set(map(str, source['nodes']))
        text_ok = True
        for node in source['nodes']:
            label = reverse_key.get(str(node), str(node)).replace('\n', '')
            text_ok &= any(t['text'].replace('\n', '') == label and equal(t['position'], positions.get(str(node))) for t in clean[0].get('texts', []))
        anchors = [p.get('endpoint_anchors') for p in clean[0]['patches'] if p['type'] == 'FancyArrowPatch']
        wanted = [[positions[str(u)], positions[str(v)]] for u, v, *_ in source['edges']]
        edge_values = source.get('events', source.get('probabilities', source.get('edge_labels', [])))
        annotations_ok = not edge_values or len(edge_values) == len(wanted)
        keyed_edges = any(len(str(value)) > 10 for value in edge_values)
        expected_edge_key = []
        for edge_index, (endpoints, value) in enumerate(zip(wanted, edge_values)):
            first, second = np.asarray(endpoints, dtype=float)
            layouts=meta.get('edge_annotation_layout',[])
            layout=layouts[edge_index] if edge_index < len(layouts) else None
            if layout is not None:
                match=next((p for p in clean[0]['patches'] if p['type']=='FancyArrowPatch' and equal(p.get('endpoint_anchors'),endpoints)),None)
                t=layout.get('curve_t',.5)
                annotations_ok &= isinstance(t,(int,float)) and .2 <= t <= .8
                midpoint=(1-t)**2*np.array(match['vertices'][0])+2*(1-t)*t*np.array(match['vertices'][1])+t*t*np.array(match['vertices'][2]) if match is not None else [float('inf')]*2
                annotations_ok &= equal(layout['edge'],source['edges'][edge_index]) and equal(layout['value'],value) and any(t['text']==layout['label'] and equal(t['position'],layout['position']) and equal(t['position'],np.asarray(midpoint).tolist()) for t in clean[0].get('texts',[]))
                expected_label = f'E{edge_index+1}' if keyed_edges else str(value)
                annotations_ok &= layout['label'] == expected_label
                expected_edge_key.append(f'{expected_label}：{reverse_key.get(str(source["edges"][edge_index][0]), str(source["edges"][edge_index][0]))} → {reverse_key.get(str(source["edges"][edge_index][1]), str(source["edges"][edge_index][1]))}；{value}')
            else:
                midpoint=(first+second)/2
                if abs(second[1]-first[1]) > abs(second[0]-first[0]): midpoint += [.22,0]
                annotations_ok &= any(t['text'].replace('\n','')==str(value).replace('\n','') and equal(t['position'],midpoint.tolist()) for t in clean[0].get('texts',[]))
        classify('DOCUMENTED_LAYOUT_CHANGE', 'Graph layout changes preserve every node, directed edge and supplied annotation.',
                 all_source_nodes_and_edges_retained=equal(meta.get('nodes'), source['nodes']) and equal(meta.get('edges'), source['edges']),
                 complete_finite_node_positions=nodes_ok and all(np.asarray(v).shape == (2,) and np.isfinite(v).all() for v in positions.values()),
                 every_node_label_at_its_position=text_ok,
                 actual_directed_edge_anchors_match_source=_multiset_equal(anchors, wanted),
                 supplied_edge_annotations_match_values_and_endpoints=annotations_ok,
                 full_edge_key_actually_rendered=not keyed_edges or any([''.join(v.split()) for v in legend] == [''.join(v.split()) for v in expected_edge_key] for legend in clean[0].get('figure_legends', [])),
                 complete_node_key=_key_matches(meta, source['nodes']),
                 full_name_key_is_actually_rendered=_rendered_key_matches(meta, after),
                 supplied_positions_preserved='positions' not in source or equal(positions, source['positions']),
                 only_expected_metadata_added=_only_metadata_added(old_meta, meta, {'node_label_key','edge_annotation_layout'}),
                 axes_remain_linear=all(v['xscale'] == v['yscale'] == 'linear' for v in clean))
    elif name == 'dendrogram':
        from scipy.cluster.hierarchy import dendrogram
        expected = dendrogram(np.asarray(source['linkage']), no_plot=True)
        orientation = meta.get('orientation'); horizontal = orientation in {'left', 'right'}
        actual = [p for c in after[0]['collections'] for p in c['paths']]
        wanted = [np.column_stack([y, x] if horizontal else [x, y]).tolist() for x, y in zip(expected['icoord'], expected['dcoord'])]
        distance_axis = after[0]['xlim' if horizontal else 'ylim']
        leaf_axis = after[0]['ylim' if horizontal else 'xlim']
        classify('DOCUMENTED_LAYOUT_CHANGE', 'Dendrogram orientation changes; every merge, distance and leaf order is preserved.',
                 exact_linkage_branch_geometry=equal(actual, wanted),
                 leaf_order_unchanged=equal(meta.get('leaf_order'), expected['leaves']),
                 distance_and_leaf_domains_valid=min(distance_axis) == 0 and max(distance_axis) >= max(np.asarray(source['linkage'])[:, 2]) and equal(sorted(leaf_axis), [0, len(source['labels'])*10]),
                 only_expected_metadata_added=_only_metadata_added(old_meta, meta, {'orientation'}))
    elif name == 'risk_return':
        points = _points(after[0])
        classify('DOCUMENTED_LAYOUT_CHANGE', 'Ordered side labels and additional whitespace preserve all risk/return coordinates.',
                 exact_risk_return_coordinates=len(points) == 1 and equal(points[0]['offsets'], np.column_stack([source['risk'], source['returns']]).tolist()),
                 primary_marks_unchanged=equal(core(before, domains=False), core(after, domains=False)),
                 domain_only_expanded=_no_crop(before, after),
                 only_expected_metadata_added=_only_metadata_added(old_meta, meta, {'label_layout'}))
    elif name == 'high_dim_density':
        data = np.asarray(source['data']); p = data.shape[1]
        panels = [v for v in after if v.get('auxiliary_role') != 'colorbar']
        same = len(panels) == p*p and equal(_hexbin_core(before), _hexbin_core(panels))
        domains = len(panels) == p*p
        norms = []
        for i in range(p):
            for j in range(p):
                if i*p+j >= len(panels): domains = False; continue
                panel = panels[i*p+j]
                domains &= equal(panel['xlim'], [data[:, j].min(), data[:, j].max()])
                if i != j:
                    domains &= equal(panel['ylim'], [data[:, i].min(), data[:, i].max()])
                    norms.extend(c.get('color_domain') for c in panel['collections'])
        maximum = max((max(c['array']) for panel in panels for c in panel['collections'] if c.get('array')), default=0)
        classify('DOCUMENTED_DISPLAY_CHANGE', 'All pairwise counts are retained with actual endpoint ticks and a shared count scale.',
                 all_pairwise_histograms_and_hexbin_counts_unchanged=same,
                 actual_range_endpoint_domains=domains,
                 shared_count_color_domain=bool(norms) and all(equal(n, [0, maximum]) for n in norms) and equal(meta.get('density_color_domain'), [0, maximum]),
                 observation_dimensions_unchanged=meta.get('observation_count') == len(data) and meta.get('dimensions') == p,
                 only_expected_metadata_added=_only_metadata_added(old_meta, meta, {'density_color_domain', 'tick_policy'}))
    elif name == 'polar_stacked_bar':
        classify('DOCUMENTED_DISPLAY_CHANGE', 'Polar origin angles canonicalized only at r=0; all nonzero geometry is identical.',
                 exact_nonzero_geometry_and_domains=equal(a, b),
                 values_and_denominators_unchanged=equal(numerical_metadata(old_meta), numerical_metadata(meta)))
    elif name == 'time_heatmap':
        time = np.asarray(source['time']); matrix = source['matrix']
        edges = np.r_[time[0]-.5, time[0]+.5] if len(time) == 1 else np.r_[time[0]-(time[1]-time[0])/2, (time[:-1]+time[1:])/2, time[-1]+(time[-1]-time[-2])/2]
        mesh = after[0]['collections'][0]; coords = mesh.get('mesh_coordinates')
        classify('DOCUMENTED_SEMANTIC_REPAIR', 'Column-index coordinates replaced by actual time centers and midpoint cell edges.',
                 source_matrix_exact=equal(meta.get('matrix'), matrix) and equal(mesh['array'], matrix),
                 actual_time_and_midpoint_edges=equal(meta.get('time'), time.tolist()) and equal(meta.get('time_edges'), edges.tolist()) and coords is not None and equal(np.asarray(coords)[0, :, 0].tolist(), edges.tolist()),
                 time_domain_uses_real_edges=equal(after[0]['xlim'], [edges[0], edges[-1]]),
                 row_domain_and_order=equal(after[0]['ylim'], before[0]['ylim']),
                 actual_row_labels_preserved=equal([v.replace('\n', '') for v in after[0].get('tick_labels', {}).get('y', [])], [str(v).replace('\n', '') for v in source['row_labels']]),
                 only_expected_metadata_added=_only_metadata_added(old_meta, meta, {'time', 'time_edges', 'time_encoding'}))
    elif name in {'correlation_matrix', 'indicator_correlation', 'correlation_bubble'}:
        with np.errstate(divide='ignore', invalid='ignore'):
            matrix = np.atleast_2d(np.corrcoef(np.asarray(source['data']), rowvar=False))
        expected = np.where(np.isfinite(matrix), matrix, None).tolist()
        checks['independent_Pearson_values'] = equal(meta.get('correlation'), expected)
        if name == 'correlation_bubble':
            colorbars = [c for axis in after if axis.get('auxiliary_role') == 'colorbar' for c in axis['collections'] if c.get('array') is not None]
            lut = colorbars[0].get('colormap_lut') if colorbars else None
            points = _points(after[0]); index = 0; correct = True; colors_correct = lut is not None
            for i in range(len(matrix)):
                for j in range(i+1):
                    if index >= len(points): correct = False; continue
                    point = points[index]; index += 1
                    correct &= equal(point['offsets'], [[j, i]])
                    if np.isfinite(matrix[i, j]):
                        correct &= equal(point['sizes'], [abs(matrix[i, j])*meta['area_scale']])
                        if lut is not None:
                            color_index = min(len(lut)-1, int((matrix[i, j]+1)/2*len(lut)))
                            colors_correct &= equal(point.get('facecolors'), [lut[color_index]])
                    else: correct &= len(point['offsets']) == 1
            classify('DOCUMENTED_SEMANTIC_REPAIR', 'Bubble area equals absolute Pearson r; fixed diverging domain and explicit undefined values.',
                     all_lower_triangle_coordinates_and_areas=correct and len(points) == len(matrix)*(len(matrix)+1)//2,
                     fixed_color_domain=bool(colorbars) and equal(meta.get('color_domain'), [-1, 1]) and all(equal(c.get('color_domain'), [-1, 1]) for c in colorbars),
                     all_bubble_colors_match_shared_colorbar=colors_correct,
                     only_axis_margin_expanded=_no_crop(before[:1], after[:1]),
                     full_variable_key=_key_matches(meta, source.get('labels', meta.get('variables', []))) and _rendered_key_matches(meta, after),
                     only_expected_metadata_added=_only_metadata_added(old_meta, meta, {'area_scale', 'color_domain', 'correlation', 'size_semantics', 'variable_label_key'}))
        else:
            classify('DOCUMENTED_SEMANTIC_REPAIR', 'Former composite view replaced by a true Pearson matrix; undefined entries remain explicit.',
                     actual_matrix_cells_exact=len(after[0]['images']) == 1 and equal(after[0]['images'][0], expected),
                     fixed_color_domain=equal(after[0].get('image_color_domains'), [[-1, 1]]),
                     numerical_metadata_unchanged=equal(numerical_metadata(old_meta), numerical_metadata(meta)))
    elif name == 'bubble':
        size = np.asarray(source['size']); x = np.asarray(source['x']); y = np.asarray(source['y'])
        groups = source.get('groups', ['组A']*len(size)); unique = list(dict.fromkeys(groups))
        points = _points(after[0]); correct = len(points) >= len(unique)
        for index, group in enumerate(unique):
            mask = np.asarray(groups) == group
            if index >= len(points): correct = False; continue
            correct &= equal(points[index]['offsets'], np.column_stack([x[mask], y[mask]]).tolist()) and equal(points[index]['sizes'], (size[mask]*meta['area_scale']).tolist())
        classify('DOCUMENTED_SEMANTIC_REPAIR', 'Bubble areas are proportional to original magnitudes; zero values retain coordinates.',
                 every_point_and_area_matches_source=correct,
                 saved_magnitudes_exact=equal(meta.get('magnitude'), size.tolist()),
                 only_expected_metadata_added=_only_metadata_added(old_meta, meta, {'area_scale', 'magnitude', 'marker_area_pt2', 'size_semantics'}),
                 original_domains_preserved=equal([[v['xlim'], v['ylim']] for v in before], [[v['xlim'], v['ylim']] for v in after]))
    elif name in {'raincloud', 'ridgeline'}:
        raw = source['values'] if name == 'raincloud' else source['groups']
        samples = raw if isinstance(raw[0], (list, tuple)) else [raw]
        points = _points(after[0]); correct = len(points) == len(samples)
        for i, sample in enumerate(samples):
            if i >= len(points): correct = False; continue
            displayed = np.asarray(points[i]['offsets'])[:, 1 if name == 'raincloud' else 0]
            correct &= equal(displayed.tolist(), sample)
        if name == 'raincloud':
            stats = meta.get('statistics', [])
            checks['quartiles_and_sample_sizes_exact'] = len(stats) == len(samples) and all(s['n'] == len(v) and equal(s['quartiles'], np.quantile(v, [.25, .5, .75]).tolist()) for s, v in zip(stats, samples))
            checks['one_quartile_box_per_group'] = len(after[0]['patches']) == len(samples)
        classify('DOCUMENTED_SEMANTIC_REPAIR', 'Every supplied observation is shown; no undocumented thinning or synthetic samples.',
                 all_raw_observations_exact=correct,
                 only_expected_metadata_added=_only_metadata_added(old_meta, meta, {'jitter', 'statistics'} if name == 'raincloud' else {'raw_point_counts', 'raw_point_selection'}),
                 measurement_domains_not_truncated=all(min(new['ylim' if name == 'raincloud' else 'xlim']) <= min(old['ylim' if name == 'raincloud' else 'xlim'])+1e-8 and max(new['ylim' if name == 'raincloud' else 'xlim']) >= max(old['ylim' if name == 'raincloud' else 'xlim'])-1e-8 for old, new in zip(before, after)))
    elif equal(core(before,domains=False),core(after,domains=False)) and equal(numerical_metadata(old_meta),numerical_metadata(meta)) and _no_crop(before,after):
        classify('DOCUMENTED_LAYOUT_CHANGE','Only the displayed margins expand; every numerical artist, transformation and statistic is unchanged.',
                 all_numeric_geometry_and_scales_unchanged=True,domain_only_expanded=True)
    else:
        clean_before, clean_after = deepcopy(a), deepcopy(b)
        changed_sizes = False; changed_contours = False; constant_sizes = True
        if len(clean_before) == len(clean_after):
            for axis0, axis1 in zip(clean_before, clean_after):
                if len(axis0['collections']) != len(axis1['collections']): break
                for c0, c1 in zip(axis0['collections'], axis1['collections']):
                    if not equal(c0['sizes'], c1['sizes']):
                        changed_sizes = True
                        constant_sizes &= c0['sizes'] is not None and c1['sizes'] is not None and len(c0['sizes']) == len(c1['sizes']) == 1 and c1['sizes'][0] > 0
                        c1['sizes'] = deepcopy(c0['sizes'])
                    if c0['type'] == c1['type'] == 'QuadContourSet' and not equal(c0['paths'], c1['paths']):
                        changed_contours = True; c1['paths'] = deepcopy(c0['paths'])
        if (changed_sizes or changed_contours) and equal(clean_before, clean_after) and equal(numerical_metadata(old_meta), numerical_metadata(meta)):
            # The name only identifies the source-grid formula; geometry is
            # independently checked rather than accepted by a chart whitelist.
            geometry = not changed_contours or _contour_geometry(source, name, before[0], after[0])
            if name == 'taylor_diagram':
                coordinates = [c['offsets'] for c in _points(after[0])]
                expected = [[[float(np.arccos(c)), s]] for s, c in zip(source['std'], source['correlation'])] + [[[0, source['reference_std']]]]
                checks['independent_taylor_standard_deviation_and_correlation'] = equal(coordinates, expected)
            classify('DOCUMENTED_DISPLAY_CHANGE', 'Constant decorative marker size and/or inline contour-label gaps changed; numerical evidence is preserved.',
                     all_other_marks_metadata_and_domains_unchanged=True,
                     only_constant_marker_sizes_changed=constant_sizes,
                     independently_verified_contour_geometry=geometry)

    if not all(checks.values()): status = 'FAIL'
    verified = status not in {'FAIL', 'NEEDS_REVIEW'} and all(checks.values())
    return {'status': status, 'documented_change': note, 'invariant_checks': checks,
            'verification_evidence': {'status': 'PASS' if verified else 'FAIL' if status == 'FAIL' else 'NOT_CHECKED',
                                      'method': 'saved-input-and-plotted-artists',
                                      'checks_passed': sum(checks.values()), 'checks_required': len(checks)}}
