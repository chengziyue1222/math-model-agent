# Workflow Profiles

Choose the lightest profile that can support the decision being made. A profile changes the amount of process, not the standard of mathematical honesty.

| Profile | Use for | Required minimum | Optional or deferred work | Completion claim |
|---|---|---|---|---|
| `rapid` | Exploratory work, feasibility checks, and early competition iteration | Problem/objective/units/constraints, raw-data preservation, a simple baseline, reproducible parameters or seed, a result file, and stated limitations | Full role contracts, source registry, formal figure registry, PDF/DOCX delivery, independent review | `exploratory` only; never call it submission-ready |
| `competition` | Default for a contest deliverable | Per-question selection rationale, data audit where data is used, a fair baseline, validation appropriate to the decision, reproducible result artifacts, reader-facing figures/paper, and pre-submission review | Audit-only hash binding and adversarial mutation checks | `competition-ready` after the venue's required checks pass |
| `audit` | Reproducibility-sensitive, regulated, reusable, or externally reviewed work | Everything in `competition`, plus complete role contracts, signed Skill traces, run manifest, producer registration, hash-current evidence, and independent content review | None; fix blockers rather than downgrading the claim | `formally verified` only after every audit gate passes |

## Non-negotiables in every profile

- Preserve raw inputs; do not erase inconvenient observations without a recorded reason.
- State units, decision variables, constraints, assumptions, and the applicable range.
- Compare a consequential result with a simple baseline or explain why no meaningful baseline exists.
- Record seeds and aggregation for stochastic work; do not present one random draw as a stable conclusion.
- Keep a rerunnable path from inputs to reported numbers, and disclose limitations that affect a decision.
- Never invent data, numerical results, citations, or verification.

## Profile selection

Start in `rapid` when the question is still being understood. Move to `competition` before committing to a paper structure or final recommendation. Choose `audit` only when the cost of an unverifiable result is higher than the added workflow time. A project can promote to a stricter profile, but it cannot inherit a stricter completion claim without producing the missing evidence.

## Venue rules

Use CUMCM layout and PDF/DOCX checks only when CUMCM (or an explicitly equivalent venue requirement) applies. For another contest or a research report, use that venue's official template and retain the same evidence, baseline, and validation principles.
