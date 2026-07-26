---
name: write-model-paper
description: Generate evidence-gated mathematical-modeling papers from registered results, formulas, tables, figures, and citations. Use when Codex needs a brief report, teaching example, or competition paper with claim-to-evidence traceability, readiness checks, and reproducible manuscript artifacts.
---

# Write Model Paper

Generate only the highest paper mode supported by verified evidence. A polished narrative is never evidence.

## Workflow

1. Require a declared mode: `brief_report`, `teaching_example`, or `competition_paper`. Never call a brief report a competition paper.
2. For competition mode, require `paper-spec.yaml`, `evidence-index.json`, `claim-registry.json`, `figure-registry.json`, `table-registry.json`, and `formula-registry.json` beside the manuscript target. Teaching examples still require a real formula, figure, table, and disclosed source data.
3. Verify every evidence file SHA-256 before drafting. Resolve each claim JSON Pointer; preserve failed models and invalid solver states.
4. Invoke the `review-model-paper` Skill before formal generation. On failure, write `reports/paper_readiness_gap_report.md`, return `BLOCKED_NOT_PAPER_READY`, and identify the modeling/validation stage to rerun.
5. Draft from the registries only. Bind every reported key number with `[claim:CLAIM_ID]`; describe the supporting figure/table and uncertainty.
6. For competition mode, follow the full structure in `references/paper-structure.md`, including model framework, assumptions, notation, five result/validation sections, evaluation, citations, appendix, and reproduction note. Keep paths and commands out of the main body.
7. Re-run the independent review after rendering. A formal paper is approved only when every hard gate returns `PASS`.

## Strict CUMCM Layout Profile

For a paper that declares the CUMCM/校赛 C 题 profile, use `assets/cume-template.tex` unchanged as the preamble and preserve its document lifecycle. These are release gates, not drafting suggestions:

- A4; left/right margins `3.17cm`, top/bottom margins `2.54cm`.
- Body in SimSun; headings in SimHei. Use 1.5 line spacing, no paragraph skip, and a `2em` first-line indent.
- Emit a standalone cover, then a separate abstract/keywords page; start the body with Arabic page `1`.
- Use centred 16pt SimHei first-level headings and the template's second- and third-level hierarchy.
- Use the template's centred Chinese figure/table captions, booktabs three-line tables, float spacing, superscript citations, bibliography heading, and `pycode` code appendix environment.

Run `scripts/validate_cumcm_layout.py --tex <main.tex>` after generation and before PDF compilation. A failure blocks release; do not replace this profile with `\\maketitle`, a generic LaTeX class, or manual post-processing.

## Guardrails

- Never invent numerical results, citations, experiments, or validation.
- Do not emit a formal manuscript if evidence, validation, hashes, citations, figures, or formula registry are incomplete; emit `BLOCKED_NOT_PAPER_READY` instead.
- Do not disguise AI involvement or remove required competition disclosures.
- Use `assets/cume-template.tex` for the strict CUMCM layout profile; its preamble and cover/abstract/body page sequence are authoritative.
- Never copy a number into the paper unless its `claim_id` resolves to a verified result artifact and JSON Pointer.

## Resources

Read `references/paper-structure.md`. Reuse `assets/cume-template.tex` for compatible CUMCM-style LaTeX output.

## Executable Contract

Use `scripts/execute_skill.py` with all eight registered paper inputs. Register `main_markdown`, `main_tex`, `paper_generation_report`, and `claim_usage_report`; the PDF and DOCX must then be registered by their respective formal tool producers. A project script must not write `main.tex` or compile the paper directly.
