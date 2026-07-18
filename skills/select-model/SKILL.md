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
5. Choose a primary model, a simpler baseline, and an independent validation method.
6. State why rejected candidates are weaker for this problem.
7. Return the result using the output contract below.

## Output Contract

Provide:

- problem type and evidence;
- primary, baseline, and validation models;
- variables, objective, constraints, and assumptions;
- required data and preprocessing;
- expected outputs and validation plan;
- failure risks and fallback route.

Do not claim novelty, data availability, or model performance without evidence. Do not start implementation unless the user asks for it.

## Resources

Read `references/model-catalog.md` for the selection matrix and disqualifying conditions.
