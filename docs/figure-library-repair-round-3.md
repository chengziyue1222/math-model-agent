# 图表代码库第三轮修复与验收记录

日期：2026-10-09。保留仓库已有未提交修改。本报告描述当前文件和交付审计结果，不把此前已有改动全部归为本轮新增。

## 1. 结论

154 个入口全部能在明确声明合成数据的 `preview` 模式调用并导出。当前为 **62 dedicated、84 adapter、1 alias、7 template**。1 个别名不计为独立实现；剩余注册项也不能统一视为专用统计实现。

所有预览 `source="synthetic"`、`simulated=True`。`paper_suitable=True` 为 **0**。程序和文件审计通过，不能代替数据来源审查或人工终稿复核。抽查发现的 adapter/template 语义失败仍明确保留在报告中。

| 指标 | 本轮开始状态 | 当前状态 |
| --- | --- | --- |
| 注册数 | 154 | 154 |
| dedicated / adapter / alias / template | 61 / 85 / 1 / 7 | 62 / 84 / 1 / 7 |
| 仅要求 values 的入口 | 99（更早审查为 118） | 91 |
| 论文适用标记 | 未完成全量人工复核 | 0 项为 True |
| 安装包 | 源码 7.3，用户安装运行时 7.2 | 源码、wheel、用户安装均 7.4.0 |
| 非别名像素重复 | 历史问题，不能沿用旧审计 | 最终三组全量图册和精选图册均 0 |

## 2. 已修复的问题

### 数据入口与统计语义

- `get_figure(key)(data=..., mode="formal"|"preview")` 默认正式模式。模板及尚无正式统计契约的适配器拒绝正式调用；预览要求 `simulated=True`。当前只有 `cross_validation`、`model_interval` 两个适配器允许使用已有结构化契约进入正式模式，仍需数据和视觉复核。
- 补齐学习曲线、交叉验证、模型区间、稳健性包络、龙卷风、流量与分阶段流带等字段；错维度、非有限数、非法区间、缺失类别等抛出清晰错误。森林图区间必须包围估计值。
- ROC/PR 使用真实二分类标签和分数计算；PR 返回 precision、recall 和 AP。相关矩阵保留实际数值结果。Pareto 正确去掉被支配点并处理目标方向及并列。灵敏度对参数和响应配对排序。
- 散点趋势图使用 OLS 回归与 t 分布的均值置信带；普通散点不添加趋势线。区间图使用调用者提供的中心和上下限，不在正式模式伪造不确定性。
- 桑基与 alluvial 绘制有宽度的流带，保留真实流量；alluvial 验证分阶段类别转换。普通、相关、社区和加权网络保留节点与边，社区支持字符串和整数标签，保留孤立节点。
- `multi_metric_points` 是声明明确的兼容别名，共用目标入口实现和契约；不把别名计入独立实现。Mantel 版式明确列为 adapter，未伪装成真实 Mantel 检验。

### 用户截图中的 PCA 和聚类问题

- 80 个变量不再全部挤在双标图中心。保留全部箭头；按 PC1/PC2 投影载荷长度选择默认前 12 项标注；标签排列到左右两侧，并用引导线关联。元数据保留全部载荷、选中索引和显示缩放。
- 80 个载荷不再压成 80 行极小文字。每面板最多 20 项，80 项分成 4 个面板，使用一致横轴尺度，完整保留全部变量。PC2 加纹理区分。密集图必须按实际高度导出；不能再强行压缩为普通 90 mm 图高。
- 双标图、载荷图、碎石图的普通预览来自同一组标准化合成矩阵及实际拟合的 PCA；解释方差不再手填 45%/30%。新增 120 样本 × 80 变量的压力预览，三个图共用同一模型。
- 聚类图使用不同点形、轮廓线型和相等坐标比例；图例明确写“2SD 数据椭圆”。它是描述性分布轮廓，不是置信区间或已训练分类边界。
- 压力预览已分别检查 PNG、PDF 渲染和灰度图，标签可读、4 面板完整、类别在灰度下仍可辨识。双标图背景箭头仍较淡，细节阅读应使用 PDF/SVG 或独立载荷图。

