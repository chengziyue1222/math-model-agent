---
name: run-modeling-project
description: Coordinate a mathematical-modeling project from problem intake through analysis, model selection, solution, figures, paper, review and delivery. Use when Codex needs to organize a complete modeling workflow or hand off between modeling Skills.
---

# Run Modeling Project

Plan each question's saved result, falsification check and figure purpose before solving. Keep the selected venue separate from the process profile; a failed check returns to the earliest affected stage and invalidates dependent figures and prose.

Coordinate the existing Skills around a strong final paper. The project record supports reproducibility, but it is not a second product or a substitute for modeling.

## Workflow

1. Read `references/workflow-profiles.md` and choose `rapid`, `competition` (the default), or `audit` before creating deliverables.
2. Read `references/distilled-competition-playbook.md`, then record the problem, data sources, deliverables and venue constraints. Apply CUMCM-only layout rules only when that venue requires them.
3. Invoke `analyze-model-data` where data is used and `select-model` for decomposition, dependency analysis and structure opportunities. Classify each needed input as observed, externally supplied, model-derived, or unavailable. Before blocking on a missing derived input, decide whether the problem expects it to be estimated from information available at the decision time; if so, make that estimation a leakage-safe upstream subproblem. Invoke `research-model-literature` when external facts, parameters, datasets, or citations affect a claim.
4. Invoke `solve-model` for equations, algorithms, baselines, constraints, sensitivity and independent checks.
5. Invoke `make-model-figures` only after identifying the conclusions each figure must establish.
   Use the shared `algorithms.figures` registry through `get_spec`, `list_figures` and `get_figure`.
   Select a dedicated renderer with fields matching the saved model results; use `mode="formal"`.
   Inspect the live registry and generated capability matrix for current structured formal routes.
   Preview uses the same validators with explicit `mode="preview", simulated=True`.
   Calling successfully does not establish paper suitability; verify the actual output and its evidence.
   English keys and registered Chinese names identify the same renderer. Pass provenance, units,
   independent unit and actual interval bounds into the figure handoff; never synthesize missing statistics.
   Carry the user's visual preferences with the figure handoff. For a new end-to-end project or a cross-stage revision, read `references/research-evidence-handoffs.md`; reuse existing records rather than creating parallel ledgers.
6. Invoke `write-model-paper` to turn verified results into a contest paper, then `review-model-paper` for reader-visible and technical review.
7. In competition, produce a formal PDF by default (PDF or DOCX is sufficient) and a passing submission preflight. Provide a support archive and clean-directory reproduction when the selected venue requires them. In audit, add both document formats, independent review, HMAC and complete hash/producer evidence.

## Priority Order

1. final paper quality and layout;
2. modeling and reasoning;
3. validation and consistency;
4. engineering convenience.

Read `references/paper-first-flow.md` for the actual handoff order. Existing manifests, stage gates and validations are permitted as backstage controls; their terms and traces do not belong in the submitted paper. In `rapid`, retain the non-negotiables but defer audit-only artifacts; do not label the result as formally verified.

## Handoff Minimums

Read `references/practical-evidence-flow.md` when initializing, advancing or revising a full project. Resolve the same explicit venue in all stages, plan figure fields during analysis, and use semantic gates plus `rewind` to invalidate downstream outputs. Review inputs belong to entry into review; review results belong to release.

- analysis → selection: question decomposition, data/units, constraints and dependencies;
- selection → solution: model rationale, rejected alternatives, baseline and validation plan;
- solution → figures/writing: results, formulas, source tables, validations and limitations;
- figures → writing: claim, source, figure role, final artifact and interpretation;
- writing → review: manuscript, selected rendered paper format, sources, figure inventory, layout/visual checks and a list of evidence used; include the support manifest/archive when required by venue.
- review → release: paper review, submission readiness/preflight, and clean reproduction when a support package is required; audit also supplies independent review and hash/signature binding.

A handoff is a reviewable hypothesis, not an irreversible instruction. If downstream data, solver behavior or validation contradicts an earlier choice, return to the affected stage, record the evidence and reason for the change, then regenerate dependent artifacts.

Use distinct status fields for the task result, guidance application, executable-contract runtime, and submission readiness. Never summarize a direct script run as a verified Skill run when the contract runtime was unavailable. Keep one current project state; mark older reports `SUPERSEDED` with a pointer to the replacing state instead of leaving contradictory current-looking reports.

Use the newest run for each project, Skill and profile when deciding what is current. A newer RUNNING, FAIL or BLOCKED run suspends an older PASS; a corrected new PASS can restore it without deleting history. Rewind to the earliest affected stage and regenerate its dependent evidence before advancing again.

## Resources

- For capability evaluation, reuse the repository benchmark catalog and rubric. Record development exposure, actual inputs, per-question coverage, elapsed time, interventions and failures; reserve transfer claims for cases not used in adaptation. A completed script or catalog entry alone does not establish a completed contest solution.
- `references/distilled-competition-playbook.md` — evidence-first workflow distilled from staged competition materials, including rejected shortcuts.
- `references/paper-first-flow.md` — paper-facing handoff order.
- `references/stage-gates.md` — backstage stage gates.
- `references/research-evidence-handoffs.md` — source-to-claim handoffs and semantic figure consistency distilled from research workflows.

## Executable Contract

For repository-managed work, inspect the selected profile with `python <skill-directory>/scripts/_runtime/skill_contracts.py --skill run-modeling-project --profile competition` (or `rapid`/`audit`) and pass the same `--profile` to `scripts/execute_skill.py`. Rapid does not require the complete role contract; competition uses the delivery contract without audit-only signatures/registries; audit retains the complete signed contract. Record a required preflight failure as blocked rather than repairing the trace by hand.

## Figure handoff

For figure metadata schema 3, preserve `contract.claim_status`, `source_files`, `visual_review` and `completion_status` alongside existing registry fields. `audit.passed` is only the programmatic result. Treat older metadata without visual review as `NOT_CHECKED`; use `NEEDS_VISUAL_REVIEW` until PNG, vector rendering, final-size proof, grayscale and source-value checks are recorded. A pending question is not a verified manuscript conclusion.
