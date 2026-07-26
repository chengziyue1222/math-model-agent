# 数学建模论文结构

For `competition_paper`, use the following mandatory order: 摘要、关键词、问题重述、问题分析、模型总体框架、模型假设、符号说明、数据预处理与探索性分析、问题一至五的模型/求解/验证、模型评价、最终建议、参考文献、附录、复现说明。

1. 摘要：逐个子问题给出方法、关键结果、验证和结论，不写空泛背景。
2. 问题重述与分析：明确任务、输入输出和子问题关系。
3. 模型假设：逐条说明理由、适用范围和可能影响。
4. 符号说明：统一符号、单位、维度和代码变量名。
5. 模型建立：给出目标、约束、推导和模型选择理由。
6. 求解方法：说明算法、参数、初始化、停止条件和软件环境。
7. 结果与验证：报告基线、误差、敏感性、稳健性和不确定性。
8. 讨论：解释机制、优势、局限、失败条件和可迁移性。
9. 参考文献：只保留真实、可核验且正文使用的来源。
10. 附录：放置复现所需代码、补充推导和数据说明。

建立“结论—表格/图—结果文件—代码入口”映射。任何无法追溯的数字都不得进入终稿。

Competition mode has a minimum of 10 numbered explained formulas, 8 body figures, 6 body tables, one framework diagram, one notation table, a sensitivity table, a robustness table, and 8 verifiable references. Each key number appears with `[claim:CLAIM_ID]`.
