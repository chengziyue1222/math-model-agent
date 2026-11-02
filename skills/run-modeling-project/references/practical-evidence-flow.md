# 实用图表与项目证据闭环

分析开始即在现有 figure_plan/result_object 中记录对应问题或结论、数据路径/字段、单位、图型、转换和视觉状态。求解保存完整对象与情景结果，绘图读取保存结果，写作核对正文/摘要/图注/表格数字。复用 decision_contract、quality_validation、evidence_index 与图元数据，不建立重复登记系统。

`profile` 是过程强度，`venue` 是交付规则。新状态 1.2 默认通用报告；国赛需明确 `--venue CUMCM`。共享 `resolve_project_venue` 读取状态与 config/venue.yaml；冲突拒绝。旧状态 1.0/1.1 可读取，推进前 `project_state.py set-venue --venue ...`。契约 1.5 用 layout_validation，1.1—1.4 按旧规则读取；国赛兼容旧 cumcm_layout_validation，其他赛事不套用它。

阶段按 intake→analysis→modeling→validation→writing→review→release。进入 review 提供稿件、渲染与审查输入；完成审查后进入 release 才提供 paper_review_report、submission_readiness、submission_preflight 等结果。语义门检查逐问结果、质量要求、真实报告状态；失败保留 failed_gates，不删除诊断。

返工执行 `project_state.py rewind --to <stage> --reason <原因>`。保留文件和历史，撤销目标及下游完成标记，记录 stale_evidence；修复目标阶段的产物后重新推进。competition 对已登记的关键输入输出存哈希，避免旧结论沿用；audit 保留签名和完整目录复核。不要修改旧哈希来伪造通过。

图型细节由 make-model-figures/references/practical-figures.md 按需读取。阶段入口只维护职责与交接，不要求每问固定数量的图表或所有题型都有优化术语。
