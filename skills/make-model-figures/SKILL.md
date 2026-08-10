---
name: make-model-figures
description: Design, generate, audit, and export figures for mathematical modeling problems and competition papers. Use when Codex needs data exploration, assumption checks, model diagnostics, model comparison, optimization results, sensitivity or robustness analysis, scenario and decision graphics, exact paper sizing, accessible palettes, vector masters, high-resolution proofs, or reproducible figure metadata.
---

# Make Model Figures

Generate figures that prove a particular modeling conclusion. A chart is not included merely because there is data available.

## Workflow

1. Start from a conclusion, validation claim or mechanism that the paper must establish.
2. Read `references/paper-figure-language.md`, `references/figure-standards.md` and the relevant functions in `code/algorithms/sci_figures.py` or `diagram.py`.
3. Select the smallest appropriate form: route diagram, mechanism sketch, snapshots, global-plus-inset, trend/threshold, sensitivity, convergence or a representative comparison table. Record why competing forms were not needed.
4. Plan panels and final A4 dimensions before plotting. One page should not contain four unreadable mini-plots; no run of pages should become pure figures without explanatory text.
5. Plot from saved data/results. Label variables and units; show reference values, thresholds, feasible regions, uncertainty or baseline whenever these are needed for the conclusion.
6. Apply `paper_figure_rc_params` (or `publication_rc_params` where venue settings require it), export vector masters and inspect the rendered PDF-size proof.
7. For every formal figure, record source data, model/scenario, claim, units, filtering, final size and any randomness. This metadata is for audit, not reader-facing prose.
8. In the manuscript, introduce why the figure is needed and explain its pattern, mechanism and limitation after it.

## Style

Use white backgrounds, muted semantic colors, one restrained emphasis color, weak grids and readable Chinese/Latin labels. Avoid rainbow maps, decorative 3-D effects, generic dashboard palettes, obscuring legends and unlabeled axes.

## Resources

- `references/paper-figure-language.md` — conclusion-to-figure grammar.
- `references/figure-standards.md` — sizing and export rules.
- `references/publication-workflow.md` — reproducibility and rendered inspection.

## Executable Contract

For repository-managed `competition` and `audit` projects, inspect the shared contract registry with `python -m scripts.skill_contracts --skill make-model-figures` and run this Skill through the local `scripts/execute_skill.py` with every contracted input and output role. In `rapid`, retain the plotted source data, claim, units, and generation parameters; reserve formal registry and PDF-size audit work for a stricter profile.
