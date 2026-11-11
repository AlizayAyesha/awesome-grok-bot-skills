---
name: api-docs-writer
description: When writing or updating API documentation for HTTP or GraphQL endpoints — overview, auth, request/response examples, errors, and changelog notes.
---

# API Docs Writer

Use this skill when the user wants documentation for an API (OpenAPI-style prose, a README section, or examples). Document what the API actually does. Do not invent endpoints.

## Steps

1. Collect the source of truth: route handlers, an existing OpenAPI file, or the user's list. If something is unspecified, mark it `TODO` rather than guessing a status code.
2. Write a short overview: base URL placeholder, auth method, and versioning policy if known.
3. For each endpoint include:
   - Method and path
   - Who can call it (authz)
   - Path/query/body parameters with types and required flags
   - Success response (status and example JSON)
   - Important errors (`401`, `403`, `404`, `409`, `429`, `4xx` validation)
   - Idempotency, pagination, or rate-limit notes when they apply
4. Use realistic but fake example data (`user_123`, `1990-01-01T00:00:00Z`). Never paste live secrets or real customer records.
5. If the API changed, add a short changelog entry (breaking vs additive).

## Rules

- Examples must match the field names in code. If you did not see the handler, say the docs are a proposal.
- Prefer one complete happy-path example over six partial ones.
- Do not document a secret internal endpoint as public unless the user wants that.
