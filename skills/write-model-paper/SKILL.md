---
name: write-model-paper
description: Generate rigorous, readable mathematical-modeling papers from problem analysis, models, results, figures, tables and verifiable sources. Use when Codex needs a competition paper or a grounded modeling report.
---

# Write Model Paper

Reconcile every abstract/body/caption/table number with the same saved value and denominator. Review figures at their final inserted size on the rendered manuscript pages; a standalone export cannot establish manuscript readability.

Read `references/practical-figure-insertion.md` for specialized figures. Use saved values and denominators in captions and prose; retain one semantic palette across the paper. Internal evidence IDs can remain in saved registries without visible `[claim:ID]` markers. Explicit venue controls layout; profile controls process intensity.

Write the paper a contest reader sees: mathematical reasoning, evidence, figures and readable pages. Evidence checks protect the draft backstage; they must not turn the paper into an engineering log.

## Workflow

1. Confirm the contest template, problem source, model-selection rationale, results, figures, validation evidence and citations. Do not draft numbers, references or claims that lack a source.
2. Read `references/paper-generation-guide.md` and `references/paper-structure.md`. If the working project provides `config/paper_style.yaml`, treat it as an optional local override rather than a required file. For CUMCM 2026, also read `references/cumcm-2026-authoring.md`. Use current official rules over repository defaults.
3. Draft an abstract that fits one page: problem essence and overall framework, then each question's method, decisive result and necessary validation; end with a short scope statement and 4--7 keywords.
4. Build the paper in the canonical order: abstract, keywords, restatement, analysis, assumptions, notation, conditional unified model, each question's model/solution/results, validation and sensitivity, evaluation, AI-tool declaration when required by the venue, references and appendix. CUMCM papers do not include a contents page.
5. Add a unified-model section only when upstream dependency analysis establishes a shared core. Otherwise make the separate routes clear rather than forcing a formal common layer.
6. For every formula, write purpose before it and definitions, computation and validity after it. For every result, write result, pattern, mechanism, evidence and implication; include limitations where they affect a decision.
   Read `references/evidence-and-consistency.md` when drafting results, revising claims or reconciling repeated numbers. Distinguish a supported mechanism from a proposed explanation, and keep terminology, precision and uncertainty definitions synchronized across prose, figures and tables.
7. Use figures and three-line tables as evidence, not decoration. Put a table title above the table; retain representative rows in the body and move exhaustive data to an attachment.
8. Cite only sources actually needed for methods, non-original theorems or external facts. Put references and appendix on separate pages. The appendix must list every support-package file and include every complete, self-authored runnable source file at readable size; list third-party dependencies and installation steps instead of embedding library source or binaries.
9. Render and visually inspect the PDF. Check that the abstract is electronic page 1, restatement follows it with continuous numbering, no contents or blank contents page exists, venue-specific page and package limits (30 pages and 20 MB (local cap: 20,000,000 bytes) for the configured CUMCM baseline) are respected, and no page, table, figure, bibliography or code is clipped or garbled.
10. Build the support ZIP/RAR from a manifest, verify the manifest exactly matches archive entries, include all local modules/data/config/fonts/plot assets, and rerun the declared reproduction command from a clean extracted temporary directory. RAR validation requires `rarfile` and a working `unrar`, `7zip`, `unar`, or `bsdtar` backend. Any missing dependency or nonzero run blocks submission readiness.
11. For CUMCM 2026, place `AI工具使用声明` before references. If AI was used, generate `AI工具使用详情.pdf` from actual records (use `assets/ai-tool-usage-details-template.md`), include it in the support manifest/archive and reconcile every adopted non-language output with a manual verification record.

## Guardrails

- Never invent numerical results, citations, experiments or validation.
- Do not write `rule_id`, registries, workflow states, hashes, JSON or delivery-contract language in the formal paper.
- Do not use stock AI transitions as a substitute for analysis.
- Do not add a cover page unless the contest requires one; the default first page is title, abstract and keywords.
- Never place absolute user-directory paths or identity information in reader-facing or delivery reports. A submission-ready verdict requires metadata, names/paths and text-source scanning to pass.
- Do not turn local typography defaults, preferred abstract length or counts of equations, figures or models into official requirements.

## Resources

- `references/paper-generation-guide.md` — generation behavior and prose patterns.
- `references/paper-structure.md` — section-level checklist.
- `references/evidence-and-consistency.md` — bounded claims, independent captions, terminology and numeric consistency.
- `references/cumcm-2026-authoring.md` — official 2026 authoring baseline and AI disclosure rules.
- `assets/cume-template.tex` — CUMCM-style LaTeX starter template.
- `assets/ai-tool-usage-details-template.md` — evidence-based source for the required AI-use details PDF.

## Layout Authority and Preview

Treat `assets/cume-template.tex` as the installed Skill's default CUMCM-style TeX source; current official venue rules remain the compliance authority and may override it. A project-local `config/paper_style.yaml`, when present, is an override rather than a required dependency. For a template preview, run the script from the selected Skill directory:

```powershell
python <skill-directory>/scripts/render_template_preview.py --output-dir output/pdf
```

This command must produce a PDF and rendered page images. Do not substitute HTML, browser screenshots, colored teaching callouts, invented contest/team details, or visible workflow terms for the paper artifact. Do not add a cover unless the confirmed venue requires one.

## Executable Contract

For repository-managed `competition` and `audit` projects, inspect the selected contract with `python <skill-directory>/scripts/_runtime/skill_contracts.py --skill write-model-paper --profile competition` (or `audit`) and run this Skill through `scripts/execute_skill.py` with the contracted roles. `competition` defaults to a formal PDF and accepts PDF or DOCX as the paper delivery; `audit` adds both formats and complete audit evidence. In `rapid`, write only a clearly labelled working memo from existing evidence; do not call it a formal paper or apply CUMCM layout unless the venue requires it.

## Figure handoff

For figure metadata schema 3, preserve `contract.claim_status`, `source_files`, `visual_review` and `completion_status` alongside existing registry fields. `audit.passed` is only the programmatic result. Treat older metadata without visual review as `NOT_CHECKED`; use `NEEDS_VISUAL_REVIEW` until PNG, vector rendering, final-size proof, grayscale and source-value checks are recorded. A pending question is not a verified manuscript conclusion.

Drafts may contain pending figures, but formal completion requires their current reviews and bindings to pass. A separate numerical rerun does not refresh an older paper's review; regenerate the affected figures and prose, compile again, and inspect the resulting pages before accepting the new version.

## Explicit venue configuration

Resolve `venue` before drafting or applying compliance checks. Use `algorithms.venue_config.load_venue_config(config, venue=...)` or `python scripts/resolve_paper_venue.py --config config/venue.yaml`. Supported keys are `CUMCM`, `MCM/ICM`, `MathorCup`, `journal`, and `generic-research-report` (default). Profiles are local defaults; current official rules and the project template override them. Unspecified contest limits remain null, not guessed.

Read the resolved body-page policy, disclosure, formats, citation style, figure layout, anonymity and support-package policy. Apply CUMCM-specific 30-page/20-MB/AI-detail rules and CUMCM scripts only when venue is explicitly CUMCM. Named CUMCM problem adapters remain contest-specific. Do not apply their rules to a generic report or a journal.
