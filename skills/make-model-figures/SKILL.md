---
name: make-model-figures
description: Design, generate, improve, audit, and export evidence-centered figures for mathematical modeling analysis and competition papers. Use for data or model visualizations, multi-panel result figures, mechanism and workflow diagrams, sensitivity or robustness graphics, palette redesign, print-size QA, and reproducible vector/raster delivery; do not route ordinary data analysis here when no figure is requested.
---

# Make Model Figures

For paper-style refinement, read `references/cumcm-research-style.md`: use the shared render-time configuration, chart-specific layout, and an individual three-case review for each affected entry. Keep visual decisions separate from numerical and export checks.

Build a visual argument, not a gallery of available variables. Every formal figure must support one modeling claim and remain truthful to the saved data, model, units, and uncertainty.

## Choose the operating mode

- **Create:** design a new figure from machine-readable data or saved model results.
- **Improve:** preserve the source data, statistical meaning, units, filtering, and conclusion while revising layout, chart type, typography, palette, or annotations. Record any changed scale, aggregation, normalization, or encoding.
- **Audit:** inspect the source and rendered output; report evidence or readability defects without silently redrawing it.
- **Explore:** make lightweight diagnostic plots. Do not represent them as submission-ready until the formal contract and export checks are completed.

Proceed directly when the user's goal and data mapping are clear. Ask only when a missing choice would change the scientific meaning, such as which columns represent the requested comparison.

## Required workflow

1. **State the visual claim.** Read `references/paper-figure-language.md` and write the data-derived conclusion (or an explicit pending question with `claim_status="question"`), figure role, evidence, source paths, units, sample definition, statistic, uncertainty, model/scenario, and review risks. Use `FigureContract` for a formal figure; use a shortened claim/evidence note for exploration or a cosmetic-only edit.
2. **Protect data integrity.** Use all relevant user-provided observations. Never silently select representative rows, replace real data with illustrative values, or drop inconvenient groups. For dense rendering, prefer rasterized marks, hexbin/density views, or transparent points; if aggregation, filtering, imputation, winsorization, or normalization changes what is shown, record it and keep the unmodified source.
3. **Route by information task.** Read `references/figure-standards.md`. When the chart type is unclear, specialized, or multi-panel, also read `references/design-and-routing.md`. Prefer the smallest set of non-redundant panels that proves the claim; avoid duplicate views of the same fact.
4. **Design before coding.** Fix the final physical width and approximate aspect ratio first. For two or more panels, create a `FigureDesignBrief`: core message, layout recipe, hero panel where appropriate, support sequence, and stable color roles. A hero panel should be larger only when its evidence is genuinely more important or denser.
5. **Assign semantic style.** For new figures or recoloring, read `references/palette-system.md`. Choose categorical colors and continuous maps separately by object and physical quantity; keep the same object's meaning stable across figures. Preserve useful visual emphasis in a supplied original. For power/energy maps or markers over a heatmap, also read `references/power-energy-figures.md`. Retain line/marker/label redundancy for critical distinctions. Do not change data or statistics during recoloring.
6. **Generate reproducibly.** Prefer `algorithms.figures.get_figure/get_spec/list_figures` for registered charts; `algorithms.sci_figures` remains the compatibility and export entry point. Plot from saved data/results with the registered renderer or `algorithms.diagram` when available; otherwise install the repository-built `math-model-agent` wheel; use the verified `scripts/minimal_example.py` to diagnose the runtime. Do not copy an algorithm implementation into the skill. Read `references/execution-and-migration.md` for configuration precedence, six executable routes, installation and schema migration. Use `load_figure_config` and `render_template` for common tasks. Apply `publication_rc_params` or `paper_figure_rc_params`, exact `publication_size`, consistent `add_panel_label`, and `export_publication_figure`. Do not assume the project contains a `code/algorithms` checkout.
7. **Run the quality gate.** For a formal figure, read `references/publication-workflow.md` and `references/visual-qa-checklist.md`. Run the programmatic audit, export the vector master and 450 DPI proof, then actually open the proof at final paper size. Fix clipping, overlaps, missing glyphs, misleading scales, unstable color meanings, weak hierarchy, and illegible details before delivery.
8. **Close the evidence loop.** Introduce the figure in the manuscript, explain its pattern and modeling meaning after it, and state limitations. Confirm every plotted optimum, ranking, threshold, sample size, interval, and annotation against the saved result and surrounding tables/text.

## Visual language

