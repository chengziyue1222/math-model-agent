---
name: analyze-model-data
description: Inspect, clean, analyze, and model tabular data for mathematical modeling tasks. Use when Codex needs exploratory analysis, missing-value or anomaly handling, feature engineering, statistical testing, regression or classification, train/test evaluation, or reproducible data artifacts.
---

# Analyze Model Data

Produce a reproducible evidence trail from raw data to model-ready outputs.

## Workflow

1. Preserve the raw files and identify schema, units, missingness, duplicates, and target leakage risks.
2. Run `scripts/profile_csv.py` for CSV inputs, then inspect domain-specific anomalies manually.
3. Define the analysis question and evaluation metric before choosing transformations or models.
4. Split train/test data before fitting imputers, scalers, encoders, or feature selectors.
5. Compare against a simple baseline and report uncertainty, not only point metrics.
6. Save cleaned data, analysis code, configuration, figures, and a machine-readable result summary.
7. Document every exclusion, imputation, transformation, and random seed.

## Guardrails

- Never overwrite raw data.
- Do not remove outliers solely because they weaken the result.
- Do not infer causality from association without an identification strategy.
- Use Python or R according to the project context; do not force one language.

## Resources

Read `references/analysis-standards.md` before modeling. Use `scripts/profile_csv.py` for deterministic first-pass profiling.
