# 配置、执行与迁移

## 可运行路径

算法只维护在 `math-model-agent` 的 `algorithms` 包中；skill 不复制算法实现。
从仓库安装：`python -m pip install .`；离线环境可安装由仓库构建的 wheel。
若系统包有无关版本差异，使用独立虚拟环境安装wheel，保留系统包。`minimal_example.py` 支持 `MATH_MODEL_FIGURES_PYTHON`，并可自动发现skill根目录同级的 `runtimes/math-model-figures` 环境（Windows的Scripts/python.exe或Unix的bin/python）。其他适配器直接用该环境的Python执行。

安装后，在任意项目目录执行：

```powershell
python <skill目录>/scripts/minimal_example.py --output figure-demo
python <skill目录>/scripts/minimal_example.py --output figure-demo --suite
```

第一条生成中文长标签模型比较，第二条验证全部六类。所有输入明确标为合成演示，不能用于真实论文结论。
若 `algorithms.figure_templates` 不存在，应升级算法包；不要复制一份实现到 skill，也不要猜作者机器的路径。
仓库开发时可设置 `PYTHONPATH=<仓库>/code`；正式独立验证须清除该变量并从 wheel 运行。

## 配置优先级

`load_figure_config(config, **overrides)`：显式参数 > 显式配置映射/文件（或工作目录最近祖先的 `config/paper_style.yaml`）> `algorithms.figure_config.DEFAULTS`。
明确传入 `{}` 表示只使用内置默认值；明确指定不存在的文件报错。配置来源和文件 SHA-256 写入元数据。

竞赛默认 150 × 90 mm、正文 8.5 pt、刻度/图例 8 pt、标题10 pt、面板9 pt、审查下限 7 pt。这是本项目可覆盖的默认值，不是所有比赛或期刊的官方要求。
YAML 的 `figures` 控制主题、尺寸、字体、线宽、标记、网格、背景、DPI和阈值；中文/西文字体还继承 `typography`。
`semantic_styles` 可为对象稳定名称指定 `color`、`marker`、`linestyle`。默认名称哈希映射与顺序无关，但有限色板可能碰撞，关键对比应显式绑定并检查灰度。

```python
from algorithms.figure_templates import render_template, template_registry
from algorithms.sci_figures import FigureContract, export_publication_figure

# data 来自已保存结果，不从文件名推断指标或结论。
fig = render_template("comparison", data, width_mm=150)
contract = FigureContract(
    claim="待检验：各模型在相同测试切分上的MAE如何排序？",
    claim_status="question", question="哪个模型的测试MAE较低？",
    evidence=("相同切分的模型MAE",), source_paths=("results/metrics.json",),
    width_mm=150, units="m", plotting_code=("plot_results.py",),
    model_name="记录模型版本", n_definition="记录独立测试样本定义",
    statistic="MAE", uncertainty="未提供区间", randomness="记录种子或确定性",
)
paths = export_publication_figure(fig, "figures/模型比较", contract)
```

`template_registry()` 返回六类模板的问题、必需/可选字段、单位/不确定性要求、适用/禁用条件、布局、颜色角色、接口、例子与图注骨架。
预测区间只读取输入，不自行拟合；比较要求统一 `split`、`metric` 和 `direction=min|max`；多次优化分布需要至少两次实际结果；约束余量约定非负为可行；发散色标必须给出 `midpoint_meaning`。
未提供的证据面板省略，并在 `template.omitted_panels` 记录原因。

## 导出和验收

正式入口固定交付 PDF/SVG/450 DPI RGB PNG及元数据；`formats` 表示此交付契约。探索性 `save_figure` 保留旧行为，不产生正式通过状态。
保存时显式禁用 tight 裁边；检查像素取整误差≤1 px、DPI误差≤0.05、矢量尺寸误差≤0.02 mm。
先写临时目录并验证整个包，再替换目标文件；替换异常时恢复旧文件。`.figure.json` 最后写入，作为完整性标记。
PDF使用TrueType嵌入并检查实际字体；SVG保留文字，需要查看机器有相同字体。高密度数据层可栅格化，坐标和文字保留矢量。

schema 3 保留旧 `contract`、`audit`、`export`，增加 `programmatic_audit`、`file_audit`、`configuration`、`source_files`（SHA-256）、`environment`、`output_hashes`、`visual_review`、`completion_status`。
读 schema 2 时，视觉状态应视为 `NOT_CHECKED`；旧 `audit.passed` 只表示程序检查。不得据此推出完整交付通过。
源路径相对 `source_root`（默认当前目录）；正式调用方应传明确根目录或绝对输入路径。
给 `source_hashes` 可校验此前登记的内容。每次生成记录当前哈希；输入或输出变化后需重新审查。
可复现指输入、参数、统计量和图面结构相同，不要求 PDF 字节完全相同。

