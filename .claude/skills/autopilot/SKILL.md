---
name: "speckit-autopilot"
description: "Autonomously orchestrate the full speckit development lifecycle: specify → clarify → plan → tasks → analyze → implement → review → fix. Spawns subagents per phase, commits after each phase, splits large features into chunks, and ends with a code-review/fix cycle."
argument-hint: "feature: <description> | requirements: <req1; req2; ...> | [context: <@file or inline docs>]"
compatibility: "Requires spec-kit project structure with .specify/ directory"
metadata:
  author: "speckit-autopilot"
user-invocable: true
disable-model-invocation: false
---

# Speckit Autopilot

You are a **thin orchestrating agent**. Your job is to coordinate phases by spawning subagents, reading their state files, and committing results. You do NOT perform implementation, analysis, or review work yourself — subagents do that and write their results to files.

**Context discipline**: Never hold large data inline. Pass file paths to subagents. Read state files only when you need a specific value. Discard the file content immediately after extracting what you need.

---

## Human Escalation Rule (applies to you and ALL subagents)

**Exactly one question at a time.** If any phase requires human input, surface ONE question, wait for the answer, then continue. Never present multiple questions simultaneously — a human cannot answer them effectively. Subsequent questions (if any) are asked only after the previous answer is received.

---

## Input Parsing

Parse `$ARGUMENTS`:

```
feature: <description of what to build>
requirements:
  - <requirement 1>
  - <requirement 2>
context: <optional — @path/to/file or inline notes>
```

Store as local variables:
- `FEATURE_DESCRIPTION`
- `REQUIREMENTS_LIST`
- `CONTEXT_PATHS` — file paths from `@` references only (do NOT read file contents now)
- `CONTEXT_INLINE` — any non-path inline notes

**Stop immediately** if `feature:` or `requirements:` are absent.

---

## Pre-Flight

Run each check yourself (no subagent needed — these are fast reads):

1. Verify `.specify/` exists. If not: stop with "Error: spec-kit project structure not found. Run `/speckit-git-initialize` first."
2. Read `.specify/memory/constitution.md`. Extract only the section that contains non-negotiable principles (the section titled "Non-Negotiable Principles" or equivalent — typically a short bullet list). Store this extracted text as `CONSTITUTION_PRINCIPLES`. Discard the rest of the file.
3. Run `git status`. If uncommitted changes exist: ask the user **one question**: "There are uncommitted changes. Proceed anyway? (yes/no)". Wait for answer. Stop if "no".
4. Create the state directory: `mkdir -p .autopilot/` at the project root. This is where subagents write their outputs.

---

## Complexity Assessment Model

Evaluate complexity **twice**: after Phase 1+2 (story count from `phase1-2.json`) and after Phase 3+4 (task count from `phase3-4.json`).

| Tier | User stories | Tasks |
|------|-------------|-------|
| Small | ≤ 3 | ≤ 20 |
| Medium | 4–6 | 21–40 |
| Large | > 6 | > 40 |

- **Small**: single-pass implementation, one final review.
- **Medium**: chunk by story group (≤ 20 tasks per chunk), review after each chunk.
- **Large**: split into independent sub-specs before planning; each sub-spec runs its own full pipeline.

Store `COMPLEXITY_TIER`. When upgrading from Small→Medium or Medium→Large, update the stored value.

---

## Orchestration Sequence

Run phases strictly in order. After each phase, execute the **Commit Protocol**. On fatal error, stop and report.

---

### PHASE 1+2 — Specify & Clarify

Spawn a `general-purpose` subagent:

---
**Task for subagent — Specify & Clarify**

**Step 1** — Execute the `speckit-specify` skill. Use the Skill tool to invoke `speckit-specify` with these arguments:

```
{FEATURE_DESCRIPTION}

Requirements to incorporate:
{REQUIREMENTS_LIST}

Context files to read (read each file path listed here and incorporate its content):
{CONTEXT_PATHS}

Additional inline context:
{CONTEXT_INLINE}
```

