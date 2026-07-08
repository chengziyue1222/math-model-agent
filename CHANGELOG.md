# CHANGELOG - Math Model Skill

## v6.1 (2026-07-01)

### 新增

- **template/cume-template.tex** — 国赛论文 LaTeX 排版模板（从校赛获奖论文提炼）
  - 标题等级：一级标题居中中文数字编号，二三级标题左对齐阿拉伯编号
  - 参考文献：`\cite{}` 自动右上角角标，按首次引用顺序排列
  - 附录代码框：`pycode` 环境（行号、灰背景、关键字加粗）
  - 图表格式：三线表、表注命令、中文标签
- 更新 `/mm-paper` 命令：引用模板 + 排版规范指引
- 更新 `/compile-latex` 命令：`thebibliography` 编译策略 + 格式检查点

## v4.0 (2026-06-16)

### 新增

整合36个Claude Code Skills，形成完整的学术工作流工具集：

1. **skill/latex/** — LaTeX编译相关（5个）
   - compile-latex: XeLaTeX 3遍编译Beamer
   - extract-tikz: 提取TikZ图表转SVG
   - new-diagram: 从模板生成TikZ图表
   - proofread: 语法拼写检查
   - visual-audit: 视觉布局审计

2. **skill/quarto/** — Quarto/部署（3个）
   - deploy: 部署到GitHub Pages
   - translate-to-quarto: LaTeX转Quarto
   - qa-quarto: Quarto质量对比

3. **skill/paper/** — 论文写作与审阅（6个）
   - review-paper: 7维度并行审查
   - seven-pass-review: 七遍审稿法
   - respond-to-referees: 回复审稿人
   - humanize: 检测AI写作痕迹
   - validate-bib: 验证引用完整性
   - preregister: 起草预注册文档

4. **skill/research/** — 研究与构思（5个）
   - lit-review: 结构化文献综述
   - research: 生成研究问题
   - ideation: 多轮访谈形式化
   - interview-me: 互动式访谈
   - devils-advocate: 对抗性挑战

5. **skill/data/** — 数据分析（4个）
   - data-analysis: R数据分析管道
   - review-r: R代码审查
   - audit-reproducibility: 数值声明验证
   - stata-replication: Stata复现管道

6. **skill/lecture/** — 讲座/课程（3个）
   - create-lecture: 创建Beamer讲座
   - slide-excellence: 综合幻灯片审查
   - pedagogy-review: 教学法审查

7. **skill/workflow/** — 工作流（10个）
   - commit: 完整提交流程
   - learn: 提取知识为skill
   - checkpoint: 保存状态快照
   - compress-session: 压缩会话笔记
   - context-status: 会话健康状态
   - prompt: 结构化prompt执行
   - deep-prompt: 生成prompt不执行
   - prompt-only: 只生成prompt
   - standard-save: 升级learn条目
   - promote-memory: 升级到MEMORY

8. **skill/audit/** — 审计/验证（3个）
   - deep-audit: 全仓库深度审计
   - permission-check: 权限配置诊断
   - verify-claims: 链式验证声明

### 优化

- 重构skill目录结构，按功能分类
- 创建skill/README.md主索引文件
- 更新使用说明.md，添加36个skills完整清单

---

## v3.0 (2026-06-15)

### 融合来源

- `E:\论文\数学建模算法与应用(OCR) 司守奎 第3版教材.pdf` — 534页教材，16章，覆盖LP/IP/NLP/图论/插值拟合/微分方程/数理统计/差分方程/SVM/多元统计/PLSR/智能优化/综合评价/预测方法/多目标规划

### 新增

1. **skill/model_selector.md** — 模型决策引擎 v2.0
   - 8大问题类型决策规则（规划/预测/评价/图网络/统计/微分方程/智能优化/SVM）
   - 每个模型含：IF-THEN决策规则、主模型+辅助模型+验证模型组合、Python实现代码
   - 新增：灰色预测GM(1,1)、马尔可夫预测、层次聚类(Ward法)、TOPSIS、模糊综合评价、ε约束法、目标规划、模拟退火、遗传算法

2. **skill/modeling_pipeline.md** — 统一建模流程 v2.0
   - 11步标准化流程：问题理解→假设→变量→目标→约束→模型选择→求解→验证→敏感性分析→结果解释→论文输出
   - 每步含：目标、执行步骤、输出要求、检查清单

3. **skill/python_mapping.md** — Matlab→Python工程化映射
   - 核心库对照表（linprog/fmincon/intlinprog/ode45/SVM/KMeans/PCA等）
   - 8个常用算法Python实现（线性规划/非线性规划/整数规划/ODE/GM(1,1)/TOPSIS/层次聚类/遗传算法）
   - 工程目录结构规范（data/src/model/report/）

### 优化

1. **skill/judge_engine.md** — 评审引擎升级至 v3.0
   - 评分权重调整：模型质量30(+5)、验证完整性25(+5)、创新性20、表达质量15(+5)、工程质量10
   - 新增检查项：模型合理性、参数解释、实验可信度、结果可迁移性
   - 三级验证要求明确化（解析+数值+仿真）

2. **patterns/model_selection_rules.md** — 模型选择规则库扩充
   - 新增教材来源的模型：LP/IP/NLP/多目标规划/GM(1,1)/马尔可夫/层次聚类/TOPSIS/模糊评价/PCA/DEA/SVM/模拟退火/遗传算法

### 保留

1. 所有v2.0文件完整保留
2. 波浪能项目实战经验完整保留

### 废弃

- 无：本次为教材知识蒸馏融合，不删除任何已有能力

### 原因

- 输入：司守奎《数学建模算法与应用》第3版（534页，16章）
- 目标：将教材方法论与获奖论文经验融合，形成完整的模型决策+工程实现能力
- 效果：模型覆盖从10类扩展至18类，新增统一建模流程和Python工程化映射

---

## v2.0 (2026-06-15)

### 融合来源

- `E:\论文\patterns\` — 6个模式库文件（摘要/模型选择/评估验证/图表/讨论/附录）
- `E:\论文\skill\` — 4个核心能力文件（math_model_skill/paper_generator/judge_engine/model_library）
- `E:\论文\report\` — 3个评审报告（paper_review/score_report/upgrade_report）
- `C:\Users\Blake\math-model\` — 已有波浪能项目实战经验

### 新增

1. **patterns/ 目录** — 6个模式库文件
   - `abstract_patterns.md` — 3种摘要模板（递进式/框架式/方法导向式）
   - `model_selection_rules.md` — 问题类型→模型映射决策树
   - `evaluation_rules.md` — 三级验证体系（解析/数值/仿真）
   - `visual_rules.md` — 学术图表风格规范
   - `discussion_rules.md` — 四层讨论结构（结果→对比→策略→局限）
   - `appendix_rules.md` — 附录内容与代码规范

2. **skill/ 目录** — 4个核心能力文件
   - `math_model_skill.md` — 五层能力架构（问题理解→模型选择→模型构建→求解验证→表达输出）
   - `paper_generator.md` — 结构化论文生成引擎
   - `judge_engine.md` — 六维度评审体系（100分制）+ 自动修正流程
   - `model_library.md` — 10类模型库（几何/优化/决策/数据/微分方程/搜索/成分数据/时间序列/统计/路径）

3. **使用说明.md 更新**
   - 新增附录B：核心能力文件详解
   - 新增附录D：模式库详解
   - 更新目录结构，增加 skill/ 和 patterns/ 目录

### 优化

1. **模型选择流程** — 建立问题特征→模型映射决策树，明确模型组合策略
2. **结果表达规范** — 图表必须有结论/洞察，学术风格统一，禁止默认样式
3. **讨论分析结构** — 四层讨论结构，一般性策略提炼，局限性讨论
4. **评审能力** — 六维度评审体系，自动评分与缺陷定位，最多3轮自动修正

### 保留

1. 波浪能项目的 analysis.md、model.md、code/、figures/ 完整保留
2. 使用说明.md 的阶段1-10工作流完整保留
3. 使用说明.md 的阶段11-14速查内容完整保留（已与新文件交叉引用）

### 废弃

- 无：本次为融合升级，不删除任何已有能力

### 原因

- 输入：E:\论文 下12篇获奖论文蒸馏的模式库、能力文件、评审报告
- 目标：将论文蒸馏成果与波浪能项目实战经验融合，形成完整的数学建模能力体系
- 效果：能力从单一项目经验扩展为可迁移的通用建模能力
