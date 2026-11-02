"""Figure registry and capability metadata.

The registry is deliberately data-first: ``list_figures`` can be used by
documentation and gallery builders without importing optional plotting code.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, replace
from typing import Callable, Any
import inspect
import numpy as np
import matplotlib.pyplot as plt

from .base import attach_metadata, metadata_value


@dataclass(frozen=True)
class FigureSpec:
    name: str
    category: str
    question: str
    required_fields: tuple[str, ...]
    independent_unit: str = "observation"
    status: str = "available"
    implementation_level: str = "adapter"
    paper_suitable: bool = False
    simulate: bool = False
    qa_status: str = "not_checked"
    factory: Callable[..., Any] | None = None

    @property
    def name_zh(self) -> str:
        return display_name(self.name)

    @property
    def question_zh(self) -> str:
        return f"{self.category}中的{self.name_zh}"

    def to_dict(self):
        data = asdict(self)
        data.pop("factory", None)
        data["name_zh"] = self.name_zh
        data["question_zh"] = self.question_zh
        data["aliases"] = [self.name_zh]
        data["alias_of"] = _ALIAS_OF.get(self.name)
        data["formal_supported"] = self.implementation_level in {"dedicated", "alias"}
        return data


_REGISTRY: dict[str, FigureSpec] = {}

# Chinese display names are part of the public catalog.  English identifiers
# remain stable Python keys so existing notebooks do not break, while users
# can browse or call the same chart by its Chinese name.
_ZH_NAMES_TEXT = {
    # 单变量与分布
    "histogram": "直方图", "kde": "核密度图", "ecdf": "经验累积分布图",
    "boxplot": "箱线图", "violin": "小提琴图", "raincloud": "雨云图",
    "ridgeline": "山脊图", "beeswarm": "蜂群图", "jitter": "抖动散点图",
    "qq_plot": "QQ图", "probability_plot": "概率图", "control_chart": "控制图",
    "pareto_distribution": "帕累托分布图",
    # 类别比较
    "bar": "柱状图", "horizontal_bar": "横向柱状图", "grouped_bar": "分组柱状图",
    "stacked_bar": "堆叠柱状图", "percent_stacked_bar": "百分比堆叠柱状图",
    "percent_stacked_bar_line": "百分比堆叠柱折线图",
    "diverging_bar": "发散条形图", "dot_plot": "点图", "lollipop": "棒棒糖图",
    "cleveland_dot": "克利夫兰点图", "raw_points": "原始点图", "errorbar": "误差棒图",
    "forest": "森林图", "effect_size": "效应量图", "multi_metric_comparison": "多指标比较图",
    "waterfall": "瀑布图",
    # 关系与相关
    "scatter": "散点图", "scatter_trend": "趋势散点图", "bubble": "气泡图", "volcano": "火山图",
    "joint_density": "联合密度图", "contour_density": "等高线密度图", "hexbin": "六边形分箱图",
    "pairgrid": "成对关系图", "correlation_matrix": "相关矩阵", "correlation_bubble": "相关气泡图",
    "clustered_heatmap": "聚类热图", "mantel": "Mantel关联图", "bland_altman": "Bland-Altman一致性图",
    "partial_correlation": "偏相关图", "partial_dependence": "部分依赖图",
    # 时间序列与动态过程
    "time_series": "时间序列图", "line": "折线图", "multi_series": "多序列折线图",
    "step": "阶梯图", "area": "面积图", "stacked_area": "堆叠面积图", "error_band": "误差带图",
    "event_timeline": "事件时间线", "gantt": "甘特图", "time_heatmap": "时间热图",
    "calendar_heatmap": "日历热图", "rolling_mean": "滚动均值图", "decomposition": "时间序列分解图",
    "autocorrelation": "自相关图", "partial_autocorrelation": "偏自相关图", "forecast_interval": "预测区间图",
    "observed_predicted": "观测值-预测值图", "state_trajectory": "状态轨迹图",
    # 热图与矩阵
    "heatmap": "热图", "diverging_heatmap": "发散色热图", "clustered_heatmap_matrix": "聚类矩阵热图",
    "confusion_matrix": "混淆矩阵", "transition_matrix": "转移矩阵", "adjacency_matrix": "邻接矩阵",
    "response_surface": "响应面图", "feasible_heatmap": "可行域热图", "circular_heatmap": "环形热图",
    "faceted_heatmap": "分面热图", "threshold_heatmap": "阈值热图",
    # 模型评估
    "roc_curve": "ROC曲线", "pr_curve": "PR曲线", "calibration_curve": "校准曲线",
    "confusion_matrix_eval": "模型混淆矩阵", "lift_gain": "提升-增益曲线", "residuals": "残差图",
    "residual_distribution": "残差分布图", "learning_curve": "学习曲线", "cross_validation": "交叉验证图",
    "model_interval": "模型区间图", "taylor_diagram": "泰勒图", "coverage": "覆盖率图",
    "error_by_time": "随时间误差图", "shap_summary": "SHAP汇总图", "shap_beeswarm": "SHAP蜂群图",
    "feature_importance": "特征重要性图", "ice": "个体条件期望图",
    # 优化、灵敏度与稳健性
    "convergence": "收敛曲线", "repeated_convergence": "重复收敛曲线", "optimum_distribution": "最优值分布图",
    "sensitivity": "灵敏度曲线", "tornado": "龙卷风图", "response_1d": "一维响应曲线",
    "response_surface_opt": "优化响应面图", "feasible_region": "可行域图", "constraint_slack": "约束松弛图",
    "perturbation": "扰动分析图", "scenario": "情景分析图", "risk_return": "风险-收益图",
    "pareto": "帕累托前沿图", "robustness_envelope": "稳健性包络图", "threshold_crossing": "阈值穿越图",
    "global_local": "全局-局部敏感性图", "scenario_ranking": "情景排序图",
    # 降维、聚类与高维结构
    "pca_scores": "主成分得分图", "pca_loadings": "主成分载荷图", "scree_plot": "碎石图",
    "pca_biplot": "主成分双标图", "tsne": "t-SNE图", "umap": "UMAP图", "embedding": "嵌入空间图",
    "embedding_trajectory": "嵌入轨迹图", "cluster_scatter": "聚类散点图", "dendrogram": "树状图",
    "parallel_coordinates": "平行坐标图", "high_dim_density": "高维密度图", "separation_loadings": "分离载荷图",
    "cluster_stability": "聚类稳定性图",
    # 网络、流量与空间关系
    "correlation_network": "相关网络图", "dependency_graph": "依赖关系图", "weighted_network": "加权网络图",
    "community_network": "社区网络图", "network": "节点网络图", "chord": "弦图", "sankey": "桑基图", "alluvial": "冲积图",
    "flowchart": "流程图", "state_transition": "状态转移图", "adjacency": "邻接关系图",
    "spatial_scatter": "空间散点图", "spatial_heatmap": "空间热图", "contour": "空间等高线图",
    "spatial_3d": "三维空间图",
    # 多指标与综合评价
    "radar": "雷达图", "multi_metric": "多指标对比图", "multi_metric_points": "多指标点图",
    "score_bar": "综合得分柱状图", "topsis_weights": "TOPSIS权重图", "ahp_weights": "AHP权重图",
    "weight_sensitivity": "权重敏感性图", "indicator_correlation": "指标相关图",
    "contribution_decomposition": "贡献分解图", "ranking": "排名图", "scheme_indicator_matrix": "方案-指标矩阵",
    # 数学建模专用图
    "geometry": "几何结构图", "coordinate_system": "坐标系图", "parameter_response": "参数响应图",
    "constraint_boundary": "约束边界图", "mechanism": "机制示意图", "technical_route": "技术路线图",
    "variable_dependency": "变量依赖图", "decision_tree": "决策树图", "state_machine": "状态机图",
    "task_decomposition": "任务分解图", "algorithm_flow": "算法流程图",
    "input_model_validation_output": "输入-模型-验证-输出图",
}
FIGURE_NAMES_ZH = dict(_ZH_NAMES_TEXT)


def display_name(name: str) -> str:
    """Return the Chinese catalog label while keeping ``name`` as the key."""
    if name in FIGURE_NAMES_ZH:
        return FIGURE_NAMES_ZH[name]
    return name.replace("_", " ")


_ALIASES_ZH = {label: key for key, label in FIGURE_NAMES_ZH.items()}


def _resolve_name(name: str) -> str:
    return _ALIASES_ZH.get(name, name)


def register(name: str, *, category: str, question: str, required_fields=(),
             independent_unit="observation", status="available", implementation_level="adapter",
             paper_suitable=False, simulate=False, qa_status="not_checked"):
    def decorator(factory):
        _REGISTRY[name] = FigureSpec(name, category, question, tuple(required_fields), independent_unit,
                                     status, implementation_level, paper_suitable, simulate, qa_status, factory)
        return factory
    return decorator


def _generic(*args, **kwargs):
    category = kwargs.pop("_category", "")
    figure_name = kwargs.pop("figure_name", "generic")
    data = kwargs.pop("data", None) or (args[0] if args and isinstance(args[0], dict) else {})
    if not data:
        raise ValueError("this figure requires data=...; synthetic data are never invented by the API")
    ax = kwargs.pop("ax", None) or plt.subplots(constrained_layout=True)[1]
    values = np.asarray(data.get("values", data.get("y", [])), dtype=float)
    if values.size == 0: raise ValueError("data must contain values or y")
    x = np.arange(values.size)
    if category in {"单变量与分布"}:
        ax.hist(values, bins=8, color="#3C6E8F", alpha=.82, edgecolor="#262626")
        ax.set(xlabel="值", ylabel="频数")
    elif category in {"类别比较", "多指标与综合评价"}:
        ax.bar(x, values, color=["#3C6E8F", "#D97745", "#5B8C6A", "#8A6E9C"] * 4)
        ax.set(xlabel="类别", ylabel="指标值")
    elif category in {"关系与相关"}:
        ax.scatter(values, np.roll(values, 3), s=22, color="#3C6E8F", alpha=.8)
        ax.set(xlabel="变量 X", ylabel="变量 Y")
    elif category in {"热图与矩阵"}:
        n = max(3, min(10, int(np.ceil(np.sqrt(values.size)))))
        matrix = np.resize(values, (n, n))
        image = ax.imshow(matrix, cmap="YlOrRd", aspect="auto")
        ax.figure.colorbar(image, ax=ax, label="强度")
        ax.set(xlabel="列", ylabel="行")
    elif category in {"网络、流量与空间关系", "数学建模专用图"}:
        points = np.column_stack([np.cos(np.linspace(0, 2*np.pi, min(values.size, 8), endpoint=False)),
                                  np.sin(np.linspace(0, 2*np.pi, min(values.size, 8), endpoint=False))])
        ax.scatter(points[:, 0], points[:, 1], s=110, color="#3C6E8F", edgecolor="#262626", zorder=2)
        for i in range(len(points) - 1):
            ax.plot(points[i:i+2, 0], points[i:i+2, 1], color="#6B6B6B", lw=.8, zorder=1)
        ax.axis("off")
    else:
        ax.plot(x, values, color="#3C6E8F", marker="o", ms=3)
        ax.set(xlabel="索引", ylabel="值")
    ax.set_title(f"{display_name(figure_name)} · 模板演示", fontsize=9)
    return attach_metadata(ax.figure, name=figure_name, name_zh=display_name(figure_name),
                           category=category, generic_demo=True, required_fields=tuple(data))


def _generic_for(name: str):
    """Build a safe adapter for a catalog entry without fabricating fields."""
    def factory(*args, **kwargs):
        data = kwargs.get("data") or (args[0] if args and isinstance(args[0], dict) else None)
        if not isinstance(data, dict) or not ("values" in data or "y" in data):
            raise ValueError(f"{name} generic adapter requires data={{'values': ...}}")
        kwargs["figure_name"] = name
        kwargs["_category"] = _REGISTRY[name].category
        return _generic(*args, **kwargs)
    factory.__name__ = name
    return factory


def _register_catalog():
    catalogs = {
      "distribution": "单变量与分布", "comparison": "类别比较", "relationship": "关系与相关", "timeseries": "时间序列与动态过程", "heatmap": "热图与矩阵", "evaluation": "模型评估", "optimization": "优化、灵敏度与稳健性", "dimensionality": "降维、聚类与高维结构", "network": "网络、流量与空间关系", "multi_metric": "多指标与综合评价", "diagram": "数学建模专用图"
    }
    names = {
      "distribution": "histogram kde ecdf boxplot violin raincloud ridgeline beeswarm jitter qq_plot probability_plot control_chart pareto_distribution",
      "comparison": "bar horizontal_bar grouped_bar stacked_bar percent_stacked_bar percent_stacked_bar_line diverging_bar dot_plot lollipop cleveland_dot raw_points errorbar forest effect_size multi_metric_comparison waterfall",
      "relationship": "scatter scatter_trend bubble volcano joint_density contour_density hexbin pairgrid correlation_matrix correlation_bubble clustered_heatmap mantel bland_altman partial_correlation partial_dependence",
      "timeseries": "time_series multi_series step area stacked_area error_band event_timeline gantt time_heatmap calendar_heatmap rolling_mean decomposition autocorrelation partial_autocorrelation forecast_interval observed_predicted state_trajectory",
      "heatmap": "heatmap diverging_heatmap clustered_heatmap_matrix confusion_matrix transition_matrix adjacency_matrix response_surface feasible_heatmap circular_heatmap faceted_heatmap threshold_heatmap",
      "evaluation": "roc_curve pr_curve calibration_curve confusion_matrix_eval lift_gain observed_predicted residuals residual_distribution learning_curve cross_validation model_interval taylor_diagram coverage error_by_time shap_summary shap_beeswarm feature_importance partial_dependence ice",
      "optimization": "convergence repeated_convergence optimum_distribution sensitivity tornado response_1d response_surface_opt feasible_region constraint_slack perturbation scenario risk_return pareto robustness_envelope threshold_crossing global_local scenario_ranking",
      "dimensionality": "pca_scores pca_loadings scree_plot pca_biplot tsne umap embedding_trajectory cluster_scatter dendrogram parallel_coordinates high_dim_density separation_loadings cluster_stability",
      "network": "correlation_network dependency_graph weighted_network community_network chord sankey alluvial flowchart state_transition adjacency spatial_scatter spatial_heatmap contour spatial_3d",
      "multi_metric": "radar parallel_coordinates multi_metric_points score_bar topsis_weights ahp_weights weight_sensitivity indicator_correlation contribution_decomposition ranking scheme_indicator_matrix",
      "diagram": "geometry coordinate_system parameter_response constraint_boundary mechanism technical_route variable_dependency decision_tree state_machine task_decomposition algorithm_flow input_model_validation_output",
    }
    for category, names_text in names.items():
        for name in names_text.split():
            if name not in _REGISTRY:
                _REGISTRY[name] = FigureSpec(name=name, category=catalogs[category], question=f"{catalogs[category]}: {name}",
                                              required_fields=("values",), status="generic adapter; validate input before use", implementation_level="adapter",
                                              paper_suitable=False, factory=_generic_for(name))


_register_catalog()

# Replace generic adapters with the small, validated implementations shipped in
# the category modules.  The remaining catalog entries intentionally stay
# generic adapters so that the registry is complete without pretending that a
# specialized statistical implementation exists for every named chart.
from .distributions import histogram, kde, ecdf, boxplot, violin, raincloud, qq_plot
from .comparisons import horizontal_bar, dot_plot, forest, waterfall
from .relationships import scatter, bland_altman
from .timeseries import line, forecast_interval
from .heatmaps import heatmap, confusion_matrix, response_surface
from .model_evaluation import pr_curve, observed_predicted, residuals
from .optimization import convergence, sensitivity, pareto
from .dimensionality import embedding, pca_scores, tsne, umap
from .networks import network, dependency
from .diagrams import flowchart
from .academic_style import (
    grouped_bar_academic, bar_academic, roc_multi, correlation_pairgrid, correlation_matrix, radar_comparison,
    ridgeline, bubble_scatter, correlation_bubble_matrix,
    correlation_network_academic, weighted_network_academic,
    community_network_academic, chord_academic, embedding_trajectory_academic,
    cluster_scatter_academic, pca_biplot_academic, pca_loadings_academic, scree_plot_academic,
    mantel_linkage, make_academic_catalog_adapter,
)
from .validated import stacked_bar, errorbar, error_band, learning_curve, robustness_envelope, transition_matrix, sankey, alluvial
from .combinations import percent_stacked_bar_line, validate_percent_stacked_bar_line

_BUILTINS = {
    "percent_stacked_bar_line": percent_stacked_bar_line,
    "stacked_bar": stacked_bar, "errorbar": errorbar, "error_band": error_band,
    "learning_curve": learning_curve, "robustness_envelope": robustness_envelope,
    "transition_matrix": transition_matrix, "sankey": sankey, "alluvial": alluvial,
    "histogram": histogram, "kde": kde, "ecdf": ecdf, "boxplot": boxplot,
    "violin": violin, "raincloud": raincloud, "qq_plot": qq_plot,
    "grouped_bar": grouped_bar_academic, "bar": bar_academic, "horizontal_bar": horizontal_bar,
    "dot_plot": dot_plot, "forest": forest, "waterfall": waterfall,
    "scatter": scatter, "scatter_trend": scatter, "correlation_matrix": correlation_matrix,
    "bland_altman": bland_altman, "time_series": line, "line": line,
    "forecast_interval": forecast_interval, "heatmap": heatmap,
    "confusion_matrix": confusion_matrix, "response_surface": response_surface,
    "roc_curve": roc_multi, "pr_curve": pr_curve,
    "observed_predicted": observed_predicted, "residuals": residuals,
    "convergence": convergence, "sensitivity": sensitivity, "pareto": pareto,
    "embedding": embedding, "pca_scores": pca_scores, "network": network,
    "tsne": tsne, "umap": umap,
    "dependency_graph": dependency, "flowchart": flowchart,
    # Specialized patterns adapted from the local academic-data-visualization
    # reference atlas.  Stable registry keys and Chinese aliases are preserved.
    "pairgrid": correlation_pairgrid, "radar": radar_comparison,
    "ridgeline": ridgeline, "bubble": bubble_scatter,
    "correlation_bubble": correlation_bubble_matrix,
    "correlation_network": correlation_network_academic, "weighted_network": weighted_network_academic,
    "community_network": community_network_academic, "chord": chord_academic,
    "embedding_trajectory": embedding_trajectory_academic, "cluster_scatter": cluster_scatter_academic,
    "pca_biplot": pca_biplot_academic, "pca_loadings": pca_loadings_academic, "scree_plot": scree_plot_academic,
    "mantel": mantel_linkage,
}
for _name, _factory in _BUILTINS.items():
    if _name in _REGISTRY:
        old = _REGISTRY[_name]
        _REGISTRY[_name] = FigureSpec(name=old.name, category=old.category, question=old.question,
                                      required_fields=old.required_fields, independent_unit=old.independent_unit,
                                      status="available", implementation_level="dedicated",
                                      paper_suitable=False, simulate=old.simulate, qa_status="not_checked",
                                      factory=_factory)

# Every remaining catalog entry now uses the same publication-oriented visual
# grammar.  The adapter consumes chart-specific fields when available and
# accepts ``values`` for quick previews, so all registered names are callable
# from a modeling notebook without falling back to the old blue template.
for _name, _spec in list(_REGISTRY.items()):
    if _spec.status.startswith("generic adapter"):
        _REGISTRY[_name] = FigureSpec(name=_spec.name, category=_spec.category, question=_spec.question,
                                      required_fields=_spec.required_fields, independent_unit=_spec.independent_unit,
                                      status="available", implementation_level="adapter", paper_suitable=False,
                                      simulate=_spec.simulate, qa_status="not_checked",
                                      factory=make_academic_catalog_adapter(_name, display_name(_name)))

_REQUIRED_FIELDS = {
    "percent_stacked_bar_line": ("categories", "values", "groups", "line_values"),
    "histogram": ("values",), "kde": ("values",), "ecdf": ("values",),
    "boxplot": ("values",), "violin": ("values",), "raincloud": ("values",),
    "bar": ("categories", "values"), "grouped_bar": ("categories", "values", "groups"),
    "stacked_bar": ("categories", "values", "groups"), "horizontal_bar": ("categories", "values"),
    "dot_plot": ("categories", "values"), "forest": ("categories", "estimate", "lower", "upper", "interval_kind"),
    "errorbar": ("categories", "values", "lower", "upper", "interval_kind"),
    "scatter": ("x", "y"), "scatter_trend": ("x", "y", "trend"), "bubble": ("x", "y", "size"), "volcano": ("x", "y"),
    "joint_density": ("x", "y"), "hexbin": ("x", "y"),
    "correlation_matrix": ("data",), "bland_altman": ("reference", "comparison"),
    "time_series": ("time", "values"), "forecast_interval": ("time", "observed", "predicted", "lower", "upper", "interval_kind"),
    "heatmap": ("matrix",), "confusion_matrix": ("matrix",), "transition_matrix": ("matrix",),
    "response_surface": ("x_grid", "y_grid", "z"),
    "roc_curve": ("y_true", "y_score"), "pr_curve": ("y_true", "y_score"),
    "observed_predicted": ("observed", "predicted"), "residuals": ("observed", "predicted"),
    "convergence": ("iterations", "objective"), "sensitivity": ("x", "response"), "pareto": ("x", "y"),
    "learning_curve": ("train_size", "mean_score", "lower", "upper", "interval_kind"),
    "cross_validation": ("fold", "score"),
    "model_interval": ("center", "lower", "upper", "interval_kind"),
    "robustness_envelope": ("x", "center", "lower", "upper", "interval_kind"),
    "tornado": ("parameters", "low", "high"),
    "response_surface_opt": ("x_grid", "y_grid", "z"),
    "feasible_region": ("x_grid", "y_grid", "z"),
    "parameter_response": ("x_grid", "y_grid", "z"),
    "embedding": ("embedding",), "pca_scores": ("scores",), "pca_biplot": ("scores", "loadings", "explained_variance"),
    "pca_loadings": ("loadings",), "scree_plot": ("explained_variance",), "tsne": ("embedding",), "umap": ("embedding",), "network": ("nodes", "edges"),
    "dependency_graph": ("edges",), "flowchart": ("nodes", "edges"),
    "state_machine": ("nodes", "edges"), "state_transition": ("nodes", "edges"),
    "adjacency": ("nodes", "edges"),
    "radar": ("metrics", "values"), "ridgeline": ("groups",),
    "correlation_bubble": ("data",),
    "correlation_network": ("nodes", "edges"), "weighted_network": ("nodes", "edges", "weights"),
    "community_network": ("nodes", "edges", "community"), "chord": ("nodes", "flows"),
    "embedding_trajectory": ("embedding", "time"), "cluster_scatter": ("embedding", "groups"),
    "sankey": ("source", "target", "value"), "alluvial": ("source", "target", "value", "source_stage", "target_stage"),
    "spatial_scatter": ("longitude", "latitude", "size", "group"),
    "error_band": ("time", "center", "lower", "upper", "interval_kind"),
    "calibration_curve": ("probability", "observed_rate"),
    "mantel": ("matrix", "env_matrix"), "pairgrid": ("data",),
}
for _name, _required in _REQUIRED_FIELDS.items():
    if _name in _REGISTRY:
        old = _REGISTRY[_name]
        _REGISTRY[_name] = FigureSpec(name=old.name, category=old.category, question=old.question,
                                      required_fields=tuple(_required), independent_unit=old.independent_unit,
                                      status=old.status, implementation_level=old.implementation_level,
                                      paper_suitable=old.paper_suitable, simulate=old.simulate,
                                      qa_status=old.qa_status, factory=old.factory)

# Compatibility aliases are explicit and never count as independent chart
# implementations.  The rest of the catalog remains available as adapters or
# templates until it receives a dedicated statistical implementation.
_ALIAS_OF = {"multi_metric_points": "multi_metric_comparison"}
_TEMPLATE_NAMES = {"geometry", "coordinate_system", "mechanism", "technical_route",
                   "task_decomposition", "algorithm_flow", "input_model_validation_output"}
_PRIORITY_DEDICATED = {
    "bar", "grouped_bar", "stacked_bar", "forest", "errorbar", "scatter", "scatter_trend", "bubble",
    "joint_density", "hexbin", "volcano", "heatmap", "correlation_matrix", "confusion_matrix", "transition_matrix",
    "roc_curve", "pr_curve", "calibration_curve", "residuals", "learning_curve", "pca_biplot", "pca_loadings",
    "scree_plot", "tsne", "umap", "response_surface", "sensitivity", "pareto", "tornado", "robustness_envelope",
    "correlation_network", "community_network", "weighted_network", "sankey", "spatial_scatter",
}
for _name, _spec in list(_REGISTRY.items()):
    if _name in _ALIAS_OF:
        level, status = "alias", f"alias of {_ALIAS_OF[_name]}"
    elif _name in _TEMPLATE_NAMES:
        level, status = "template", "layout template; validate semantics before paper use"
    elif _name == "mantel":
        level, status = "adapter", "Pearson linkage preview; Mantel distance/permutation test pending"
    elif _name in _PRIORITY_DEDICATED or _spec.implementation_level == "dedicated":
        level, status = "dedicated", "dedicated statistical renderer; visual QA pending"
    else:
        level, status = "adapter", "academic adapter; validate input before paper use"
    _REGISTRY[_name] = FigureSpec(name=_spec.name, category=_spec.category, question=_spec.question,
                                  required_fields=_spec.required_fields, independent_unit=_spec.independent_unit,
                                  status=status, implementation_level=level, paper_suitable=False,
                                  simulate=_spec.simulate, qa_status="not_checked", factory=_spec.factory)

for _alias, _target in _ALIAS_OF.items():
    _REGISTRY[_alias] = replace(_REGISTRY[_alias], required_fields=_REGISTRY[_target].required_fields,
                                factory=_REGISTRY[_target].factory)


def _validate_legacy_data(name: str, data: dict[str, Any], spec: FigureSpec) -> None:
    """Validate required fields and high-risk shape semantics before drawing."""
    missing = [field for field in spec.required_fields if field not in data]
    if missing:
        raise ValueError(f"{name} requires fields: {', '.join(missing)}")
    def arr(field, ndim=None):
        value = np.asarray(data[field])
        if value.size == 0:
            raise ValueError(f"{name}.{field} must be non-empty")
        if field not in {"group", "community"}:
            try:
                numeric = value.astype(float)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{name}.{field} must be numeric") from exc
            if not np.isfinite(numeric).all():
                raise ValueError(f"{name}.{field} must be finite")
        if ndim is not None and value.ndim != ndim:
            raise ValueError(f"{name}.{field} must be {ndim}D")
        return value
    if name == "percent_stacked_bar_line":
        validate_percent_stacked_bar_line(data["categories"], data["values"], data["groups"], data["line_values"])
    elif name in {"bar", "grouped_bar", "stacked_bar", "horizontal_bar", "dot_plot"}:
        values = arr("values")
        if values.ndim not in {1, 2} or values.shape[0] != len(data["categories"]):
            raise ValueError(f"{name}.values must align with categories")
        if name in {"grouped_bar", "stacked_bar"} and values.ndim != 2:
            raise ValueError(f"{name}.values must be a 2D category-by-group array")
        if name in {"grouped_bar", "stacked_bar"} and len(data["groups"]) != values.shape[1]:
            raise ValueError(f"{name}.groups must align with values columns")
    elif name in {"forest", "errorbar"}:
        est = arr("estimate" if "estimate" in data else "values")
        lower, upper = arr("lower"), arr("upper")
        if not (est.shape == lower.shape == upper.shape == np.asarray(data["categories"]).shape):
            raise ValueError(f"{name} interval fields must align with categories")
        if np.any(lower > est) or np.any(est > upper): raise ValueError(f"{name} requires lower <= estimate <= upper")
        if not str(data["interval_kind"]).strip(): raise ValueError(f"{name}.interval_kind cannot be empty")
    elif name in {"scatter", "scatter_trend", "bubble"}:
        x, y = arr("x"), arr("y")
        if x.ndim != 1 or y.ndim != 1 or x.shape != y.shape: raise ValueError(f"{name}.x and y must align")
        if name == "bubble" and arr("size").shape != x.shape: raise ValueError("bubble.size must align with x and y")
    elif name in {"heatmap", "confusion_matrix", "transition_matrix"}:
        matrix = arr("matrix", 2)
        if matrix.shape[0] < 2 or matrix.shape[1] < 2: raise ValueError(f"{name}.matrix must be at least 2x2")
    elif name == "response_surface":
        x, y, z = arr("x_grid"), arr("y_grid"), arr("z", 2)
        if z.shape != (y.size, x.size): raise ValueError("response_surface.z must have shape (len(y_grid), len(x_grid))")
    elif name in {"response_surface_opt", "feasible_region", "parameter_response"}:
        x, y, z = arr("x_grid"), arr("y_grid"), arr("z", 2)
        if z.shape != (y.size, x.size): raise ValueError(f"{name}.z must have shape (len(y_grid), len(x_grid))")
    elif name in {"roc_curve", "pr_curve"}:
        truth, score = arr("y_true"), arr("y_score")
        if truth.ndim != 1 or truth.shape != score.shape or set(np.unique(truth)) != {0, 1}: raise ValueError(f"{name} needs aligned binary y_true and y_score with classes 0 and 1")
    elif name == "calibration_curve":
        p, o = arr("probability"), arr("observed_rate")
        if p.shape != o.shape or np.any((p < 0) | (p > 1)) or np.any((o < 0) | (o > 1)): raise ValueError("calibration probabilities and observed rates must align in [0,1]")
    elif name in {"time_series", "error_band"}:
        t = arr("time"); center = arr("center" if name == "error_band" else "values")
        if t.shape != center.shape: raise ValueError(f"{name}.time and values must align")
        if name == "error_band":
            lo, hi = arr("lower"), arr("upper")
            if not (lo.shape == hi.shape == center.shape) or np.any(lo > hi): raise ValueError("error_band interval fields must align and satisfy lower <= upper")
            if not str(data["interval_kind"]).strip(): raise ValueError("error_band.interval_kind cannot be empty")
    elif name in {"network", "correlation_network", "weighted_network", "community_network"}:
        edges = list(data["edges"]); nodes = list(data["nodes"])
        if not edges: raise ValueError(f"{name}.edges cannot be empty")
        if any(len(e) < 2 or e[0] not in nodes or e[1] not in nodes for e in edges): raise ValueError(f"{name}.edges must reference nodes")
        if name == "weighted_network" and len(data["weights"]) != len(edges): raise ValueError("weighted_network.weights must align with edges")
        if name == "community_network":
            community = np.asarray(data["community"], dtype=object)
            if community.ndim != 1 or len(community) != len(nodes) or any(v is None or not str(v).strip() for v in community):
                raise ValueError("community_network.community must contain non-empty labels aligned with nodes")
    elif name in {"sankey", "alluvial"}:
        fields = [list(data[k]) for k in ("source", "target", "value")]
        if not (len(fields[0]) == len(fields[1]) == len(fields[2]) and fields[0]): raise ValueError(f"{name} source, target, value must have equal non-zero lengths")
        value = arr("value", 1)
        if np.any(value < 0): raise ValueError(f"{name}.value cannot be negative")
    elif name == "spatial_scatter":
        for field in ("longitude", "latitude", "size", "group"): arr(field)
        sizes = [np.asarray(data[field]).shape for field in ("longitude", "latitude", "size", "group")]
        if len(set(sizes)) != 1: raise ValueError("spatial_scatter coordinates, size, group must align")
    elif name == "pca_biplot":
        scores, loadings = arr("scores", 2), arr("loadings", 2); ev = arr("explained_variance")
        if scores.shape[1] < 2 or loadings.shape[1] < 2 or ev.size < 2: raise ValueError("pca_biplot needs 2D scores/loadings and explained_variance")
        if ev.ndim != 1 or scores.shape[1] != loadings.shape[1] or ev.size < scores.shape[1] or np.any(ev < 0) or ev.sum() > 1.00001:
            raise ValueError("pca_biplot scores/loadings dimensions and explained_variance ratios must agree")
    elif name == "learning_curve":
        arrays = [arr(field) for field in ("train_size", "mean_score", "lower", "upper")]
        if len({a.shape for a in arrays}) != 1 or np.any(arrays[2] > arrays[3]):
            raise ValueError("learning_curve fields must align and satisfy lower <= upper")
        if not str(data["interval_kind"]).strip(): raise ValueError("learning_curve.interval_kind cannot be empty")
    elif name == "cross_validation":
        fold, score = arr("fold"), arr("score")
        if fold.shape != score.shape: raise ValueError("cross_validation.fold and score must align")
    elif name == "model_interval":
        center, lower, upper = [arr(field) for field in ("center", "lower", "upper")]
        if len({a.shape for a in (center, lower, upper)}) != 1 or np.any(lower > upper):
            raise ValueError("model_interval fields must align and satisfy lower <= upper")
        if not str(data["interval_kind"]).strip(): raise ValueError("model_interval.interval_kind cannot be empty")
    elif name == "robustness_envelope":
        x, center, lower, upper = [arr(field) for field in ("x", "center", "lower", "upper")]
        if len({a.shape for a in (x, center, lower, upper)}) != 1 or np.any(lower > upper):
            raise ValueError("robustness_envelope fields must align and satisfy lower <= upper")
        if not str(data["interval_kind"]).strip(): raise ValueError("robustness_envelope.interval_kind cannot be empty")
    elif name == "tornado":
        labels, low, high = np.asarray(data["parameters"]), arr("low"), arr("high")
        if labels.ndim != 1 or labels.shape != low.shape or low.shape != high.shape or np.any(low > high):
            raise ValueError("tornado parameters, low and high must align and satisfy low <= high")


from .specialized import FIELDS as _STRUCTURED_FIELDS, factory as _structured_factory, validate as _structured_validate
from .practical import FIELDS as _PRACTICAL_FIELDS, NAMES as _PRACTICAL_NAMES, factory as _practical_factory, validate as _practical_validate

_ALIAS_OF = {
    "multi_metric_points": "multi_metric_comparison",
    "confusion_matrix_eval": "confusion_matrix",
    "clustered_heatmap_matrix": "clustered_heatmap",
    "indicator_correlation": "correlation_matrix",
    "scheme_indicator_matrix": "heatmap",
}
for _name, _fields in _STRUCTURED_FIELDS.items():
    if _name in _REGISTRY:
        _REGISTRY[_name] = replace(_REGISTRY[_name], required_fields=_fields,
            factory=_structured_factory(_name, display_name(_name)), implementation_level="dedicated",
            status="dedicated semantic renderer; visual QA pending", paper_suitable=False)
for _alias, _target in _ALIAS_OF.items():
    _REGISTRY[_alias] = replace(_REGISTRY[_alias], required_fields=_REGISTRY[_target].required_fields,
        factory=_REGISTRY[_target].factory, implementation_level="alias", status=f"alias of {_target}")
if 'line' in _REGISTRY:
    _REGISTRY['line'] = replace(_REGISTRY['line'], required_fields=('time', 'values'))
_REGISTRY['waterfall'] = replace(_REGISTRY['waterfall'], required_fields=('values', 'labels'))

FIGURE_NAMES_ZH.update(_PRACTICAL_NAMES)
_ALIASES_ZH.update({label: key for key, label in _PRACTICAL_NAMES.items()})
for _name, _fields in _PRACTICAL_FIELDS.items():
    _REGISTRY[_name] = FigureSpec(
        _name, "实用矩阵、日历与组成", f"saved-result comparison: {_name}", _fields,
        implementation_level="dedicated", status="dedicated semantic renderer; visual QA pending",
        factory=_practical_factory(_name),
    )


def _validate_data(name, data, spec):
    if name in _PRACTICAL_FIELDS:
        _practical_validate(name, data)
    elif name in _STRUCTURED_FIELDS:
        _structured_validate(name, data)
    else:
        _validate_legacy_data(name, data, spec)
    for field in ("lower", "upper"):
        if field in data:
            interval = data.get("interval_kind")
            if not interval or not str(interval).strip():
                raise ValueError(f"{name}.interval_kind required with bounds")


def list_figures(*, category: str | None = None, detailed: bool = False,
                 chinese: bool = False):
    """List registered figures.

    ``name`` stays the stable English identifier by default.  Set
    ``chinese=True`` when a catalog or script needs the concrete Chinese
    chart names.  ``detailed=True`` always includes both identifiers.
    """
    specs = [s for s in _REGISTRY.values() if category is None or s.category == category]
    specs = sorted(specs, key=lambda s: s.name)
    if detailed:
        return [s.to_dict() for s in specs]
    return [display_name(s.name) if chinese else s.name for s in specs]


def get_figure(name: str):
    name = _resolve_name(name)
    try:
        spec = _REGISTRY[name]
        factory = spec.factory
        if factory is None:
            raise KeyError(name)
        # The public entry point accepts either normal positional arguments or
        # a mapping that follows the fields documented by the registry.  This
        # keeps new and legacy functions composable without hiding validation.
        def figure(*args, **kwargs):
            mode = kwargs.pop("mode", "formal")
            config = kwargs.pop("config", None)
            style_fields = ("width_mm", "height_mm", "theme", "minimum_text_pt", "text_pt", "tick_pt", "legend_pt", "title_pt", "panel_pt", "line_width", "marker_size", "semantic_styles", "grid", "background", "latin_font", "chinese_font", "categorical_colors", "maximum_height_mm", "dpi", "color", "cmap")
            style_overrides = {("primary_color" if key == "color" else key): kwargs.pop(key) for key in style_fields if key in kwargs}
            from ..figure_config import load_figure_config
            cfg = load_figure_config(config, **style_overrides)
            cfg["explicit_style_fields"] = sorted(style_overrides)
            if mode not in {"formal", "preview"}:
                raise ValueError("mode must be 'formal' or 'preview'")
            canonical = _ALIAS_OF.get(name, name)
            canonical_spec = _REGISTRY[canonical]
            data = kwargs.pop("data", None)
            if data is not None:
                if args or not isinstance(data, dict):
                    raise TypeError("data= mapping cannot be combined with positional arguments")
                overlap = set(data) & set(kwargs)
                if overlap:
                    raise ValueError(f"duplicate data/keyword fields: {sorted(overlap)}")
                kwargs = {**data, **kwargs}
            elif args:
                if len(args) == 1 and isinstance(args[0], dict):
                    overlap = set(args[0]) & set(kwargs)
                    if overlap: raise ValueError(f"duplicate fields: {sorted(overlap)}")
                    kwargs = {**args[0], **kwargs}
                else:
                    fields = getattr(factory, "positional_fields", None)
                    if fields is None:
                        fields = [p.name for p in inspect.signature(factory).parameters.values()
                                  if p.kind in {p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD}]
                    if len(args) > len(fields): raise ValueError(f"{name} accepts positional fields {fields}")
                    for field, value in zip(fields, args):
                        if field in kwargs: raise ValueError(f"duplicate field: {field}")
                        kwargs[field] = value
            if isinstance(kwargs.get('contract'), dict):
                from .contracts import DataContract
                try:
                    kwargs['contract'] = DataContract(**kwargs['contract'])
                except TypeError as exc:
                    raise ValueError('invalid serialized DataContract: '+str(exc)) from exc
            is_simulated = bool(kwargs.get("simulated", False) or getattr(kwargs.get("contract"), "simulated", False))
            if mode == "preview" and not is_simulated:
                raise ValueError("preview requires simulated=True or a simulated DataContract")
            if mode == "formal" and canonical_spec.implementation_level != "dedicated":
                raise ValueError(f"{name} has no dedicated formal route")
            if canonical == 'forest' and 'values' in kwargs and 'estimate' not in kwargs:
                kwargs['estimate'] = kwargs.pop('values')
            if canonical == 'scatter_trend':
                if args: kwargs.setdefault('trend', True)
                if 'trend' in kwargs and kwargs['trend'] is not True: raise ValueError('scatter_trend requires regression; use scatter without trend')
            try:
                _validate_data(canonical, kwargs, canonical_spec)
            except (TypeError, IndexError, OverflowError) as exc:
                raise ValueError(f'{name} invalid structured data: {exc}') from exc
            kwargs["mode"] = mode
            # The public API also works outside a builder's rc_context.
            import matplotlib as mpl
            from ..sci_figures import publication_rc_params
            from .styles import rendering_style, finish
            explicit_height = cfg["explicit_height"]
            with rendering_style(cfg, canonical, kwargs, explicit_height=explicit_height), mpl.rc_context(publication_rc_params(language='zh', config=cfg)):
                fig = factory(**kwargs)
                finish(fig, cfg)
            cfg = {**cfg, "height_mm": float(fig.get_figheight()*25.4)}
            fig._figure_config = cfg
            for label in ('xlabel', 'ylabel', 'zlabel'):
                if label in kwargs and hasattr(fig.axes[0], 'set_'+label): getattr(fig.axes[0], 'set_'+label)(kwargs[label])
            if hasattr(fig, "_figure_metadata"):
                fig._figure_metadata["name"] = name
                fig._figure_metadata["canonical_key"] = canonical
                fig._figure_metadata['input_data'] = metadata_value({field: kwargs[field] for field in canonical_spec.required_fields})
                if 'calculation' in kwargs: fig._figure_metadata['calculation'] = metadata_value(kwargs['calculation'])
                fig._figure_metadata["name_zh"] = display_name(name)
                fig._figure_metadata["mode"] = mode
                fig._figure_metadata["implementation_level"] = spec.implementation_level
                fig._figure_metadata["paper_suitable"] = False
                fig._figure_metadata["source"] = fig._figure_metadata.get("data_contract", {}).get("source")
                fig._figure_metadata["simulated"] = is_simulated
                provenance = fig._figure_metadata.get("data_contract", {})
                interval = fig._figure_metadata.get("interval_kind", provenance.get("interval_kind"))
                provenance["interval_kind"] = interval
                for field in ("independent_unit", "units"):
                    fig._figure_metadata[field] = provenance.get(field)
                fig._figure_metadata["interval_kind"] = interval
            return fig
        figure.__name__ = getattr(factory, "__name__", name)
        figure.__doc__ = getattr(factory, "__doc__", None)
        return figure
    except KeyError as exc: raise KeyError(f"unknown figure {name!r}; use list_figures()") from exc


def get_spec(name: str) -> FigureSpec:
    name = _resolve_name(name)
    try: return _REGISTRY[name]
    except KeyError as exc: raise KeyError(f"unknown figure {name!r}; use list_figures()") from exc

