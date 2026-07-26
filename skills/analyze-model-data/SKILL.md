---
name: analyze-model-data
description: Inspect, clean, analyze, and model tabular data for mathematical modeling tasks. Use when Codex needs exploratory analysis, missing-value or anomaly handling, feature engineering, statistical testing, regression or classification, train/test evaluation, or reproducible data artifacts.
---

# Analyze Model Data

Produce a reproducible evidence trail from raw data to model-ready outputs.

## Workflow

1. Preserve the raw files and identify schema, units, missingness, duplicates, and target leakage risks.
2. Run `scripts/profile_csv.py` for CSV inputs, then inspect domain-specific anomalies manually.
3. Define the analysis question and evaluation metric before choosing transformations or models. For planning data, profile temporal dependence, cross-entity correlation, support/zero inflation, and unit-conversion risk before choosing an uncertainty model.
4. Split train/test data before fitting imputers, scalers, encoders, or feature selectors.
5. Compare against a simple baseline and report uncertainty, not only point metrics.
6. Save cleaned data, analysis code, configuration, figures, and a machine-readable result summary.
7. Document every exclusion, imputation, transformation, random seed, and the evidence for or against independent sampling. Preserve a time-aware holdout or stress slice when the task contains future planning.

## Guardrails

- Never overwrite raw data.
- Do not remove outliers solely because they weaken the result.
- Do not infer causality from association without an identification strategy.
- Use Python or R according to the project context; do not force one language.

## Resources

Read `references/analysis-standards.md` before modeling. Use `scripts/profile_csv.py` for deterministic first-pass profiling.

## Executable Contract

Use `scripts/execute_skill.py` with the shared runtime. Supply the `raw_data`, `data_dictionary`, and `official_problem` inputs, and produce every contracted output role: `data_profile`, `data_quality_report`, `cleaning_actions`, `eda_findings`, `leakage_report`, `processed_data_manifest`, and `data_analysis`. Do not advance a project or register a data-audit artifact without its successful signed Skill run.
