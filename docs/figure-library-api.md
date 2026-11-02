# 图表库 API

## 注册表

```python
from algorithms.figures import get_figure, get_spec, list_figures
figure = get_figure("grouped_bar")
available = list_figures()

# 中文名是同一注册项的真实调用别名，不是网页显示文字。
figure = get_figure("分组柱状图")
assert get_spec("分组柱状图").name == "grouped_bar"
chinese_names = list_figures(chinese=True)
detailed = list_figures(detailed=True)  # name 与 name_zh 同时返回
# 当前目录：155 个入口，150 个专用实现，5 个兼容别名。
volcano = get_figure("火山图")(
    data={"x": effect_size, "y": p_values, "contract": contract}
)
```

## 数据契约

```python
from algorithms.figures import DataContract
contract = DataContract(
    source="data/results.csv",
    fields={"value": "模型输出"},
    units={"value": "W"},
    independent_unit="实验批次",
    interval_kind="95% CI",
    simulated=False,
)
```

每个注册项同时声明 `implementation_level`：`dedicated`（专用图形语义与校验；示意图不宣称统计推断）、`adapter`（学术视觉适配器）、`alias`（兼容别名）或 `template`（版式/流程模板）。`paper_suitable` 只有在相应实现通过程序审计和人工视觉复核后才应为 `True`；当前全量目录保持 `False`，因为 `visual_review` 尚未完成。

高频图型不会再把一维 `values` 当作万能输入。例如：

```python
get_figure("响应面图")(data={"x_grid": x_grid, "y_grid": y_grid, "z": z})
get_figure("加权网络图")(data={"nodes": nodes, "edges": edges, "weights": weights})
get_figure("桑基图")(data={"source": source, "target": target, "value": value})
```

缺字段、维度不匹配、区间 `lower > upper` 或网络边未引用节点时，入口会抛出包含图型和字段名称的 `ValueError`。

## 导出

```python
from algorithms.figures.export import export_publication_figure
paths = export_publication_figure(fig, "output/result", figure_contract)
```

导出同时生成 PDF、SVG、450 DPI RGB PNG 和 `.figure.json`。程序审计通过不等于人工视觉复核通过；查看 `visual_review` 状态。

## 旧 API 兼容

TaylorDiagram、PairedRaincloud、CvRocCurve、CorrelationPairgrid、PredictionMarginal、HyperparamSurface、CorrSplitViolin、CircularHeatmap、ComboComparison、ChordDiagram、ShapBeeswarm 继续从 `algorithms.sci_figures` 导出。

## 正式调用与预览（7.5.0）

全部 155 个入口均接受正确结构化数据正式调用；其中 150 个专用入口和 5 个兼容别名。当前没有注册的占位适配器或占位模板。`get_spec(key).required_fields` 是每个入口的必需字段，能力矩阵列出全部契约。除真正单变量分布图之外，不能以一维 `values` 替代矩阵、坐标、时间或关系。

默认 `mode="formal"`；`mode="preview"` 也经过相同校验，并要求 `DataContract(simulated=True, ...)`。合成预览只表示接口和图面检查，不表示真实统计结论。`data=`、关键字及支持的旧位置参数统一经过校验；不得混用 `data=` 和位置参数。

```python
from algorithms.figures import DataContract, get_figure, get_spec

contract = DataContract(source="data/results.csv", simulated=False,
                        independent_unit="模型方案", units={"values": "分"})
fig = get_figure("ranking")(
    data={"categories": ["方案甲", "方案乙", "方案丙"],
          "values": [78, 91, 91], "direction": "max", "contract": contract},
    mode="formal",
)
assert get_spec("ranking").implementation_level == "dedicated"
```

五个兼容别名：`multi_metric_points → multi_metric_comparison`、`confusion_matrix_eval → confusion_matrix`、`clustered_heatmap_matrix → clustered_heatmap`、`indicator_correlation → correlation_matrix`、`scheme_indicator_matrix → heatmap`。别名继承规范入口的契约，输出同时记录请求名称与 `canonical_key`，不计入独立实现。

专业计算助手位于 `algorithms.figures.compute`，绘图读取其结果及 `calculation` 元数据。可显式计算 PCA、Mantel、Taylor、PDP/ICE、线性模型 SHAP、提升增益、偏相关、时间分解、覆盖率和 AHP。普通绘图不自动训练模型或补造区间。t-SNE/UMAP 绘图接收真实嵌入结果；计算 UMAP 需安装可选 `figures-compute` 依赖，缺少依赖会明确报错。演示用 UMAP 是已保存的真实算法计算结果及原始合成矩阵，不需要运行时安装 UMAP。

