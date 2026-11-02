---
name: select-model
description: Select and justify mathematical models for competition problems. Use when Codex needs to classify a modeling problem, compare candidate methods, design a primary/backup/validation model combination, or explain why a model fits the available data and constraints.
---

# Select Model

Bind each candidate, baseline and validation route to an actual evidence artifact in the existing model decision. Separate a fixed plan from a decision that observes future scenarios, and declare the scope of optimality and uncertainty before comparing them.

Include the required evidence shape in the existing decision contract: saved time series and holdout errors for forecasts, full scenario matrices for comparisons, group quantities and denominators for compositions. Specify figure fields before solving; see `references/visual-evidence-plan.md` when chart data affects the modeling route.

Choose a defensible route before writing code. The output is a modeling argument a reader can follow, not an algorithm label.

## Workflow

1. Read the complete problem; list each deliverable, object, datum, unit, objective, constraint and ambiguity.
2. Decompose the problem into subproblems and draw their input/output dependencies. Mark every input as observed, externally supplied, model-derived, or unavailable. When a decision needs a future quantity and historical observations exist, explicitly compare a causal forecasting submodel with justified non-forecast alternatives before declaring the problem blocked.
3. Read `references/structure-opportunity-scan.md` and inspect shared states, constraints, data, geometry, objectives and solvers. Decide explicitly whether a unified core is justified.
4. Use `references/model-catalog.md` to shortlist only genuinely plausible candidates for each subproblem. Compare structural fit, assumptions, identifiability, data demand, interpretability, computational cost, validation route and what would falsify each candidate; do not force a candidate count.
5. Prefer a route where analytical reasoning exposes structure and numerical methods resolve only the remaining unknowns. Treat reduction, symmetry, monotonicity and event functions as hypotheses requiring evidence.
6. Select a primary route, a simple baseline and a validation route. For threshold search, state the monotonicity evidence or select a non-monotone alternative.
   For research-depth work, specify the identifiable parameters, the decision-time information and the independent experimental unit as applicable. Plan one discriminating ablation or changed-condition check where it can distinguish the claimed mechanism from an alternative.
   Match validation to the strength of the proposed claim: prediction accuracy, causal mechanism, feasibility, robustness and global optimality need different evidence. Specify the discriminating observation or counterexample, the artifact that will contain it, and a fallback if that evidence cannot be obtained. More metrics alone do not strengthen a claim.
7. State rejected candidates and the reason each fails this problem.
8. Treat the selected route as provisional until implementation and validation agree with its assumptions. If downstream evidence contradicts it, revise the selection and record which dependent artifacts must be regenerated.

## Output

Return a concise `模型选择与结构分析` containing:

- dependency diagram and the unified-core decision;
- per-question objective, variables, units, constraints and assumptions;
- primary, baseline and independent validation methods;
- proposed formulas/outputs, critical events and anticipated figures;
- data requirements, uncertainty/limitation risks and fallback route.

Keep internal decision records machine-readable when a project uses them, but do not mistake a record for an explanation. Do not claim novelty, data availability or expected performance without evidence.

## Resources

- `references/model-catalog.md` — candidate matrix and disqualifying conditions.
- `references/structure-opportunity-scan.md` — structural reasoning before algorithm choice.

## Executable Contract

For repository-managed `competition` and `audit` projects, inspect the bundled contract with `python <skill-directory>/scripts/_runtime/skill_contracts.py --skill select-model --profile competition` (or `audit`) and run this Skill through `scripts/execute_skill.py` with every contracted input and output role. In `rapid`, return the Output above with a baseline and falsification plan; do not claim the route is formally verified.

At selection, validate the question obligations and their planned artifact paths; completed solutions and figures belong to later stages. If later validation falsifies the chosen route, revise this decision and invalidate the affected downstream outputs rather than retaining an older successful run.
