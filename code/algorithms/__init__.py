"""
数学建模算法工具箱
==================
基于 Algorithms_MathModels + ravenxrz/Mathematical-Modeling 仓库转化的 Python 实现

模块列表:
- ahp: AHP 层次分析法
- grey_system: 灰色系统 (GM(1,1), 灰色关联, 灰色聚类等)
- interpolation: 插值方法 (拉格朗日, 牛顿, 样条等)
- regression: 回归分析 (线性, 多项式, 岭, 逐步, 非线性, Logistic)
- graph_theory: 图论 (Dijkstra, Floyd, 最小生成树, 最大流, 关键路径)
- fuzzy_math: 模糊数学 (模糊综合评价, 模糊聚类, 模式识别)
- neural_network: 神经网络 (BP, RBF, SOM, MIV变量重要性)
- metaheuristic: 智能优化 (GA, PSO, SA, ACO, 鱼群)
- cellular_automata: 元胞自动机 (生命游戏, 森林火灾, DLA, SIRS, NaSch交通流)
- diagram: 图表绘制 (流程图, ER图, 系统模块图, 三线表, SQL解析)
- sci_figures: 科研图表 (泰勒图, 云雨图, ROC曲线, SHAP图等 11 种模板)
- evaluation: 综合评价 (TOPSIS, 熵权法, DEA, PCA, RSR, FAHP, 灰色关联)
- paper_check: 论文质量检查与验收
- monte_carlo: 蒙特卡罗算法 (随机模拟, 排队仿真M/M/c, M/M/S/k, 随机游走)
- image_processing: 图像处理 (边缘检测, 图像分割, 形态学, 特征提取)
- time_series: 时间序列分析 (移动平均, 指数平滑, 趋势外推)
- math_programming: 数学规划 (线性规划, 整数规划, 目标规划, 非线性规划)
"""

from .ahp import ahp_weight, consistency_check, hierarchical_ahp
from .grey_system import gm11_predict, grey_correlation, grey_clustering, grey_auto_predict
from .interpolation import lagrange_interp, newton_interp, cubic_spline_interp
from .regression import linear_regression, polynomial_regression, ridge_regression, stepwise_regression, nonlinear_regression, logistic_regression
from .graph_theory import dijkstra, floyd, prim_mst, max_flow, critical_path, min_cost_flow, graph_coloring, euler_path, hungarian_matching
from .fuzzy_math import fuzzy_comprehensive_evaluation, fuzzy_cmeans, multi_level_fuzzy_evaluation
from .neural_network import BPNeuralNetwork, RBFNetwork, SOM, miv_variable_importance
from .metaheuristic import genetic_algorithm, particle_swarm, simulated_annealing, ant_colony_tsp
from .cellular_automata import GameOfLife, ForestFire, ElementaryCA, DLA, SIRSModel, NaSchTraffic
from .diagram import (
    FlowchartLayout, ERDiagramLayout, SystemModuleLayout,
    AcademicTable, SQLParser, save_svg, save_drawio, save_html,
)
from .evaluation import (
    entropy_weight, topsis, ahp_topsis, dea, pca, rsr, fahp,
    grey_relational, combined_weight,
    TOPSISResult, DEAResult, PCAResult, RSRResult,
)
from .paper_check import PaperChecker, check_paper
from .sci_figures import (
    TaylorDiagram, PairedRaincloud, CvRocCurve, CorrelationPairgrid,
    PredictionMarginal, HyperparamSurface, CorrSplitViolin,
    CircularHeatmap, ComboComparison, ChordDiagram, ShapBeeswarm,
    TaylorPoint, RocModelSpec, PredModelPanel, HeatmapTrait, HeatmapGroup,
    ChordNode, save_figure as save_sci_figure,
)
from .monte_carlo import (
    monte_carlo_integration, monte_carlo_pi, monte_carlo_optimization,
    monte_carlo_simulation, queuing_simulation, queuing_mmsk, random_walk, MCResult,
)
from .image_processing import (
    noise_filter, edge_detection, image_segmentation, morphological_ops,
    histogram_analysis, histogram_equalization, feature_extraction,
)
from .time_series import (
    simple_moving_average, weighted_moving_average, trend_moving_average,
    single_exponential_smoothing, double_exponential_smoothing, triple_exponential_smoothing,
    gompertz_curve, logistic_curve, modified_exponential_curve, adaptive_filter,
)
from .math_programming import (
    linear_programming, integer_programming, goal_programming, nonlinear_programming,
)

__all__ = [
    # AHP
    'ahp_weight', 'consistency_check', 'hierarchical_ahp',
    # 灰色系统
    'gm11_predict', 'grey_correlation', 'grey_clustering', 'grey_auto_predict',
    # 插值
    'lagrange_interp', 'newton_interp', 'cubic_spline_interp',
    # 回归
    'linear_regression', 'polynomial_regression', 'ridge_regression',
    'stepwise_regression', 'nonlinear_regression', 'logistic_regression',
    # 图论
    'dijkstra', 'floyd', 'prim_mst', 'max_flow', 'critical_path',
    'min_cost_flow', 'graph_coloring', 'euler_path', 'hungarian_matching',
    # 模糊数学
    'fuzzy_comprehensive_evaluation', 'fuzzy_cmeans', 'multi_level_fuzzy_evaluation',
    # 神经网络
    'BPNeuralNetwork', 'RBFNetwork', 'SOM', 'miv_variable_importance',
    # 智能优化
    'genetic_algorithm', 'particle_swarm', 'simulated_annealing', 'ant_colony_tsp',
    # 元胞自动机
    'GameOfLife', 'ForestFire', 'ElementaryCA', 'DLA', 'SIRSModel', 'NaSchTraffic',
    # 图表绘制
    'FlowchartLayout', 'ERDiagramLayout', 'SystemModuleLayout',
    'AcademicTable', 'SQLParser',
    # 综合评价
    'entropy_weight', 'topsis', 'ahp_topsis', 'dea', 'pca', 'rsr', 'fahp',
    'grey_relational', 'combined_weight',
    'TOPSISResult', 'DEAResult', 'PCAResult', 'RSRResult',
    # 论文检查
    'PaperChecker', 'check_paper',
    # 科研图表
    'TaylorDiagram', 'PairedRaincloud', 'CvRocCurve', 'CorrelationPairgrid',
    'PredictionMarginal', 'HyperparamSurface', 'CorrSplitViolin',
    'CircularHeatmap', 'ComboComparison', 'ChordDiagram', 'ShapBeeswarm',
    'TaylorPoint', 'RocModelSpec', 'PredModelPanel', 'save_sci_figure',
    # 蒙特卡罗
    'monte_carlo_integration', 'monte_carlo_pi', 'monte_carlo_optimization',
    'monte_carlo_simulation', 'queuing_simulation', 'queuing_mmsk', 'random_walk', 'MCResult',
    # 图像处理
    'noise_filter', 'edge_detection', 'image_segmentation', 'morphological_ops',
    'histogram_analysis', 'histogram_equalization', 'feature_extraction',
    # 时间序列
    'simple_moving_average', 'weighted_moving_average', 'trend_moving_average',
    'single_exponential_smoothing', 'double_exponential_smoothing', 'triple_exponential_smoothing',
    'gompertz_curve', 'logistic_curve', 'modified_exponential_curve', 'adaptive_filter',
    # 数学规划
    'linear_programming', 'integer_programming', 'goal_programming', 'nonlinear_programming',
]
