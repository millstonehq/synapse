---
name: agent-teams
description: Orchestrate Claude Code agent teams for complex parallel work. Creates teams with shared task lists, inter-agent messaging, and coordinated task execution. Use when work spans multiple modules, disciplines, or can be parallelized across independent owners.
allowed-tools: Read, Grep, Glob, Bash, Task, AskUserQuestion
---

# Agent Teams Orchestration

Create and run Claude Code agent teams — multiple Claude Code instances working together with shared task lists and direct inter-agent messaging.

## When to Use Agent Teams

Use agent teams when:
- Work spans multiple modules, packages, or disciplines
- Tasks can be parallelized across independent file owners
- Teammates need to share findings and coordinate (not just report back)
- A TDD, PRD, or plan has a multi-phase work plan with assignable units
- Debugging requires competing hypotheses investigated simultaneously
- Code review needs parallel security, performance, and correctness lenses

Do NOT use agent teams for:
- Single-file or trivially sequential changes
- Work where every step depends on the previous step's output
- Quick fixes or isolated research — use subagents (Task tool) instead
- Tasks that would require multiple teammates editing the same file

## Prerequisites

Agent teams require the experimental flag. Verify it's enabled:

```bash
grep -r "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS" ~/.claude/settings.json
```

If not present, the user must add to their settings.json:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

## How to Create a Team

### Step 1: Analyze the Work

Before creating the team, understand the work to be done. Read the relevant TDD, PRD, issue, or plan. Identify:

- **Deliverables** — concrete outputs (files, configs, tests, docs)
- **Dependencies** — which tasks block others
- **Ownership** — which files/modules each teammate will own (no overlap!)
- **Parallelism** — what can run simultaneously vs what must be sequential

### Step 2: Create the Team

```
TeamCreate:
  team_name: descriptive-kebab-case-name
  description: Brief description of the goal
```

### Step 3: Create Tasks with Dependencies

Create tasks for each deliverable using `TaskCreate`. Good tasks are:
- **Specific** — one clear output (a file, a module, a test suite)
- **Independent** — minimal file overlap with other tasks
- **Right-sized** — completable in one focused session (not too large, not trivially small)
- **Ordered** — use `addBlockedBy` for dependencies

```
TaskCreate: "Implement user authentication service"     → task 1
TaskCreate: "Add auth middleware to API routes"          → task 2, blockedBy: [1]
TaskCreate: "Create login/register UI components"        → task 3 (parallel with 2)
TaskCreate: "Write integration tests for auth flow"      → task 4, blockedBy: [2, 3]
```

Good task: "Add validation for scaffold command options in packages/cli/src/commands/scaffold.ts"
Bad task: "Set up the project" (too vague, touches too many files)

### Step 4: Spawn Teammates

Use the `Task` tool with `team_name` and `name` parameters. Each teammate needs:

- **name**: descriptive role name (e.g., "backend-engineer", "test-engineer")
- **subagent_type**: "general-purpose" (full tool access for implementation)
- **mode**: "bypassPermissions" for autonomous work, or "plan" to require plan approval
- **prompt**: detailed instructions including:
  - Their role and assigned tasks
  - Key file paths they own
  - Patterns and conventions to follow
  - How to report completion

**Spawn prompt template:**

```
You are the {role} on the {team-name} team. Your job is {brief role description}.

## Your Tasks

Check TaskList to find your assigned work. Start with Task #{id} ({title}).

### Task #{id}: {title}

{Detailed instructions with:}
1. What to read first to understand context
2. What to implement/change
3. Key file paths
4. Patterns to follow from existing code
5. How to verify the work (tests, validation, etc.)

## Guidelines
- Working directory: {path}
- Mark tasks completed via TaskUpdate when done
- Check TaskList after completing each task for newly unblocked work
- Send a message to team-lead when you complete milestones or get blocked
- Run tests after changes: {test command}
```

### Step 5: Assign Tasks

Use `TaskUpdate` with `owner` parameter to assign tasks to teammates by name. Assign initial tasks immediately, and reassign as work completes.

### Step 6: Monitor and Steer

- Teammate messages arrive automatically — respond promptly to unblock issues
- Check `TaskList` periodically to track progress
- When a teammate finishes, assign their next task or redirect to help others
- If a teammate goes off-track, message them with course correction
- **Do not implement tasks yourself** — stay in coordination mode

