---
name: code-review
description: When reviewing a pull request, diff, or changeset for correctness, security, tests, and maintainability before merge.
---

# Code Review

Use this skill whenever the user asks you to review a PR, a local diff, or a set of commits. Focus on defects and risk, not style that a linter already covers.

## Steps

1. Identify the scope: branch, files, and the stated intent (bug fix, feature, refactor). If the intent is missing, infer it from the diff and state your assumption.
2. Skim the whole diff once for shape (too large? mixed concerns? generated files?).
3. Walk each change and check:
   - Correctness and edge cases (empty input, retries, concurrency).
   - Authorization and validation on new or changed endpoints.
   - Secrets, logging of PII, and unsafe query or HTML construction.
   - Tests that would fail if the change were wrong. Note missing coverage of the risky path.
   - Migrations and backward compatibility if the schema or API moved.
4. Separate blocking issues from nits. Do not block on formatting if a formatter is already in CI.
5. Write a summary a merger can act on.

## Output

- **Verdict:** approve, request changes, or comment (not enough confidence).
- **Blocking:** numbered findings with file and brief why.
- **Non-blocking:** nits and suggestions.
- **Tests I would still want:** short list, or "existing tests cover this."

## Rules

- Do not rubber-stamp a diff you only summarized. If you cannot run or read the tests, say so.
- For AI-generated patches, verify packages and APIs exist (see also `fullstack-vibe-coder`).
- Do not commit or merge unless the user explicitly asks.