### 导出、交接和 Skill

- 新增独立安装验证，使用临时工作目录、移除 PYTHONPATH、使用包内默认配置；验证六种模板的四格式导出与实际注册表加载。
- Skill 通过 `algorithms.figures` 调用实现；`sci_figures` 保留导出兼容入口。建模主 Skill 明确连接选图、真实数据契约、导出和交接。
- 修复 claim 交接：未绑定返回 `NEEDS_CLAIM_BINDING`；绑定后仍为 `NEEDS_BODY_INSERTION`，绘图脚本不会声称图已插入正文。
- 仓库及用户安装位置的四个 Skill 已同步：make-model-figures、run-modeling-project、write-model-paper、review-model-paper。覆盖前备份到 `output/repair-round-3-installed-backup-20261009-225628/`；变更文件哈希见同步记录。用户安装的 Python 包亦已升级并在仓库外验证为 7.4.0。
- capability matrix 从注册表自动生成；程序成功、样本检查、完整人工 QA 和论文适用性分别记录。

## 3. 主要修改文件

下列清单为本轮主要触及文件；部分文件开始时已有未提交改动，未重置或覆盖无关工作。

- `code/algorithms/figures/`：registry.py、contracts.py、base.py、validated.py、academic_style.py、relationships.py、model_evaluation.py、optimization.py、timeseries.py、comparisons.py、heatmaps.py、fixtures.py。
- `code/algorithms/figure_handoff.py`、`code/algorithms/venue_config.py`；`pyproject.toml` 与 `requirements-lock-py314-windows.txt`。
- `scripts/build_random_figure_previews.py`、`scripts/build_figure_library.py`、`scripts/build_academic_style_showcase.py`、`scripts/build_pca_diagnostic_preview.py`。
- `scripts/audit_figure_delivery.py`、`scripts/render_figure_review_proofs.py`、`scripts/verify_figure_installation.py`、`scripts/generate_figure_capability_matrix.py`、`scripts/resolve_paper_venue.py`。
- `code/tests/test_figure_statistics.py`、`code/tests/test_figure_library.py`、`code/tests/test_figure_handoff_and_venue.py` 及相关契约/运行时测试。
- 四个 Skill 的 SKILL.md；make-model-figures 的 `references/execution-and-migration.md`、minimal_example.py、render_process_figures.py、render_supplier_figures.py；写作/审稿 Skill 的 venue 调用脚本。
- `docs/figure-library-api.md`、`docs/figure-library-capability-matrix.md`、本报告及原审查的追加更新。

## 4. 真实数据与合成数据

本轮没有读取并采用可验证语义的外部真实数据行，没有将参考库示例数据当成真实研究结果。七类夹具均为合成数据：分类比较、时间序列、模型预测、多变量矩阵、网络边表、空间点、优化参数与目标。

曾以外部目录或数据表描述作为来源的夹具，已统一改为 `source="synthetic"`；参考描述放在 `schema_reference`，避免把模式参考误报为实际数据来源。元数据记录 source、simulated、independent_unit、units、interval_kind。合成单位是示例单位，不能直接当作论文中的实际物理单位。

PCA 压力测试原始矩阵、scores、loadings、解释方差、分组与种子完整保存在 `output/pca-repair-preview/pca_source.json`。合成预览用于检查数据编码和版式；数值正确性由独立测试补充。

## 5. wheel、依赖与环境验证