排名要求 `categories, values, direction=min|max`；得分柱状图还要求 `score_kind`；空间热图要求 `x_grid, y_grid, z`；空间三维图要求 `x, y, z`。流程图要求 `nodes, edges, edge_labels, node_types`，技术路线还需 `stages`；几何图接收 `points, segments, polygons`。完整字段以 `get_spec()` 为准。

- 学习曲线：train_size、mean_score、lower、upper、interval_kind。
- 交叉验证：fold、score；不推导不存在的折间区间。
- 稳健性包络：x、center、lower、upper、interval_kind。
- 龙卷风图：parameters、low、high。
- 冲积图：source、target、value、source_stage、target_stage，阶段严格递增。
- 桑基图：source、target、value，非负流量，输入图须无环。

能力矩阵必须通过生成脚本更新；安装验证须在清除 PYTHONPATH 的新环境中进行。

## 百分比堆叠柱与数量折线

`percent_stacked_bar_line`（中文调用名：`百分比堆叠柱折线图`）将每个类别的组成归一化到 100%，并用独立的右轴展示数量折线与数值标签。

```python
from algorithms.figures import DataContract, get_figure

fig = get_figure("百分比堆叠柱折线图")(
    data={
        "categories": ["主题1", "主题2", "主题3"],
        "values": [[10, 50, 40], [20, 30, 50], [60, 25, 15]],
        "groups": ["中性", "消极", "积极"],
        "line_values": [1200, 800, 1500],
    },
    contract=DataContract(source="illustrative", simulated=True, independent_unit="示例主题",
                          units={"values": "比例权重", "line_values": "条"}),
    mode="preview",
    title="不同主题的情感倾向占比（示例）",
    xlabel="主题", ylabel="情感倾向占比 (%)",
    right_ylabel="文本数量 (条)", line_label="文本数量",
)
```

`values` 的形状必须是 `(主题数量, 情感类型数量)`；可以传入数量、比例或百分数，每行必须非负且总和大于零。`line_values` 必须是与主题一一对应的非负有限数组，保持原值，不从组成矩阵推断。左轴固定 0–100%，右轴从 0 开始，两个轴的交点不代表数值相等或统计关联。

可选参数：`group_colors`（每组一个颜色）、`line_color`、`bar_width`（默认 0.5）、`annotate`（默认 True，可关闭数量标签），以及 `ax`（复用已有绘图区）。输出元数据保存原始数据、归一化结果、轴映射与配色。

运行 `python scripts/build_stacked_bar_line_preview.py` 生成与参考图结构对应的合成示例，输出到 `output/stacked-bar-line-preview/`，包含示例数据 JSON、PDF/SVG、450 DPI PNG 和图表元数据。

## 密集 PCA 与聚类图

`pca_biplot` 接受 `max_labels`（默认 12）。所有载荷向量仍绘制并保存在元数据中；文字标注按 PC1/PC2 投影范数选择。标签使用外置引线，元数据记录选择规则与统一的显示缩放，箭头位置不能直接当作样本得分。PCA 的 scores、loadings 和 explained_variance 必须来自同一模型，解释方差使用 0–1 比例。

`pca_loadings` 每面板最多显示 20 个变量，自动分面并保持共同横轴尺度；80 个变量完整显示为 4 个面板，不会自动删掉变量。密集图必须保留自动生成的高度，不能再强制压缩成普通小图。PC2 使用斜线纹理以支持灰度阅读。

`cluster_scatter` 使用类别标记和不同轮廓线型；轮廓是描述性的 2SD 数据椭圆，不是类别边界、95% 置信域或聚类算法的验证结果。

可执行 `python scripts/build_pca_diagnostic_preview.py` 生成 120 个模拟样本、80 个变量的压力预览。原始矩阵、PCA 数值和类别记录在 `output/pca-repair-preview/pca_source.json`。

## 收口与可用性边界

正式调用成功与论文终稿合格分别验收。注册项及合成图册的 `paper_suitable` 保持 False；只有具体输出经过数据、程序、文件与实际视觉审查后，才可在独立交付中登记审核结果。7.5.0 的全部入口通过正式结构化调用测试，但完整 SVG、色盲模拟与人工物理校样仍须按实际图逐项核对。旧 `sci_figures` 的独立兼容类保留原来的探索假设；不要把其模拟示例当作正式数据接口。

当前实现已修正两项语义缺陷：`raincloud` 包含半密度、四分位箱线和全部原始点，常数或单点组不估计密度；`correlation_matrix` 为固定 [-1, 1] 色域的 Pearson 热图，常数列相关系数明确未定义。成对关系复合视图保留在 `pairgrid`。注册专用等级仍不能代替逐项成品审查；新的三类案例验收记录保存在独立成果目录。
