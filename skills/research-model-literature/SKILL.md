---
name: research-model-literature
description: Search, verify, synthesize, and cite literature for mathematical modeling. Use when Codex needs prior models, parameter sources, benchmark methods, datasets, a literature review, research-gap analysis, or verified BibTeX for a competition paper.
---

# Research Model Literature

For national-award design references, cross-check official showcase identity with award evidence, record the exact PDF/printed pages actually viewed, and exclude inaccessible or unverified papers from completed samples. Keep design notes separate from model facts and prohibit reference-solution numbers from entering the independent solve.

Verify document completeness separately from award identity: compare page order and missing pages when a mirror differs from the official display. An abridged journal version may connect authorship but cannot replace unread contest pages. End a candidate search when independent routes add no identity evidence, then seek another eligible sample; never fill the count from a provincial award or a repository's unsupported label.

Attach external parameters and supported claims to existing evidence pointers, keeping source identity verification separate from content support. Ordinary chart types do not require invented citations; read `references/figure-source-handoff.md` when an external method, scale or parameter changes the plotted interpretation.

Build a traceable evidence base for modeling choices and parameters.

## Workflow

1. Turn the topic into model, application, data, and validation search concepts.
2. Search current authoritative sources; prioritize original papers, official datasets, standards, and competition rules.
3. Search with an identifiable provider and fetch the source or authoritative metadata page. Save candidates explicitly in `source_candidates`; never inject a problem-specific bibliography from inside a reusable Skill script.
4. For every candidate record `origin` (`SEARCHED`, `USER_SUPPLIED`, or `MANUALLY_ENTERED`), `retrieval_provider`, UTC `retrieval_timestamp`, `source_fetch_status`, metadata-verification status/evidence, and content-relevance evidence. `USER_SUPPLIED` is not equivalent to `VERIFIED`.
5. Cluster findings by method and compare assumptions, datasets, metrics, limitations, decision coupling, uncertainty semantics, and validation design. Treat competition exemplars as style/method evidence only: never recover their hidden numerical solution, named entities, or tuned parameters.
6. Separate established findings, source-supported inference, and open questions.
   For each intended citation, record the exact supported claim, source locator, reading depth and transfer limits. Bibliographic identity and content support are separate checks; source-service failure is not proof of a fabricated reference.
7. Validate candidate identities and duplicates with `algorithms.modeling_contracts.validate_source_records`, then generate BibTeX with `records_to_bibtex` only from passing records. Record transferable design patterns separately from problem-specific outputs so that a later project cannot inherit an exemplar's answer.

## Integrity Rules

Read `references/integrity-rules.md` before producing citations. Never invent a source, DOI, quotation, result, or BibTeX field. Mark inaccessible or uncertain records as unverified instead of completing them from memory.

## Executable Contract

For repository-managed `competition` and `audit` work, run `scripts/execute_skill.py` with `model_problem`, `selected_model`, `citation_requirements`, and the explicit `source_candidates` file. Emit the contracted evidence roles; inspect them with `python <skill-directory>/scripts/_runtime/skill_contracts.py --skill research-model-literature --profile competition` (or `audit`). A bibliography without fetched-source provenance and relevance evidence, or generated from hard-coded task sources, is unverified. For an ordinary scoped literature lookup, keep only the evidence needed to support the answer instead of manufacturing empty registry artifacts.
