---
name: select-model
description: Select and justify mathematical models for competition problems. Use when Codex needs to classify a modeling problem, compare candidate methods, design a primary/backup/validation model combination, or explain why a model fits the available data and constraints.
---

# Select Model

Choose a defensible route before writing code. The output is a modeling argument a reader can follow, not an algorithm label.

## Workflow

1. Read the complete problem; list each deliverable, object, datum, unit, objective, constraint and ambiguity.
2. Decompose the problem into subproblems and draw their input/output dependencies.
3. Read `references/structure-opportunity-scan.md` and inspect shared states, constraints, data, geometry, objectives and solvers. Decide explicitly whether a unified core is justified.
4. Use `references/model-catalog.md` to shortlist two to four candidates for each subproblem. Compare assumptions, data demand, interpretability, computational cost and what would falsify each candidate.
5. Prefer a route where analytical reasoning exposes structure and numerical methods resolve only the remaining unknowns. Treat reduction, symmetry, monotonicity and event functions as hypotheses requiring evidence.
6. Select a primary route, a simple baseline and a validation route. For threshold search, state the monotonicity evidence or select a non-monotone alternative.
7. State rejected candidates and the reason each fails this problem.

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

For repository-managed `competition` and `audit` projects, inspect the shared contract registry with `python -m scripts.skill_contracts --skill select-model` and run this Skill through the local `scripts/execute_skill.py` with every contracted input and output role. In `rapid`, return the Output above with a baseline and falsification plan; do not claim the route is formally verified.