`record_visual_review` 只登记实际完成的五项：PNG、矢量渲染、物理尺寸校样、灰度、源值核对；记录人员、依据并绑定输出哈希。登记前同时核对输入和绘图代码，以及算法包内全部注册渲染器与共享样式的 SHA-256；变化后拒绝沿用旧图的审查。任一实际检查为 FAIL 时，完整验收状态为 FAIL。
状态用 PASS/WARN/FAIL/NOT_CHECKED。未执行不得填 PASS。自动几何检查不能证明统计结论正确。

## 兼容性

- `publication_size("single"/"double", height)` 仍是 89/183 mm；`publication_size(None, None, config=cfg)` 继承项目宽高；显式 `width_mm` 最高优先。
- `FigureContract` 原有参数可用，旧 `column` 决定未显式指定时的宽度。新模板导出须填其实际目标 `width_mm`。
- 所有旧专业图类 `make()` 现在恢复 rcParams。保留它们的探索性画布与数据假设，避免破坏接口；正式图优先使用新路由或在目标尺寸手工构图。
- 尤其旧 `CvRocCurve` 与 `PredictionMarginal` 会模拟数据，不能当作真实结果模板；真实预测应使用新 `prediction` 路由，真实ROC应从标签和概率计算。
- 严格导出现在拒绝源文件缺失、哈希变化和缺字；旧脚本必须补正确来源。重叠边界框仅 WARN，图例在轴内只是位置提示，不代表遮挡。

## 上下游交接

保持现有 skill 输入/输出角色不变：接收 `result_object`、`quality_validation`、`claim_registry`、`figure_plan`；输出 `figure_registry`、`figure_audit_report`。
每个 registry 条目保留旧路径/哈希字段，附元数据路径、`visual_review` 与 `completion_status`。
`run-modeling-project` 安排待核对问题；`write-model-paper` 只从已核对结论写正文，question/uncertain 必须明确限定；`review-model-paper` 检查输入哈希、物理校样和独立视觉状态。
报告总体 PASS 必须同时满足程序、文件和视觉检查；模板脚本默认返回 NEEDS_VISUAL_REVIEW。通用“展示登记结果”不作为科学结论。

## 正式注册表和预览隔离

优先调用 `algorithms.figures.get_figure/get_spec/list_figures`；`algorithms.sci_figures` 保留旧类和导出契约。正式调用默认 `mode="formal"`，缺少统计字段时抛出 ValueError。仅在预览脚本中显式使用 `mode="preview"` 和 `simulated=True`（或模拟 DataContract）。当前注册入口均支持结构化正式调用；数量和专用实现、别名的划分以实时注册表和生成的能力矩阵为准。没有注册占位适配器或模板。不得用图名或颜色代替其统计实现。能力矩阵由 `scripts/generate_figure_capability_matrix.py` 生成。

导出完成、claim 绑定和正文插入分别登记。绘图脚本始终将 `inserted_in_body=False`；没有映射时为 `NEEDS_CLAIM_BINDING`，有实际 claim 映射但尚未正文插入时为 `NEEDS_BODY_INSERTION`。正文生成器核对插入位置后才能更新插入状态。空 claim_ids 永远不能声明已插入。

## 密集 PCA 图的调用约束

PCA 三组输入必须来自同一次模型拟合。`pca_biplot(max_labels=12)` 会保留所有箭头，仅按投影范数选择文字标注并记录规则；载荷使用统一显示缩放，不应按样本坐标解读。`pca_loadings` 超过 20 个变量会自动分面，保留全部变量与共同尺度；导出时保持相应高度。`cluster_scatter` 的 2SD 数据椭圆只描述分布，不代表置信域或分类边界。正式报告应另行验证分组、降维和聚类结果。

## 7.5.0 入口与计算模块

先使用 `get_spec(key).required_fields` 匹配保存的结果，再用 `get_figure(key)(data={..., "contract": data_contract}, mode="formal")`。`data=`、关键字和支持的旧位置参数均经过校验；预览也不会绕过契约。五个别名继承规范入口契约。

`algorithms.figures.compute` 提供显式统计计算，返回结果及计算元数据；渲染函数不补造统计量。UMAP 计算依赖可选包，已有嵌入结果的绘制不依赖它。示意图读取调用者提供的节点、关系和几何，专用等级不表示完成统计推断。完整字段、别名和迁移说明见仓库 `docs/figure-library-api.md` 与能力矩阵。

合成预览、正式调用、论文终稿审核分别登记。当前目录 `paper_suitable=False`；不得把自动程序 PASS 写成人工终稿通过。
