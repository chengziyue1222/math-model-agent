# Math Model Agent

> **数学建模 AI 助手** — 55 个 Slash Commands + 15 个算法模块，覆盖从选题到答辩的完整竞赛工作流。
>
> An AI-powered toolkit for mathematical modeling competitions: 55 slash commands + 15 algorithm modules, covering the full workflow from problem selection to final presentation.

---

## 功能特性 / Features

### 🧮 算法库 / Algorithm Library (`code/algorithms/`)

| 模块 | 核心方法 | 竞赛场景 |
|------|---------|---------|
| `ahp.py` | AHP、CR 检验 | 多准则决策、权重分配 |
| `grey_system.py` | GM(1,1)、灰色关联 | 小样本预测、因素分析 |
| `regression.py` | 多元回归、岭回归、Lasso、Logistic | 数据拟合、因果分析、二分类 |
| `interpolation.py` | Lagrange、样条、径向基 | 曲面重建、缺失值填补 |
| `graph_theory.py` | Dijkstra、Floyd、Kruskal、最小费用流、图染色、Euler路径、匈牙利匹配 | 最短路径、网络优化、指派问题 |
| `fuzzy_math.py` | 隶属函数、模糊评价 | 不确定性建模 |
| `neural_network.py` | BP、RBF、SVM、MIV变量重要性 | 分类、回归、特征筛选 |
| `metaheuristic.py` | GA、SA、PSO、蚁群 | 组合优化、参数搜索 |
| `cellular_automata.py` | 1D/2D CA、生命游戏、NaSch交通流 | 交通流、传染病扩散、森林火灾 |
| `monte_carlo.py` | 积分、优化、M/M/c、M/M/S/k、随机游走 | 随机模拟、风险分析、排队论 |
| `image_processing.py` | 边缘检测、分割、形态学 | 遥感、医学影像 |
| `time_series.py` | 移动平均、指数平滑、趋势外推、自适应滤波 | 趋势预测、信号去噪 |
| `math_programming.py` | 线性规划、整数规划、目标规划、非线性规划 | 资源分配、背包问题、选址 |
| `evaluation.py` | TOPSIS、DEA、PCA、RSR | 综合评价、效率分析 |
| `sci_figures.py` | 11 种科研图表 | 论文可视化 |
| `diagram.py` | TikZ 图表生成 | LaTeX 配图 |
| `paper_check.py` | 论文质量检查 | 格式、引用、一致性 |

**快速使用 / Quick Start:**

```python
from algorithms import monte_carlo_integration, edge_detection, topsis

# 蒙特卡罗积分
result = monte_carlo_integration(lambda x: x**2, 0, 1)

# 图像边缘检测
edges = edge_detection(image, method='canny')

# TOPSIS 综合评价
rank = topsis(decision_matrix, weights, benefit_indicators)
```

### 🎯 Skills 体系 / Slash Commands (`skill/`)

**16 个核心建模 Skills (`skill/core/`):**

| Skill | 用途 |
|-------|------|
| `/math-model-skill` | 五层能力架构总控 |
| `/model-selector` | 18 种问题类型→模型决策 |
| `/model-library` | 15 个模块模型库速查 |
| `/modeling-pipeline` | 11 步统一建模流程 |
| `/judge-engine` | 六维度评审引擎 |
| `/paper-generator` | 结构化论文生成 |
| `/python-mapping` | MATLAB→Python 映射 |
| `/evaluation` | 综合评价方法指南 |
| `/monte-carlo` | 蒙特卡罗决策与模板 |
| `/image-processing` | 图像处理流水线 |
| `/sci-figures` | 11 种科研图表规范 |
| `/math-competition-guide` | 竞赛实战全流程 |
| `/modeling-norms` | 建模规范与最佳实践 |
| `/paper-check` | 论文质量检查清单 |
| `/diagram-tools` | TikZ/图表工具指南 |
| `/model-library-extended` | 扩展模型库 |

**39 个专业 Skills:**