- wheel：`dist/math_model_agent-7.4.0-py3-none-any.whl`
- SHA-256：`f7db03556a68ad2f447f2ea391250f49abd599cbec019e5c5fc477a67046850e`
- wheel 内全部 50 个 algorithms Python 模块逐字节匹配当前源码；包含 figures（含 contracts）、figure_config、figure_templates、sci_figures、venue_config、figure_handoff。
- 独立环境：`.runtime-figures-7.4/`，`include-system-site-packages=false`。仓库外导入确认 154 项，六种模板导出及包内配置加载通过；`pip check` 无损坏依赖。证据：`output/repair-round-3-wheel-validation.json`。
- 用户安装环境：`C:/Users/Blake/AppData/Roaming/Python/Python314/site-packages/`，已加载 7.4.0；实际安装 Skill 在仓库外调用六种模板通过。证据：`output/repair-round-3-installed-skill-validation.json`。
- Windows / CPython 3.14.2 / Agg；中文字体 Microsoft YaHei，`C:/Windows/Fonts/msyh.ttc`。交付图册使用用户环境：numpy 2.4.3、scipy 1.17.1、matplotlib 3.10.9、sklearn 1.8.0。干净环境为 numpy 2.5.3、scipy 1.18.1、matplotlib 3.11.2、sklearn 1.9.1；完整锁定见 `requirements-lock-py314-windows.txt`。两套环境的独立六模板验证均通过；不能声称跨环境 PNG 必须逐像素一致。
- 锁文件是该 Windows/Python 环境的精确快照；其他系统和 Python 版本需重新解析并验证。没有把当前依赖快照夸大为任意系统兼容保证。

## 6. 命令与结果

以下命令在仓库根目录执行。日志留在 `output/repair-round-3-*.log`。

```powershell
python -m pytest -q
ruff check code scripts skills
python -S skills/make-model-figures/scripts/minimal_example.py --help
python -S scripts/build_figure_library.py --help
python -m build --wheel
.runtime-figures-7.4/Scripts/python.exe -m pip install --force-reinstall --no-deps dist/math_model_agent-7.4.0-py3-none-any.whl
.runtime-figures-7.4/Scripts/python.exe -m pip check
.runtime-figures-7.4/Scripts/python.exe scripts/verify_figure_installation.py --skill skills/make-model-figures --wheel dist/math_model_agent-7.4.0-py3-none-any.whl --report output/repair-round-3-wheel-validation.json
python scripts/verify_figure_installation.py --wheel dist/math_model_agent-7.4.0-py3-none-any.whl --report output/repair-round-3-installed-skill-validation.json
python scripts/build_random_figure_previews.py
python scripts/build_figure_library.py --strict
python scripts/build_figure_library.py --output output/figure-library-gallery-academic --strict
python scripts/build_academic_style_showcase.py
python scripts/build_pca_diagnostic_preview.py
python scripts/render_figure_review_proofs.py
python scripts/audit_figure_delivery.py output/random-figure-previews output/figure-library-gallery output/figure-library-gallery-academic output/academic-style-showcase --zip
python scripts/resolve_paper_venue.py --output output/repair-round-3-default-venue.json
```

- 测试：**436 passed，1 个既有 Starlette/httpx 弃用警告**；Ruff：All checks passed。
- 数值测试覆盖 ROC/PR、相关矩阵、PCA、Pareto、灵敏度、森林/误差区间、桑基/alluvial 流量、网格响应面、字符串/整数社区映射九类；新增密集 PCA 完整数据与单一拟合模型一致性检查。
- 两个 `--help` 在 `python -S` 无 site-packages 条件下通过，帮助命令不提前加载绘图库。
- 注册数与中文名映射、别名、字段/尺寸/区间错误、结构化图元及四格式导出由已有和扩展测试覆盖。全量交付审计另外检查文件可读性、中文字体缺字、完整数据来源字段及输出哈希。
- 最终三组全量预览各 154/154，精选 24/24；共 486 个四格式图束（1944 个核心文件），另有 3 个 PCA 压力图束。四组程序/文件审计均 PASS，非别名像素重复为 0。两个全量示例图册中 multi_metric_points 与 multi_metric_comparison 相同，属于声明的别名。所有 ZIP CRC 检查通过。

## 7. 视觉抽查与未通过项

抽查 **37 张**，覆盖 12 组（11 个注册类别和额外空间组）。比较、分布、趋势、关系、网络、优化、空间、多变量八个主要家族均至少 3 张。每张检查 PNG、实际 PDF 渲染和灰度样本。证据：`output/repair-round-3-visual-proofs/index.html`、`sample-manifest.json`、`review.json`；记录绑定当前 PNG/PDF 哈希。另检查 3 张 80 变量 PCA 压力图的上述三个视图。

