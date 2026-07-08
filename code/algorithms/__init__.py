"""
数学建模算法工具箱
==================

106 个导出函数/类，覆盖数学建模竞赛全流程。
全部基于 numpy/scipy 实现，无深度学习框架依赖。

来源:
- Algorithms_MathModels (HuangCongQing) — MATLAB → Python 转写
- ravenxrz/Mathematical-Modeling — 补充算法
- MathModelAgent (jihe520) — 论文检查、科研图表
- 自研 — 蒙特卡罗、图像处理

使用方式::

    from algorithms import *
    weights, CR = ahp_weight(matrix)
    result = gm11_predict(data, predict_count=5)
"""

# ── 1. 决策与评价 ─────────────────────────────────────────────
from .ahp import ahp_weight, consistency_check, hierarchical_ahp
from .fuzzy_math import fuzzy_comprehensive_evaluation, fuzzy_cmeans, multi_level_fuzzy_evaluation
from .evaluation import (
    entropy_weight, topsis, ahp_topsis, dea, pca, rsr, fahp,
    grey_relational, combined_weight,
    TOPSISResult, DEAResult, PCAResult, RSRResult,
)

# ── 2. 预测与回归 ─────────────────────────────────────────────
from .grey_system import gm11_predict, grey_correlation, grey_clustering, grey_auto_predict
from .regression import (
    linear_regression, polynomial_regression, ridge_regression,
    stepwise_regression, nonlinear_regression, logistic_regression,
)
from .interpolation import lagrange_interp, newton_interp, cubic_spline_interp
from .time_series import (
    simple_moving_average, weighted_moving_average, trend_moving_average,
    single_exponential_smoothing, double_exponential_smoothing, triple_exponential_smoothing,
    gompertz_curve, logistic_curve, modified_exponential_curve, adaptive_filter,
)

# ── 3. 优化与规划 ─────────────────────────────────────────────
from .metaheuristic import genetic_algorithm, particle_swarm, simulated_annealing, ant_colony_tsp
from .math_programming import linear_programming, integer_programming, goal_programming, nonlinear_programming

# ── 4. 图论与网络 ─────────────────────────────────────────────
from .graph_theory import (
    dijkstra, floyd, prim_mst, max_flow, critical_path,
    min_cost_flow, graph_coloring, euler_path, hungarian_matching,
)

# ── 5. 随机模拟 ───────────────────────────────────────────────
from .monte_carlo import (
    monte_carlo_integration, monte_carlo_pi, monte_carlo_optimization,
    monte_carlo_simulation, queuing_simulation, queuing_mmsk, random_walk, MCResult,
)

# ── 6. 机器学习与神经网络 ─────────────────────────────────────
from .neural_network import BPNeuralNetwork, RBFNetwork, SOM, miv_variable_importance

# ── 7. 元胞自动机 ─────────────────────────────────────────────
from .cellular_automata import GameOfLife, ForestFire, ElementaryCA, DLA, SIRSModel, NaSchTraffic

# ── 8. 图像处理 ───────────────────────────────────────────────
from .image_processing import (
    noise_filter, edge_detection, image_segmentation, morphological_ops,
    histogram_analysis, histogram_equalization, feature_extraction,
)

# ── 9. 论文与图表 ─────────────────────────────────────────────
from .paper_check import PaperChecker, check_paper
from .sci_figures import (
    TaylorDiagram, PairedRaincloud, CvRocCurve, CorrelationPairgrid,
    PredictionMarginal, HyperparamSurface, CorrSplitViolin,
    CircularHeatmap, ComboComparison, ChordDiagram, ShapBeeswarm,
    TaylorPoint, RocModelSpec, PredModelPanel, HeatmapTrait, HeatmapGroup,
    ChordNode, save_figure as save_sci_figure,
)
from .diagram import (
    FlowchartLayout, ERDiagramLayout, SystemModuleLayout,
    AcademicTable, SQLParser, save_svg, save_drawio, save_html,
)

# ── 公开接口 ──────────────────────────────────────────────────
__all__ = [
    # ── 决策与评价 (19) ──
    'ahp_weight', 'consistency_check', 'hierarchical_ahp',
    'fuzzy_comprehensive_evaluation', 'fuzzy_cmeans', 'multi_level_fuzzy_evaluation',
    'entropy_weight', 'topsis', 'ahp_topsis', 'dea', 'pca', 'rsr', 'fahp',
    'grey_relational', 'combined_weight',
    'TOPSISResult', 'DEAResult', 'PCAResult', 'RSRResult',

    # ── 预测与回归 (20) ──
    'gm11_predict', 'grey_correlation', 'grey_clustering', 'grey_auto_predict',
    'linear_regression', 'polynomial_regression', 'ridge_regression',
    'stepwise_regression', 'nonlinear_regression', 'logistic_regression',
    'lagrange_interp', 'newton_interp', 'cubic_spline_interp',
    'simple_moving_average', 'weighted_moving_average', 'trend_moving_average',
    'single_exponential_smoothing', 'double_exponential_smoothing', 'triple_exponential_smoothing',
    'gompertz_curve', 'logistic_curve', 'modified_exponential_curve', 'adaptive_filter',

    # ── 优化与规划 (8) ──
    'genetic_algorithm', 'particle_swarm', 'simulated_annealing', 'ant_colony_tsp',
    'linear_programming', 'integer_programming', 'goal_programming', 'nonlinear_programming',

    # ── 图论与网络 (9) ──
    'dijkstra', 'floyd', 'prim_mst', 'max_flow', 'critical_path',
    'min_cost_flow', 'graph_coloring', 'euler_path', 'hungarian_matching',

    # ── 随机模拟 (8) ──
    'monte_carlo_integration', 'monte_carlo_pi', 'monte_carlo_optimization',
    'monte_carlo_simulation', 'queuing_simulation', 'queuing_mmsk', 'random_walk', 'MCResult',

    # ── 机器学习与神经网络 (4) ──
    'BPNeuralNetwork', 'RBFNetwork', 'SOM', 'miv_variable_importance',

    # ── 元胞自动机 (6) ──
    'GameOfLife', 'ForestFire', 'ElementaryCA', 'DLA', 'SIRSModel', 'NaSchTraffic',

    # ── 图像处理 (7) ──
    'noise_filter', 'edge_detection', 'image_segmentation', 'morphological_ops',
    'histogram_analysis', 'histogram_equalization', 'feature_extraction',

    # ── 论文与图表 (25) ──
    'PaperChecker', 'check_paper',
    'TaylorDiagram', 'PairedRaincloud', 'CvRocCurve', 'CorrelationPairgrid',
    'PredictionMarginal', 'HyperparamSurface', 'CorrSplitViolin',
    'CircularHeatmap', 'ComboComparison', 'ChordDiagram', 'ShapBeeswarm',
    'TaylorPoint', 'RocModelSpec', 'PredModelPanel', 'save_sci_figure',
    'FlowchartLayout', 'ERDiagramLayout', 'SystemModuleLayout',
    'AcademicTable', 'SQLParser', 'save_svg', 'save_drawio', 'save_html',
]
