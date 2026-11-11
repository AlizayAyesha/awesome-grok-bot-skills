---
name: write-pr-description
description: When writing or rewriting a pull request title and description from a diff, branch, or commit list so reviewers know what changed and why.
---

# Write a PR Description

Use this skill when the user wants a pull request title, body, or summary of a branch. Draft only — do not open or merge the PR unless they ask.

## Steps

1. Collect the diff, commit list, and any issue numbers the user mentioned. If you are missing the base branch, assume `main` and say so.
2. Restate the problem in one or two sentences, then what this change does about it.
3. Call out anything a reviewer could miss: migrations, feature flags, API or schema breaks, follow-up work, and how you verified it.
4. Keep the title under ~72 characters, imperative (`Add cursor pagination to /events`), no trailing period.

## Template

```markdown
## Why
<problem or context>

## What changed
- <concrete change>
- <concrete change>

## How to test
- [ ] <command or path to click>
- [ ] <edge case>

## Risk and rollout
- Breaking changes: <none / describe>
- Migrations or flags: <none / describe>
- Rollback: <revert is safe / needs a down migration>
```

## Rules

- Do not invent tests you did not see or run. If unknown, write "not verified here."
- Do not include secrets, tokens, or private customer data from the diff.
- Prefer bullets over essays. Link issues with the project's usual syntax (`Fixes #123`) only when the user provided the id.