这是 Codex 的图像抽查，**不是独立人工复核**。没有物理缩印、专业色盲模拟和全量 SVG 视觉检查；SVG 已做文件解析与哈希完整性检查。全量图元数据的 visual_review/qa_status 保持 NOT_CHECKED，paper_suitable 保持 False。

7 张抽查样本语义失败：

- `ranking`：通用横向条形未按数值排名；正式模式禁止调用。
- `score_bar`：仍为通用折线，未表达评分柱状结构；正式模式禁止调用。
- `algorithm_flow`：仍为占位线性节点链，没有实际算法分支语义。
- `geometry`：仍为占位线性节点链，未实现几何结构。
- `technical_route`：仍为占位线性节点链，未反映实际任务依赖。
- `spatial_heatmap`：仍为按 Y 值着色的二维散点，没有空间网格或热度聚合。
- `spatial_3d`：仍为二维散点，没有三维坐标轴。

这些图虽然能导出，仍不符合其名义图型，正式模式已阻断。另有 joint_density 对比偏淡、weighted_network 缺定量边宽图例、PR 模型对比宜统一纵轴、spatial_scatter 的类别灰度区分不足。压力双标图背景箭头仍偏淡；选中箭头相近时引导线可能穿过点云。以上不隐瞒为“所有图已通过”。

## 8. 论文使用边界与剩余工作

- **当前能无条件认定适合论文终稿的图型：0。** 所有图都需真实数据、问题语义、单位与人工 QA。
- 62 个 dedicated 是建模过程优先调用的候选，包括 bar/grouped_bar/forest/errorbar、散点/回归、热图/响应面、ROC/PR/校准、PCA、灵敏度/Pareto、网络与流带。该等级表示已有专用绘图与校验，不表示每一项都经过全部统计和终稿证明。
- 84 个 adapter 中 82 个尚无正式调用入口；7 个 template 只用于版式预览。cross_validation、model_interval 可使用其真实结构化字段，但仍未获论文终稿资格。别名只能提供兼容性。
- 尚未完成：91 个 values-only 长尾入口的真实结构化契约；82 个适配器的正式统计实现；7 个模板的具体语义；真实外部数据验证；全量人工/色盲/缩印复核。7 张失败抽查样本优先于继续新增图型。
- SHAP、Taylor、Mantel、空间热度、三维空间、稳定性等预览不能被当作真实统计推断。转换成正式实现时应明确计算方法及契约，并增加与参考数值对照的测试。

## 9. venue 配置

支持 CUMCM、MCM/ICM、MathorCup、journal、generic-research-report 五种；默认 generic，显式配置优先，不能通过普通覆盖项偷换 venue。区分页数、匿名、AI 披露、附录、引用、图宽和列策略。30 页限制仅在显式 CUMCM 配置出现，其他类型默认不强加该限制。

这些是本地工作流默认配置，**未核验当前官方赛事规则或期刊投稿规定**；已有专门 CUMCM 脚本仍是专门入口。写作/审稿 Skill 通过 venue 层解析，实际投稿需按对应官方规定显式覆盖。

## 10. 成品与证据

- `output/random-figure-previews/` 与同名 ZIP：154 张随机合成预览。
- `output/figure-library-gallery/`、`output/figure-library-gallery-academic/` 与同名 ZIP：各 154 张结构化示例。
- `output/academic-style-showcase/` 与同名 ZIP：24 张精选版式。
- `output/pca-repair-preview/` 与同名 ZIP：80 变量压力修复预览及可复算输入。
- `output/repair-round-3-delivery-audit.json`：注册等级、导出/字体/来源、精确重复、ZIP 哈希。
- `output/repair-round-3-final-verification.json`：最终源码与 wheel 一致、同步与 ZIP CRC。
- `output/repair-round-3-visual-proofs/`：抽查视图与诚实的未通过记录。
- `docs/figure-library-capability-matrix.md`：154 项当前契约和等级，自动生成。

