---
name: "speckit-autopilot-continue"
description: "Resume an interrupted speckit-autopilot workflow from where it left off. Reads .autopilot/ state files to determine the last completed phase and continues autonomously."
argument-hint: "[feature-dir: <path>]"
compatibility: "Requires spec-kit project structure with .specify/ directory and an existing .autopilot/ directory from a prior speckit-autopilot run"
metadata:
  author: "speckit-autopilot"
user-invocable: true
disable-model-invocation: false
---

# Speckit Autopilot — Continue

You are a **thin orchestrating agent** resuming an interrupted speckit-autopilot run. Your job is to determine exactly where the previous run stopped and continue from there without redoing completed work.

---

## Step 1 — Locate the active run

If `$ARGUMENTS` contains `feature-dir: <path>`, use that as `FEATURE_DIR`.

Otherwise, scan `.autopilot/phase1-2.json`. If it exists and has `"status": "done"`, read `feature_dir` from it and use that as `FEATURE_DIR`. If the file is absent or malformed, stop with: "Error: no interrupted autopilot run found. Start a new run with speckit-autopilot."

## Step 2 — Re-establish context

Run these reads yourself (no subagent):

1. Read `.specify/memory/constitution.md`. Extract only the Non-Negotiable Principles section. Store as `CONSTITUTION_PRINCIPLES`. Discard the rest.
2. Read `.autopilot/phase1-2.json`. Extract `FEATURE_DIR`, `USER_STORY_COUNT`, `clarifications_made`.
3. Derive preliminary `COMPLEXITY_TIER` from `USER_STORY_COUNT`: ≤ 3 = Small, 4–6 = Medium, > 6 = Large.
4. If `.autopilot/phase3-4.json` exists and has `"status": "done"`, read `total_task_count` and upgrade `COMPLEXITY_TIER` if thresholds crossed: ≤ 20 = Small, 21–40 = Medium, > 40 = Large.
5. If `.autopilot/chunk-plan.json` exists, read it and store `CHUNK_PLAN` as the parsed array.

## Step 3 — Determine resume point

Check each state file in sequence. A phase is **complete** if its file exists with `status` equal to `"done"`, `"skipped-no-files"`, or `"skipped-small-complexity"`.

| State file | Phase |
|---|---|
| `.autopilot/phase1-2.json` | Phase 1+2 — Specify & Clarify |
| `.autopilot/phase1b-subspecs.json` | Sub-spec split (Large only) |
| `.autopilot/phase3-4.json` | Phase 3+4 — Plan & Tasks |
| `.autopilot/phase5.json` | Phase 5a — Analyze & Fix |
| `.autopilot/chunk-plan.json` | Phase 5c — Chunk Planning |
| `.autopilot/{chunk.id}-implement.json` | Phase 6a — Implement (per chunk) |
| `.autopilot/{chunk.id}-review-fix.json` | Phase 6b — Review & Fix (per chunk) |
| `.autopilot/final-review-fix.json` | Phase 7+8 — Final Review & Fix |

Find the **first incomplete phase** — the earliest phase whose state file is absent or does not have a completed status. That is `RESUME_PHASE`.

Print: "Resuming from: {RESUME_PHASE}" then proceed.

## Step 4 — Continue the pipeline

Hand off to the speckit-autopilot orchestration sequence starting at `RESUME_PHASE`. Use the Skill tool to invoke `speckit-autopilot` with:

```
feature: (resume — read from {FEATURE_DIR}/spec.md title line)
requirements: (resume — read from {FEATURE_DIR}/spec.md Functional Requirements section)
```

**Do not re-run any already-completed phase.** Skip directly to `RESUME_PHASE` and run all remaining phases in order through to the Final Summary.

Carry forward:
- `FEATURE_DIR` from Step 2
- `COMPLEXITY_TIER` from Step 2
- `CONSTITUTION_PRINCIPLES` from Step 2
- `CHUNK_PLAN` from Step 2 (if already computed)

---

## Orchestrator Rules

1. Never redo a phase whose state file already has a completed status.
2. If `CHUNK_PLAN` is not yet written and `COMPLEXITY_TIER` is Small, write `.autopilot/chunk-plan.json` yourself as `[{ "id": "chunk-1", "label": "full feature", "task_ids": "ALL", "goal": "resume" }]` before continuing to Phase 6.
3. One question at a time — if truly blocked, ask the user exactly ONE question and wait for the answer.
4. Forward momentum — continue past non-critical failures; log them in the Final Summary.

---

## Arguments

```text
$ARGUMENTS
```
