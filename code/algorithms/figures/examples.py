"""Seeded, structured examples. Never used implicitly by production renderers."""
from __future__ import annotations
import hashlib
import numpy as np
from scipy.cluster.hierarchy import linkage
from .contracts import DataContract
from .compute import (compute_pca, compute_mantel, distances, compute_taylor, compute_dependence,
                      compute_lift_gain, compute_timeseries, compute_probability_plot, compute_ahp)

_EMBEDDINGS = {}


def _stress_labels(result, case):
    """Long-label fixtures retain IDs, numerical evidence and all category text."""
    if case != "long_labels":
        return result
    fields = {"labels", "categories", "groups", "row_labels", "column_labels", "metrics",
              "feature_names", "feature_labels", "parameters", "components", "facets",
              "events", "tasks", "constraints", "schemes", "runs", "dimensions"}
    for key in fields & result.keys():
        values = result[key]
        if isinstance(values, (list, tuple)) and values and all(isinstance(v, str) for v in values):
            result[key] = [v if len(v) > 15 else v + "（长期综合测量与约束条件）" for v in values]
    # Network IDs and their references must change together; merely replacing
    # nodes would break edges or create different nodes without warning.
    node_ids = result.get("nodes") or list(dict.fromkeys(
        [*result.get("source", []), *result.get("target", [])]))
    if node_ids and all(isinstance(v, str) for v in node_ids):
        renamed = {v: v + "（长期综合评估阶段）" for v in node_ids}
        if "nodes" in result:
            result["nodes"] = [renamed[v] for v in node_ids]
        for field in ("edges", "flows"):
            if field in result:
                result[field] = [(renamed.get(row[0], row[0]), renamed.get(row[1], row[1]), *row[2:])
                                 for row in result[field]]
        for field in ("source", "target"):
            if field in result:
                result[field] = [renamed.get(v, v) for v in result[field]]
    return result


