# Project Instructions for AI Agents

This file provides instructions and context for AI coding agents working on this
project.

## Collaboration between you and the user

### Language

The chat uses English.

### One question after another

Whenever you want to ask the user questions, then ask one question after
another, so that the user can focus on a single question at a time.

### Avoid Ambiguity

If your instructions are unclear, ambiguous, inconsistent or contradicting to
the rules or to previous instructions, you must describe this situation and
ask the user clarifying questions before proceeding.

## How to follow your custom instructions

Whenever the user says "follow your custom instructions", then use the
/memory-bank-by-cline skill to understand the memory bank concept and structure.

If there is no memory bank, then you MUST ask the user for clarification
before proceeding.

Then read the memory bank and identify the immediate next action.

Afterwards, identify the applicable rules and read them.

After having read the memory bank, you must summarize your current
understanding. The summary shall end with the next immediate action.

Finally, ask whether you should execute the next immediate action.

## LS tool does not show hidden files

When you want to check whether a hidden file or directory exists, then
you MUST use the Bash tool to run `ls -la <path>`. The LS tool does not handle
hidden files.

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->

## Conventions & Patterns

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->
