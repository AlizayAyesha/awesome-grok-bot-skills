# Layer 7 — CI/CD & Version Control

Use this file when branching, reviewing, linting, or automating checks. Pair with [14-ai-process.md](14-ai-process.md) for tests and code review of AI output, and [08-security-rls.md](08-security-rls.md) for dependency risk.

## Git, Branching Strategies, Merge Conflicts, Rebasing, and Pull Requests

**Why it matters:** Git is how you collaborate and how you go back in time. A messy default branch is a production risk.

**Checklist for the agent**

- Use Git (not a folder of zips). `main` (or `trunk`) is protected: no direct pushes for humans in a team setting, required reviews, required CI.
- Branching Strategies: short-lived feature branches or trunk-based with flags. Avoid long-lived "dev" branches that only merge when they hurt.
- Pull Requests: small, described, with tests and a screenshot or API example when useful. One concern per PR when you can. Do not merge your own change on a team without a review policy exception.
- Rebasing is fine for unpushed or agreed local cleanup; do not rebase shared branches without coordination. Do not rewrite published release tags.
- Merge Conflicts: resolve deliberately, re-run tests, and look for duplicated blocks or dropped security checks — conflict markers must never ship.

**Common vibe-coding mistakes:** force-push to `main`; 3,000-line PRs titled "updates"; committing conflict markers; a branch that lived three months.

**Quick verification:** branch protection is on; CI is required; a test PR cannot merge if CI is red.

## Commit Messages, .gitignore, Git Tags and Releases, Changelogs, and Semantic Versioning

**Why it matters:** The history is documentation you will search during an incident.

**Checklist for the agent**

- Commit Messages: imperative, specific (`Hash refresh tokens before persist`), not `fix` or `wip`. Use a body when the why is not obvious.
- `.gitignore`: include `.env`, secret files, `node_modules`, build output, OS junk, and editor folders. Confirm they were never tracked (`git ls-files`).
- Git Tags and Releases: tag what you deploy (`v1.4.0` or a git SHA you record). Tags used for releases should be annotated and not moved.
- Changelogs: user-facing notes for shipped versions (features, fixes, breaking changes). Generate or edit them from PRs, not from memory a month later.
- Semantic Versioning (`MAJOR.MINOR.PATCH`) for libraries and public APIs. A breaking API change is a major bump. Apps can version by date or SemVer — be consistent.

**Common vibe-coding mistakes:** committing `.env` then "ignoring it later" (it stays in history); `latest` with no tag; changelog that is empty or marketing-only.

**Quick verification:** `git ls-files |` secrets patterns empty; a release tag points at the artifact you deployed; CHANGELOG has the last version.

**Links:** [Semantic Versioning](https://semver.org/), [gitignore documentation](https://git-scm.com/docs/gitignore)

## CI/CD, Linting, Formatting, Type Safety, and Pre-Commit Hooks

**Why it matters:** CI/CD is the gate that keeps broken or unsafe code off the default branch and out of production.

**Checklist for the agent**

- On every Pull Request: install from the lockfile, Lint, typecheck, unit/integration tests, and a production build. On `main`: deploy to staging, then production with approval or a baked pipeline.
- Fail the pipeline on lint, type, or test errors — not `|| true`. Cache dependencies honestly (keyed on the lockfile).
- Formatting (Prettier, Black, gofmt, etc.) is automatic so review is not about spaces. Linting covers bugs and a few security rules, not taste wars.
- Type Safety: enable strict TypeScript/mypy/etc. in CI. Do not add `any` / `# type: ignore` to "make CI green" without a reason.
- Pre-Commit Hooks (pre-commit, husky, leftover): useful for format and secret scanning on the developer machine; they are not a substitute for CI (hooks can be skipped).
- Store CI secrets in the platform vault. Least-privilege deploy keys. Do not reuse personal access tokens.

**Common vibe-coding mistakes:** CI only runs on `main` after merge; a 20-minute install with no cache; types skipped; deploy from a laptop.

**Quick verification:** a typo or failing test in a PR is red; a green `main` build is what production runs; no long-lived secrets in workflow files.

## Code Review

**Why it matters:** Code Review is where you catch IDOR, missing tests, and hallucinated packages — especially when the patch was AI-generated (layer 14).

**Checklist for the agent**

- Review for correctness, security, observability, and tests — not only style (the linter does style).
- Call out missing Authorization, migrations, and rollback notes. Ask "how do we know this works?" 
- Keep reviews timely and scoped. A nit should not block a safe fix; a security hole should.
- Do not rubber-stamp huge generated diffs. If you cannot read it, split it.

**Common vibe-coding mistakes:** approving to "unblock"; reviewing only the description; ignoring deleted tests.

**Quick verification:** a recent PR shows a real conversation about a risk; AI-heavy PRs have a checklist (layer 14).

## Package Managers, Lockfiles, Dependency Pinning, and License Compliance

**Why it matters:** The supply chain of your app is your app. See also Dependency Vulnerabilities in layer 8.

**Checklist for the agent**

- Use the standard Package Managers for the stack (npm/pnpm/yarn, pip/uv/poetry, cargo, go modules). Commit Lockfiles and install with `--frozen-lockfile` / `npm ci` in CI.
- Dependency Pinning: lock exact versions for production installs. Review upgrades; do not depend on floating `latest`.
- Avoid unnecessary dependencies (each is code you now operate). Prefer well-maintained libraries.
- License Compliance: know which licenses you ship. GPL in a proprietary product, or missing attribution, is a legal problem. Automated scanners help; someone still has to read the report.
- Command Line Basics for installs belong in the README (see layer 14), including the package manager version.

**Common vibe-coding mistakes:** deleting the lockfile to resolve a conflict; `npm i package` without review; a transitive GPL dependency you did not notice; committing `node_modules`.

**Quick verification:** CI uses the lockfile; `license` check job or a periodic report; `git ls-files node_modules` is empty.

## Security Scanning (SAST/DAST)

**Why it matters:** Security Scanning (SAST/DAST) is automated review for known bug patterns and some runtime issues. It does not replace thinking, but it catches the easy misses.

**Checklist for the agent**

- SAST (static): run in CI on the default branch and PRs (CodeQL, Semgrep, language tools, secret scanners). Fix or formally accept findings; do not leave hundreds of ignored alerts.
- DAST (dynamic): scan a staging environment for obvious issues (headers, forgotten routes) when you have a running app.
- Also scan containers and Infrastructure as Code. Fail on high/critical dependency CVEs with a documented exception process.
- Secret scanning should catch keys before they reach `main` (and hook git history if they already did — then rotate).

**Common vibe-coding mistakes:** a SAST badge that nobody opens; ignoring `npm audit` because it is noisy; DAST against production with destructive payloads.

**Quick verification:** a known bad pattern (e.g. a dummy `eval` or a fake AWS key in a test PR) is flagged; dependency scan is in the required checks.

**Links:** [OWASP CI/CD Security](https://owasp.org/www-project-devsecops-guideline/)
