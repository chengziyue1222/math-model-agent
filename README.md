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
| `regression.py` | 多元回归、岭回归、Lasso | 数据拟合、因果分析 |
| `interpolation.py` | Lagrange、样条、径向基 | 曲面重建、缺失值填补 |
| `graph_theory.py` | Dijkstra、Floyd、Kruskal | 最短路径、网络优化 |
| `fuzzy_math.py` | 隶属函数、模糊评价 | 不确定性建模 |
| `neural_network.py` | BP、RBF、SVM | 分类、回归、模式识别 |
| `metaheuristic.py` | GA、SA、PSO、蚁群 | 组合优化、参数搜索 |
| `cellular_automata.py` | 1D/2D CA、生命游戏 | 交通流、传染病扩散 |
| `monte_carlo.py` | 积分、优化、排队、随机游走 | 随机模拟、风险分析 |
| `image_processing.py` | 边缘检测、分割、形态学 | 遥感、医学影像 |
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
├── code/
│   ├── algorithms/          # 15 个 Python 算法模块
│   │   ├── __init__.py      # 统一导出入口
│   │   ├── ahp.py           # 层次分析法
│   │   ├── grey_system.py   # 灰色系统
│   │   ├── regression.py    # 回归分析
│   │   ├── interpolation.py # 插值拟合
│   │   ├── graph_theory.py  # 图论算法
│   │   ├── fuzzy_math.py    # 模糊数学
│   │   ├── neural_network.py# 神经网络
│   │   ├── metaheuristic.py # 元启发式
│   │   ├── cellular_automata.py # 元胞自动机
│   │   ├── monte_carlo.py   # 蒙特卡罗
│   │   ├── image_processing.py # 图像处理
│   │   ├── evaluation.py    # 综合评价
│   │   ├── sci_figures.py   # 科研图表
│   │   ├── diagram.py       # TikZ 图表
│   │   └── paper_check.py   # 论文检查
│   ├── solve.py             # 求解脚本示例
│   └── visualize.py         # 可视化示例
├── skill/
│   ├── core/                # 16 个核心建模 Skills
│   ├── latex/               # LaTeX 编译 (5)
│   ├── paper/               # 论文写作 (6)
│   ├── research/            # 研究构思 (5)
│   ├── data/                # 数据分析 (4)
│   ├── quarto/              # Quarto 部署 (3)
│   ├── lecture/             # 讲座课程 (3)
│   ├── workflow/             # 工作流 (10)
│   └── audit/               # 审计验证 (3)
├── patterns/                # 6 个模式库
├── data/                    # 示例数据
├── figures/                 # 示例图表
├── paper/                   # 论文模板
├── 使用说明.md              # 完整使用指南
├── CHANGELOG.md             # 版本历史
└── README.md                # 本文件
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
