# Math Model Skills

数学建模工作流工具集 - 36个Claude Code Skills

## 目录结构

```
skill/
├── core/ (核心skills)
├── latex/ (LaTeX编译相关 - 5个)
├── quarto/ (Quarto/部署 - 3个)
├── paper/ (论文写作与审阅 - 6个)
├── research/ (研究与构思 - 5个)
├── data/ (数据分析 - 4个)
├── lecture/ (讲座/课程 - 3个)
├── workflow/ (工作流 - 10个)
└── audit/ (审计/验证 - 3个)
```

## Skills清单

### LaTeX/编译相关 (5个)
| Skill | 用途 | 用法 |
|-------|------|------|
| /compile-latex | XeLaTeX 3遍编译Beamer | /compile-latex Lecture01 |
| /extract-tikz | 提取TikZ图表 | /extract-tikz Lecture2 |
| /new-diagram | 生成TikZ图表 | /new-diagram DAG output |
| /proofread | 语法拼写检查 | /proofread file.tex |
| /visual-audit | 视觉布局审计 | /visual-audit Lecture01.qmd |

### Quarto/部署 (3个)
| Skill | 用途 | 用法 |
|-------|------|------|
| /deploy | 渲染部署到GitHub Pages | /deploy Lecture1 |
| /translate-to-quarto | LaTeX转Quarto | /translate-to-quarto file.tex |
| /qa-quarto | Quarto质量对比 | /qa-quarto Lecture |

### 论文写作与审阅 (6个)
| Skill | 用途 | 用法 |
|-------|------|------|
| /review-paper | 7维度并行审查 | /review-paper paper.pdf |
| /seven-pass-review | 七遍审稿法 | /seven-pass-review manuscript.pdf |
| /respond-to-referees | 回复审稿人 | /respond-to-referees refs.pdf revised.pdf |
| /humanize | 检测AI写作痕迹 | /humanize file.tex |
| /validate-bib | 验证引用完整性 | /validate-bib -semantic |
| /preregister | 起草预注册文档 | /preregister --style osf |

### 研究与构思 (5个)
| Skill | 用途 | 用法 |
|-------|------|------|
| /lit-review | 结构化文献综述 | /lit-review "主题" |
| /research | 生成研究问题 | /research "话题" |
| /ideation | 多轮访谈形式化 | /ideation "话题" |
| /interview-me | 互动式访谈 | /interview-me "话题" |
| /devils-advocate | 对抗性挑战 | /devils-advocate file.tex |

### 数据分析 (4个)
| Skill | 用途 | 用法 |
|-------|------|------|
| /data-analysis | R数据分析管道 | /data-analysis dataset.csv |
| /review-r | R代码审查 | /review-r scripts.R |
| /audit-reproducibility | 数值声明验证 | /audit-reproducibility paper.pdf |
| /stata-replication | Stata复现管道 | /stata-replication paper.pdf |

### 讲座/课程 (3个)
| Skill | 用途 | 用法 |
|-------|------|------|
| /create-lecture | 创建Beamer讲座 | /create-lecture 主题 |
| /slide-excellence | 综合幻灯片审查 | /slide-excellence file.tex |
| /pedagogy-review | 教学法审查 | /pedagogy-review file.tex |

### 工作流 (10个)
| Skill | 用途 | 用法 |
|-------|------|------|
| /commit | 完整提交流程 | /commit "提交信息" |
| /learn | 提取知识为skill | /learn skill-name |
| /checkpoint | 保存状态快照 | /checkpoint topic |
| /compress-session | 压缩会话笔记 | /compress-session topic |
| /context-status | 会话健康状态 | /context-status |
| /prompt | 结构化prompt执行 | /prompt "想法" |
| /deep-prompt | 生成prompt不执行 | /deep-prompt "想法" |
| /prompt-only | 只生成prompt | /prompt-only "想法" |
| /standard-save | 升级learn条目 | /standard-save path.md |
| /promote-memory | 升级到MEMORY.md | /promote-memory |

### 审计/验证 (3个)
| Skill | 用途 | 用法 |
|-------|------|------|
| /deep-audit | 全仓库深度审计 | /deep-audit |
| /permission-check | 权限配置诊断 | /permission-check |
| /verify-claims | 链式验证声明 | /verify-claims draft.pdf |

## 使用方法

1. 切换到项目目录
2. 输入对应的skill命令
3. 按照提示提供参数

## 核心Skills

详见 `core/` 目录：
- math_model_skill.md - 核心能力
- judge_engine.md - 评判引擎
- model_library.md - 模型库
- model_selector.md - 模型选择器
- modeling_pipeline.md - 建模流程
- paper_generator.md - 论文生成器
- python_mapping.md - Python映射
