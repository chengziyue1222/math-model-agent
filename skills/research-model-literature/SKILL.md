---
name: research-model-literature
description: Search, verify, synthesize, and cite literature for mathematical modeling. Use when Codex needs prior models, parameter sources, benchmark methods, datasets, a literature review, research-gap analysis, or verified BibTeX for a competition paper.
---

# Research Model Literature

Build a traceable evidence base for modeling choices and parameters.

## Workflow

1. Turn the topic into model, application, data, and validation search concepts.
2. Search current authoritative sources; prioritize original papers, official datasets, standards, and competition rules.
3. Record query terms, search date, title, authors, year, DOI or stable URL, and relevance.
4. Verify each citation against the source page or paper metadata.
5. Cluster findings by method and compare assumptions, datasets, metrics, and limitations.
6. Separate established findings, source-supported inference, and open questions.
7. Generate BibTeX only from verified metadata.

## Integrity Rules

Read `references/integrity-rules.md` before producing citations. Never invent a source, DOI, quotation, result, or BibTeX field. Mark inaccessible or uncertain records as unverified instead of completing them from memory.

## Executable Contract

Run `scripts/execute_skill.py` with `model_problem`, `selected_model`, and `citation_requirements`. Emit and register `search_queries`, `search_results`, `selected_sources`, `rejected_sources`, `literature_evidence`, `references_bib`, and `bib_validation`. A bibliography without this trace is unverified.