### Step 7: Verify Results

Before declaring victory:
- Run the full test suite yourself
- Run any validation commands
- Check that all tasks are marked completed
- Review git status for unexpected changes

### Step 8: Shut Down and Clean Up

When all tasks are verified:
1. Send `shutdown_request` to each teammate (one at a time)
2. Wait for each shutdown confirmation before proceeding
3. Use `TeamDelete` to clean up team resources

## Team Composition Recipes

### Feature Implementation
- **team-lead** (you) — orchestrate, verify
- **module-a-engineer** — implements one module/package
- **module-b-engineer** — implements another module/package
- **test-engineer** — writes tests across both modules

### Codebase Refactor
- **team-lead** (you) — orchestrate, verify
- **refactor-engineer-1** — refactors package A files
- **refactor-engineer-2** — refactors package B files
- **migration-engineer** — updates imports, configs, docs

### Parallel Code Review
- **team-lead** (you) — synthesize findings
- **security-reviewer** — security implications
- **performance-reviewer** — performance impact
- **correctness-reviewer** — logic, edge cases, test coverage

### Bug Investigation
- **team-lead** (you) — synthesize, decide fix
- **hypothesis-a** — investigate one theory
- **hypothesis-b** — investigate alternative theory
- **reproducer** — write reproduction tests

## Task Coordination Patterns

### Parallel Independent
Tasks don't depend on each other — spawn all teammates at once:
```
Task 1: Implement module A  (engineer-a)
Task 2: Implement module B  (engineer-b)
Task 3: Write documentation (docs-engineer)
```

### Pipeline (Sequential)
Use `addBlockedBy` for ordering:
```
Task 1: Define interfaces        → unblocked
Task 2: Implement backend        → blockedBy: [1]
Task 3: Implement frontend       → blockedBy: [1]
Task 4: Integration tests        → blockedBy: [2, 3]
```
Tasks 2+3 run in parallel after task 1. Task 4 waits for both.

### Fan-Out / Fan-In
Multiple teammates work in parallel, then results merge:
1. Create N parallel tasks (no dependencies between them)
2. Create a synthesis task blocked by all N
3. Assign parallel tasks to different teammates
4. Synthesis task unblocks when all complete

### Rolling Assignment
For uneven workloads, don't pre-assign all tasks. Assign 2-3 tasks each, then reassign as teammates finish — faster teammates pick up slack.

## Critical Rules

### File Ownership
**Two teammates editing the same file causes silent overwrites.** Enforce strict file ownership:
- Each teammate owns specific files/directories
- If a file must be touched by multiple teammates, sequence with task dependencies
- When in doubt, have one teammate own the file and the other describe changes needed via message

### Communication
- Use `SendMessage` type "message" for targeted questions to one teammate
- Use `broadcast` only for critical blockers affecting everyone
- Teammates should message the lead when blocked — don't let them wait silently
- Idle notifications are normal — teammates go idle after every turn

### Task Granularity
- Aim for 3-6 tasks per teammate
- Too few = teammates idle waiting for more work
- Too many = context thrashing and overhead
- Each task should produce a verifiable deliverable

### Always Verify
**Never trust self-reported results from teammates.** After all tasks complete:
- Run tests yourself
- Run validation yourself
- Check the actual output files
- Teammates may report success despite failing tests or partial implementation

### Plan Approval Mode
For risky or architectural changes, spawn teammates with `mode: "plan"`:
```
Task:
  name: "architect"
  mode: "plan"
  prompt: "Design the migration strategy..."
```
They must submit a plan for your approval before implementing.

## Troubleshooting

### Teammate not responding
Teammates go idle after every turn — this is normal. Send them a message to wake them up.

### Task stuck as in_progress
The teammate may have finished but forgotten to mark it complete. Check their output, then update the task yourself with `TaskUpdate`.

### File conflicts
If two teammates edited the same file, one change was lost. Check git diff, resolve manually, and restructure remaining tasks to avoid overlap.

### Teammate went off-track
Message them directly with correction. If too far gone, shut them down, spawn a replacement with clearer instructions.

### Lead implementing instead of coordinating
Enter delegate mode (Shift+Tab) to restrict yourself to coordination-only tools.
