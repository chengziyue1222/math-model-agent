---
name: review-model-paper
description: Audit mathematical-modeling papers with fail-closed hard gates for structure, mathematics, figures/tables, evidence, validation, and citations. Use when Codex needs a pre-submission review, explicit PASS/FAIL decision, claim verification, stale-evidence detection, or LaTeX/Typst/Markdown inspection.
---

# Review Model Paper

Review in read-only mode by default and separate evidence from judgment.

## Workflow

1. Identify the manuscript, rendered PDF and DOCX, compile/render reports, visual audit, declared paper mode, registries, manifest, result files, figures, citations, decision contract, and quality validation.
2. For Markdown, run `scripts/run_paper_check.py <paper.md> --project-root <root> --mode <mode> --report-dir <output>`; for LaTeX/Typst run the legacy structural check as a supplemental check.
3. Enforce six fail-closed gates: structure; mathematics; figures/tables; evidence; validation; citations. A failure must produce `FAIL`, never a conditional pass.
4. Resolve every `[claim:ID]` through its evidence JSON Pointer and SHA-256. Detect changed results, invalid pointers, uninserted registered figures/tables, invalid solver claims, absent seeds/intervals, and missing formulas.
5. Enforce the decision contract: each question needs an existing executable result artifact and validation; declared multi-period state needs period balance checks; declared uncertainty needs scenario provenance and holdout/stress evidence; declared multi-objective optimization needs explicit trade-off evidence; a complex method needs a fair baseline comparison.
6. For every competition paper, run `scripts/second_pass_content_review.py` with the manuscript, decision contract, and quality validation; do not make the second pass conditional on the first pass finding nothing. Require all structured checks plus hashes for all three artifacts before passing.
7. Write `paper_review_report`, `independent_content_review`, `review_hash_binding`, and `submission_readiness`. Bind the latter two to the manuscript, PDF, DOCX, decision contract, quality validation, layout, compile, render, and visual-audit hashes.
8. Keep subjective rubric observations separate from machine gates. Do not create a competition score from a constant or use it as quality evidence.

## Guardrails

- Do not edit the manuscript unless the user explicitly requests revision.
- Do not assert that a citation or numerical claim is verified without checking its source; invalid evidence is a blocker.
- Do not use agent count as a proxy for review quality.
- Require explicit authorization before publishing, pushing, or submitting anything.

## Resources

Read `references/review-rubric.md`. Run `scripts/run_paper_check.py <paper-path>` for deterministic structural checks.

## Executable Contract

Run `scripts/execute_skill.py` with the manuscript, PDF, DOCX, source problem, decision contract, quality validation, result object, registries, bibliography, project manifest, layout validation, compile report, DOCX render report, and visual audit. Register `paper_review_report`, `independent_content_review`, `review_hash_binding`, and `submission_readiness`. The runtime trace, not a hand-written review log, is the evidence that this Skill was invoked.