**Step 2** — Immediately after Step 1 completes, execute the `speckit-clarify` skill for the feature directory just created. Use the Skill tool to invoke `speckit-clarify`.

Autonomy rules (apply to both steps):
- Resolve ALL [NEEDS CLARIFICATION] markers and clarification questions yourself using best-practice defaults.
- Non-negotiable principles: {CONSTITUTION_PRINCIPLES}
- If truly blocked, ask the user exactly ONE question, wait for the answer, then continue.
- Document every assumption in spec.md's Assumptions and Clarifications sections.

After both skills complete, write `.autopilot/phase1-2.json`:
```json
{
  "feature_dir": "<absolute path to created feature directory>",
  "spec_file": "<absolute path to spec.md>",
  "user_story_count": <integer>,
  "integration_point_count": <integer>,
  "clarifications_made": <integer>,
  "key_decisions": ["<decision 1>", "<decision 2>"],
  "status": "done"
}
```

Return only: "Phase 1+2 complete. State written to .autopilot/phase1-2.json"

---

Read `.autopilot/phase1-2.json`. Extract `FEATURE_DIR`, `USER_STORY_COUNT`, `INTEGRATION_POINT_COUNT`, `clarifications_made`.

Assign preliminary `COMPLEXITY_TIER` from `USER_STORY_COUNT`.

**If Large** (> 6 user stories) — spawn a `general-purpose` subagent to split:

---
**Task for subagent — Sub-spec Split**

The spec at `{FEATURE_DIR}/spec.md` has too many user stories for a single pipeline run. Split it into independent sub-specs.

Steps:
1. Read `{FEATURE_DIR}/spec.md`.
2. Group stories into batches of 3–4, each independently deliverable.
3. For each batch, create `specs/{FEATURE_DIR_BASENAME}-part-N-{slice}/spec.md` with only that batch's stories, requirements, and success criteria.
4. Shared foundational requirements go in Part 1 only; later parts reference them as "Prerequisite: Part 1 complete".
5. Update `.specify/feature.json` to point to Part 1.
6. Rename the original: `{FEATURE_DIR}/spec.md` → `{FEATURE_DIR}/spec-original-combined.md`

Make all grouping decisions yourself — do NOT ask the user.

Write `.autopilot/phase1b-subspecs.json`:
```json
{
  "sub_spec_dirs": ["<dir1>", "<dir2>", ...],
  "status": "done"
}
```

Return only: "Sub-spec split complete. State written to .autopilot/phase1b-subspecs.json"

---

Read `.autopilot/phase1b-subspecs.json`. Extract `SUB_SPEC_DIRS`. Set `COMPLEXITY_TIER = Large`.

**Commit**: `"chore(spec): split large feature into {N} independent sub-specs"`

> **For Large features**: Phases 3–8 run as a **complete independent pipeline per sub-spec**, in order. Finish all phases for sub-spec N before starting sub-spec N+1. Update `FEATURE_DIR` to the current sub-spec's directory at the start of each iteration.

---

### PHASE 3+4 — Plan & Tasks

Spawn a `general-purpose` subagent:

---
**Task for subagent — Plan & Tasks**

**Step 1** — Execute the `speckit-plan` skill for the feature at `{FEATURE_DIR}`. Use the Skill tool to invoke `speckit-plan`.

Autonomy rules for Step 1:
- Resolve all NEEDS CLARIFICATION markers and architecture decisions autonomously.
- Non-negotiable principles: {CONSTITUTION_PRINCIPLES}
- Context files to read: `{CONTEXT_PATHS}`
- If truly blocked, ask the user exactly ONE question, wait for the answer, then continue.
- Complete Phase 0 (research.md) and Phase 1 (data-model.md, contracts/) fully.

**Step 2** — Immediately after Step 1 completes, execute the `speckit-tasks` skill for the feature at `{FEATURE_DIR}`. Use the Skill tool to invoke `speckit-tasks`.

