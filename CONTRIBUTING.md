# Contributing

Thanks for helping grow this list. This repository has two kinds of contribution: **index entries** (links to skills that already exist elsewhere) and **starter skills** (original `SKILL.md` files in this repo).

The curated index is inspired by, and largely drawn from, [sergebulaev/awesome-agent-skills](https://github.com/sergebulaev/awesome-agent-skills). Please keep credits accurate.

## Adding an index entry

Open a pull request that adds one bullet under the right category in `README.md`:

```markdown
- [owner/skill-name](https://github.com/owner/repo/tree/main/path-to-skill) — One-line description of what it does. Author: Owner or Org.
```

Rules:

- Link the **original source** (the skill's repo or folder), not a mirror or copy.
- Use a real, working URL. Do not invent paths.
- Give a one-line description and credit the original author or organization.
- Linked third-party skills keep **their own licenses**. Do not re-license them here.
- Prefer skills that have a `SKILL.md` (or equivalent) with a clear when-to-use description and concrete instructions. Skip mass-generated filler.
- One skill per bullet. Do not paste the skill's full text into the README.

## Adding or improving a starter skill

Original skills live in `skills/<kebab-slug>/SKILL.md`.

```markdown
---
name: skill-name
description: When to use this skill, in one or two sentences an agent can match against.
---

# Skill Title

Short setup, then step-by-step instructions. Keep it generic: no personal data, no secrets, no private URLs.
```

Rules:

- Write **original wording**. Do not copy another author's skill text verbatim.
- Frontmatter must include `name` and `description`. The description should say *when* an agent should load the skill.
- Keep instructions concise and actionable. If you need more depth, add a `references/` file next to `SKILL.md` and tell the agent when to open it.
- Draft-only communication skills (email, outreach, social posts) must say the agent should not send anything unless the user explicitly asks.
- If you change `skills/`, also update the table in `skills/README.md`.

The `fullstack-vibe-coder` skill is the production-readiness guide, organized as 14 production layers. Improvements should keep topic coverage complete (run the check in `skills/fullstack-vibe-coder/COVERAGE.md`), keep the main `SKILL.md` scannable, and put deep checklists in `skills/fullstack-vibe-coder/references/` (one file per layer).

## Pull requests

- Use a clear title (`Add index entry: firebase/firebase-auth-basics`, `Fix typo in seo-audit`).
- Keep unrelated changes out of the same PR.
- By contributing, you license your original work in this repository under the MIT License.
