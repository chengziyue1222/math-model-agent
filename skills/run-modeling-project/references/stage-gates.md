# Modeling Project Stage Gates

Stages are strictly ordered. Evidence means an existing project-relative file with a recorded SHA-256 hash; a prose claim is not evidence.

| Enter stage | Required evidence roles | Exit question |
|---|---|---|
| `intake` | none | Has the project been initialized? |
| `analysis` | `problem_source`, `task_decomposition` | Is every subproblem, objective, constraint, datum, unit, and ambiguity explicit? |
| `modeling` | `data_audit`, `model_selection` | Is there a leakage-safe data contract, a baseline, and a justified model route? |
| `validation` | `implementation`, `machine_results`, `run_manifest` | Can the solver be rerun with recorded parameters and seeds? |
| `writing` | `validation_report`, `sensitivity_report` | Do baselines, boundary checks, robustness, and independent checks support the claims? |
| `review` | `manuscript`, `figure_inventory`, `run_manifest` | Are all important numbers and figures traceable to verified artifacts? |
| `release` | `review_report`, `submission_checklist`, `run_manifest` | Are blockers resolved and competition-specific submission rules checked? |

## Transition Rules

- Advance exactly one stage at a time.
- Hash every evidence file when entering a stage.
- Never reuse a stale `run_manifest` record after changing an input or artifact.
- A failed or partial run remains in the manifest and is not silently replaced by a later success.
- A blocker freezes transitions but does not erase completed-stage history.
- Gate completion means evidence exists and is internally consistent; it does not guarantee a prize or publication outcome.

## Recommended Artifact Paths

Use stable names where practical:

```text
docs/problem-source.md
docs/task-decomposition.md
reports/data-audit.json
docs/model-selection.md
src/solve.py
results/results.json
run-manifest.json
reports/validation.json
reports/sensitivity.json
paper/main.tex
figures/figure-inventory.json
reports/review.md
reports/submission-checklist.md
```
