# 图表库修复与扩展计划

本次盘点建立模块化 `algorithms.figures` 注册表，保留旧 API，并把统计含义、数据来源和导出状态写入元数据。已有未提交修改未被覆盖。

## 执行计划

1. 以 `DataContract` 记录字段、单位、独立分析单位、区间和变换。
2. 以 `registry.py` 提供 `get_figure`/`list_figures`，类别模块提供可复用入口。
3. 旧类继续从 `algorithms.sci_figures` 导出；ChordDiagram 与 CvRocCurve 增加语义保护。
4. 画廊中的合成示例只验证模板和导出，不代表真实研究结果。
5. 所有投稿级判断保留给人工查看 PDF/SVG、物理尺寸和灰度校样。

## 已有实现盘点

| API | 解决的问题 | 文件 | 状态 | 修复/限制 |
|---|---|---|---|---|
| TaylorDiagram | Taylor diagram | 模型误差、相关性和标准差的联合比较 | code/algorithms/sci_figures.py | 已实现但存在缺陷 | 需确认参考标准差与相关定义 |
| PairedRaincloud | Paired raincloud | 配对条件下的分布和个体变化 | code/algorithms/sci_figures.py | 已实现但存在缺陷 | 必须提供配对 ID 和独立分析单位 |
| CvRocCurve | ROC/PR curve | 二分类排序性能 | code/algorithms/sci_figures.py | 已实现且可复用 | simulate=True 仅演示；真实模式需标签和分数 |
| CorrelationPairgrid | Correlation pairgrid | 变量分布、相关和趋势 | code/algorithms/sci_figures.py | 已实现但存在缺陷 | 回归线不等于相关检验 |
| PredictionMarginal | Prediction marginal | 预测误差和边缘分布 | code/algorithms/sci_figures.py | 已实现且可复用 | 区间须显式声明 |
| HyperparamSurface | Hyperparameter surface | 参数与目标响应 | code/algorithms/sci_figures.py | 已实现且可复用 | 确定性扫描不作置信区间 |
| CorrSplitViolin | Correlation split violin | 组间分布与相关 | code/algorithms/sci_figures.py | 已实现但存在缺陷 | 训练/测试不自动解释为重复测量 |
| CircularHeatmap | Circular heatmap | 周期/分组强度矩阵 | code/algorithms/sci_figures.py | 已实现且可复用 | 需要固定色域和单位 |
| ComboComparison | Combo comparison | 类别计数与指标比较 | code/algorithms/sci_figures.py | 已实现但存在缺陷 | 误差类型和原始点须显式 |
| ChordDiagram | Chord diagram | 流量或关联强度 | code/algorithms/sci_figures.py | 已实现且可复用 | 关系语义不是因果证据 |
| ShapBeeswarm | SHAP beeswarm | 特征贡献分布 | code/algorithms/sci_figures.py | 已实现且可复用 | 须使用真实 SHAP 值 |
| figure_templates | prediction/comparison/optimization/sensitivity/robustness/mechanism | 模型结果和机制证据 | code/algorithms/figure_templates.py | 已实现且可复用 | 模板不补造区间 |
| visualize.py | 热图、灵敏度、时域和柱图 | 当前波浪能案例 | code/visualize.py | 已实现且可复用 | 保留原始模型结果 |
| evaluation.pca | PCA | 降维和载荷 | code/algorithms/evaluation.py | 已实现且可复用 | 不得标作 PHATE |
| diagram.py | 流程图、依赖图、系统图 | 模型机制和依赖关系 | code/algorithms/diagram.py | 已实现且可复用 | 箭头表示声明的依赖关系 |

## 仍需完成或人工复核

- 真实数据入口的领域单位、独立样本定义和区间估计必须由研究者填写。
- 多面板主张、图注和最终印刷效果不能由程序静态检查完全代替。
- PHATE、Mantel、ICE 等需要专用算法/真实模型输出时，注册表只提供名称和输入契约，不冒充算法实现。
- 3D 图、雷达图和和弦图仅在二维表达不足且语义明确时使用。
