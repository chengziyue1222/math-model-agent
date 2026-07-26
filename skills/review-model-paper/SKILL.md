---
name: review-model-paper
description: Audit mathematical-modeling papers with fail-closed hard gates for structure, mathematics, figures/tables, evidence, validation, and citations. Use when Codex needs a pre-submission review, explicit PASS/FAIL decision, claim verification, stale-evidence detection, or LaTeX/Typst/Markdown inspection.
---

# Review Model Paper

Review in read-only mode by default and separate evidence from judgment.

## Workflow

1. Identify the manuscript, declared paper mode, registries, manifest, result files, figures, citations, decision contract, and quality validation.
2. For Markdown, run `scripts/run_paper_check.py <paper.md> --project-root <root> --mode <mode> --report-dir <output>`; for LaTeX/Typst run the legacy structural check as a supplemental check.
3. Enforce six fail-closed gates: structure; mathematics; figures/tables; evidence; validation; citations. A failure must produce `FAIL`, never a conditional pass.
4. Resolve every `[claim:ID]` through its evidence JSON Pointer and SHA-256. Detect changed results, invalid pointers, uninserted registered figures/tables, invalid solver claims, absent seeds/intervals, and missing formulas.
5. Enforce the decision contract: each question needs an executable result artifact and validation; declared multi-period state needs period balance checks; declared uncertainty needs scenario provenance and holdout/stress evidence; declared multi-objective optimization needs explicit trade-off evidence; a complex method needs a fair baseline comparison. If a complex paper has no automatic semantic finding, run `scripts/second_pass_content_review.py` and require its hash-bound report before clearing the anti-shallow gate.
6. Write both `paper_review_report.md` and `paper_review_report.json`, including blocking issues, unsupported claims, missing figures/tables, stale evidence, and return stage.
7. Keep subjective rubric observations separate from machine gates. Do not create a competition score from a constant or use it as quality evidence.

## Guardrails

- Do not edit the manuscript unless the user explicitly requests revision.
- Do not assert that a citation or numerical claim is verified without checking its source; invalid evidence is a blocker.
- Do not use agent count as a proxy for review quality.
- Require explicit authorization before publishing, pushing, or submitting anything.

## Resources

Read `references/review-rubric.md`. Run `scripts/run_paper_check.py <paper-path>` for deterministic structural checks.

## Executable Contract

Run `scripts/execute_skill.py` with the manuscript, source problem, decision contract, quality validation, result object, registries, bibliography, and project manifest. Register `paper_review_report`. The runtime trace, not a hand-written review log, is the evidence that this Skill was invoked.