Use readable text, clear data marks, unobtrusive axes, and only necessary guide lines. Prefer saturated, distinct colors for important curves and categories; reserve pale colors for supporting bands and context. For power or energy increasing in magnitude, favor a deep-red → orange → gold continuous map with visible detail at both ends. Other quantities may need different maps. Unify object meanings, fonts and notation across the paper; do not impose one pale palette or a single visual mood on every figure. Prefer direct labels or reserved legend space when practical. Avoid rainbow/jet maps, decorative 3-D perspective, unexplained dual axes, hidden truncation, and effects that compete with the evidence.

If the user requests only advice, an audit, or skill refinement, keep existing plots unchanged. A later authorized redraw should repair the original's specific defects while preserving its useful semantic choices.

Unless the user requests another language, use Chinese for filenames, titles, axes, legends, annotations, captions, and unit descriptions. Preserve standard mathematical symbols and recognized unit abbreviations. Configure a Chinese-capable font stack and verify the rendered proof contains neither missing-glyph boxes nor broken minus signs.

## Deliverables

For a formal figure, return:

- reproducible plotting code and the machine-readable source/result path;
- editable PDF/SVG master plus 450 DPI RGB PNG proof;
- `.figure.json` containing the contract, design brief, palette, transformations, randomness, and audit;
- a concise QA note distinguishing passed checks, warnings, and any review risk still requiring judgment.

Do not claim submission readiness from source-code inspection alone. A rendered visual check is mandatory.

## Resources

- `references/paper-figure-language.md` — claim-to-figure grammar for modeling papers.
- `references/figure-standards.md` — chart and export invariants.
- `references/design-and-routing.md` — information-task routing and multi-panel composition; read when needed.
- `references/palette-system.md` — named themes and semantic color rules; read for creation or recoloring.
- `references/power-energy-figures.md` — warm continuous maps, outlined parameter markers and clear legends; read for power/energy figures or heatmap overlays.
- `references/publication-workflow.md` — reproducible implementation and bundle export; read for formal figures.
- `references/visual-qa-checklist.md` — four-pass review; read for audit or final delivery.
- `references/visual-repairs.md` — common visual defects, repairs and applicability.
- `references/execution-and-migration.md` — executable setup, configuration, templates, export/review states, compatibility and handoffs.
- `scripts/minimal_example.py` — portable executable synthetic demonstration; `--suite` covers six routes.
- `scripts/preview_palettes.py` — render any built-in theme before choosing or personalizing colors.

## Executable contract

For repository-managed `competition` and `audit` projects, inspect the bundled contract with `python <skill-directory>/scripts/_runtime/skill_contracts.py --skill make-model-figures --profile competition` (or `audit`) and run this Skill through `scripts/execute_skill.py` with every contracted input and output role. In `rapid`, retain the plotted source data, claim, units, palette, transformations, and generation parameters; reserve the formal registry and full bundle audit for a stricter profile.

Exporting a bundle leaves it pending visual review. Finish the formal Skill only after the actual PNG, PDF and SVG, physical-size proof, grayscale and source values have been checked. Consumers use `algorithms.figure_export.validate_figure_review(metadata_path, source_root=project_root)` to recheck the current files and implementation; a cached registry PASS cannot substitute for that check.

## Registered runtime 7.5.0

Read `list_figures(detailed=True)` and the generated capability matrix for current entries and aliases; counts are generated from the registry. All accept their own structured inputs in formal mode. Inspect `get_spec(key).required_fields`; a flat `values` array cannot replace matrices, networks, coordinates or model outputs. Dedicated diagrams validate supplied relationships and geometry; they do not claim statistical inference. Use the explicit `algorithms.figures.compute` helpers when statistics must be computed before drawing. Preview calls use the same validators and require a simulated contract. Keep paper suitability False until the concrete output and its evidence receive the required review.

For matrix sparklines, polar compositions, pictograms, calendar glyphs, matrix pies, correlation/covariance heatmaps, saved regression curves or frequency bubbles, read `references/practical-figures.md`. Use `scripts/practical_examples.py` for reproducible synthetic bundles. Route by the information task and prepare each figure's fields upstream; a chart name does not establish its appropriateness.

For coded interviews, sample hierarchies, people waffles, three-column alluvial flows, frequency/coverage quadrants or group-proportion radar charts, read `references/interview-figure-patterns.md`: conserve counts and joint membership, keep unknown categories, preserve coincident coordinates and distinguish descriptive records from population inference.

`raincloud` now combines half densities, quartile boxes and every raw observation; constant and singleton groups retain their observations without estimating a density. `correlation_matrix` is a Pearson heatmap with a fixed [-1, 1] domain and explicitly undefined constant columns; `pairgrid` remains the composite pairwise diagnostic. Record these semantic corrections when comparing older outputs. A registered implementation still requires review of its actual exported figure.
