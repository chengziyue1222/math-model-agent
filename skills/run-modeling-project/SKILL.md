---
name: run-modeling-project
description: Coordinate a mathematical-modeling project from problem intake through analysis, model selection, solution, figures, paper, review and delivery. Use when Codex needs to organize a complete modeling workflow or hand off between modeling Skills.
---

# Run Modeling Project

Coordinate the existing Skills around a strong final paper. The project record supports reproducibility, but it is not a second product or a substitute for modeling.

## Workflow

1. Read `references/workflow-profiles.md` and choose `rapid`, `competition` (the default), or `audit` before creating deliverables.
2. Record the problem, data sources, deliverables and venue constraints. Apply CUMCM-only layout rules only when that venue requires them.
3. Invoke `analyze-model-data` where data is used and `select-model` for decomposition, dependency analysis and structure opportunities. Invoke `research-model-literature` when external facts, parameters, datasets, or citations affect a claim.
4. Invoke `solve-model` for equations, algorithms, baselines, constraints, sensitivity and independent checks.
5. Invoke `make-model-figures` only after identifying the conclusions each figure must establish.
6. Invoke `write-model-paper` to turn verified results into a contest paper, then `review-model-paper` for reader-visible and technical review.
7. Render and inspect the final PDF when the selected profile requires a paper; revise the original Skill outputs rather than creating a parallel demonstration workflow.

## Priority Order

1. final paper quality and layout;
2. modeling and reasoning;
3. validation and consistency;
4. engineering convenience.

Read `references/paper-first-flow.md` for the actual handoff order. Existing manifests, stage gates and validations are permitted as backstage controls; their terms and traces do not belong in the submitted paper. In `rapid`, retain the non-negotiables but defer audit-only artifacts; do not label the result as formally verified.

## Handoff Minimums

- analysis → selection: question decomposition, data/units, constraints and dependencies;
- selection → solution: model rationale, rejected alternatives, baseline and validation plan;
- solution → figures/writing: results, formulas, source tables, validations and limitations;
- figures → writing: claim, source, figure role, final artifact and interpretation;
- writing → review: manuscript, PDF, sources and a list of evidence used.

## Executable Contract

For repository-managed `competition` and `audit` projects, inspect the shared contract registry with `python -m scripts.skill_contracts --skill run-modeling-project` and execute this Skill through the local `scripts/execute_skill.py`. Supply every contracted input and output role. Record a failed preflight as blocked rather than repairing the trace by hand.