## 附录 A：仍为 adapter 的全部 84 项

- `adjacency`：邻接关系图
- `adjacency_matrix`：邻接矩阵
- `ahp_weights`：AHP权重图
- `area`：面积图
- `autocorrelation`：自相关图
- `beeswarm`：蜂群图
- `calendar_heatmap`：日历热图
- `circular_heatmap`：环形热图
- `cleveland_dot`：克利夫兰点图
- `cluster_stability`：聚类稳定性图
- `clustered_heatmap`：聚类热图
- `clustered_heatmap_matrix`：聚类矩阵热图
- `confusion_matrix_eval`：模型混淆矩阵
- `constraint_boundary`：约束边界图
- `constraint_slack`：约束松弛图
- `contour`：空间等高线图
- `contour_density`：等高线密度图
- `contribution_decomposition`：贡献分解图
- `control_chart`：控制图
- `coverage`：覆盖率图
- `cross_validation`：交叉验证图
- `decision_tree`：决策树图
- `decomposition`：时间序列分解图
- `dendrogram`：树状图
- `diverging_bar`：发散条形图
- `diverging_heatmap`：发散色热图
- `effect_size`：效应量图
- `error_by_time`：随时间误差图
- `event_timeline`：事件时间线
- `faceted_heatmap`：分面热图
- `feasible_heatmap`：可行域热图
- `feasible_region`：可行域图
- `feature_importance`：特征重要性图
- `gantt`：甘特图
- `global_local`：全局-局部敏感性图
- `high_dim_density`：高维密度图
- `ice`：个体条件期望图
- `indicator_correlation`：指标相关图
- `jitter`：抖动散点图
- `lift_gain`：提升-增益曲线
- `lollipop`：棒棒糖图
- `mantel`：Mantel关联图
- `model_interval`：模型区间图
- `multi_metric_comparison`：多指标比较图
- `multi_series`：多序列折线图
- `optimum_distribution`：最优值分布图
- `parallel_coordinates`：平行坐标图
- `parameter_response`：参数响应图
- `pareto_distribution`：帕累托分布图
- `partial_autocorrelation`：偏自相关图
- `partial_correlation`：偏相关图
- `partial_dependence`：部分依赖图
- `percent_stacked_bar`：百分比堆叠柱状图
- `perturbation`：扰动分析图
- `probability_plot`：概率图
- `ranking`：排名图
- `raw_points`：原始点图
- `repeated_convergence`：重复收敛曲线
- `residual_distribution`：残差分布图
- `response_1d`：一维响应曲线
- `response_surface_opt`：优化响应面图
- `risk_return`：风险-收益图
- `rolling_mean`：滚动均值图
- `scenario`：情景分析图
- `scenario_ranking`：情景排序图
- `scheme_indicator_matrix`：方案-指标矩阵
- `score_bar`：综合得分柱状图
- `separation_loadings`：分离载荷图
- `shap_beeswarm`：SHAP蜂群图
- `shap_summary`：SHAP汇总图
- `spatial_3d`：三维空间图
- `spatial_heatmap`：空间热图
- `stacked_area`：堆叠面积图
- `state_machine`：状态机图
- `state_trajectory`：状态轨迹图
- `state_transition`：状态转移图
- `step`：阶梯图
- `taylor_diagram`：泰勒图
- `threshold_crossing`：阈值穿越图
- `threshold_heatmap`：阈值热图
- `time_heatmap`：时间热图
- `topsis_weights`：TOPSIS权重图
- `variable_dependency`：变量依赖图
- `weight_sensitivity`：权重敏感性图

## 附录 B：仅用于模板预览的全部 7 项

- `algorithm_flow`：算法流程图
- `coordinate_system`：坐标系图
- `geometry`：几何结构图
- `input_model_validation_output`：输入-模型-验证-输出图
- `mechanism`：机制示意图
- `task_decomposition`：任务分解图
- `technical_route`：技术路线图

## 附录 C：兼容别名

- `multi_metric_points`：多指标点图
