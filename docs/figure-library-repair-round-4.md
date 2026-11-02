# 图表库第四轮：运行与交付收口记录

日期：2026-10-10。按用户“先优先收口，收尾后再进行下一轮修复”的最新要求，冻结功能扩展，完成现有代码、测试、图册、安装包及 Skill 的交付验证。保留已有未提交修改与历史文件。

## 1. 当前结论

**运行和打包收口完成；“全部入口语义与论文终稿完整合格”的终验尚未达成。**

154 个入口在仓库、干净 wheel 环境和用户实际安装环境中均能用结构化数据正式调用。注册等级为 149 dedicated、5 alias、0 adapter、0 template。此处等级是注册表状态，不能推出 149 个入口全部完成独立统计推断或语义终审：尤其继承的 `raincloud` 仍直接调用小提琴实现，后续必须修复。

所有图册为合成数据，`paper_suitable=True` 为 0，原始导出元数据的 `visual_review` 保持 NOT_CHECKED。另有 37 张样本经 Codex 实际查看 PNG、PDF 渲染及灰度，记录为 WARN；这不等于独立人工终稿复核。

| 项目 | 第三轮 | 本轮收口 |
| --- | --- | --- |
| 注册入口 | 154 | 154 |
| dedicated / adapter / alias / template | 62 / 84 / 1 / 7 | 149 / 0 / 5 / 0（仍需语义终审） |
| 仅要求 values | 91 | 8，仅单变量分布家族 |
| 正式调用 | 62 dedicated + 2 adapter | 全部 154 项在两种安装环境实测 |
| 全套回归 | 436 | 1068 通过、1 条第三方弃用警告 |
| 全量图册 | 三组 × 154 | 三组 × 154，精选 24，另有 3 张密集 PCA 压力图 |
| 非别名像素重复 | 0 | 0；兼容别名的相同输出保留 |
| 源码 / wheel / 用户包 | 7.4.0 | 7.5.0 |
| 论文终稿通过 | 未完成 | 未完成；不能由程序 PASS 推定 |

## 2. 已完成改动

### 入口、契约和实现

- `data=`、关键字和支持的旧位置参数统一校验；缺字段、错维度及非法数值报错，不再用位置参数绕过契约。预览和正式模式共用绘图函数及验证器，预览要求模拟契约。
- 新增 `specialized.py` 的图型字段、校验和专用渲染，替换注册路径中的通用占位适配器与模板。比较、时间、矩阵、模型解释、优化、网络及示意家族读取对应结构，不在正式路径由平面数组复制出假矩阵或假关系。
- 排名保留并列并明确升降序；得分柱使用真实类别与数值；空间热图有实际网格；三维空间图使用实际三维轴；流程和技术路线读取节点、边、节点类型或阶段；几何图读取点、线段和多边形。
- 聚类矩阵读取真实 linkage 并记录重排；百分比堆叠校验分母并记录归一化；原始点与抖动保留观测，抖动只改变显示；龙卷风的 low/high 是参数端点响应，可反向，不按置信区间强制递增。
- SHAP、PDP/ICE、Taylor、Mantel、覆盖率、提升增益和重复优化读取已提供结果；绘图不训练模型。显式计算移至 `compute.py`，保存方法、种子及计算结果。
- 演示 PCA 来自同一拟合；t-SNE/UMAP 使用真实算法结果。UMAP 原始合成矩阵、算法参数、软件版本和坐标随 wheel 打包；普通渲染不依赖可选 UMAP 计算包。
- 森林图演示 CI 来自每组 20 个合成观测的 t 均值区间；线性 SHAP 演示来自声明线性模型的精确归因；重复收敛演示来自梯度下降，聚类稳定性来自实际重复 KMeans 与 ARI。
- 保留全部中文名称及英文 key；唯一五个兼容别名列在 API 与能力矩阵，输出保留请求名称和规范名称。

### 风格与收尾缺陷

