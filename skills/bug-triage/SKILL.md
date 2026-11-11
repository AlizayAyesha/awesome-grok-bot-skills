---
name: bug-triage
description: When triaging a bug report, log, or incident note — reproducing if possible, classifying severity, and proposing the next debug or fix step.
---

# Bug Triage

Use this skill when the user reports a bug, pastes a stack trace, or asks you to triage a list of issues. Investigate first; do not jump to a large rewrite.

## Steps

1. Restate the expected vs actual behavior in one sentence. List what you still need (steps, environment, request id, version).
2. Classify, with a one-line reason:
   - **Severity:** blocker, high, medium, low (user impact, blast radius, data loss or security).
   - **Type:** regression, data, logic, integration, UX, performance, security.
3. Try to find a likely locus from the stack, logs, or recent changes. Prefer Reading Error Messages fully (including "Caused by") before proposing a new architecture.
4. Propose the smallest next experiment: a failing test, a query, a feature flag off, or a log line — not five unrelated refactors.
5. If you suggest a fix, say how you would verify it and what could go wrong (especially data migrations and permissions).

## Output

- Symptom and impact
- Severity and confidence
- Leading hypothesis
- Next check
- Suggested fix (only if confidence is high) plus test plan

## Rules

- Do not claim you reproduced a production-only bug if you did not.
- Security-sensitive bugs (auth bypass, injection, data leak) get a higher severity and a careful write-up — no full exploit recipes for third-party systems.
- Strip secrets and PII from any quoted logs in your reply.
