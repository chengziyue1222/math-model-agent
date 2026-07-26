---
name: select-model
description: Select and justify mathematical models for competition problems. Use when Codex needs to classify a modeling problem, compare candidate methods, design a primary/backup/validation model combination, or explain why a model fits the available data and constraints.
---

# Select Model

Select a defensible modeling route before writing equations or code.

## Workflow

1. Read the complete problem and separate its subproblems.
2. Extract objectives, decision variables, constraints, data availability, uncertainty, and required outputs.
3. Classify each subproblem with `references/model-catalog.md`.
4. Shortlist two to four candidate models. Compare assumptions, sample requirements, interpretability, computational cost, and validation options.
5. Choose a primary model, a simpler baseline run on the same inputs, and an independent validation method.
6. Create a machine-readable decision contract for every subproblem: objective, decisions, constraints, required state transitions, uncertainty mode, multi-objective strategy, executable output, and validation evidence.
7. Validate the contract with `algorithms.modeling_contracts.validate_decision_contract`; duplicate question IDs, missing result artifacts, or missing validation artifacts block handoff.
8. For a multi-period decision, declare whether a state balance is required; for uncertainty, declare scenario/robust/stochastic semantics and calibration evidence; for competing objectives, declare a Pareto, epsilon-constraint, lexicographic, or weight-sensitivity route.
9. State why rejected candidates are weaker for this problem.
10. Return the result using the output contract below.

## Output Contract

Provide:

- problem type and evidence;
- primary, baseline, and validation models;
- variables, objective, constraints, and assumptions;
- required data and preprocessing;
- expected outputs and validation plan;
- a per-question decision contract, not only a narrative model list;
- failure risks and fallback route.

Do not claim novelty, data availability, or model performance without evidence. Do not start implementation unless the user asks for it.

## Resources

Read `references/model-catalog.md` for the selection matrix and disqualifying conditions.

## Executable Contract

Use `scripts/execute_skill.py` before implementation. Record `official_problem`, `data_dictionary`, `constraint_summary`, and `project_goal`; register `problem_decomposition`, `candidate_models`, `baseline_plan`, `selected_model_plan`, `decision_contract`, `risk_register`, and `model_selection_report`. Keep task-specific decomposition in an adapter script, but keep contract validation problem-agnostic. A prose-only or unvalidated selection is not a completed run.
