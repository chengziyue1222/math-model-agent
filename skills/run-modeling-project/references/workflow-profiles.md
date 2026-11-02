# Workflow Profiles

Choose the lightest profile that can support the decision being made. A profile changes the amount of process, not the standard of mathematical honesty.

| Profile | Use for | Required minimum | Optional or deferred work | Completion claim |
|---|---|---|---|---|
| `rapid` | Problem understanding, exploration, and preliminary modeling | Explicit problem/objective/units/constraints, raw-data preservation, exploratory model or simple baseline, reproducible parameters/seed, preliminary result, and limitations | Formal paper, complete role contracts, registries, support archive, submission review | `exploratory` only; never call it submission-ready |
| `competition` | Complete contest work under the explicitly selected venue | Full modeling, fair baselines and validation, reproducible results, formal paper, applicable support package and clean-directory reproduction, resolved venue page/byte/anonymity checks, pre-submission review | HMAC trace signing, complete hash/producer registries, independent content review, dual-format delivery | `competition-ready` only after every applicable submission preflight passes |
| `audit` | Reproducibility-sensitive, regulated, reusable, or externally reviewed work | Everything in `competition`, plus complete role contracts and registries, HMAC-signed Skill traces, full input/output/implementation hashes, producer registration, independent content review, review hash binding, and both PDF and DOCX | None; fix blockers rather than downgrading the claim | `formally verified` only after every audit gate passes |

## Non-negotiables in every profile

- Preserve raw inputs; do not erase inconvenient observations without a recorded reason.
- State units, decision variables, constraints, assumptions, and the applicable range.
- Compare a consequential result with a simple baseline or explain why no meaningful baseline exists.
- Record seeds and aggregation for stochastic work; do not present one random draw as a stable conclusion.
- Keep a rerunnable path from inputs to reported numbers, and disclose limitations that affect a decision.
- Never invent data, numerical results, citations, or verification.

## Profile selection

Start in `rapid` while understanding the problem and exploring candidate models. Move to `competition` for full modeling, necessary baselines/validation, the formal paper, complete support materials and submission checks. Choose `audit` when independent verification and tamper-evident provenance justify HMAC, full hashes/registries and dual-format delivery. A project can promote to a stricter profile, but it cannot inherit a stricter completion claim without producing the missing evidence.

## Venue rules

Use CUMCM layout and delivery checks only when CUMCM (or an explicitly equivalent venue requirement) applies. The configured CUMCM defaults have no contents page, start numbering at 1 on the abstract, permit no more than 30 pages before the appendix, and cap the paper and support archive separately at 20,000,000 bytes. Record the applicable year's official requirements in the venue policy before applying these defaults. For another contest or a research report, use that venue's official template and retain the same evidence, baseline, validation, anonymity, and reproducibility principles.