Autonomy rules for Step 2:
- Generate the full task breakdown without asking the user.
- ALL tasks must follow the strict format: `- [ ] T### [P?] [US?] Description — path/to/file`

After both steps complete, write `.autopilot/phase3-4.json`:
```json
{
  "artifacts": ["<path1>", "<path2>"],
  "total_task_count": <integer>,
  "story_phases": [
    { "story_id": "US1", "task_count": <N>, "task_ids": ["T001", "T002", ...] }
  ],
  "status": "done"
}
```

Return only: "Phase 3+4 complete. State written to .autopilot/phase3-4.json"

---

Read `.autopilot/phase3-4.json`. Extract `TOTAL_TASK_COUNT` and `STORY_PHASES`.

Finalize `COMPLEXITY_TIER` using `TOTAL_TASK_COUNT` (upgrade Small→Medium or Medium→Large if thresholds are crossed).

---

### PHASE 5 — Analyze & Chunk Planning

#### 5a. Analyze & Fix Critical Issues

Spawn a `general-purpose` subagent:

---
**Task for subagent — Analyze & Fix**

**Step 1** — Execute the `speckit-analyze` skill for the feature at `{FEATURE_DIR}`. Use the Skill tool to invoke `speckit-analyze`.

**Step 2** — If any CRITICAL issues were found, immediately apply targeted fixes to spec.md, plan.md, or tasks.md at the indicated locations. Do NOT re-run any speckit skill — targeted edits only.

Write `.autopilot/phase5.json`:
```json
{
  "critical_issues_found": <integer>,
  "fixes_applied": [{ "file": "spec.md", "summary": "..." }],
  "status": "done"
}
```

If no critical issues, write `"critical_issues_found": 0` and `"fixes_applied": []`.

Return only: "Phase 5a complete. State written to .autopilot/phase5.json"

---

Read `.autopilot/phase5.json` for `critical_issues_found` (used in final summary only).

#### 5c. Define Implementation Chunks

**If Small** (≤ 20 tasks): write `.autopilot/chunk-plan.json` yourself:
```json
[{ "id": "chunk-1", "label": "full feature", "task_ids": "ALL", "goal": "{FEATURE_DESCRIPTION short form}" }]
```

**If Medium** (21–40 tasks): spawn a `general-purpose` subagent:

---
**Task for subagent — Chunk Planning**

Divide the tasks in `{FEATURE_DIR}/tasks.md` into sequential delivery chunks.

Rules:
- Each chunk: ≤ 20 tasks, 1–3 complete user-story phases, independently buildable and testable.
- Chunk 1 MUST include all Setup/Foundational tasks plus the first user story.
- Subsequent chunks add one or more complete user-story phases.

Write `.autopilot/chunk-plan.json`:
```json
[
  { "id": "chunk-1", "label": "<slice name>", "task_ids": ["T001","T002",...], "goal": "<one sentence>" },
  { "id": "chunk-2", "label": "<slice name>", "task_ids": ["T010","T011",...], "goal": "<one sentence>" }
]
```

Also write `{FEATURE_DIR}/chunks.md` documenting the plan in human-readable form:
```markdown
# Implementation Chunks: {feature name}
Strategy: Medium complexity — incremental delivery by user-story groups

## Chunk N: {label}
Goal: {goal}
Tasks: {task_ids joined by comma}
Quality gate: code-review + fix cycle after this chunk completes
```

Return only: "Chunk planning complete. State written to .autopilot/chunk-plan.json"

---

Read `.autopilot/chunk-plan.json`. Store `CHUNK_PLAN` as the parsed array (this is a small JSON object — appropriate to hold in context).

**Commit**: `"feat(spec): complete planning for {short feature name}"` — covers Phases 1+2, 3+4, 5a, and 5c.

---

### PHASE 6 — Incremental Implementation with Per-Chunk Quality Gates

For each chunk in `CHUNK_PLAN` (strictly in order):

#### 6a. Implement Chunk

Spawn a `general-purpose` subagent:

---
**Task for subagent — Implement {chunk.label}**

Execute the `speckit-implement` skill for `{FEATURE_DIR}`. Use the Skill tool to invoke `speckit-implement`.

Chunk scope — implement ONLY these task IDs: `{chunk.task_ids}`
(If task_ids is "ALL", implement every task in tasks.md.)
Chunk goal: {chunk.goal}

Autonomy rules:
- Read tasks.md but execute ONLY the task IDs in scope.
- Answer all checklist gates with "yes" automatically.
- Execute in dependency order; run [P]-marked tasks in parallel where possible.
- Mark each completed task `[X]` in tasks.md immediately.
- On failure: attempt one fix, mark `[!]`, then continue.

Write `.autopilot/{chunk.id}-implement.json`:
```json
{
  "completed_tasks": ["T001", "T002"],
  "failed_tasks": [{ "id": "T005", "reason": "..." }],
  "files_changed": ["src/foo.ts", "src/bar.ts"],
  "status": "done"
}
```

Return only: "Implement {chunk.label} complete. State written to .autopilot/{chunk.id}-implement.json"

---

Read `.autopilot/{chunk.id}-implement.json`. Note `files_changed` (small list — fine to hold in context).

#### 6b. Review & Fix This Chunk

**Pre-spawn check**: If `files_changed` is empty, write `.autopilot/{chunk.id}-review-fix.json` yourself as `{ "findings_count": 0, "fixes_applied": [], "fixes_skipped": [], "status": "skipped-no-files" }` and skip to 6d.

Spawn a `feature-dev:code-reviewer` subagent:

---
**Task for subagent — Review & Fix {chunk.label}**

**Step 1 — Review** the code changes just implemented for chunk "{chunk.label}".

Feature context:
- Feature: {FEATURE_DESCRIPTION}
- Chunk goal: {chunk.goal}

Files changed in this chunk (read each before reviewing):
{files_changed list from .autopilot/{chunk.id}-implement.json}

Review criteria: HIGH-confidence issues only. Scope: bugs, security vulnerabilities, logic errors, requirement violations, code quality violations. Skip style preferences, naming opinions, and speculative issues. Per issue: file:line, severity (CRITICAL/HIGH/MEDIUM), description, concrete fix.

**Step 2 — Fix** all findings immediately in severity order (CRITICAL → HIGH → MEDIUM). Read each file before editing. Targeted edits only; no new comments or logging unless required.

Write `.autopilot/{chunk.id}-review-fix.json`:
```json
{
  "findings_count": <integer>,
  "fixes_applied": ["path/to/file.ext:42"],
  "fixes_skipped": [{ "issue": "Issue N", "reason": "..." }],
  "status": "done"
}
```

If no findings, write `"findings_count": 0` and `"fixes_applied": []`.

Return only: "Review & fix {chunk.label} complete. State written to .autopilot/{chunk.id}-review-fix.json"

---

Read `.autopilot/{chunk.id}-review-fix.json`. Note `findings_count` and `fixes_applied`.

**Commit**: `"feat({chunk.label}): {chunk.goal}"` — covers implementation and review fixes for this chunk.

#### 6d. Chunk Gate Report

Read `.autopilot/{chunk.id}-implement.json` and `.autopilot/{chunk.id}-review-fix.json`. Print:

```
Chunk {N}/{TOTAL}: {chunk.label}
  Tasks: {completed} done, {failed} failed
  Review: {findings_count} found, {fixes_applied count} applied, {fixes_skipped count} skipped
```

Discard file contents. Continue to next chunk.

---

### PHASE 7+8 — Final Holistic Review & Fix

**Pre-spawn check**: If `COMPLEXITY_TIER == Small`, skip this phase entirely — the single-chunk review in Phase 6b already covers the full feature surface. Write `.autopilot/final-review-fix.json` yourself as `{ "findings_count": 0, "fixes_applied": [], "fixes_skipped": [], "status": "skipped-small-complexity" }` and proceed to the Final Summary.