- 正式公共入口自身设置学术样式和中文字体，脱离图册构建脚本也能绘制中文。
- 社区及空间类别增加形状编码；加权网络增加边宽量化图例。
- 密集 PCA 保留 80 个载荷，仅给前 12 个标注；载荷分成四个面板，保留自动高度，PC2 增加纹理。类别椭圆明确为 2SD 数据轮廓。
- 安装验证发现 JSON 数字列表进入小提琴/雨云图时被误作多个数组，本轮已修复并增加回归测试。
- 三维空间图固定轴内有效刻度，避免未绘制的轴外刻度被误审为裁切；所有最终图册重建后通过审计。
- 旧 PCA 预览 PNG 被外部程序占用；新压力预览改到 `output/pca-repair-round-4/`，保留旧目录。

## 3. 统计与数据证据

`test_figure_round4.py` 覆盖全部入口的普通、密集、长标签数据及必需字段失败，共 632 项。另有原统计、导出、Skill 与建模测试，完整合计 1068 项。

数值对照覆盖：SHAP 平均绝对归因、已知预测函数的 PDP/ICE、Mantel 距离相关与置换重现、Taylor 标准差及中心化误差的统一自由度、覆盖率、AHP、偏相关残差对照、分解重构、提升增益、百分比归一化、排序并列及龙卷风反向端点。复杂计算与图形结构分别检查。

**这些测试并未给全部 149 个规范入口逐项建立独立参考统计实现；剩余逐项数值证明和退化数据检查仍应继续。** 单纯 formal 调用或随机导出不作为统计正确性的充分证据。

七类小型夹具仍为明确合成数据：分类、时间、预测、多变量、网络、空间、优化。本轮另读取授权目录 `E:\数据要素` 的实际项目表，生成 `output/repair-round-4-local-fixtures.json`：

- 分类、多变量和空间来自 `data/node_classification.csv`，完整保留 145 行；分别用于类别计数、四列多变量及空间坐标结构验证。
- 网络来自 `data/processed/waterway_nodes.csv` 与 `waterway_edges_weighted.csv`：378 个声明节点、428 条源边记录。无向渲染显式按无序端点求和，保留节点与孤立点，不静默丢弃反向边。
- 保存来源、哈希、单位、分析单位和转换；这些是导入的本地项目表，原始采集真实性未独立核验。`simulated=False` 表示读取原表，不能解读为已证明数据采集真实性。
- **全量交付图册仍使用合成数据。** 本地表已分别通过柱状图、相关矩阵、空间点图和加权网络的正式调用及画布绘制，记录在 `output/repair-round-4-local-formal-validation.json`；未导出为本轮图册，也未将其当作全库的真实研究结论；时间、预测与优化没有使用未经确认的真实来源。

## 4. 导出、安装与 Skill

全部三组 154 项及精选 24 项均有 PNG、PDF、SVG、figure.json。审计检查来源/模拟标记、分析单位、单位、区间类型、字体缺字、尺寸、输出哈希、PDF 页和 SVG 结构；四组均 PASS，非别名精确重复 0。视觉警告未被清除。

ZIP 只收录当前清单中的图及交付辅助文件。目录里的历史文件保留，未纳入有效图数或用来证明本轮覆盖。五个 ZIP 均通过 CRC 检查。

安装验证在仓库外临时工作目录运行，清除 PYTHONPATH：干净环境 NumPy 2.5.3 / Matplotlib 3.11.2，与用户环境分别逐项调用全部 154 个入口、绘制画布并运行六类正式导出。两份报告均 PASS，运行包为 7.5.0。干净依赖 `pip check` 通过。

已同步 `make-model-figures`、`run-modeling-project`、`write-model-paper`、`review-model-paper`，安装前有目录备份。源 Skill 与安装 Skill 文件逐项一致；建模 Skill 经公共注册表调用图表库，统计计算模块在算法 wheel 中，不复制到 Skill。

## 5. 视觉复核与下一轮清单

查看了 12 个抽样家族的 37 张图，分别检查 PNG、实际 PDF 渲染和灰度；另查看三张密集 PCA PNG。证据位于 `output/repair-round-4-visual-proofs/visual-review.json`，绑定 PNG/PDF 哈希。所有样本保留 WARN，并未填入五项完整人工复核 PASS。

下一轮按下列顺序处理，当前不扩展新图型：

