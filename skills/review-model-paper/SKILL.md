---
name: review-model-paper
description: Audit mathematical-modeling papers for reasoning, evidence, figures/tables, citations and final layout. Use when Codex needs a pre-submission review, revision plan, claim verification, or LaTeX/Typst/Markdown inspection.
---

# Review Model Paper

Report mathematical evidence, figure expression and page-layout defects separately in the existing review record. After a repair, inspect the regenerated dependent outputs and their current hashes; keep unresolved uncertainty and unviewed pages pending.

For practical matrix/calendar/composition figures or a failed stage gate, read `references/practical-figure-review.md`. Check source numbers, units, composition denominators, size/height/angle encoding, missing states and final insertion. Return the earliest affected stage; release requires passing review, preflight and current evidence, without fixed counts of equations, figures or citations.

Review in read-only mode unless revision is explicitly requested. First judge the reader-visible paper, then run backend consistency checks.

## Workflow

1. Collect the problem, manuscript, selected paper delivery (PDF by default; PDF or DOCX for competition, both for audit), result files, figures/tables, validation material, citations, support archive/manifest and contest template.
2. Read `references/paper-quality-review.md` and `references/review-rubric.md`. For CUMCM 2026, also read `references/cumcm-2026-preflight.md` and label each finding as official compliance or quality advice.
3. Check abstract, problem analysis, unified-core decision, formula explanation, per-question model/solution/result coverage, result reasoning and limitation disclosure.
4. Check that figures and tables have different evidentiary roles, are readable on A4 pages, and receive useful surrounding prose.
5. Check citations for relevance and verifiability. Require the appendix to list every support-package file and contain every complete self-authored runnable source file; third-party libraries belong in a versioned dependency list with installation instructions, not as copied source or binaries.
6. Render and inspect layout against the selected venue/template. For CUMCM, the abstract is electronic page 1, the restatement follows with continuous numbering, and no contents page exists. References and appendices must read cleanly; the body obeys the resolved venue page limit. Treat typography and heading alignment as local quality defaults unless explicitly mandated.
7. Keep ordinary review read-only. For a final anonymity preflight, use a user-supplied private identity dictionary outside the support tree or explicit `--identity-term` values when available. Do not create or populate an identity file during review. If no private dictionary is supplied, still run generic identity-label, path, filename and metadata checks and report the personalized term scan as not run rather than failing the whole review.
8. Run structural, value-consistency, resolved venue package-size/anonymity, path and PDF/DOCX metadata checks. Verify the support manifest exactly matches ZIP/RAR entries and rerun it from a clean extracted temporary directory. For CUMCM 2026, require the AI declaration before references and, when AI was used, the exact support file `AI工具使用详情.pdf`. Reconcile disclosure against records rather than guessing from writing style. RAR review requires `rarfile` plus a detected extraction backend and records that backend in the report. Any missing local import/data/config/font/plot dependency, confirmed identity leak or absolute user path blocks readiness.
9. Report findings by severity with direct evidence, impact and the smallest repair. A PASS means the visible paper and its evidence both meet the declared standard, not that it will win a contest.
   Use `references/evidence-review.md` for claim/source pointers, statistical ambiguity, figure semantics and a revision closure check. Separate confirmed defects, unresolved evidence gaps and optional aesthetic preferences.

## Guardrails

- Do not claim a citation or numerical result is verified without checking its source.
- Do not use a fixed count of equations, figures or references as a proxy for quality.
- Do not use an AI-text detector or prose style as proof of AI use, and do not tune validation repeatedly until a holdout threshold passes.
- Do not edit, publish or submit the paper without authorization.

## Resources

- `references/paper-quality-review.md` — reader-visible quality checklist.
- `references/review-rubric.md` — modeling quality rubric.
- `references/evidence-review.md` — evidence-grounded findings and revision verification.
- `references/cumcm-2026-preflight.md` — official 2026 compliance and AI-disclosure checks.

## Executable Contract

For repository-managed work, select the contract explicitly with `python <skill-directory>/scripts/_runtime/skill_contracts.py --skill review-model-paper --profile competition` (or `audit`). Competition requires the paper/support preflight and permits a PDF-only delivery; audit additionally requires independent content review, HMAC-signed traces, complete hashes/registries, review hash binding and both PDF/DOCX. In `rapid`, provide a labelled peer-style critique; do not issue a submission-ready or formally verified verdict.

## Figure handoff

For figure metadata schema 3, preserve `contract.claim_status`, `source_files`, `visual_review` and `completion_status` alongside existing registry fields. `audit.passed` is only the programmatic result. Treat older metadata without visual review as `NOT_CHECKED`; use `NEEDS_VISUAL_REVIEW` until PNG, vector rendering, final-size proof, grayscale and source-value checks are recorded. A pending question is not a verified manuscript conclusion.

Read each registered figure's actual metadata with `algorithms.figure_export.validate_figure_review(metadata_path, source_root=project_root)`. Any failed, pending or stale dimension blocks formal readiness even if a summary report says PASS. After repair, verify the new output and page hashes; do not clear the finding by editing the old verdict or rebinding an unreviewed file.

## Explicit venue configuration

Resolve `venue` before drafting or applying compliance checks. Use `algorithms.venue_config.load_venue_config(config, venue=...)` or `python scripts/resolve_paper_venue.py --config config/venue.yaml`. Supported keys are `CUMCM`, `MCM/ICM`, `MathorCup`, `journal`, and `generic-research-report` (default). Profiles are local defaults; current official rules and the project template override them. Unspecified contest limits remain null, not guessed.

Read the resolved body-page policy, disclosure, formats, citation style, figure layout, anonymity and support-package policy. Apply CUMCM-specific 30-page/20-MB/AI-detail rules and CUMCM scripts only when venue is explicitly CUMCM. Named CUMCM problem adapters remain contest-specific. Do not apply their rules to a generic report or a journal.
