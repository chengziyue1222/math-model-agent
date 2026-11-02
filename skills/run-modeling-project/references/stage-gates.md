# Modeling Project Stage Gates

Stages are strictly ordered. All evidence paths are project-relative. Competition hashes registered key artifacts and checks semantic validation; audit additionally retains full signed runtime evidence. Use `references/practical-evidence-flow.md` for migration and rewind.

| Enter stage | Required evidence roles | Exit question |
|---|---|---|
| `intake` | none | Has the project been initialized? |
| `analysis` | `problem_source`, `task_decomposition` | Is every subproblem, objective, constraint, datum, unit, and ambiguity explicit? |
| `modeling` | `data_audit`, `model_selection`, `decision_contract` | Is there a leakage-safe data contract, a fair baseline, and a justified model route for every question? |
| `validation` | `implementation`, `machine_results`, `quality_validation`, `run_manifest` | Can the solver be rerun with recorded parameters and seeds, and are balance, uncertainty, baseline, and trade-off checks appropriate to the declared decisions? |
| `writing` | Competition: `validation_report`, `quality_validation`, `paper_spec`, `evidence_index`, `figure_registry`. Audit adds `claim_registry`, `table_registry`, `formula_registry`. | Is the project `READY_FOR_DRAFT`, and does each question have a decision-grade result and validation artifact? |
| `review` | Manuscript, PDF or DOCX and render report, `decision_contract`, `quality_validation`, `figure_inventory`, `layout_validation`, `visual_layout_audit`, `run_manifest`; support archive/manifest only when venue requires them. Audit adds both formats, producer registry and signed trace. | Are the draft and review inputs ready for review? |
| `release` | `paper_review_report`, `submission_readiness`, `submission_preflight`, `submission_checklist`, `run_manifest`; `reproduction_report` when support is required. Audit adds independent review and hash binding. | Did actual review and delivery checks pass, with no failed or stale evidence? |

## Transition Rules

- Advance exactly one stage at a time.
- In competition and audit, revalidate registered key artifact hashes before every transition. Rewind preserves files/history and marks affected outputs stale; never update an old accepted hash to hide changed data.
- When a later gate reuses the same hashed file for the same role, retain its verified production stage. Changing its path or contents requires fresh producer evidence; citing an upstream contract in a paper does not turn it into a writing-stage output.
- Apply the profile's Skill role contract before execution. Rapid has no complete role-contract obligation; audit retains the complete contract. A required preflight failure is recorded as `BLOCKED`.
- Never reuse a stale `run_manifest` record after changing an input or artifact; audit proves this with full hashes.
- A failed or partial run remains in the manifest and is not silently replaced by a later success.
- A blocker freezes transitions but does not erase completed-stage history.
- Paper status is one of `NOT_READY`, `READY_FOR_DRAFT`, `DRAFT_GENERATED`, `REVIEW_FAILED`, `RETURNED_TO_MODELING`, or `FORMAL_PAPER_APPROVED`. A failed review must return to modeling/validation or writing; it cannot advance to release.
- Gate completion means evidence exists and is internally consistent; it does not guarantee a prize or publication outcome.
- Scope a stage trace check to its required Skills; pending downstream runs do not invalidate an upstream retry. Final release must explicitly validate all eight Skills and their current file bindings. Trace authentication still covers historical events.

## Recommended Artifact Paths

Use stable names where practical:

```text
docs/problem-source.md
docs/task-decomposition.md
reports/data-audit.json
docs/model-selection.md
reports/decision-contract.json
src/solve.py
results/results.json
run-manifest.json
reports/validation.json
reports/quality-validation.json
reports/sensitivity.json
paper/main.tex
figures/figure-inventory.json
reports/review.md
reports/submission-checklist.md
```