1. **语义和等级再核查**：`raincloud` 仍只是调用 `violin`，必须加入真实密度、原始点及摘要编码或降低等级；`pairgrid` 与 `correlation_matrix` 使用同一矩阵图语法，复查是否需要明确区别或兼容关系。重新审查继承专用实现，不以工厂名称或注册等级为语义证明。
2. **负值色彩和矩阵标签**：热图含负值时需声明零点并选择合适发散色标；矩阵使用实际行列/状态标签，避免默认半整数刻度。删除响应面与流图的重复标题。
3. **类别和密度可读性**：聚类图例外置、使用具有解释力且真实计算的聚类示例；联合密度增加定量色标，箱线中位数、小提琴中央线及三维点提高灰度对比。空间气泡补面积图例及投影说明；网络长节点名避免挤压。
4. **单位和统计注释**：元数据已有单位，但轴仍有“值”“变量 X”等通用文字，需按实际字段显式映射。PR 显示 AP 并声明坐标范围；校准展示分箱样本量；流程版式按论文最终宽度重新分配字号与留白。
5. **完整终验**：逐入口补常量、极小样本、奇异协方差、边界网格、循环/长标签等退化条件和可对照数值证据；补齐所有 SVG 渲染、色盲模拟、物理尺寸校样及独立人工终稿审核。当前不得标成已做。

已登记 adapter/template 的剩余项为 0；仍未完成的是上述已确认语义、视觉和完整统计终验，不能因此把所有图型宣称为独立统计实现。当前可用于建模过程中的结构化结果绘制、诊断及预览；**没有任何入口获得本轮全局论文终稿适用认证**。真实数据的具体输出需单独审核。

## 6. 可复现命令与结果

```powershell
python -m pytest code/tests -q
# 1068 passed, 1 warning（FastAPI/Starlette 第三方弃用提示）
ruff check code scripts skills
# All checks passed
python -m build --wheel
python scripts/build_random_figure_previews.py
python scripts/build_figure_library.py --strict --no-zip
python scripts/build_figure_library.py --strict --no-zip --output output/figure-library-gallery-academic
python scripts/build_academic_style_showcase.py
python scripts/build_pca_diagnostic_preview.py --output output/pca-repair-round-4
python scripts/audit_figure_delivery.py output/random-figure-previews output/figure-library-gallery output/figure-library-gallery-academic output/academic-style-showcase --zip --report output/repair-round-4-delivery-audit.json
python scripts/render_figure_review_proofs.py --output output/repair-round-4-visual-proofs
.runtime-figures-7.5/Scripts/python.exe scripts/verify_figure_installation.py --skill skills/make-model-figures --wheel dist/math_model_agent-7.5.0-py3-none-any.whl --fixtures output/repair-round-4-catalog-inputs.json --report output/repair-round-4-wheel-validation.json
python scripts/verify_figure_installation.py --wheel dist/math_model_agent-7.5.0-py3-none-any.whl --fixtures output/repair-round-4-catalog-inputs.json --report output/repair-round-4-user-install-validation.json
.runtime-figures-7.5/Scripts/python.exe -m pip check
```

所有最终命令通过；更早发现并已修复的失败记录仍保存在 output 日志。图册构建、文件和重复审计的 PASS 不等同于视觉终审 PASS。

## 7. 交付入口

- API：`docs/figure-library-api.md`；逐项契约和别名：`docs/figure-library-capability-matrix.md`。
- 全量图册：`output/random-figure-previews/index.html`、`output/figure-library-gallery/index.html`、`output/figure-library-gallery-academic/index.html`。
- 精选：`output/academic-style-showcase/index.html`；压力图：`output/pca-repair-round-4/index.html`。对应 ZIP 同目录名。
- 安装包：`dist/math_model_agent-7.5.0-py3-none-any.whl`；干净运行依赖：`requirements-lock-py314-windows-7.5.txt`。
- 审计：`output/repair-round-4-delivery-audit.json`、`repair-round-4-wheel-validation.json`、`repair-round-4-user-install-validation.json`、`repair-round-4-wheel-integrity.json`、`repair-round-4-package-integrity.json`。

Wheel SHA-256：`7ef695b77000a99c91abd24b1c791d28b2b47c94bf63fbd8825d9813f0a43504`。

安装 Skill 备份：`C:\Users\Blake\math-model\output\repair-round-4-installed-backup-20261010-210605`。

仅要求 values 的八项：`boxplot`, `ecdf`, `histogram`, `kde`, `pareto_distribution`, `qq_plot`, `raincloud`, `violin`。
