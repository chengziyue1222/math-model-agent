---
name: run-modeling-project
description: Orchestrate an end-to-end mathematical-modeling project through resumable stage gates and evidence-based handoffs. Use when Codex needs to start, continue, recover, or coordinate a multi-stage competition project spanning problem intake, data analysis, model selection, solving, validation, figures, paper writing, review, and release.
---

# Run Modeling Project

Coordinate the existing specialist Skills without letting artifacts, decisions, or failed runs fall between stages.

## Start or Resume

1. Read `references/stage-gates.md` and `references/handoff-schema.md`.
2. Run `scripts/project_state.py status --project-root <root>` before doing project work.
3. If no state exists, initialize it with a project ID and the project-relative `run-manifest.json` path.
4. If state exists, resume its `current_stage`; do not restart completed work unless its evidence is invalid.
5. Inspect the run manifest and verify registered files before relying on prior results.

## Orchestration Loop

1. State the current stage, its exit gate, known blocker, and smallest next action.
2. Invoke only the specialist Skill needed for that action:
   - intake or route selection: `$select-model`
   - data work: `$analyze-model-data`
   - source support: `$research-model-literature`
   - implementation, optimization, simulation, validation: `$solve-model`
   - figures: `$make-model-figures`
   - manuscript: `$write-model-paper`
   - audit: `$review-model-paper`
3. Carry the `decision_contract` from model selection through solving, figure design, writing, and review; carry `quality_validation` from solving through figure design, writing, and review.
4. Save machine-readable evidence under stable project-relative paths.
5. Update and verify `run-manifest.json`; preserve failed runs, diagnostics, seeds, metrics, and limitations.
6. Advance with `scripts/project_state.py advance` only when every required evidence role exists and hashes successfully.
6. Emit the handoff described in `references/handoff-schema.md` before changing stages or ending the task.

## Failure and Recovery

- Record a real blocker with `scripts/project_state.py block`; include the cause and next action.
- Use `resume` only after the cause is addressed. The blocker remains in history.
- Never skip a stage, silently replace evidence, or mark a gate complete from narrative alone.
- If evidence changed after a gate, treat the downstream state as suspect, revalidate the manifest, and rerun affected gates.
- Stop before publishing or submitting unless the user explicitly authorizes that external action.

## Completion

The project is complete only at `release`, after the review report, submission checklist, decision contract, quality validation, and verified run manifest pass the final gate. Report unresolved limitations even when every gate passes.

## Resources

- Read `references/stage-gates.md` for required evidence and transition rules.
- Read `references/handoff-schema.md` for status and artifact handoffs.
- Run `scripts/project_state.py` to initialize, inspect, block, resume, advance, and export state.

## Executable Contract

Use `scripts/execute_skill.py` to record the orchestration invocation with `project_config` and `skill_trace`, then register `project_state`, `stage_gate`, and `handoff`. Before release, run the repository workflow validator; it fails if a required standard Skill has no successful trace, an artifact producer is invalid, or a project script bypasses the workflow.