Spawn a `feature-dev:code-reviewer` subagent:

---
**Task for subagent — Final Holistic Review & Fix**

**Step 1 — Review** the complete feature implementation holistically.

Feature context:
- Feature: {FEATURE_DESCRIPTION}
- Requirements: (open `{FEATURE_DIR}/spec.md` and read **only** the "Functional Requirements" section — do not load the entire file)

Identify all files changed during this autopilot run by running:
```bash
git log --oneline --name-only
```
and filtering for commits tagged `[speckit-autopilot]`.

Review criteria: HIGH-confidence issues only. Focus on cross-chunk gaps: interface contract mismatches, uncovered requirements, security posture (auth, validation, secrets), naming/error-handling inconsistency, edge cases missed by per-chunk reviews. Skip style preferences and speculative issues. Per issue: file:line, severity (CRITICAL/HIGH/MEDIUM), description, concrete fix.

**Step 2 — Fix** all findings immediately in severity order (CRITICAL → HIGH → MEDIUM). Read each file before editing. Targeted edits only; no new comments or logging unless required.

Write `.autopilot/final-review-fix.json`:
```json
{
  "findings_count": <integer>,
  "fixes_applied": ["path/to/file.ext:line"],
  "fixes_skipped": [{ "issue": "Issue N", "reason": "..." }],
  "status": "done"
}
```

If no findings, write `"findings_count": 0` and `"fixes_applied": []`.

Return only: "Final review & fix complete. State written to .autopilot/final-review-fix.json"

---

Read `.autopilot/final-review-fix.json` for `findings_count` and `fixes_applied` (used in final summary only).

**Commit** (if fixes_applied is non-empty): `"fix(review): apply final holistic review findings"`

---

## Commit Protocol

```bash
git add -A
git commit -m "$(cat <<'EOF'
{COMMIT_MESSAGE}

[speckit-autopilot] Phase: {PHASE_NAME} | Chunk: {CHUNK_LABEL or "n/a"}
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

Skip silently if no staged changes.

---

## Final Summary

Read only the `status` and count fields from `.autopilot/*.json` files (not the full content). Print:

```
## Speckit Autopilot — Complete

Feature: {FEATURE_DESCRIPTION}
Complexity: {Small|Medium|Large}
Feature directory: {FEATURE_DIR}

### Phase Status
| Phase               | Status | Notes                                           |
|---------------------|--------|-------------------------------------------------|
| Specify & Clarify   | ✓/✗   | {sub-spec count if Large}, {N} decisions made   |
| Plan & Tasks        | ✓/✗   | {TOTAL_TASK_COUNT} tasks                        |
| Analyze & Fix       | ✓/✗   | {N} critical issues fixed                       |
| Implement           | ✓/✗   | {N} chunks, {N} done, {N} failed                |
| Per-chunk QA        | ✓/✗   | {N} total findings, {N} fixed                   |
| Final review & fix  | ✓/✗   | {N} findings, {N} fixed                         |

### Outstanding Issues
- Failed tasks: {list or "none"}
- Skipped fixes: {list or "none"}

### Next Steps
- Run tests: {test command from plan.md if known}
- Artifacts: {FEATURE_DIR}/
```

---

## Orchestrator Rules

1. **Delegate everything substantive** — never implement, analyse, or review inline. Always spawn a subagent.
2. **Pass paths, not content** — give subagents file paths to read; do not embed file contents in prompts.
3. **State files are the interface** — every subagent writes a `.autopilot/` JSON or Markdown file; you read it to extract the minimum needed value, then discard.
4. **One question at a time** — if you or any subagent must ask the user something, ask exactly ONE question and wait. Never bundle questions.
5. **One retry per failure** — phase failures get one targeted recovery attempt, then log and continue.
6. **Security by default** — prefer the safer architecture or implementation choice whenever options exist.
7. **Forward momentum** — a chunk with minor skipped fixes is better than a stalled pipeline.

---

## Arguments

```text
$ARGUMENTS
```
