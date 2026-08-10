---
name: review-model-paper
description: Audit mathematical-modeling papers for reasoning, evidence, figures/tables, citations and final layout. Use when Codex needs a pre-submission review, revision plan, claim verification, or LaTeX/Typst/Markdown inspection.
---

# Review Model Paper

Review in read-only mode unless revision is explicitly requested. First judge the reader-visible paper, then run backend consistency checks.

## Workflow

1. Collect the problem, manuscript, rendered PDF, result files, figures/tables, validation material, citations and contest template.
2. Read `references/paper-quality-review.md` and `references/review-rubric.md`.
3. Check abstract, problem analysis, unified-core decision, formula explanation, per-question model/solution/result coverage, result reasoning and limitation disclosure.
4. Check that figures and tables have different evidentiary roles, are readable on A4 pages, and receive useful surrounding prose.
5. Check citations for relevance and verifiability; check appendices for structured, readable code rather than a miniature dump of the full repository.
6. Render and inspect layout: title and first-level headings centered; no top-left running header; natural body flow; no orphan headings; references and appendices begin on clean pages.
7. Run structural, value-consistency and PDF preflight checks. Keep backend findings separate from the paper's own prose.
8. Report findings by severity with direct evidence, impact and the smallest repair. A PASS means the visible paper and its evidence both meet the declared standard, not that it will win a contest.

## Guardrails

- Do not claim a citation or numerical result is verified without checking its source.
- Do not use a fixed count of equations, figures or references as a proxy for quality.
- Do not edit, publish or submit the paper without authorization.

## Resources

- `references/paper-quality-review.md` — reader-visible quality checklist.
- `references/review-rubric.md` — modeling quality rubric.

## Executable Contract

For repository-managed `competition` and `audit` projects, inspect the shared contract registry with `python -m scripts.skill_contracts --skill review-model-paper` and run this Skill through the local `scripts/execute_skill.py` with every contracted input and output role. In `rapid`, provide a labelled peer-style critique of the available artifact; do not issue a submission-ready or formally verified verdict.