def _stress_density(name, result, rng, case, seed):
    """Increase the relevant information dimension, never duplicate evidence."""
    if case != "dense":
        return result
    cats = [f"方案{i + 1:02d}" for i in range(12)]
    labels = [f"指标{i + 1:02d}" for i in range(8)]
    single = {"bar", "horizontal_bar", "dot_plot", "lollipop", "cleveland_dot",
              "diverging_bar", "ranking", "scenario_ranking", "score_bar",
              "feature_importance", "topsis_weights"}
    if name in single:
        vals = rng.uniform(.2, .9, len(cats))
        if name == "diverging_bar": vals -= .5
        if name == "topsis_weights": vals /= vals.sum()
        result.update(categories=cats, values=vals)
    elif name == "ahp_weights":
        weights = rng.uniform(.2, .9, len(labels))
        result = compute_ahp(weights[:, None] / weights[None, :], labels=labels)
    elif name in {"grouped_bar", "stacked_bar", "percent_stacked_bar", "percent_stacked_bar_line"}:
        result.update(categories=cats, groups=[f"处理{i+1}" for i in range(6)],
                      values=rng.uniform(.4, 1.5, (len(cats), 6)))
        if name == "percent_stacked_bar_line": result["line_values"] = rng.integers(100, 3500, len(cats))
    elif name in {"forest", "errorbar", "effect_size"}:
        from scipy.stats import t as t_distribution, sem
        observations = rng.normal(rng.normal(0, .4, (12, 1)), .5, (12, 30))
        center = observations.mean(1)
        half = t_distribution.ppf(.975, 29) * sem(observations, axis=1)
        result.update(categories=cats, lower=center-half, upper=center+half,
                      calculation={"method": "Student t mean interval", "independent_n_per_group": 30,
                                   "observations": observations.tolist()})
        result["values" if name == "errorbar" else "estimate"] = center
    elif name == "multi_metric_comparison":
        result.update(categories=cats, metrics=labels, values=rng.uniform(.2, .9, (12, 8)))
    elif name in {"boxplot", "violin", "ridgeline", "raw_points", "jitter", "beeswarm"}:
        groups = [rng.normal(i*.18, .6, 80) for i in range(10)]
        if name in {"raw_points", "jitter", "beeswarm"}:
            result.update(categories=cats[:10], samples=groups)
        elif name == "ridgeline": result.update(labels=cats[:10], groups=groups)
        else: result.update(labels=cats[:10], values=groups)
    elif name == "raincloud":
        result.update(values=[rng.normal(i*.3, .6, 85+i*7) for i in range(6)], labels=cats[:6])
    elif name == "waterfall": result.update(values=rng.normal(0, .4, 12), labels=cats)
    elif name in {"correlation_matrix", "correlation_bubble", "pairgrid", "partial_correlation"}:
        a = rng.multivariate_normal(np.zeros(6), np.eye(6)*.6+.4, size=180)
        if name == "partial_correlation":
            from .compute import compute_partial_correlation
            result = compute_partial_correlation(a, rng.normal(size=(180, 2)))
            result.update(labels=labels[:6], control_labels=["控制甲", "控制乙"])
        else: result.update(data=a, labels=labels[:6])
    elif name in {"parallel_coordinates", "high_dim_density"}:
        result.update(data=rng.normal(size=(180, 8)), features=labels)
    elif name == "event_timeline":
        result.update(time=np.arange(12), events=[f"事件{i+1:02d}" for i in range(12)])
    elif name == "gantt":
        start = np.arange(12)*.7
        result.update(tasks=cats, start=start, end=start+rng.uniform(1, 3, 12))
    elif name == "cross_validation": result.update(fold=[f"折{i+1:02d}" for i in range(12)], score=rng.uniform(.6, .95, 12))
    elif name in {"heatmap", "adjacency_matrix", "diverging_heatmap", "circular_heatmap", "clustered_heatmap", "threshold_heatmap", "time_heatmap"}:
        matrix = rng.normal(size=(12, 12))
        if name == "adjacency_matrix": matrix = (np.abs(matrix)>.8).astype(float)
        result.update(matrix=matrix, row_labels=cats, column_labels=[f"指标{i+1:02d}" for i in range(12)])
        if name == "clustered_heatmap": result.update(row_linkage=linkage(matrix), column_linkage=linkage(matrix.T))
        if name == "time_heatmap":
            result.update(matrix=rng.normal(size=(12, 100)), time=np.linspace(0, 12, 100))
            result.pop("column_labels", None)
    elif name == "dendrogram": result.update(linkage=linkage(rng.normal(size=(20, 4))), labels=[f"样本{i+1:02d}" for i in range(20)])
    elif name == "faceted_heatmap":
        result.update(matrices=rng.normal(size=(4, 8, 8)), facets=[f"情景{i+1}" for i in range(4)],
                      row_labels=labels, column_labels=labels)
    elif name == "confusion_matrix": result.update(matrix=rng.integers(0, 30, (8, 8)), labels=[f"类别{i+1}" for i in range(8)])
    elif name == "transition_matrix":
        matrix = rng.uniform(.1, 1, (8, 8)); result["matrix"] = matrix/matrix.sum(1, keepdims=True)
    elif name in {"response_surface", "contour", "spatial_heatmap", "response_surface_opt", "parameter_response", "feasible_heatmap", "feasible_region", "constraint_boundary"}:
        grid = np.linspace(-2, 2, 45); x, y = np.meshgrid(grid, grid); z = x*x+.7*y*y+.4*x*y
        result.update(x_grid=grid, y_grid=grid, z=z)
        if name.startswith("feasible"): result["feasible"] = z<=2
        if name == "constraint_boundary": result["constraint"] = z
    elif name == "spatial_scatter":
        result.update(longitude=rng.uniform(105, 120, 150), latitude=rng.uniform(25, 40, 150),
                      size=rng.uniform(5, 25, 150), group=np.resize(cats[:6], 150))
    elif name == "taylor_diagram":
        reference = rng.normal(size=180)
        result = compute_taylor(reference, np.column_stack([reference*(.5+.1*i)+rng.normal(0, .1+.05*i, 180) for i in range(8)]), labels=cats[:8])
    elif name in {"pca_scores", "pca_biplot", "pca_loadings", "scree_plot"}:
        pca_rng = np.random.default_rng(seed+317)
        base = pca_rng.normal(size=(180, 3))
        raw = np.column_stack([base, base@pca_rng.normal(size=(3, 9))+pca_rng.normal(0, .25, (180, 9))])
        model = compute_pca(raw, components=12)
        names = [f"变量{i+1:02d}" for i in range(12)]
        if name == "pca_scores": result = dict(scores=model['scores'][:, :2])
        elif name == "pca_biplot": result = dict(scores=model['scores'][:, :2], loadings=model['loadings'][:, :2], explained_variance=model['explained_variance'][:2], feature_labels=names)
        elif name == "pca_loadings": result = dict(loadings=model['loadings'][:, :2], labels=names)
        else: result = dict(explained_variance=model['explained_variance'])
        result['calculation'] = {'method': 'PCA with 12 retained components', 'input_matrix': raw.tolist()}
    elif name == "separation_loadings":
        result.update(loadings=rng.normal(size=(12, 4)), labels=cats,
                      components=[f"分量{i+1}" for i in range(4)])
    elif name == "mantel":
        a = rng.normal(size=(40, 4))
        result = compute_mantel(distances(a), distances(a+rng.normal(0, .2, a.shape)), permutations=199, seed=seed)
    elif name == "coverage":
        from scipy.stats import norm
        from .compute import compute_coverage
        nominal = np.linspace(.1, .99, 12); observations = rng.normal(size=180)
        prediction = observations+rng.normal(0, .3, 180)
        half = norm.ppf((1+nominal)/2)*.3
        result = compute_coverage(observations, prediction[:, None]-half, prediction[:, None]+half, nominal)
    elif name == "calendar_heatmap":
        from datetime import date, timedelta
        result.update(dates=[(date(2024, 1, 1)+timedelta(days=i)).isoformat() for i in range(366)],
                      values=np.sin(np.arange(366)/20)+rng.normal(0, .2, 366))
    elif name == "cluster_stability":
        from sklearn.cluster import KMeans
        from sklearn.metrics import adjusted_rand_score
        a = rng.normal(size=(180, 6)); reference = np.digitize(a[:, 0], [-.5, .5])
        scores = [[adjusted_rand_score(reference, KMeans(n_clusters=clusters, n_init=1, random_state=i).fit_predict(a)) for i in range(12)] for clusters in range(2, 8)]
        result.update(settings=[f"{i} 类" for i in range(2, 8)], scores=np.asarray(scores), runs=[f"重复{i+1}" for i in range(12)],
                      calculation={'method': 'KMeans repeated seeds; adjusted Rand index', 'seeds': list(range(12)), 'reference': reference.tolist()})
    elif name == "pareto":
        x = np.linspace(1, 12, 60); frontier = 12/x
        result.update(x=np.r_[x, x[:20]], y=np.r_[frontier, frontier[:20]+rng.uniform(.1, 1, 20)])
    elif name == "weight_sensitivity":
        weights = np.linspace(0, 1, 36)
        intercept = rng.uniform(.1, .8, (8, 1)); slope = rng.uniform(-.3, .3, (8, 1))
        result.update(weights=weights, scores=intercept+slope*weights, schemes=cats[:8])
    elif name == "coordinate_system":
        result.update(origin=[0, 0, 0], basis=[[1.5, .2, .1], [.3, 1.2, .2], [.2, .1, 1.4]])
    elif name == "radar": result.update(metrics=labels, values=rng.uniform(.3, 1, (6, 8)), groups=cats[:6])
    elif name in {"tornado", "constraint_slack", "global_local", "risk_return", "contribution_decomposition"}:
        if name == "tornado": result.update(parameters=labels, low=rng.uniform(-.5, .3, 8), high=rng.uniform(-.3, .5, 8))
        elif name == "constraint_slack": result.update(constraints=labels, slack=rng.uniform(-.2, .8, 8))
        elif name == "global_local": result.update(parameters=labels, local=rng.uniform(.1, 1, 8), global_values=rng.uniform(.1, 1, 8))
        elif name == "risk_return": result.update(risk=rng.uniform(.1, 1, 12), returns=rng.uniform(.1, 1, 12), labels=cats)
        else: result.update(components=labels, values=rng.normal(0, .4, 8))
    elif name in {"correlation_network", "community_network", "weighted_network", "adjacency", "dependency_graph", "flowchart", "algorithm_flow", "technical_route", "variable_dependency", "mechanism", "task_decomposition", "decision_tree", "input_model_validation_output", "state_machine", "state_transition"}:
        nodes = [f"阶段{i+1:02d}" for i in range(10)]
        edges = [(nodes[i], nodes[i+1]) for i in range(9)]+[(nodes[i], nodes[i+2]) for i in range(0, 8, 2)]
        if name in {"decision_tree", "task_decomposition"}:
            edges = [(nodes[(i-1)//2], nodes[i]) for i in range(1, 10)]
        result.update(nodes=nodes, edges=edges)
        if name in {"algorithm_flow", "technical_route", "input_model_validation_output"}:
            result.update(stages=[f"流程{i+1}" for i in range(10)], edge_labels=[f"关系{i+1}" for i in range(len(edges))])
            if name == "input_model_validation_output":
                result["stages"] = ["输入", "模型", "模型", "模型", "模型", "验证", "验证", "验证", "输出", "输出"]
        if name == "algorithm_flow": result["node_types"] = ["start"]+["process"]*7+["decision", "end"]
        if name in {"mechanism", "decision_tree"}: result["edge_labels"] = [f"条件{i+1}" for i in range(len(edges))]
        if name == "state_machine": result["events"] = [f"触发{i+1}" for i in range(len(edges))]
        if name == "state_transition":
            counts = {u: sum(a==u for a, b in edges) for u, v in edges}
            result["probabilities"] = [1/counts[u] for u, v in edges]
        if name == "correlation_network": result["weights"] = rng.uniform(-1, 1, len(edges))
        if name == "weighted_network": result["weights"] = rng.uniform(.1, 8, len(edges))
        if name == "community_network": result["community"] = [f"社区{i//2+1}" for i in range(10)]
    elif name == "chord":
        nodes = [f"对象{i+1}" for i in range(8)]
        result.update(nodes=nodes, flows=[(nodes[i], nodes[(i+1)%8], i+1) for i in range(8)]+[(nodes[i], nodes[(i+3)%8], i+2) for i in range(8)])
    elif name in {"sankey", "alluvial"}:
        source = [f"输入{i+1}" for i in range(6)]+[f"处理中{i+1}" for i in range(6)]
        target = [f"处理中{i+1}" for i in range(6)]+[f"输出{i+1}" for i in range(6)]
        values = list(range(2, 8))*2
        result.update(source=source, target=target, value=values)
        if name == "alluvial": result.update(source_stage=[0]*6+[1]*6, target_stage=[1]*6+[2]*6)
    elif name == "geometry":
        theta = np.arange(12)*2*np.pi/12
        result.update(points=np.column_stack([np.cos(theta), np.sin(theta)]).tolist(),
                      segments=[[i, (i+4)%12] for i in range(12)], polygons=[list(range(12))])
    return result


def example_data(name, *, seed=20261010, case='standard'):
    from .registry import get_spec
    name = get_spec(name).to_dict().get('alias_of') or name
    stable = int.from_bytes(hashlib.sha256(name.encode()).digest()[:4], 'little')
    rng = np.random.default_rng(seed+stable)
    n = 100 if case == 'dense' else 36
    categories = ['方案甲', '方案乙', '方案丙', '方案丁']
    labels = ['指标甲', '指标乙', '指标丙', '指标丁']
    if case == 'long_labels':
        categories = [v+'（包含多种约束条件和长期影响的比较方案）' for v in categories]
        labels = [v+'（标准化后的长期综合测量值）' for v in labels]
    t = np.linspace(0, 12, n)
    y = .35*t+np.sin(t)+rng.normal(0,.2,n)
    values = rng.uniform(.2,.9,4)
    data = rng.multivariate_normal(np.zeros(4),np.eye(4)*.6+.4,size=n)
    sample_groups = [rng.normal(i*.45,.6,n//3) for i in range(4)]
    grid = np.linspace(-2,2,15); X,Y = np.meshgrid(grid,grid); z = X**2+.7*Y**2+.4*X*Y
    matrix = rng.normal(size=(4,4))
    nodes = ['数据', '模型甲', '模型乙', '验证', '输出']
    edges = [(nodes[0],nodes[1]),(nodes[0],nodes[2]),(nodes[1],nodes[3]),(nodes[2],nodes[3]),(nodes[3],nodes[4])]
    truth = (data[:,0] > np.median(data[:,0])).astype(int)
    probability = 1/(1+np.exp(-data[:,0]+rng.normal(0,.5,n)))
    result = None
    from .practical import FIELDS as practical_fields
    if name in practical_fields and name != 'calendar_heatmap':
        from .practical_examples import example
        result = example(name)
        result['contract'] = DataContract(
            source='synthetic', simulated=True, independent_unit='synthetic scenario',
            units={'values': '合成单位', 'matrix': '见矩阵单位字段', 'y': result.get('unit', '合成单位')},
            transformations=('fixed structured practical-chart fixture',))
        if case == 'dense':
            if name in {'sparkline_matrix', 'matrix_pie', 'bubble_matrix'}:
                result['row_labels'] = [f'地区{i+1}' for i in range(5)]
                result['column_labels'] = [f'时期{i+1}' for i in range(5)]
                if name == 'sparkline_matrix':
                    result['series'] = [[dict(x=list(range(30)), y=(np.sin(np.arange(30)/3)+i+j).tolist(), unit='件') for j in range(5)] for i in range(5)]
                    result['series'][2][3] = None
                elif name == 'matrix_pie': result['values'] = rng.integers(0, 12, (5, 5, 3))
                else: result['values'] = rng.integers(0, 20, (5, 5))
            elif name in {'calendar_glyphs'}:
                from datetime import date, timedelta
                result['dates'] = [(date(2024, 1, 1)+timedelta(days=i)).isoformat() for i in range(366) if i%17]
                result['values'] = [i%13 for i in range(len(result['dates']))]
            elif name in {'correlation_heatmap', 'covariance_heatmap'}:
                from .compute import compute_matrix_statistics
                a = rng.normal(size=(180, 8)); a[:, -1] = 2
                result.update(compute_matrix_statistics(
                    a, labels=[f'变量{i+1}' for i in range(8)],
                    variable_units=['件', '元', '小时', '米', '千克', '秒', '升', '次'],
                    kind='correlation' if name == 'correlation_heatmap' else 'covariance', missing='raise'))
            elif name == 'regression_curve':
                x = np.linspace(0, 4, 180); cx = np.linspace(-1, 5, 200)
                result.update(x=x, y=2*x+1+rng.normal(0, .2, x.size), curve_x=cx, curve_y=2*cx+1,
                              calculation={'method': 'synthetic observed y=2x+1+noise; exact generating curve', 'simulated': True})
            elif name == 'pictogram': result['values'] = [54, 83, 66]
            elif name == 'polar_stacked_bar':
                result['categories'] = [f'类别{i+1}' for i in range(12)]
                result['values'] = rng.integers(0, 20, (12, 3))
        return _stress_labels(result, case)
    if name in {'bar','horizontal_bar','dot_plot','lollipop','cleveland_dot','diverging_bar','ranking','scenario_ranking','score_bar','feature_importance','topsis_weights'}:
        result=dict(categories=categories,values=values)
        if name=='diverging_bar': result['values']=values-.5
        if name in {'ranking','scenario_ranking'}: result['direction']='max'
        if name=='score_bar': result['score_kind']='归一化综合得分 (0–1)'
        if name=='feature_importance': result['method']='模型提供的非负重要性'
        if name=='topsis_weights': result.update(values=values/values.sum(),method='调用者给定的 TOPSIS 指标权重')
    elif name=='ahp_weights':
        result=compute_ahp(values[:,None]/values[None,:],labels=labels)
    elif name in {'grouped_bar','stacked_bar','percent_stacked_bar'}:
        result=dict(categories=categories,values=rng.uniform(.4,1.5,(4,3)),groups=['处理甲','处理乙','处理丙'])
    elif name == 'percent_stacked_bar_line':
        result = dict(categories=categories, values=rng.integers(1, 100, (4, 3)),
                      groups=['中性', '消极', '积极'], line_values=rng.integers(100, 3500, 4),
                      line_label='文本数量', right_ylabel='文本数量 (条)', xlabel='主题')
    elif name in {'forest','errorbar','effect_size'}:
        from scipy.stats import t as t_distribution, sem
        observations=rng.normal(rng.normal(0,.4,(4,1)),.5,(4,20)); center=observations.mean(1)
        half=t_distribution.ppf(.975,19)*sem(observations,axis=1)
        result=dict(categories=categories,lower=center-half,upper=center+half,interval_kind='95% CI',calculation={'method':'Student t mean interval','independent_n_per_group':20,'observations':observations.tolist()})
        result['estimate' if name!='errorbar' else 'values']=center
        if name=='effect_size': result['effect_kind']='标准化效应（模拟结果）'
    elif name=='multi_metric_comparison': result=dict(categories=categories,metrics=labels,values=rng.uniform(.2,.9,(4,4)))
    elif name in {'histogram','kde','ecdf','qq_plot','raincloud'}: result=dict(values=y)
    elif name in {'boxplot','violin'}: result=dict(values=sample_groups,labels=categories)
    elif name in {'raw_points','jitter','beeswarm'}: result=dict(categories=categories,samples=sample_groups,seed=seed)
    elif name=='probability_plot': result=compute_probability_plot(y)
    elif name=='pareto_distribution': result=dict(values=rng.pareto(2.5,n)+1)
    elif name=='ridgeline': result=dict(groups=sample_groups,labels=categories)
    elif name=='waterfall': result=dict(values=rng.normal(0,.4,4),labels=categories)
    elif name in {'scatter','scatter_trend','hexbin','joint_density','contour_density'}:
        result=dict(x=data[:,0],y=.6*data[:,0]+rng.normal(0,.4,n))
        if name=='scatter_trend': result['trend']=True
    elif name=='bubble': result=dict(x=data[:,0],y=data[:,1],size=rng.uniform(10,40,n),groups=np.resize(categories,n))
    elif name=='volcano': result=dict(x=data[:,0]*2,y=np.clip(10**(-np.abs(data[:,0])*2-rng.uniform(0,2,n)),1e-8,1))
    elif name=='bland_altman': result=dict(reference=y,comparison=y+rng.normal(.05,.3,n))
    elif name in {'correlation_matrix','correlation_bubble','pairgrid'}: result=dict(data=data,labels=labels)
    elif name in {'parallel_coordinates','high_dim_density'}: result=dict(data=data,features=labels)
    elif name=='partial_correlation':
        from .compute import compute_partial_correlation
        result=compute_partial_correlation(data,rng.normal(size=(n,1))); result.update(labels=labels,control_labels=['控制变量'])
    elif name in {'time_series','line','area','step','threshold_crossing'}:
        result=dict(time=t,values=y)
        if name=='threshold_crossing': result['threshold']=2.
    elif name in {'multi_series','stacked_area'}: result=dict(time=t,values=np.column_stack([y-y.min()+1,y*.6-y.min()+1,y*.3-y.min()+1]),groups=categories[:3])
    elif name in {'rolling_mean','decomposition','autocorrelation','partial_autocorrelation'}:
        calculated=compute_timeseries(t,y,window=5 if name=='rolling_mean' else None,period=6 if name=='decomposition' else None,max_lag=8 if name in {'autocorrelation','partial_autocorrelation'} else None)
        if name in {'autocorrelation','partial_autocorrelation'}: result=dict(lag=calculated['lag'],correlation=calculated['acf' if name=='autocorrelation' else 'pacf'],calculation=calculated['calculation'])
        else: result=calculated
    elif name=='event_timeline': result=dict(time=[1,4,7,10],events=['数据准备','模型拟合','验证完成','交付'])
    elif name=='gantt': result=dict(tasks=categories,start=[0,2,4,7],end=[3,5,8,11])
    elif name=='calendar_heatmap':
        import pandas as pd
        result=dict(dates=pd.date_range('2025-01-01',periods=n).strftime('%Y-%m-%d').tolist(),values=y)
    elif name in {'error_band','forecast_interval','control_chart','model_interval','robustness_envelope','learning_curve'}:
        result=dict(lower=y-.4,upper=y+.4,interval_kind='情景包络')
        if name=='error_band': result.update(time=t,center=y)
        elif name=='forecast_interval': result.update(time=t,observed=y+rng.normal(0,.1,n),predicted=y)
        elif name=='control_chart': result.update(time=t,values=y+rng.normal(0,.4,n),center=y,interval_kind='调用者给定的控制限')
        elif name=='model_interval': result.update(center=y)
        elif name=='robustness_envelope': result.update(x=t,center=y)
        else: result.update(train_size=np.arange(10,10+n),mean_score=y)
    elif name=='cross_validation': result=dict(fold=['折一','折二','折三','折四'],score=values)
    elif name in {'heatmap','adjacency_matrix','diverging_heatmap','circular_heatmap','clustered_heatmap','threshold_heatmap','time_heatmap'}:
        result=dict(matrix=matrix,row_labels=categories,column_labels=labels)
        if name=='adjacency_matrix': result['matrix']=(np.abs(matrix)>.8).astype(float)
        if name=='threshold_heatmap': result['threshold']=.5
        if name=='time_heatmap': result.update(matrix=rng.normal(size=(4,n)),time=t)
        if name=='clustered_heatmap': result.update(row_linkage=linkage(matrix),column_linkage=linkage(matrix.T))
    elif name=='dendrogram': result=dict(linkage=linkage(data[:8]),labels=[f'样本{i+1}' for i in range(8)])
    elif name=='faceted_heatmap': result=dict(matrices=rng.normal(size=(2,4,4)),facets=['场景甲','场景乙'],row_labels=categories,column_labels=labels)
    elif name=='confusion_matrix': result=dict(matrix=np.array([[17,3],[4,16]]),labels=['阴性','阳性'])
    elif name=='transition_matrix': result=dict(matrix=np.array([[.7,.2,.1],[.1,.7,.2],[.2,.1,.7]]))
    elif name in {'response_surface','contour','spatial_heatmap','response_surface_opt','parameter_response','feasible_heatmap','feasible_region','constraint_boundary'}:
        result=dict(x_grid=grid,y_grid=grid,z=z)
        if name=='response_surface_opt': result['direction']='min'
        if name=='parameter_response': result['parameters']=['参数甲','参数乙']
        if name.startswith('feasible'): result['feasible']=z<=2
        if name=='constraint_boundary': result.update(constraint=z,limit=2.)
    elif name=='spatial_3d': result=dict(x=data[:,0],y=data[:,1],z=data[:,2])
    elif name=='spatial_scatter': result=dict(longitude=rng.uniform(105,120,12),latitude=rng.uniform(25,40,12),size=rng.uniform(5,25,12),group=np.resize(categories[:3],12))
    elif name in {'roc_curve','pr_curve'}: result=dict(y_true=truth,y_score=probability)
    elif name=='calibration_curve':
        outcome=rng.binomial(1,probability); ids=np.minimum((probability*6).astype(int),5); bins=[i for i in range(6) if np.any(ids==i)]
        result=dict(probability=np.array([probability[ids==i].mean() for i in bins]),observed_rate=np.array([outcome[ids==i].mean() for i in bins]))
    elif name=='lift_gain': result=compute_lift_gain(truth,probability)
    elif name=='coverage':
        from .compute import compute_coverage
        pred=y+rng.normal(0,.3,n); half=np.array([.2,.4,.6]); result=compute_coverage(y,pred[:,None]-half,pred[:,None]+half,[.5,.8,.95])
    elif name in {'observed_predicted','residuals','residual_distribution','error_by_time'}:
        result=dict(observed=y,predicted=y+rng.normal(.05,.3,n))
        if name=='error_by_time': result['time']=t
    elif name=='taylor_diagram': result=compute_taylor(y,np.column_stack([y+rng.normal(0,.2,n),y*.7+rng.normal(0,.4,n)]),labels=categories[:2])
    elif name=='mantel': result=compute_mantel(distances(data[:12]),distances(data[:12]+rng.normal(0,.2,(12,4))),permutations=199,seed=seed)
    elif name in {'shap_summary','shap_beeswarm'}:
        from .compute import compute_linear_shap
        result=compute_linear_shap(data,[.5,-.3,.15,.05]); result['feature_names']=labels
    elif name in {'partial_dependence','ice'}:
        result=compute_dependence(lambda a:a[:,0]**2+.4*a[:,1],data,0,grid); result['feature_name']=labels[0]
    elif name in {'pca_scores','pca_biplot','pca_loadings','scree_plot'}:
        # Six-column shared model matches the PCA consistency regression test.
        pca_rng=np.random.default_rng(20261003+17); base=pca_rng.normal(size=(90,3)); raw=np.column_stack([base,base@pca_rng.normal(size=(3,3))+pca_rng.normal(0,.25,(90,3))])
        model=compute_pca(raw,components=6)
        if name=='pca_scores': result=dict(scores=model['scores'][:,:2])
        elif name=='pca_biplot': result=dict(scores=model['scores'][:,:2],loadings=model['loadings'][:,:2],explained_variance=model['explained_variance'][:2],feature_labels=['投入','产出','成本','效率','资源','质量'])
        elif name=='pca_loadings': result=dict(loadings=model['loadings'][:,:2],labels=['投入','产出','成本','效率','资源','质量'])
        else: result=dict(explained_variance=model['explained_variance'])
    elif name=='separation_loadings': result=dict(loadings=rng.normal(size=(4,3)),labels=labels,components=['分量甲','分量乙','分量丙'],method='调用者提供的线性分离模型系数')
    elif name=='umap':
        import json
        from importlib.resources import files
        resource=files(__package__).joinpath('resources/umap_example.json')
        stored=json.loads(resource.read_text(encoding='utf-8'))[str(n)]
        result=dict(embedding=np.asarray(stored['embedding']),calculation=dict(stored['calculation'],input_matrix=stored['matrix'],resource='resources/umap_example.json'))
    elif name=='tsne':
        key=(name,seed,case)
        if key not in _EMBEDDINGS:
            from sklearn.manifold import TSNE
            _EMBEDDINGS[key]=TSNE(n_components=2,perplexity=min(12,n-1),random_state=seed,init='pca').fit_transform(data)
        result=dict(embedding=_EMBEDDINGS[key],calculation={'method':name,'seed':seed,'input_matrix':data.tolist()})
    elif name in {'embedding_trajectory','cluster_scatter'}:
        embedding=np.column_stack([np.cos(t),np.sin(t)])+rng.normal(0,.1,(n,2))
        result=dict(embedding=embedding,time=t) if name=='embedding_trajectory' else dict(embedding=embedding,groups=np.resize(categories[:3],n))
    elif name=='state_trajectory': result=dict(time=t,states=np.column_stack([np.cos(t),np.sin(t)]),dimensions=['状态甲','状态乙'])
    elif name=='radar': result=dict(metrics=labels,values=rng.uniform(.3,1,(3,4)),groups=categories[:3])
    elif name=='convergence': result=dict(iterations=t,objective=np.exp(-t)+rng.uniform(0,.05,n))
    elif name=='repeated_convergence':
        traces=[]
        for rate in [.08,.12,.2]:
            position=float(rng.uniform(1,3)); trace=[]
            for _ in range(n): trace.append(position**2); position-=rate*2*position
            traces.append(trace)
        result=dict(iterations=np.arange(n),objectives=np.asarray(traces),runs=categories[:3],calculation={'method':'gradient descent on x squared','learning_rates':[.08,.12,.2]})
    elif name=='pareto': result=dict(x=np.arange(1,13),y=12/np.arange(1,13)+rng.uniform(0,.2,12))
    elif name in {'sensitivity','response_1d','perturbation'}:
        result=dict(x=grid,response=grid**2+.2*grid)
        if name!='sensitivity': result['parameter']='参数甲（标准化）'
    elif name=='tornado': result=dict(parameters=labels,low=[-.4,.3,-.2,.1],high=[.2,-.3,.3,.4])
    elif name=='optimum_distribution': result=dict(runs=[f'运行{i+1}' for i in range(n)],values=rng.normal(.1,.03,n))
    elif name=='cluster_stability':
        from sklearn.cluster import KMeans
        from sklearn.metrics import adjusted_rand_score
        reference=np.digitize(data[:,0],[-.5,.5]); scores=[]
        for clusters in [2,3,4]: scores.append([adjusted_rand_score(reference,KMeans(n_clusters=clusters,n_init=1,random_state=i).fit_predict(data)) for i in range(6)])
        result=dict(settings=['2 类','3 类','4 类'],scores=np.asarray(scores),runs=[f'重复{i+1}' for i in range(6)],metric='对合成参考分组的 ARI',calculation={'method':'KMeans repeated seeds; adjusted Rand index','seeds':list(range(6)),'reference':reference.tolist()})
    elif name=='scenario': result=dict(x=t,responses=np.array([y,y*.8,y*1.2]),scenarios=categories[:3])
    elif name=='constraint_slack': result=dict(constraints=labels,slack=[.3,-.1,.5,.2])
    elif name=='global_local': result=dict(parameters=labels,local=values,global_values=values[::-1]*.8,method='调用者提供的敏感性统计量')
    elif name=='risk_return': result=dict(risk=values,returns=values*.6+rng.uniform(0,.2,4),labels=categories)
    elif name=='weight_sensitivity': result=dict(weights=np.linspace(0,1,12),scores=np.array([np.linspace(.2,.8,12),np.linspace(.8,.3,12),np.full(12,.5)]),schemes=categories[:3])
    elif name=='contribution_decomposition': result=dict(components=labels,values=[.3,-.1,.4,.2],baseline=1.)
    elif name in {'correlation_network','community_network','weighted_network'}:
        result=dict(nodes=nodes,edges=edges)
        if name=='correlation_network': result['weights']=[.8,-.4,.6,-.5,.3]
        if name=='weighted_network': result['weights']=[2,4,7,3,1]
        if name=='community_network': result['community']=['社区甲','社区甲','社区乙','社区乙','社区丙']
    elif name=='chord': result=dict(nodes=nodes[:4],flows=[(nodes[0],nodes[1],5),(nodes[1],nodes[2],3),(nodes[2],nodes[3],2),(nodes[3],nodes[0],4)])
    elif name in {'sankey','alluvial'}:
        result=dict(source=[nodes[0],nodes[0],nodes[1],nodes[2]],target=[nodes[1],nodes[2],nodes[4],nodes[4]],value=[6,4,6,4])
        if name=='alluvial': result.update(source_stage=[0,0,1,1],target_stage=[1,1,2,2])
    elif name=='geometry': result=dict(points=[[0,0],[3,0],[2,2],[.5,1.5]],segments=[[0,2]],polygons=[[0,1,2,3]])
    elif name=='coordinate_system': result=dict(origin=[0,0],basis=[[1.5,.2],[.3,1.2]])
    elif name in {'adjacency','dependency_graph','flowchart','algorithm_flow','technical_route','variable_dependency','mechanism','task_decomposition','decision_tree','input_model_validation_output','state_machine','state_transition'}:
        result=dict(nodes=nodes,edges=edges)
        if name in {'decision_tree','task_decomposition'}: result['edges']=[(nodes[0],nodes[1]),(nodes[0],nodes[2]),(nodes[1],nodes[3]),(nodes[2],nodes[4])]
        if name in {'algorithm_flow','technical_route','input_model_validation_output'}: result.update(stages=['输入','模型','模型','验证','输出'],edge_labels=['拟合甲','拟合乙','检验甲','检验乙','交付'])
        if name=='algorithm_flow': result['node_types']=['start','process','process','decision','end']
        if name=='decision_tree': result['edge_labels']=['条件甲成立','条件甲不成立','条件乙成立','条件乙不成立']
        if name=='mechanism': result['edge_labels']=['模型假设甲','模型假设乙','作用路径甲','作用路径乙','观测对应']
        if name=='state_machine': result.update(edges=edges+[(nodes[3],nodes[0])],events=['拟合甲','拟合乙','检验甲','检验乙','通过','重试'])
        if name=='state_transition': result['probabilities']=[.6,.4,1,1,1]
    if result is None: raise ValueError(f'no structured example for {name}')
    if name == 'raincloud' and case == 'long_labels':
        result.update(values=sample_groups, labels=categories)
    result = _stress_density(name, result, rng, case, seed)
    result['contract']=DataContract(source='synthetic',simulated=True,independent_unit='synthetic scenario',
        units={'values':'合成单位','coordinates':'合成坐标','scores':'无量纲'},random_seed=seed,
        transformations=('chart-specific synthetic fixture',))
    return _stress_labels(result, case)
