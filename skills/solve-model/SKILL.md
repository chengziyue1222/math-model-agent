---
name: solve-model
description: Formulate, implement, solve, and validate mathematical models with the repository algorithm library. Use when Codex needs to translate assumptions into equations, call or extend algorithms, optimize parameters, run simulations, or perform sensitivity and robustness analysis.
---

# Solve Model

Turn an agreed modeling route into a reproducible solution.

## Workflow

1. Confirm the objective, variables, constraints, units, assumptions, and evaluation metric.
2. Run `scripts/check_environment.py` before importing the algorithm package.
3. Read `references/algorithm-api.md` only for the relevant model family.
4. Build a simple baseline before a complex method.
5. Implement with explicit seeds, input validation, stable paths, and saved configuration.
6. Validate with boundary checks, dimensional checks, baseline comparison, and an independent method where feasible.
7. Run sensitivity or uncertainty analysis on influential parameters.
8. Save machine-readable results separately from figures and narrative.
9. Create or update the project `run-manifest.json` with the repository run-manifest CLI; validate it with `--verify-files` before handoff.

## Guardrails

- Do not install dependencies, overwrite source data, or start long computations without explaining the impact.
- Do not treat optimizer convergence as proof of global optimality.
- Do not report more precision than the data supports.
- Preserve failed runs and limitations in the handoff.
- Record every input, output, model version, parameter source, seed, metric, and failed attempt in the run manifest.

## Resources

- Read `references/algorithm-api.md` for supported repository APIs.
- Read `references/validation-checklist.md` before accepting final results.
- Run `scripts/check_environment.py` for a deterministic import and dependency check.

## Executable Contract

Invoke `scripts/execute_skill.py` with `selected_model_plan`, `data_analysis`, `model_config`, and `baseline_plan`. Its outputs must include a `model_specification`, a single status-bearing `result_object`, and `solver_validation`. Do not accept an infeasible or failed result as optimal, and do not let an orchestration script create these formal outputs.
