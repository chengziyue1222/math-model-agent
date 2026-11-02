# 图表库能力矩阵（由 registry 自动生成）

> 本文件由 `scripts/generate_figure_capability_matrix.py` 生成。请修改注册表后重新生成，不要手工维护表格。

注册项总数：**164**。
注册为专用的入口（独立语义仍须终审）：**159**；别名不计入。
仅要求 values 的注册项：**8**。
paper_suitable=True：**0**。

## 实现等级统计

| implementation_level | 数量 | 含义 |
|---|---:|---|
| dedicated | 159 | 专用图形语义与校验实现 |
| adapter | 0 | 学术视觉适配器，需核对输入语义 |
| alias | 5 | 兼容别名，不计为独立图型 |
| template | 0 | 版式或流程预览模板 |

## 完整目录

| English key | 中文名称 | category | implementation_level | status | required_fields | paper_suitable | qa_status | alias_of | 允许真实论文使用 |
|---|---|---|---|---|---|---:|---|---|---|
| `adjacency` | 邻接关系图 | 网络、流量与空间关系 | `dedicated` | dedicated semantic renderer; visual QA pending | `nodes`, `edges` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `adjacency_matrix` | 邻接矩阵 | 热图与矩阵 | `dedicated` | dedicated semantic renderer; visual QA pending | `matrix`, `row_labels`, `column_labels` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `ahp_weights` | AHP权重图 | 多指标与综合评价 | `dedicated` | dedicated semantic renderer; visual QA pending | `categories`, `values`, `method` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `algorithm_flow` | 算法流程图 | 数学建模专用图 | `dedicated` | dedicated semantic renderer; visual QA pending | `nodes`, `edges`, `node_types`, `edge_labels` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `alluvial` | 冲积图 | 网络、流量与空间关系 | `dedicated` | dedicated statistical renderer; visual QA pending | `source`, `target`, `value`, `source_stage`, `target_stage` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `area` | 面积图 | 时间序列与动态过程 | `dedicated` | dedicated semantic renderer; visual QA pending | `time`, `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `autocorrelation` | 自相关图 | 时间序列与动态过程 | `dedicated` | dedicated semantic renderer; visual QA pending | `lag`, `correlation` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `bar` | 柱状图 | 类别比较 | `dedicated` | dedicated statistical renderer; visual QA pending | `categories`, `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `beeswarm` | 蜂群图 | 单变量与分布 | `dedicated` | dedicated semantic renderer; visual QA pending | `categories`, `samples` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `bland_altman` | Bland-Altman一致性图 | 关系与相关 | `dedicated` | dedicated statistical renderer; visual QA pending | `reference`, `comparison` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `boxplot` | 箱线图 | 单变量与分布 | `dedicated` | dedicated statistical renderer; visual QA pending | `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `bubble` | 气泡图 | 关系与相关 | `dedicated` | dedicated statistical renderer; visual QA pending | `x`, `y`, `size` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `bubble_matrix` | 频次气泡矩阵 | 实用矩阵、日历与组成 | `dedicated` | dedicated semantic renderer; visual QA pending | `row_labels`, `column_labels`, `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `calendar_glyphs` | 日历小图 | 实用矩阵、日历与组成 | `dedicated` | dedicated semantic renderer; visual QA pending | `dates`, `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `calendar_heatmap` | 日历热图 | 实用矩阵、日历与组成 | `dedicated` | dedicated semantic renderer; visual QA pending | `dates`, `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `calibration_curve` | 校准曲线 | 模型评估 | `dedicated` | dedicated semantic renderer; visual QA pending | `probability`, `observed_rate` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `chord` | 弦图 | 网络、流量与空间关系 | `dedicated` | dedicated statistical renderer; visual QA pending | `nodes`, `flows` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `circular_heatmap` | 环形热图 | 热图与矩阵 | `dedicated` | dedicated semantic renderer; visual QA pending | `matrix`, `row_labels`, `column_labels` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `cleveland_dot` | 克利夫兰点图 | 类别比较 | `dedicated` | dedicated semantic renderer; visual QA pending | `categories`, `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `cluster_scatter` | 聚类散点图 | 降维、聚类与高维结构 | `dedicated` | dedicated statistical renderer; visual QA pending | `embedding`, `groups` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `cluster_stability` | 聚类稳定性图 | 降维、聚类与高维结构 | `dedicated` | dedicated semantic renderer; visual QA pending | `settings`, `scores`, `runs`, `metric` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `clustered_heatmap` | 聚类热图 | 关系与相关 | `dedicated` | dedicated semantic renderer; visual QA pending | `matrix`, `row_labels`, `column_labels`, `row_linkage`, `column_linkage` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `clustered_heatmap_matrix` | 聚类矩阵热图 | 热图与矩阵 | `alias` | alias of clustered_heatmap | `matrix`, `row_labels`, `column_labels`, `row_linkage`, `column_linkage` | false | not_checked | clustered_heatmap | 否（需完成数据和视觉复核） |
| `community_network` | 社区网络图 | 网络、流量与空间关系 | `dedicated` | dedicated statistical renderer; visual QA pending | `nodes`, `edges`, `community` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `confusion_matrix` | 混淆矩阵 | 热图与矩阵 | `dedicated` | dedicated statistical renderer; visual QA pending | `matrix` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `confusion_matrix_eval` | 模型混淆矩阵 | 模型评估 | `alias` | alias of confusion_matrix | `matrix` | false | not_checked | confusion_matrix | 否（需完成数据和视觉复核） |
| `constraint_boundary` | 约束边界图 | 数学建模专用图 | `dedicated` | dedicated semantic renderer; visual QA pending | `x_grid`, `y_grid`, `constraint`, `limit` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `constraint_slack` | 约束松弛图 | 优化、灵敏度与稳健性 | `dedicated` | dedicated semantic renderer; visual QA pending | `constraints`, `slack` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `contour` | 空间等高线图 | 网络、流量与空间关系 | `dedicated` | dedicated semantic renderer; visual QA pending | `x_grid`, `y_grid`, `z` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `contour_density` | 等高线密度图 | 关系与相关 | `dedicated` | dedicated semantic renderer; visual QA pending | `x`, `y` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `contribution_decomposition` | 贡献分解图 | 多指标与综合评价 | `dedicated` | dedicated semantic renderer; visual QA pending | `components`, `values`, `baseline` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `control_chart` | 控制图 | 单变量与分布 | `dedicated` | dedicated semantic renderer; visual QA pending | `time`, `values`, `center`, `lower`, `upper`, `interval_kind` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `convergence` | 收敛曲线 | 优化、灵敏度与稳健性 | `dedicated` | dedicated statistical renderer; visual QA pending | `iterations`, `objective` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `coordinate_system` | 坐标系图 | 数学建模专用图 | `dedicated` | dedicated semantic renderer; visual QA pending | `origin`, `basis` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `correlation_bubble` | 相关气泡图 | 关系与相关 | `dedicated` | dedicated statistical renderer; visual QA pending | `data` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `correlation_heatmap` | 相关热图 | 实用矩阵、日历与组成 | `dedicated` | dedicated semantic renderer; visual QA pending | `matrix`, `labels` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `correlation_matrix` | 相关矩阵 | 关系与相关 | `dedicated` | dedicated statistical renderer; visual QA pending | `data` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `correlation_network` | 相关网络图 | 网络、流量与空间关系 | `dedicated` | dedicated statistical renderer; visual QA pending | `nodes`, `edges` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `covariance_heatmap` | 协方差热图 | 实用矩阵、日历与组成 | `dedicated` | dedicated semantic renderer; visual QA pending | `matrix`, `labels`, `variable_units` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `coverage` | 覆盖率图 | 模型评估 | `dedicated` | dedicated semantic renderer; visual QA pending | `nominal`, `empirical` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `cross_validation` | 交叉验证图 | 模型评估 | `dedicated` | dedicated semantic renderer; visual QA pending | `fold`, `score` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `decision_tree` | 决策树图 | 数学建模专用图 | `dedicated` | dedicated semantic renderer; visual QA pending | `nodes`, `edges`, `edge_labels` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `decomposition` | 时间序列分解图 | 时间序列与动态过程 | `dedicated` | dedicated semantic renderer; visual QA pending | `time`, `values`, `trend`, `seasonal`, `residual`, `period` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `dendrogram` | 树状图 | 降维、聚类与高维结构 | `dedicated` | dedicated semantic renderer; visual QA pending | `linkage`, `labels` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `dependency_graph` | 依赖关系图 | 网络、流量与空间关系 | `dedicated` | dedicated semantic renderer; visual QA pending | `nodes`, `edges` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `diverging_bar` | 发散条形图 | 类别比较 | `dedicated` | dedicated semantic renderer; visual QA pending | `categories`, `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `diverging_heatmap` | 发散色热图 | 热图与矩阵 | `dedicated` | dedicated semantic renderer; visual QA pending | `matrix`, `row_labels`, `column_labels` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `dot_plot` | 点图 | 类别比较 | `dedicated` | dedicated statistical renderer; visual QA pending | `categories`, `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `ecdf` | 经验累积分布图 | 单变量与分布 | `dedicated` | dedicated statistical renderer; visual QA pending | `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `effect_size` | 效应量图 | 类别比较 | `dedicated` | dedicated semantic renderer; visual QA pending | `categories`, `estimate`, `lower`, `upper`, `interval_kind`, `effect_kind` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `embedding_trajectory` | 嵌入轨迹图 | 降维、聚类与高维结构 | `dedicated` | dedicated statistical renderer; visual QA pending | `embedding`, `time` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `error_band` | 误差带图 | 时间序列与动态过程 | `dedicated` | dedicated statistical renderer; visual QA pending | `time`, `center`, `lower`, `upper`, `interval_kind` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `error_by_time` | 随时间误差图 | 模型评估 | `dedicated` | dedicated semantic renderer; visual QA pending | `time`, `observed`, `predicted` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `errorbar` | 误差棒图 | 类别比较 | `dedicated` | dedicated statistical renderer; visual QA pending | `categories`, `values`, `lower`, `upper`, `interval_kind` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `event_timeline` | 事件时间线 | 时间序列与动态过程 | `dedicated` | dedicated semantic renderer; visual QA pending | `time`, `events` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `faceted_heatmap` | 分面热图 | 热图与矩阵 | `dedicated` | dedicated semantic renderer; visual QA pending | `matrices`, `facets`, `row_labels`, `column_labels` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `feasible_heatmap` | 可行域热图 | 热图与矩阵 | `dedicated` | dedicated semantic renderer; visual QA pending | `x_grid`, `y_grid`, `feasible` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `feasible_region` | 可行域图 | 优化、灵敏度与稳健性 | `dedicated` | dedicated semantic renderer; visual QA pending | `x_grid`, `y_grid`, `feasible` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `feature_importance` | 特征重要性图 | 模型评估 | `dedicated` | dedicated semantic renderer; visual QA pending | `categories`, `values`, `method` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `flowchart` | 流程图 | 网络、流量与空间关系 | `dedicated` | dedicated semantic renderer; visual QA pending | `nodes`, `edges` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `forecast_interval` | 预测区间图 | 时间序列与动态过程 | `dedicated` | dedicated statistical renderer; visual QA pending | `time`, `observed`, `predicted`, `lower`, `upper`, `interval_kind` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `forest` | 森林图 | 类别比较 | `dedicated` | dedicated statistical renderer; visual QA pending | `categories`, `estimate`, `lower`, `upper`, `interval_kind` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `gantt` | 甘特图 | 时间序列与动态过程 | `dedicated` | dedicated semantic renderer; visual QA pending | `tasks`, `start`, `end` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `geometry` | 几何结构图 | 数学建模专用图 | `dedicated` | dedicated semantic renderer; visual QA pending | `points`, `segments`, `polygons` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `global_local` | 全局-局部敏感性图 | 优化、灵敏度与稳健性 | `dedicated` | dedicated semantic renderer; visual QA pending | `parameters`, `local`, `global_values`, `method` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `grouped_bar` | 分组柱状图 | 类别比较 | `dedicated` | dedicated statistical renderer; visual QA pending | `categories`, `values`, `groups` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `heatmap` | 热图 | 热图与矩阵 | `dedicated` | dedicated statistical renderer; visual QA pending | `matrix` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `hexbin` | 六边形分箱图 | 关系与相关 | `dedicated` | dedicated semantic renderer; visual QA pending | `x`, `y` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `high_dim_density` | 高维密度图 | 降维、聚类与高维结构 | `dedicated` | dedicated semantic renderer; visual QA pending | `data`, `features` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `histogram` | 直方图 | 单变量与分布 | `dedicated` | dedicated statistical renderer; visual QA pending | `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `horizontal_bar` | 横向柱状图 | 类别比较 | `dedicated` | dedicated statistical renderer; visual QA pending | `categories`, `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `ice` | 个体条件期望图 | 模型评估 | `dedicated` | dedicated semantic renderer; visual QA pending | `grid`, `curves`, `feature_name` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `indicator_correlation` | 指标相关图 | 多指标与综合评价 | `alias` | alias of correlation_matrix | `data` | false | not_checked | correlation_matrix | 否（需完成数据和视觉复核） |
| `input_model_validation_output` | 输入-模型-验证-输出图 | 数学建模专用图 | `dedicated` | dedicated semantic renderer; visual QA pending | `nodes`, `edges`, `stages` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `jitter` | 抖动散点图 | 单变量与分布 | `dedicated` | dedicated semantic renderer; visual QA pending | `categories`, `samples` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `joint_density` | 联合密度图 | 关系与相关 | `dedicated` | dedicated semantic renderer; visual QA pending | `x`, `y` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `kde` | 核密度图 | 单变量与分布 | `dedicated` | dedicated statistical renderer; visual QA pending | `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `learning_curve` | 学习曲线 | 模型评估 | `dedicated` | dedicated statistical renderer; visual QA pending | `train_size`, `mean_score`, `lower`, `upper`, `interval_kind` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `lift_gain` | 提升-增益曲线 | 模型评估 | `dedicated` | dedicated semantic renderer; visual QA pending | `population_fraction`, `gain`, `lift` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `lollipop` | 棒棒糖图 | 类别比较 | `dedicated` | dedicated semantic renderer; visual QA pending | `categories`, `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `mantel` | Mantel关联图 | 关系与相关 | `dedicated` | dedicated semantic renderer; visual QA pending | `distance_a`, `distance_b`, `r`, `p`, `permutations`, `seed` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `matrix_pie` | 饼图矩阵 | 实用矩阵、日历与组成 | `dedicated` | dedicated semantic renderer; visual QA pending | `row_labels`, `column_labels`, `groups`, `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `mechanism` | 机制示意图 | 数学建模专用图 | `dedicated` | dedicated semantic renderer; visual QA pending | `nodes`, `edges`, `edge_labels` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `model_interval` | 模型区间图 | 模型评估 | `dedicated` | dedicated semantic renderer; visual QA pending | `center`, `lower`, `upper`, `interval_kind` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `multi_metric_comparison` | 多指标比较图 | 类别比较 | `dedicated` | dedicated semantic renderer; visual QA pending | `categories`, `metrics`, `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `multi_metric_points` | 多指标点图 | 多指标与综合评价 | `alias` | alias of multi_metric_comparison | `categories`, `metrics`, `values` | false | not_checked | multi_metric_comparison | 否（需完成数据和视觉复核） |
| `multi_series` | 多序列折线图 | 时间序列与动态过程 | `dedicated` | dedicated semantic renderer; visual QA pending | `time`, `values`, `groups` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `observed_predicted` | 观测值-预测值图 | 时间序列与动态过程 | `dedicated` | dedicated statistical renderer; visual QA pending | `observed`, `predicted` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `optimum_distribution` | 最优值分布图 | 优化、灵敏度与稳健性 | `dedicated` | dedicated semantic renderer; visual QA pending | `runs`, `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `pairgrid` | 成对关系图 | 关系与相关 | `dedicated` | dedicated statistical renderer; visual QA pending | `data` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `parallel_coordinates` | 平行坐标图 | 降维、聚类与高维结构 | `dedicated` | dedicated semantic renderer; visual QA pending | `data`, `features` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `parameter_response` | 参数响应图 | 数学建模专用图 | `dedicated` | dedicated semantic renderer; visual QA pending | `x_grid`, `y_grid`, `z`, `parameters` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `pareto` | 帕累托前沿图 | 优化、灵敏度与稳健性 | `dedicated` | dedicated statistical renderer; visual QA pending | `x`, `y` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `pareto_distribution` | 帕累托分布图 | 单变量与分布 | `dedicated` | dedicated semantic renderer; visual QA pending | `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `partial_autocorrelation` | 偏自相关图 | 时间序列与动态过程 | `dedicated` | dedicated semantic renderer; visual QA pending | `lag`, `correlation` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `partial_correlation` | 偏相关图 | 关系与相关 | `dedicated` | dedicated semantic renderer; visual QA pending | `matrix`, `labels`, `control_labels` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `partial_dependence` | 部分依赖图 | 关系与相关 | `dedicated` | dedicated semantic renderer; visual QA pending | `grid`, `response`, `feature_name` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `pca_biplot` | 主成分双标图 | 降维、聚类与高维结构 | `dedicated` | dedicated statistical renderer; visual QA pending | `scores`, `loadings`, `explained_variance` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `pca_loadings` | 主成分载荷图 | 降维、聚类与高维结构 | `dedicated` | dedicated statistical renderer; visual QA pending | `loadings` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `pca_scores` | 主成分得分图 | 降维、聚类与高维结构 | `dedicated` | dedicated statistical renderer; visual QA pending | `scores` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `percent_stacked_bar` | 百分比堆叠柱状图 | 类别比较 | `dedicated` | dedicated semantic renderer; visual QA pending | `categories`, `values`, `groups` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `percent_stacked_bar_line` | 百分比堆叠柱折线图 | 类别比较 | `dedicated` | dedicated statistical renderer; visual QA pending | `categories`, `values`, `groups`, `line_values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `perturbation` | 扰动分析图 | 优化、灵敏度与稳健性 | `dedicated` | dedicated semantic renderer; visual QA pending | `x`, `response`, `parameter` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `pictogram` | 人物比例图 | 实用矩阵、日历与组成 | `dedicated` | dedicated semantic renderer; visual QA pending | `categories`, `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `polar_stacked_bar` | 极坐标堆叠图 | 实用矩阵、日历与组成 | `dedicated` | dedicated semantic renderer; visual QA pending | `categories`, `groups`, `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `pr_curve` | PR曲线 | 模型评估 | `dedicated` | dedicated statistical renderer; visual QA pending | `y_true`, `y_score` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `probability_plot` | 概率图 | 单变量与分布 | `dedicated` | dedicated semantic renderer; visual QA pending | `theoretical`, `observed`, `distribution` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `qq_plot` | QQ图 | 单变量与分布 | `dedicated` | dedicated statistical renderer; visual QA pending | `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `radar` | 雷达图 | 多指标与综合评价 | `dedicated` | dedicated statistical renderer; visual QA pending | `metrics`, `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `raincloud` | 雨云图 | 单变量与分布 | `dedicated` | dedicated statistical renderer; visual QA pending | `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `ranking` | 排名图 | 多指标与综合评价 | `dedicated` | dedicated semantic renderer; visual QA pending | `categories`, `values`, `direction` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `raw_points` | 原始点图 | 类别比较 | `dedicated` | dedicated semantic renderer; visual QA pending | `categories`, `samples` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `regression_curve` | 拟合曲线图 | 实用矩阵、日历与组成 | `dedicated` | dedicated semantic renderer; visual QA pending | `x`, `y`, `curve_x`, `curve_y` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `repeated_convergence` | 重复收敛曲线 | 优化、灵敏度与稳健性 | `dedicated` | dedicated semantic renderer; visual QA pending | `iterations`, `objectives`, `runs` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `residual_distribution` | 残差分布图 | 模型评估 | `dedicated` | dedicated semantic renderer; visual QA pending | `observed`, `predicted` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `residuals` | 残差图 | 模型评估 | `dedicated` | dedicated statistical renderer; visual QA pending | `observed`, `predicted` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `response_1d` | 一维响应曲线 | 优化、灵敏度与稳健性 | `dedicated` | dedicated semantic renderer; visual QA pending | `x`, `response`, `parameter` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `response_surface` | 响应面图 | 热图与矩阵 | `dedicated` | dedicated statistical renderer; visual QA pending | `x_grid`, `y_grid`, `z` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `response_surface_opt` | 优化响应面图 | 优化、灵敏度与稳健性 | `dedicated` | dedicated semantic renderer; visual QA pending | `x_grid`, `y_grid`, `z`, `direction` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `ridgeline` | 山脊图 | 单变量与分布 | `dedicated` | dedicated statistical renderer; visual QA pending | `groups` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `risk_return` | 风险-收益图 | 优化、灵敏度与稳健性 | `dedicated` | dedicated semantic renderer; visual QA pending | `risk`, `returns`, `labels` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `robustness_envelope` | 稳健性包络图 | 优化、灵敏度与稳健性 | `dedicated` | dedicated statistical renderer; visual QA pending | `x`, `center`, `lower`, `upper`, `interval_kind` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `roc_curve` | ROC曲线 | 模型评估 | `dedicated` | dedicated statistical renderer; visual QA pending | `y_true`, `y_score` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `rolling_mean` | 滚动均值图 | 时间序列与动态过程 | `dedicated` | dedicated semantic renderer; visual QA pending | `time`, `center`, `window` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `sankey` | 桑基图 | 网络、流量与空间关系 | `dedicated` | dedicated statistical renderer; visual QA pending | `source`, `target`, `value` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `scatter` | 散点图 | 关系与相关 | `dedicated` | dedicated statistical renderer; visual QA pending | `x`, `y` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `scatter_trend` | 趋势散点图 | 关系与相关 | `dedicated` | dedicated statistical renderer; visual QA pending | `x`, `y`, `trend` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `scenario` | 情景分析图 | 优化、灵敏度与稳健性 | `dedicated` | dedicated semantic renderer; visual QA pending | `x`, `responses`, `scenarios` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `scenario_ranking` | 情景排序图 | 优化、灵敏度与稳健性 | `dedicated` | dedicated semantic renderer; visual QA pending | `categories`, `values`, `direction` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `scheme_indicator_matrix` | 方案-指标矩阵 | 多指标与综合评价 | `alias` | alias of heatmap | `matrix` | false | not_checked | heatmap | 否（需完成数据和视觉复核） |
| `score_bar` | 综合得分柱状图 | 多指标与综合评价 | `dedicated` | dedicated semantic renderer; visual QA pending | `categories`, `values`, `score_kind` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `scree_plot` | 碎石图 | 降维、聚类与高维结构 | `dedicated` | dedicated statistical renderer; visual QA pending | `explained_variance` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `sensitivity` | 灵敏度曲线 | 优化、灵敏度与稳健性 | `dedicated` | dedicated statistical renderer; visual QA pending | `x`, `response` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `separation_loadings` | 分离载荷图 | 降维、聚类与高维结构 | `dedicated` | dedicated semantic renderer; visual QA pending | `loadings`, `labels`, `components`, `method` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `shap_beeswarm` | SHAP蜂群图 | 模型评估 | `dedicated` | dedicated semantic renderer; visual QA pending | `attributions`, `features`, `feature_names` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `shap_summary` | SHAP汇总图 | 模型评估 | `dedicated` | dedicated semantic renderer; visual QA pending | `attributions`, `feature_names` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `sparkline_matrix` | 矩阵迷你折线图 | 实用矩阵、日历与组成 | `dedicated` | dedicated semantic renderer; visual QA pending | `row_labels`, `column_labels`, `series` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `spatial_3d` | 三维空间图 | 网络、流量与空间关系 | `dedicated` | dedicated semantic renderer; visual QA pending | `x`, `y`, `z` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `spatial_heatmap` | 空间热图 | 网络、流量与空间关系 | `dedicated` | dedicated semantic renderer; visual QA pending | `x_grid`, `y_grid`, `z` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `spatial_scatter` | 空间散点图 | 网络、流量与空间关系 | `dedicated` | dedicated semantic renderer; visual QA pending | `longitude`, `latitude`, `size`, `group` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `stacked_area` | 堆叠面积图 | 时间序列与动态过程 | `dedicated` | dedicated semantic renderer; visual QA pending | `time`, `values`, `groups` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `stacked_bar` | 堆叠柱状图 | 类别比较 | `dedicated` | dedicated statistical renderer; visual QA pending | `categories`, `values`, `groups` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `state_machine` | 状态机图 | 数学建模专用图 | `dedicated` | dedicated semantic renderer; visual QA pending | `nodes`, `edges`, `events` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `state_trajectory` | 状态轨迹图 | 时间序列与动态过程 | `dedicated` | dedicated semantic renderer; visual QA pending | `time`, `states`, `dimensions` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `state_transition` | 状态转移图 | 网络、流量与空间关系 | `dedicated` | dedicated semantic renderer; visual QA pending | `nodes`, `edges`, `probabilities` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `step` | 阶梯图 | 时间序列与动态过程 | `dedicated` | dedicated semantic renderer; visual QA pending | `time`, `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `task_decomposition` | 任务分解图 | 数学建模专用图 | `dedicated` | dedicated semantic renderer; visual QA pending | `nodes`, `edges` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `taylor_diagram` | 泰勒图 | 模型评估 | `dedicated` | dedicated semantic renderer; visual QA pending | `reference_std`, `std`, `correlation`, `labels` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `technical_route` | 技术路线图 | 数学建模专用图 | `dedicated` | dedicated semantic renderer; visual QA pending | `nodes`, `edges`, `stages` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `threshold_crossing` | 阈值穿越图 | 优化、灵敏度与稳健性 | `dedicated` | dedicated semantic renderer; visual QA pending | `time`, `values`, `threshold` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `threshold_heatmap` | 阈值热图 | 热图与矩阵 | `dedicated` | dedicated semantic renderer; visual QA pending | `matrix`, `row_labels`, `column_labels`, `threshold` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `time_heatmap` | 时间热图 | 时间序列与动态过程 | `dedicated` | dedicated semantic renderer; visual QA pending | `time`, `matrix`, `row_labels` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `time_series` | 时间序列图 | 时间序列与动态过程 | `dedicated` | dedicated statistical renderer; visual QA pending | `time`, `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `topsis_weights` | TOPSIS权重图 | 多指标与综合评价 | `dedicated` | dedicated semantic renderer; visual QA pending | `categories`, `values`, `method` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `tornado` | 龙卷风图 | 优化、灵敏度与稳健性 | `dedicated` | dedicated semantic renderer; visual QA pending | `parameters`, `low`, `high` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `transition_matrix` | 转移矩阵 | 热图与矩阵 | `dedicated` | dedicated statistical renderer; visual QA pending | `matrix` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `tsne` | t-SNE图 | 降维、聚类与高维结构 | `dedicated` | dedicated statistical renderer; visual QA pending | `embedding` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `umap` | UMAP图 | 降维、聚类与高维结构 | `dedicated` | dedicated statistical renderer; visual QA pending | `embedding` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `variable_dependency` | 变量依赖图 | 数学建模专用图 | `dedicated` | dedicated semantic renderer; visual QA pending | `nodes`, `edges` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `violin` | 小提琴图 | 单变量与分布 | `dedicated` | dedicated statistical renderer; visual QA pending | `values` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `volcano` | 火山图 | 关系与相关 | `dedicated` | dedicated semantic renderer; visual QA pending | `x`, `y` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `waterfall` | 瀑布图 | 类别比较 | `dedicated` | dedicated statistical renderer; visual QA pending | `values`, `labels` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `weight_sensitivity` | 权重敏感性图 | 多指标与综合评价 | `dedicated` | dedicated semantic renderer; visual QA pending | `weights`, `scores`, `schemes` | false | not_checked | — | 否（需完成数据和视觉复核） |
| `weighted_network` | 加权网络图 | 网络、流量与空间关系 | `dedicated` | dedicated statistical renderer; visual QA pending | `nodes`, `edges`, `weights` | false | not_checked | — | 否（需完成数据和视觉复核） |
