---
name: write-model-paper
description: Draft and revise mathematical modeling competition papers from verified models, code, results, and figures. Use when Codex needs an abstract, assumptions, notation, derivation, results, sensitivity analysis, discussion, references, appendix, or a complete CUMCM/MCM-style manuscript.
---

# Write Model Paper

Write a traceable paper in which every claim can be linked to a model, source, computation, or figure.

## Workflow

1. Validate `run-manifest.json` with file verification and inventory only its verified problem statement, equations, code, results, figures, citations, failed runs, and limitations.
2. Read `references/paper-structure.md` and choose the required competition format.
3. Create a claim-to-evidence outline before drafting prose.
4. Define symbols and units once; keep names aligned with code and figures.
5. Explain why each model fits, how it was solved, and how it was validated.
6. Report concrete results with appropriate precision and uncertainty.
7. Discuss strengths, failure modes, transferability, and limitations.
8. Run a separate paper review before submission.

## Guardrails

- Never invent numerical results, citations, experiments, or validation.
- Mark missing evidence with an explicit placeholder and action owner.
- Do not disguise AI involvement or remove required competition disclosures.
- Use `assets/cume-template.tex` only when its format matches the competition rules.
- Never copy a number into the paper unless its metric or source artifact is traceable through the run manifest.

## Resources

Read `references/paper-structure.md`. Reuse `assets/cume-template.tex` for compatible CUMCM-style LaTeX output.
