# 数学建模 skills 蒸馏优化记录

## 本次范围

依据用户的波浪能图反馈，阅读本地 `E:\ai数模\nature-skills-main` 的技能入口，并深入检查与数模相关的图表、统计、数据可用性、文献、写作和审查指导。增量更新现有 8 个数学建模 skills；保留原有算法接口、执行契约和未提交的升级工作。

本次只更新技能说明与参考资料。不重绘当前项目图、不修改数据或模型结果、不调整项目绘图配置、不安装 Nature Skills 的运行依赖。暖色方案以可执行样式片段提供，没有伪装成算法库已注册主题。

修改前的仓库与已安装 Markdown 备份位于 `C:\Users\Blake\.codex\backups\modeling-skill-distillation-20260930-181904`，含原文件和哈希清单。

## 用户意见的整理与落点

| 意见 | 写入后的可执行决策 |
|---|---|
| 浅蓝浅绿、细线与低饱和叠加后缺乏张力 | 重要曲线和类别优先明确饱和色，淡色留给区间带和背景；按最终尺寸调整线宽 |
| 红橙黄贴合功率/能量 | 非负强度图优先深红—橙—金黄；净功率或残差有正负时仍按中点选发散色标 |
| `hot` 低值近黑、高值近白 | 提供避开两端的五色连续方案；保留数据范围与真实梯度 |
| 白星在高值区消失 | 保存参数点用亮填充、深粗边，检查低中高背景；保存点与最优点分别命名 |
| 图例遮住数据 | 预留图例/色条空间，检查所有有效数据、误差带和可行域边界 |
| 不能只靠颜色区分 | 线型、标记、直接标签与灰度复核继续保留 |
| 无需所有图一个气质 | 连续物理量与类别对象分别配色；跨图统一对象含义、术语和字体 |
| 当前不修改图 | 明确审查意见和 skill 更新不触发现有图重绘 |

主要落点为 [配色系统](../skills/make-model-figures/references/palette-system.md)、[功率与能量图](../skills/make-model-figures/references/power-energy-figures.md)、[成图检查](../skills/make-model-figures/references/visual-qa-checklist.md)。

## 源库覆盖与取舍

以下路径均相对本地源库 `skills/`。相关模块深入阅读正文与对应参考；不相关模块只核对入口与边界，不声称执行过其程序。

| 源模块 | 提炼内容 / 取舍 | 落点 |
|---|---|---|
| `nature-figure` | 证据作用分工、模板复用层级、渲染几何、图注自足；不继承统一降饱和 | make-model-figures |
| `nature-statistics` | 独立分析单位、重复类型、统计量与区间定义 | analyze-model-data、图表 QA、审稿 |
| `nature-data` | 复现数据版本、来源和访问方式；不自动上传 | analyze-model-data |
| `nature-experiment-log` | 原始材料与运行记录分离、异常与版本关联；不引入实验室设备编码 | solve-model |
| `nature-academic-search` | 检索记录、权威来源和内容支持定位 | research-model-literature |
| `nature-ref-verifier` | 逐字段比对 DOI、标题、作者和版本；修正单次 404 即判错的做法 | research-model-literature |
| `nature-paper-card` | 主张—证据关系、可靠定位、全文/摘要边界；不强制 16 节卡片 | 文献、选模 |
| `nature-literature-pipeline` | 阅读层级、去重、来源降级；不引入固定评分、定时推送 | research-model-literature |
| `nature-citation` | 采用主张对应来源的原则；不限制文献必须来自 Nature/CNS | research-model-literature |
| `nature-reader` | 保留已核实的结构定位和材料范围；不强制生成双语全文 | research-model-literature |
| `nature-writing` | 按读者问题组织论证、措辞对应证据强度 | write-model-paper |
| `nature-polishing` | 语言编辑保持事实、术语和边界 | write-model-paper |
| `nature-shared` | 术语、单位、数值精度和跨图文一致性；修正误差线重叠判据 | 写作、审查 |
| `nature-reviewer` | 主张/证据双定位、严重程度与最小修复 | review-model-paper |
| `nature-response` | 问题—修改—证据—复核闭环；不强制回复信或三审稿人 | review-model-paper |
| `nature-proposal-writer` | 入口核对：研究计划输出超出本次数模核心更新 | 不迁入专用管线 |
| `nature-downloader` | 入口核对：机构访问与批量下载应由具体文献任务决定 | 不迁入浏览器/凭据流程 |
| `nature-paper2ppt` | 入口核对：汇报文件与论文不同 | 不迁入 PPTX 管线 |
| `nature-image2ppt` | 入口核对：截图还原与数模制图不同 | 不迁入重建与图像后端 |
| `nature-paper-to-patent` | 入口核对：专利不是数模论文交付 | 不迁入专利管线 |

图表重点参考了 `nature-figure/static/core/contract.md`、`stance.md`，以及 `references/` 下的 `multipanel-evidence-architecture.md`、`asset-adaptation.md`、`qa-contract.md`、`design-theory.md`、`figure-legend-conventions.md`。写作与审查还参考了 `nature-shared/core/reader-workflow.md`、`consistency-sweep.md` 和各模块 core/入口。

这些是根据本地材料独立编写的决策规则，没有复制其脚本、图形素材、样例数据或大段正文。源库根许可为 Apache-2.0，部分模块另标 MIT；本次不分发源库代码。源库研究经验不作为比赛或期刊的官方规定。

## 特别纠正的规则

- 顺序色标可以随值增大而变亮；移除“深色只能对应较大值”的限制。
- 误差线重叠不能独立判断显著性、无差异或等效。
- Crossref 单次查询失败不能证明文献伪造；DOI 字符串年份也不必等于出版年份。
- 不为强化差异默认收紧柱图基线、逐列归一化热图或使用非线性色标。
- 不把源库的 Python/R 询问、固定审稿人数、外部 API、专属脚本和期刊尺寸要求变成当前技能的依赖。
- 自定义暖色色板只应用于具体绘图对象；`custom:power-energy` 仅是现有 FigureContract 支持的记录名称，不可传给 `get_modeling_palette()`。

## 验证

- 仓库 `scripts/validate_skills.py`：8 个技能通过。
- `skill-creator/scripts/quick_validate.py`：8 个技能逐一通过。
- 暖色参考中的 Python 片段在内存合成输入上执行通过，数据、保存点坐标、色域上下限不变；未写出任何图文件。
- 对色板 256 个采样值计算 sRGB 相对明度，严格递增，端点约为 0.051 和 0.559，无纯黑/纯白。该检查不等于感知均匀性、色觉模拟或实际论文图的视觉验收。
- 最终尺寸、真实数据背景下的标记可读性、色觉模拟仍须在后续实际绘图时检查，本次未宣称通过。

- 22 个新增或修改的技能 Markdown 文件已同步至 `C:\Users\Blake\.codex\skills`，逐文件哈希一致；安装目录下 8 个技能再次通过两套校验。
- 修改文件中的 Markdown 本地链接全部可解析，`git diff --check` 通过。
- 同步前检查安装目录未发生并发修改；仅复制本次涉及的说明文件，保留脚本、运行时和安装元数据。原安装目录仅有 3 个入口缺少仓库已存在的 figure handoff 段落，同步时保留了这些衔接说明。
- 仓库额外新增本记录；已在备份目录保存本次更新文件清单及安装后哈希清单。