| 分类 | 数量 | 典型命令 |
|------|------|---------|
| LaTeX 编译 | 5 | `/compile-latex`, `/extract-tikz` |
| 论文写作 | 6 | `/review-paper`, `/seven-pass-review` |
| 研究构思 | 5 | `/lit-review`, `/ideation` |
| 数据分析 | 4 | `/data-analysis`, `/audit-reproducibility` |
| Quarto 部署 | 3 | `/deploy`, `/translate-to-quarto` |
| 讲座课程 | 3 | `/create-lecture`, `/slide-excellence` |
| 工作流 | 10 | `/commit`, `/checkpoint`, `/learn` |
| 审计验证 | 3 | `/deep-audit`, `/verify-claims` |

### 📐 国赛论文排版模板 / CUMCM Paper Template (`template/`)

从校赛获奖论文中提炼的国赛标准排版规范，开箱即用：

| 排版要素 | 实现方式 |
|---------|---------|
| 一级标题 | 居中 16pt 黑体，中文数字编号（一、二、三...）自动生成 |
| 二级/三级标题 | 左对齐正文黑体，阿拉伯数字编号（1.1 / 1.1.1） |
| 正文引用 | `\cite{key}` 自动渲染为右上角角标 `[1]` |
| 参考文献 | `thebibliography` 按正文中首次引用顺序排列 |
| 附录代码框 | `pycode` 环境：10.5pt 等宽字体、行号、灰背景、单线框 |
| 图表 | 图题在下居中、表题在上居中、三线表、`\tabnote{}` 表注 |

编译方式：`xelatex` × 2（无需 bibtex）

### 📋 竞赛工作流 / Competition Workflow

```
Day 1: 选题分析 → 文献调研 → 问题拆解
Day 2: 模型假设 → 数学推导 → 方案设计
Day 3: 编程求解 → 数据处理 → 敏感性分析
Day 4: 论文撰写 → 图表制作 → 结果验证
Day 5: 全文审校 → 格式排版 → 最终检查
```

---

## 项目结构 / Project Structure

