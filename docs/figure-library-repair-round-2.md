# 图表库第二轮修复记录

日期：2026-10-03

## 修复目标

本轮按照 `figure-library-critical-review-2026-10-03.md` 和 `make-model-figures` 的数据契约、视觉 QA、矢量导出要求，处理四类问题：注册表等级失真、图型重复、字段契约过宽、预览脚本没有按语义供数。

## 已完成

### 1. 注册表分层

`FigureSpec` 现在提供 `implementation_level`，并在目录和 `figure.json` 中记录：

- `dedicated`：独立绘图结构或统计计算；
- `adapter`：统一学术视觉适配器，仍需用户提供并核对统计语义；
- `alias`：兼容名称，不计为独立图型；
- `template`：流程、几何和版式示意，只用于预览。

本轮目录快照：154 个注册项，其中 61 个 dedicated、85 个 adapter、1 个 alias、7 个 template。`paper_suitable` 不再默认开启；当前均为 `False`，因为全量人工视觉复核仍是 `not_checked`。

### 2. 高风险重复图拆分

已拆分单序列柱状图/分组柱状图、无趋势散点/趋势散点、相关/加权/社区网络、嵌入轨迹/聚类散点、矩阵热图/响应面、收敛/帕累托/灵敏度。响应面现在要求二维网格并绘制填充等高线；网络图分别使用边线型、边宽和节点社区颜色；轨迹图使用顺序箭头，聚类图使用协方差边界。

桑基图和冲积图现在要求 `source`、`target`、`value`，并绘制流带；旧的 `nodes/flows` 只保留在弦图中。

### 3. 数据契约和错误信息

已补齐高频图型的字段校验，包括柱状、森林、散点、ROC/PR、校准、PCA 双标图、热图、响应面、网络、桑基、空间散点、时间趋势和误差带。字段缺失、维度不匹配、区间上下界反转、网络边不引用节点时会抛出带图型名称和字段名称的 `ValueError`。

### 4. 夹具和元数据

新增 `code/algorithms/figures/fixtures.py`，提供分类比较、时间序列、模型预测、多变量矩阵、网络边表、空间点和优化参数七类固定夹具。夹具记录 `source`、`simulated`、`independent_unit`、`units` 和 `interval_kind`；`E:\数据要素` 中的船舶属性、AIS 和节点分类文件仅作为字段设计参考，语义未确认的数值仍标记为 simulated。

### 5. 输出和去重

重新生成随机预览、全量学术画廊和精选学术展示。随机预览和全量学术画廊均为 154/154 导出成功、0 个错误。PNG 精确哈希检查结果为 0 组重复（别名不生成额外独立图片）。每个图仍输出 PNG、PDF、SVG 与 `figure.json`。

## 仍需人工复核

- 已抽查类别比较、关系与相关、网络/流量/空间、优化/灵敏度四类接触表，每类至少 3 张；结构差异、中文字体、图例和区间可读性通过本轮抽查。154 张图的 `visual_review` 仍保持 `NOT_CHECKED`，因为程序无法替代最终印刷尺寸、灰度打印、色盲和论文图注一致性检查。
- adapter 和 template 图型不能直接当作统计结果使用，需先提供真实字段并确认单位、独立分析单位和区间含义。
- `paper_suitable=True` 只应在目标图通过人工视觉复核后写回；本轮没有虚报为论文终稿。

## 验证命令

```text
pytest -q code/tests/test_figure_library.py
ruff check code/algorithms/figures/registry.py code/algorithms/figures/academic_style.py code/algorithms/figures/heatmaps.py code/algorithms/figures/optimization.py code/algorithms/figures/comparisons.py code/algorithms/figures/fixtures.py scripts/build_random_figure_previews.py scripts/build_figure_library.py code/tests/test_figure_library.py
python scripts/build_random_figure_previews.py
python scripts/build_figure_library.py
python scripts/build_academic_style_showcase.py
```

最近一次图表库测试结果：10 passed；全量随机预览：154 rendered / 0 errors；全量学术画廊：154 exported / 0 errors。

## 适用范围

当前 dedicated 图型可作为数学建模代码库的优先调用入口，但在论文终稿前仍需提交真实数据、保存图表契约并完成人工视觉 QA。adapter 图型适合建模过程中的探索和版式预览；template 图型只表达布局或流程，不应被解释为统计证据。
