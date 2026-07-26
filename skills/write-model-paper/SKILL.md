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

## Guardrails

- Never invent numerical results, citations, experiments, or validation.
- Do not emit a formal manuscript if evidence, validation, hashes, citations, figures, or formula registry are incomplete; emit `BLOCKED_NOT_PAPER_READY` instead.
- Do not disguise AI involvement or remove required competition disclosures.
- Use `assets/cume-template.tex` only when its format matches the competition rules.
- Never copy a number into the paper unless its `claim_id` resolves to a verified result artifact and JSON Pointer.

## Resources

Read `references/paper-structure.md`. Reuse `assets/cume-template.tex` for compatible CUMCM-style LaTeX output.

## Executable Contract

Use `scripts/execute_skill.py` with all eight registered paper inputs. Register `main_markdown`, `main_tex`, `paper_generation_report`, and `claim_usage_report`; the PDF and DOCX must then be registered by their respective formal tool producers. A project script must not write `main.tex` or compile the paper directly.