```
math-model-agent/
│
├── code/                            # 🔧 代码模块
│   ├── algorithms/                  # 15 个 Python 算法模块（可直接 import）
│   │   ├── __init__.py              # 统一导出入口，from algorithms import * 即用
│   │   ├── ahp.py                   # 层次分析法：AHP 构造、一致性检验 CR
│   │   ├── grey_system.py           # 灰色系统：GM(1,1) 预测、灰色关联分析
│   │   ├── regression.py            # 回归分析：多元回归、岭回归、Lasso
│   │   ├── interpolation.py         # 插值拟合：Lagrange、样条、径向基
│   │   ├── graph_theory.py          # 图论算法：Dijkstra、Floyd、Kruskal 最小生成树
│   │   ├── fuzzy_math.py            # 模糊数学：隶属函数、模糊综合评价
│   │   ├── neural_network.py        # 神经网络：BP、RBF、SVM
│   │   ├── metaheuristic.py         # 元启发式优化：遗传算法 GA、模拟退火 SA、粒子群 PSO、蚁群
│   │   ├── cellular_automata.py     # 元胞自动机：1D/2D CA、生命游戏
│   │   ├── monte_carlo.py           # 蒙特卡罗：积分、优化、排队系统、随机游走
│   │   ├── image_processing.py      # 图像处理：边缘检测、分割、形态学
│   │   ├── evaluation.py            # 综合评价：TOPSIS、DEA、PCA、RSR
│   │   ├── sci_figures.py           # 科研图表：11 种标准科研可视化
│   │   ├── diagram.py               # TikZ 图表生成：LaTeX 配图自动化
│   │   ├── paper_check.py           # 论文检查：格式、引用、一致性审查
│   │   ├── time_series.py           # 时间序列：移动平均、指数平滑、趋势外推
│   │   └── math_programming.py      # 数学规划：线性/整数/目标/非线性规划
│   ├── solve.py                     # 求解脚本示例（2022 国赛 A 题波浪能）
│   ├── visualize.py                 # 可视化示例脚本
│   └── results.json                 # 求解结果存档
│
├── skill/                           # 🎯 55 个 Slash Commands（Claude Code Skills）
│   ├── README.md                    # Skills 索引与使用说明
│   │
│   ├── core/                        # 📦 16 个核心建模 Skills
│   │   ├── math_model_skill.md      # 五层能力架构总控
│   │   ├── model_selector.md        # 18 种问题类型 → 模型决策树
│   │   ├── model_library.md         # 15 个模块模型库速查
│   │   ├── model_library_extended.md# 扩展模型库（更多方法）
│   │   ├── modeling_pipeline.md     # 11 步统一建模流程
│   │   ├── modeling_norms.md        # 建模规范与最佳实践
│   │   ├── judge_engine.md          # 六维度评审引擎
│   │   ├── paper_generator.md       # 结构化论文生成
│   │   ├── paper_check.md           # 论文质量检查清单
│   │   ├── python_mapping.md        # MATLAB → Python 映射表
│   │   ├── evaluation.md            # 综合评价方法指南
│   │   ├── monte_carlo.md           # 蒙特卡罗决策与模板
│   │   ├── image_processing.md      # 图像处理流水线
│   │   ├── sci_figures.md           # 11 种科研图表规范
│   │   ├── diagram_tools.md         # TikZ / 图表工具指南
│   │   └── math_competition_guide.md# 竞赛实战全流程指南
│   │
│   ├── latex/                       # 📄 5 个 LaTeX 编译 Skills
│   │   ├── compile-latex.md         # XeLaTeX 自动编译（含错误修复重试）
│   │   ├── extract-tikz.md          # 提取 TikZ 图表转 SVG
│   │   ├── new-diagram.md           # 从模板生成 TikZ 图表
│   │   ├── proofread.md             # 语法拼写检查
│   │   └── visual-audit.md          # 视觉布局审计
│   │
│   ├── paper/                       # ✍️ 6 个论文写作 Skills
│   │   ├── review-paper.md          # 论文审阅（七维度）
│   │   ├── seven-pass-review.md     # 七遍审稿法
│   │   ├── validate-bib.md          # 参考文献一致性检查
│   │   ├── humanize.md              # AI 痕迹消除、人味润色
│   │   ├── preregister.md           # 预注册研究方案
│   │   └── respond-to-referees.md   # 审稿回复信撰写
│   │
│   ├── research/                    # 🔬 5 个研究构思 Skills
│   │   ├── lit-review.md            # 文献综述系统梳理
│   │   ├── ideation.md              # 研究选题与创意生成
│   │   ├── interview-me.md          # 苏格拉底式提问引导
│   │   ├── devils-advocate.md       # 魔鬼代言人（挑刺反驳）
│   │   └── research.md              # 研究设计全流程
│   │
│   ├── data/                        # 📊 4 个数据分析 Skills
│   │   ├── data-analysis.md         # 数据清洗 / EDA / 统计检验 / 特征工程
│   │   ├── audit-reproducibility.md # 可复现性审计
│   │   ├── review-r.md              # R 代码审查
│   │   └── stata-replication.md     # Stata 复现映射
│   │
│   ├── quarto/                      # 🌐 3 个 Quarto 部署 Skills
│   │   ├── deploy.md                # 部署到 GitHub Pages
│   │   ├── translate-to-quarto.md   # LaTeX → Quarto 转换
│   │   └── qa-quarto.md             # Quarto 质量对比检查
│   │
│   ├── lecture/                     # 🎓 3 个讲座课程 Skills
│   │   ├── create-lecture.md        # 课程/讲座创建
│   │   ├── pedagogy-review.md       # 教学法审查
│   │   └── slide-excellence.md      # 幻灯片优化
│   │
│   ├── workflow/                    # ⚙️ 10 个工作流 Skills
│   │   ├── commit.md                # Git 智能提交
│   │   ├── checkpoint.md            # 检查点保存
│   │   ├── learn.md                 # 学习模式
│   │   ├── prompt.md                # 提示词优化
│   │   ├── deep-prompt.md           # 深度提示词
│   │   ├── prompt-only.md           # 仅提示词模式
│   │   ├── compress-session.md      # 会话压缩
│   │   ├── context-status.md        # 上下文状态查看
│   │   ├── promote-memory.md        # 记忆提升
│   │   └── standard-save.md         # 标准保存
│   │
│   └── audit/                       # 🔍 3 个审计验证 Skills
│       ├── deep-audit.md            # 深度审计
│       ├── verify-claims.md         # 声明验证
│       └── permission-check.md      # 权限检查
│
├── template/                        # 📐 国赛 LaTeX 论文排版模板
│   └── cume-template.tex            # 完整模板（标题等级/角标引用/代码框/三线表）
│
├── patterns/                        # 📝 6 个获奖论文模式库
│   ├── abstract_patterns.md         # 摘要写作模式（问题→方法→结果→关键词）
│   ├── model_selection_rules.md     # 模型选择决策规则
│   ├── discussion_rules.md          # 讨论/分析写作规范
│   ├── evaluation_rules.md          # 模型评价写作规范
│   ├── appendix_rules.md            # 附录代码排版规范
│   └── visual_rules.md             # 图表可视化规范
│
├── data/                            # 📁 示例数据集（空，竞赛时放入题目数据）
├── figures/                         # 🖼️ 示例图表（2022 国赛 A 题波浪能配图）
│   ├── fig01_time_history.png       # 时序图
│   ├── fig02_power_vs_damping.png   # 功率-阻尼关系图
│   ├── fig03_power_heatmap.png      # 功率热力图
│   └── fig04_sensitivity.png        # 敏感性分析图
├── paper/                           # 📄 论文输出目录（空，编译产物存放处）
│
├── 使用说明.md                      # 📖 完整使用指南（含工作流演示）
├── CHANGELOG.md                     # 📋 版本历史（v1.0 ~ v6.1）
└── README.md                        # 📖 本文件
```

