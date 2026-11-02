"""Small, reproducible figure fixtures for contract and export tests.

The numeric examples are deliberately compact so tests do not depend on the
large source files in ``E:\数据要素``.  Each fixture records whether it is
    simulated and points to the reference source used to choose its schema.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np


REFERENCE_ROOT = Path(r"E:\数据要素")


def _meta(name: str, source: str, *, simulated: bool, independent_unit: str, units: dict[str, str]):
    return {"name": name, "source": "synthetic" if simulated else source, "simulated": simulated,
            "schema_reference": source,
            "independent_unit": independent_unit, "units": units,
            "interval_kind": None}


def classification_comparison():
    return {"categories": ["散货", "客船", "油船", "其他"],
            "values": [42, 31, 27, 18],
            "contract_meta": _meta("classification_comparison", str(REFERENCE_ROOT / "data/ship_profiles.csv"), simulated=True, independent_unit="ship type", units={"values": "count"})}


def time_series():
    t = np.arange(24)
    values = 30 + 4 * np.sin(t / 3) + np.linspace(0, 3, 24)
    return {"time": t, "values": values,
            "contract_meta": _meta("time_series", str(REFERENCE_ROOT / "data/merged_ais.csv"), simulated=True, independent_unit="hour", units={"values": "vessels/hour"})}


def model_predictions():
    observed = np.array([1.2, 1.8, 2.4, 3.0, 3.7, 4.1])
    predicted = observed + np.array([.08, -.04, .12, -.10, .06, -.02])
    return {"observed": observed, "predicted": predicted,
            "contract_meta": _meta("model_predictions", "synthetic fixture derived from ship-profile scale", simulated=True, independent_unit="ship", units={"observed": "normalized score", "predicted": "normalized score"})}


def multivariate_matrix():
    matrix = np.array([[82, 16, 1.2, 5.0], [88, 16, 3.0, 4.0], [106, 18, 4.2, 6.0], [74, 12, 2.1, 3.6]], dtype=float)
    return {"matrix": matrix,
            "contract_meta": _meta("multivariate_matrix", "synthetic fixture; no verified source rows", simulated=True, independent_unit="ship", units={"matrix": "mixed physical units; columns documented separately"})}


def network_edges():
    nodes = ["节点A", "节点B", "节点C", "节点D"]
    return {"nodes": nodes, "edges": [("节点A", "节点B"), ("节点B", "节点C"), ("节点C", "节点D"), ("节点A", "节点D")],
            "weights": [.72, -.38, .61, .24], "community": [0, 0, 1, 1],
            "contract_meta": _meta("network_edges", str(REFERENCE_ROOT / "data/node_classification.csv"), simulated=True, independent_unit="declared edge", units={"weights": "correlation"})}


def spatial_points():
    return {"longitude": np.array([113.18, 113.31, 113.45, 113.57]),
            "latitude": np.array([23.05, 23.10, 23.02, 23.14]),
            "size": np.array([5., 8., 4., 10.]), "group": np.array(["航道A", "航道A", "航道B", "航道B"]),
            "contract_meta": _meta("spatial_points", "synthetic fixture; no verified source rows", simulated=True, independent_unit="node", units={"longitude": "degree", "latitude": "degree", "size": "count"})}


def optimization_points():
    x = np.linspace(0, 1, 12)
    return {"x": x, "y": 1 - x + .05 * np.sin(8 * x), "response": np.exp(-x),
            "contract_meta": _meta("optimization_points", "synthetic optimization fixture", simulated=True, independent_unit="candidate solution", units={"x": "normalized parameter", "y": "objective"})}


__all__ = ["classification_comparison", "time_series", "model_predictions", "multivariate_matrix", "network_edges", "spatial_points", "optimization_points"]


def local_data_fixtures(root=REFERENCE_ROOT):
    """Read actual local tables; retain provenance and every selected source row.

    These are imported project data, not independently verified vendor records.
    No real/simulated claim is inferred from a directory's name.
    """
    import hashlib
    import pandas as pd
    root = Path(root)
    classification = root / 'data/node_classification.csv'
    nodes_file = root / 'data/processed/waterway_nodes.csv'
    edges_file = root / 'data/processed/waterway_edges_weighted.csv'
    result = {}
    def meta(path, unit, units, transform):
        return {'source': str(path.resolve()), 'simulated':False, 'independent_unit':unit,
                'units':units, 'interval_kind':'none', 'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'source_status':'imported local project table; raw acquisition not independently verified',
                'transformations':[transform]}
    if classification.is_file():
        frame = pd.read_csv(classification)
        fields = ['lat','lon','degree','pass_count','node_type_cn']
        if any(f not in frame for f in fields) or frame[fields].isna().any().any():
            raise ValueError('node classification fixture needs complete coordinates, degree, count and category')
        numeric = frame[['lat','lon','degree','pass_count']].to_numpy(float)
        if not np.isfinite(numeric).all() or np.any(frame['degree'] < 0) or np.any(frame['pass_count'] < 0):
            raise ValueError('invalid numeric node classification fixture')
        counts = frame['node_type_cn'].value_counts(sort=False)
        result['classification'] = {'categories':counts.index.tolist(),'values':counts.to_numpy(),
            'contract_meta':meta(classification,'waterway node',{'values':'节点数'},'count every row by recorded node_type_cn'), 'source_rows':len(frame)}
        result['multivariate'] = {'data':numeric,'labels':['纬度','经度','节点度','通过次数'],
            'contract_meta':meta(classification,'waterway node',{'lat':'°N','lon':'°E','degree':'邻接数','pass_count':'通过次数'},'select four complete named columns; no rows removed'), 'source_rows':len(frame)}
        result['spatial'] = {'longitude':frame['lon'].to_numpy(),'latitude':frame['lat'].to_numpy(),
            'size':frame['pass_count'].to_numpy(),'group':frame['node_type_cn'].tolist(),
            'contract_meta':meta(classification,'waterway node',{'longitude':'°E','latitude':'°N','size':'通过次数'},'retain every node; bubble area uses pass_count'), 'source_rows':len(frame)}
    if nodes_file.is_file() and edges_file.is_file():
        nodes = pd.read_csv(nodes_file); edges = pd.read_csv(edges_file)
        if not {'from_node','to_node','traversal_count'}.issubset(edges.columns) or edges[['from_node','to_node','traversal_count']].isna().any().any():
            raise ValueError('network fixture requires complete endpoints and traversal counts')
        if not np.isfinite(edges['traversal_count']).all() or np.any(edges['traversal_count'] < 0):
            raise ValueError('network traversal counts must be nonnegative')
        # The renderer is undirected. Aggregate explicitly, never silently discard parallel or reverse edges.
        totals = {}
        for row in edges.itertuples():
            key = tuple(sorted((str(int(row.from_node)),str(int(row.to_node)))))
            totals[key] = totals.get(key,0.) + float(row.traversal_count)
        declared = list(dict.fromkeys([str(int(v)) for v in nodes['node_id']] + [n for edge in totals for n in edge]))
        result['network'] = {'nodes':declared,'edges':list(totals),'weights':list(totals.values()),
            'contract_meta':meta(edges_file,'undirected waterway edge',{'weights':'通行次数（双向求和）'},'sum traversal_count by unordered endpoints; retain all declared nodes'), 'source_rows':len(edges)}
    return result
