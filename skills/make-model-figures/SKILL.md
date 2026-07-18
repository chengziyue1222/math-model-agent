---
name: make-model-figures
description: Design, generate, audit, and export figures for mathematical modeling problems and competition papers. Use when Codex needs data exploration, assumption checks, model diagnostics, model comparison, optimization results, sensitivity or robustness analysis, scenario and decision graphics, exact paper sizing, accessible palettes, vector masters, high-resolution proofs, or reproducible figure metadata.
---

# Make Model Figures

Create figures that communicate a specific modeling conclusion and remain reproducible.

## Workflow

1. Start from the modeling question, decision objective, or validation claim. Do not start from a chart template.
2. Assign each figure one role: data overview, assumption check, model result, diagnostic, comparison, sensitivity, robustness, optimization, or decision support.
3. Write a figure contract covering model/version, baseline or scenario, parameter and result sources, deterministic status or random seed, sample definition, statistics, uncertainty, review risks, and final paper size.
4. Read `references/figure-standards.md` and `references/publication-workflow.md`. Inspect relevant functions in `code/algorithms/sci_figures.py` or `diagram.py`.
5. Choose the smallest chart or multi-panel archetype that proves the modeling claim without distortion. Explain the panel plan before producing a large figure set.
6. Generate every mark from saved, machine-readable model inputs and outputs. Never silently discard rows, variables, groups, scenarios, or failed runs; report filtering and downsampling.
7. Use semantic, colorblind-safe colors with line-style or marker redundancy. Keep variables, units, constraints, baselines, uncertainty, and statistical annotations explicit.
8. For final delivery, use `FigureContract`, `publication_size`, `publication_rc_params`, and `export_publication_figure` to produce PDF/SVG masters, a 450 dpi PNG proof, and `.figure.json` audit metadata.
9. Run four reviews: anti-patterns, code/export compliance, model/data integrity, and rendered visual inspection. Cross-check plotted optima, metrics, parameters, and sample counts against saved results and paper text.

Do not use decorative 3-D effects, rainbow color maps, truncated axes without disclosure, hidden sampling, cherry-picked scenarios, or significance marks unsupported by a stated test.

## Resources

Read `references/figure-standards.md` for chart selection and formatting. Read `references/publication-workflow.md` for figure contracts, export code, and the audit checklist.
