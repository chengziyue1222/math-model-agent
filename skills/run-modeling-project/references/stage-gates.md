# Modeling Project Stage Gates

Stages are strictly ordered. Evidence means an existing project-relative file with a recorded SHA-256 hash; a prose claim is not evidence.

| Enter stage | Required evidence roles | Exit question |
|---|---|---|
| `intake` | none | Has the project been initialized? |
| `analysis` | `problem_source`, `task_decomposition` | Is every subproblem, objective, constraint, datum, unit, and ambiguity explicit? |
| `modeling` | `data_audit`, `model_selection`, `decision_contract` | Is there a leakage-safe data contract, a fair baseline, and a justified model route for every question? |
| `validation` | `implementation`, `machine_results`, `quality_validation`, `run_manifest` | Can the solver be rerun with recorded parameters and seeds, and are balance, uncertainty, baseline, and trade-off checks appropriate to the declared decisions? |
| `writing` | `validation_report`, `quality_validation`, `paper_spec`, `evidence_index`, `claim_registry`, `figure_registry`, `table_registry`, `formula_registry` | Is the project `READY_FOR_DRAFT`, are all proposed claims resolvable, and does each question have a decision-grade result and validation artifact? |
| `review` | `manuscript`, `decision_contract`, `quality_validation`, `figure_inventory`, `paper_review_report`, `run_manifest` | Is the project `DRAFT_GENERATED`; do all hard paper gates pass and are hashes current? |
| `release` | `review_report`, `submission_checklist`, `run_manifest` | Is the project `FORMAL_PAPER_APPROVED`, with no review failure or stale evidence? |

## Transition Rules

- Advance exactly one stage at a time.
- Hash every evidence file when entering a stage.
- Never reuse a stale `run_manifest` record after changing an input or artifact.
- A failed or partial run remains in the manifest and is not silently replaced by a later success.
- A blocker freezes transitions but does not erase completed-stage history.
- Paper status is one of `NOT_READY`, `READY_FOR_DRAFT`, `DRAFT_GENERATED`, `REVIEW_FAILED`, `RETURNED_TO_MODELING`, or `FORMAL_PAPER_APPROVED`. A failed review must return to modeling/validation or writing; it cannot advance to release.
- Gate completion means evidence exists and is internally consistent; it does not guarantee a prize or publication outcome.

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
