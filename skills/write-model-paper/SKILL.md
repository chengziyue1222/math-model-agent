---
name: write-model-paper
description: Generate rigorous, readable mathematical-modeling papers from problem analysis, models, results, figures, tables and verifiable sources. Use when Codex needs a competition paper or a grounded modeling report.
---

# Write Model Paper

Write the paper a contest reader sees: mathematical reasoning, evidence, figures and readable pages. Evidence checks protect the draft backstage; they must not turn the paper into an engineering log.

## Workflow

1. Confirm the contest template, problem source, model-selection rationale, results, figures, validation evidence and citations. Do not draft numbers, references or claims that lack a source.
2. Read `references/paper-generation-guide.md`, `references/paper-structure.md` and `config/paper_style.yaml` at the repository root. Use the contest template if it overrides these defaults.
3. Draft an abstract that fits one page: problem essence and overall framework, then each question's method, decisive result and necessary validation; end with a short scope statement and 4--7 keywords.
4. Build the paper in the canonical order: abstract, keywords, contents, restatement, analysis, assumptions, notation, conditional unified model, each question's model/solution/results, validation and sensitivity, evaluation, references and appendix.
5. Add a unified-model section only when upstream dependency analysis establishes a shared core. Otherwise make the separate routes clear rather than forcing a formal common layer.
6. For every formula, write purpose before it and definitions, computation and validity after it. For every result, write result, pattern, mechanism, evidence and implication; include limitations where they affect a decision.
7. Use figures and three-line tables as evidence, not decoration. Put a table title above the table; retain representative rows in the body and move exhaustive data to an attachment.
8. Cite only sources actually needed for methods, non-original theorems or external facts. Put references and appendix on separate pages; organize key appendix code by module at readable size.
9. Render and visually inspect the PDF. Check title/heading hierarchy, no top-left running header, natural body pagination, orphan headings, figure readability, table width, bibliography page and appendix/code legibility.

## Guardrails

- Never invent numerical results, citations, experiments or validation.
- Do not write `rule_id`, registries, workflow states, hashes, JSON or delivery-contract language in the formal paper.
- Do not use stock AI transitions as a substitute for analysis.
- Do not add a cover page unless the contest requires one; the default first page is title, abstract and keywords.

## Resources

- `references/paper-generation-guide.md` — generation behavior and prose patterns.
- `references/paper-structure.md` — section-level checklist.
- `assets/cume-template.tex` — CUMCM-style LaTeX starter template.

## Layout Authority and Preview

Treat `assets/cume-template.tex` as the sole authority for the CUMCM-style TeX layout; `config/paper_style.yaml` records the same defaults. The user guide is navigation, not an alternative page-design source. For a template preview, copy and compile the asset with:

```powershell
python scripts/render_template_preview.py --output-dir output/pdf
```

This command must produce a PDF and rendered page images. Do not substitute HTML, browser screenshots, colored teaching callouts, invented contest/team details, or visible workflow terms for the paper artifact. Do not add a cover unless the confirmed venue requires one.

## Executable Contract

For repository-managed `competition` and `audit` projects, inspect the shared contract registry with `python -m scripts.skill_contracts --skill write-model-paper` and run this Skill through the local `scripts/execute_skill.py` with every contracted input and output role. In `rapid`, write only a clearly labelled working memo from existing evidence; do not call it a formal paper or apply CUMCM layout unless the venue requires it.
