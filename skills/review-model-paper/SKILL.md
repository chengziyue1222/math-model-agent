---
name: review-model-paper
description: Audit mathematical modeling papers for correctness, reproducibility, evidence, citations, figures, and competition readiness. Use when Codex needs a pre-submission review, model or data integrity check, numerical claim verification, rubric-based score, prioritized revision list, or LaTeX/Typst paper inspection.
---

# Review Model Paper

Review in read-only mode by default and separate evidence from judgment.

## Workflow

1. Identify the manuscript entry file, `run-manifest.json`, supporting code, results, figures, data, and competition rules.
2. Run `scripts/run_paper_check.py` when the repository algorithm package is available.
3. Read `references/review-rubric.md` and inspect model validity, data handling, solution correctness, validation, claims, citations, figures, writing, and formatting.
4. Validate the run manifest with `--verify-files` and trace important numbers and conclusions back to registered code or result artifacts.
5. Classify findings as blocker, major, moderate, or minor.
6. Report each finding with location, evidence, impact, and a concrete correction.
7. End with submission readiness and the smallest high-value revision sequence.

## Guardrails

- Do not edit the manuscript unless the user explicitly requests revision.
- Do not assert that a citation or numerical claim is verified without checking its source.
- Do not use agent count as a proxy for review quality.
- Require explicit authorization before publishing, pushing, or submitting anything.

## Resources

Read `references/review-rubric.md`. Run `scripts/run_paper_check.py <paper-path>` for deterministic structural checks.