---

## 快速开始 / Getting Started

### 1. 克隆仓库 / Clone

```bash
git clone https://github.com/<your-username>/math-model-agent.git
cd math-model-agent
```

### 2. 安装依赖 / Install Dependencies

```bash
pip install numpy scipy matplotlib pandas scikit-learn networkx
```

### 3. 使用算法库 / Use Algorithm Library

```python
import sys
sys.path.insert(0, 'code')
from algorithms import *

# AHP 层次分析法
weights, CR = ahp(comparison_matrix)

# GM(1,1) 灰色预测
predicted = gm11(data, predict_count=5)

# 遗传算法优化
best_x, best_f = genetic_algorithm(objective, bounds)
```

### 4. 使用 Skills / Use Skills

在 Claude Code 中切换到项目目录，直接输入 slash command：

```
> /model-selector "某城市交通流量预测问题"
> /math-competition-guide
> /monte-carlo "排队系统仿真"
```

---

## 蒸馏来源 / Distillation Sources

| 来源 | 内容 | 贡献 |
|------|------|------|
| 司守奎《数学建模算法与应用》第3版 | 534页，16章 | 模型决策引擎、统一建模流程、Python 映射 |
| zhanwen/MathModel (10,588⭐) | 32 张思维导图、竞赛论文 | 10 大算法类别、竞赛工作流 |
| MathModelAgent | 6 阶段工作流 | 科研图表模板、论文校验 |
| Giyn/MathematicalModelingAlgorithm | TOPSIS/DEA/PCA/RSR | 综合评价方法实现 |
| 国赛/美赛获奖论文 (12篇) | 实战模式提炼 | 摘要模板、验证体系、讨论结构 |

---

## 竞赛覆盖 / Competition Coverage

- ✅ 全国大学生数学建模竞赛 (CUMCM)
- ✅ 美国大学生数学建模竞赛 (MCM/ICM)
- ✅ 研究生数学建模竞赛
- ✅ MathorCup、华为杯等企业赛事

---

## 版本历史 / Changelog

- **v6.0** (2026-07-08) — 蒸馏 zhanwen/MathModel + MathModelAgent，新增蒙特卡罗、图像处理、综合评价、竞赛工作流
- **v5.0** (2026-06-16) — 部署 CodeBuddy 论文 Skills + 数学建模 Skills，总计 55 个 slash commands
- **v4.0** (2026-06-16) — 整合 36 个 Claude Code Skills
- **v3.0** (2026-06-15) — 蒸馏《数学建模算法与应用》教材
- **v2.0** (2026-06-15) — 融合获奖论文模式库

详见 [CHANGELOG.md](CHANGELOG.md)。

---

## 许可证 / License

MIT
