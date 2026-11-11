# Layer 2 — APIs & Backend Logic

Use this file when adding routes, jobs, webhooks, validation, or API contracts. Pair with [04-auth-permissions.md](04-auth-permissions.md) and [08-security-rls.md](08-security-rls.md) for anything that mutates data.

## Input Validation and Server-Side Data Validation

**Why it matters:** The client is not a security boundary. Input Validation in the UI is a courtesy; Server-Side Data Validation is the real gate.

**Checklist for the agent**

- Validate type, length, range, format, and enum values on the server for every field. Reject unknown fields unless you have a reason to allow them (helps with Mass Assignment).
- Use a schema library (Zod, Pydantic, JSON Schema, etc.) and return `400` with field-level errors that do not leak internals.
- Re-validate values at trust boundaries (webhooks, jobs, admin imports), not only HTTP controllers.
- Sanitize or encode at output for the destination (HTML, SQL, shell) — validation is not a substitute for parameterization. See [08-security-rls.md](08-security-rls.md).
- File uploads: size, type (real content, not just extension), and storage path are validated on the server.

**Common vibe-coding mistakes:** required checks only in React; trusting `isAdmin` from the JSON body; parsing integers with overflow; "validation" that casts and continues on failure.

**Quick verification:** send missing, too-long, wrong-type, and extra fields; confirm `400` and no write. Bypass the UI with `curl`.

## CORS

**Why it matters:** CORS is a browser rule about which frontends may read responses. It is not an authentication system, and `Access-Control-Allow-Origin: *` with cookies is both invalid and a red flag.

**Checklist for the agent**

- Allow only the exact origins you own. No wildcard with `Access-Control-Allow-Credentials: true`.
- List methods and headers you actually use. Do not reflect arbitrary `Origin`.
- Preflight (`OPTIONS`) should be cacheable (`Access-Control-Max-Age`) and similarly protected.
- Server-to-server calls are not governed by CORS; those still need auth.

**Common vibe-coding mistakes:** `*` to "make the error go away"; echoing any Origin; using CORS as the only protection for a sensitive API.

**Quick verification:** a request from a disallowed origin is rejected; a credentialed request from the real app origin succeeds; review response headers.

**Links:** [MDN CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)

## HTTP Status Codes and Error Handling

**Why it matters:** Clients, retries, and monitors all branch on HTTP Status Codes. Error Handling should be consistent and safe.

**Checklist for the agent**

- Use `201` for creates, `204` when there is no body, `400` validation, `401` unauthenticated, `403` authenticated but forbidden, `404` missing, `409` conflict, `429` rate limit, `5xx` only for the server's fault.
- Do not return `200` with `{ "error": ... }` as the default pattern.
- Map exceptions to a single error shape (`code`, `message`, `request_id`). Hide stack traces and SQL in production.
- Fail closed on unexpected errors. Log the real cause with a Correlation ID (layer 12).
- For batch endpoints, document partial-failure behavior.

**Common vibe-coding mistakes:** every error is a `500`; leaking `e.message` from a database driver; swallowing exceptions and returning an empty list.

**Quick verification:** table-driven tests for auth, missing, and validation paths; produce a 500 in staging and confirm the client body has no stack but the log does.

**Links:** [MDN HTTP status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)

## Timeouts, Retries, Exponential Backoff, and Circuit Breakers

**Why it matters:** A hanging outbound call ties up a worker forever. Blind Retries turn a blip into an outage or a double charge.

**Checklist for the agent**

- Set Timeouts on every outbound HTTP, DB, and RPC call (connect and overall). No library default of "infinity."
- Retry only idempotent operations, or when you have an Idempotency key. Use Exponential Backoff with jitter.
- Cap retries. Distinguish 429/503 (retry) from 400/401/403/404 (do not retry).
- Circuit Breakers (or equivalent budget) stop calling a dead dependency and fail fast after a threshold, then probe to recover.
- Apply the same ideas to queue consumers.

Example (conceptual):

```ts
await callWithRetry(fn, { retries: 3, baseMs: 100, jitter: true, timeoutMs: 2000 });
```

**Common vibe-coding mistakes:** retrying POST /charge three times; no timeout on the payment SDK; a breaker that never resets; backoff without jitter that thunders the herd.

**Quick verification:** point a client at a blackhole port and confirm you fail in ~timeout; a 500ing stub is retried with growing delays; a 400 is not.

## Idempotency

**Why it matters:** Networks retry. Users double-click. Queue workers redeliver. Idempotency means those retries do not create a second order, email, or payment.

**Checklist for the agent**

- Accept an `Idempotency-Key` (or provider equivalent) on payment and other mutating endpoints. Store the key, request hash, and response; replay the same result on a repeat.
- Make webhook handlers idempotent by event id (see [extras.md](extras.md) for payments).
- Prefer unique constraints in the database to enforce "only one of these" rather than a check-then-insert.
- GET, PUT, and DELETE should be naturally idempotent; POST often needs extra help.

**Common vibe-coding mistakes:** unique in the app layer only; keys stored in memory; treating "I already sent 200" as proof the client received it so a retry is a new request.

**Quick verification:** send the same create twice with the same key — one side effect. Two keys — two side effects. Concurrent same-key requests do not double-write.

## API Gateways

**Why it matters:** An API Gateway can centralize auth, Rate Limiting, TLS, and routing — or become an unreviewed blob of rewrite rules.

**Checklist for the agent**

- Know what the gateway enforces vs what the service still must enforce (Authorization especially).
- Keep routing, request size limits, and timeouts explicit. Version paths carefully.
- Do not put business logic only in the gateway if nobody can test it in CI.
- Observe gateway 4xx/5xx separately from app errors.

**Common vibe-coding mistakes:** stripping auth headers; a 30s gateway timeout on a 60s upload; assuming the gateway's IP allow list means the app can skip auth.

## Message Queues, Background Jobs, and Cron Jobs

**Why it matters:** If you do slow work in the request, the user waits and the timeout wins. Message Queues, Background Jobs, and Cron Jobs need the same care as APIs: retries, idempotency, and visibility.

**Checklist for the agent**

- Put emails, image processing, webhooks-out, and reports on a queue. The HTTP handler should persist the work and return quickly.
- Consumers must be idempotent, have a dead-letter queue, and limit concurrency so they cannot crush the database.
- Cron Jobs should run once per cluster (distributed lock or a single scheduler). Emit a metric when a job is late or skipped.
- Visible timeouts and heartbeats so a dead worker does not hold a message forever. Prefer at-least-once delivery + idempotency over "exactly once" folklore.
- Do not hide scheduled billing or data deletion only on a developer's laptop clock.

**Common vibe-coding mistakes:** `await sendEmail()` in the request with no fallback; a cron on every Kubernetes pod; failed jobs retried into infinity; no dashboard of queue depth.

**Quick verification:** enqueue a job, kill the worker mid-way, confirm retry or dead-letter; run two instances and confirm a cron fires once; a metric exists for lag.

## Webhooks

**Why it matters:** Webhooks are unauthenticated HTTP unless you verify them. They also arrive late, twice, or out of order.

**Checklist for the agent**

- Verify signatures and timestamps. Reject unsigned events. Use HTTPS endpoints.
- Respond quickly (`200`) and process asynchronously if work is heavy. Make handlers idempotent by event id.
- Rotate signing secrets. Store raw event ids. Do not trust a webhook body for amounts without checking the provider or your records.
- Provide a replay tool for development. List outbound webhooks you send with retries and signing of your own.

**Common vibe-coding mistakes:** no signature check; doing five seconds of work before responding (the provider times out and retries); assuming order.

**Quick verification:** a replayed event does not double-apply; a bad signature is `401`/`400`; see also payments in [extras.md](extras.md).

## REST, GraphQL, and WebSockets

**Why it matters:** REST, GraphQL, and WebSockets are tools. Mixing them carelessly (a GraphQL mutation with no auth, a WebSocket with no timeout) creates holes.

**Checklist for the agent**

- **REST:** resource-oriented URLs, correct verbs and status codes, pagination, consistent error shape, HATEOAS optional, but stability matters.
- **GraphQL:** cap query depth/cost, disable risky introspection in production if that is your policy, authorize per field, and watch N+1 resolvers (dataloaders).
- **WebSockets:** authenticate on connect, re-authorize on sensitive events, heartbeat, backpressure, and a plan for horizontal scale (pub/sub, not one process memory).
- Do not expose both a loose REST debug route and the "real" API in production.

**Common vibe-coding mistakes:** GraphQL `any` query from the browser talking to admin fields; WebSockets that never expire; REST verbs that all map to POST.

**Quick verification:** an unauthorized request fails on all three styles; a GraphQL cost limit trips on a deeply nested query; a second app instance still delivers a socket event.

## API Versioning and API Documentation

**Why it matters:** Clients you do not control will not deploy the same day you do.

**Checklist for the agent**

- API Versioning: pick a scheme (`/v1`, header, or date) and a deprecation policy. Breaking changes go in a new version; add fields tolerantly.
- API Documentation: an OpenAPI (or GraphQL schema) that is generated or tested against the real routes. Include auth, errors, rate limits, and examples.
- Publish changelog notes for external APIs. Remove "try it" tools that hit production without auth.

**Common vibe-coding mistakes:** breaking a field type in place; docs that were written once at the hackathon; version in the URL that is ignored in code.

**Quick verification:** contract tests or spectral/lint against OpenAPI; a stale-client test still works on `v1` after a `v2` change.

## Pagination

**Why it matters:** Unbounded lists will eventually load the entire table. Pagination belongs on every collection endpoint.

**Checklist for the agent**

- Default and maximum page sizes (e.g. 20 / 100). Never `LIMIT` without a stable `ORDER BY`.
- Prefer cursor/keyset pagination for large or real-time lists (see Cursor-Based Pagination in [03-database-storage.md](03-database-storage.md)); offset is acceptable for small, stable admin tables.
- Return a next cursor or a clear "no more" signal. Do not leak total counts if they are expensive or sensitive unless needed.
- Apply the same filters when counting as when listing.

**Common vibe-coding mistakes:** `SELECT * FROM events` in the API; page 2 of offset pagination that duplicates rows when a new insert lands; no max page size.

**Quick verification:** request `pageSize=999999` and confirm it is capped; walk two pages with a write in between and look for dupes/skips on the cursor API.

## Concurrency, Async/Await, Memory Leaks, and Profiling

**Why it matters:** Concurrency bugs and Memory Leaks show up under load, usually after you shipped.

**Checklist for the agent**

- **Async/Await:** await every promise you care about; handle rejection; do not mix callbacks and forgotten promises. In Python, know which calls block the event loop.
- **Concurrency:** protect shared in-process state; use transactions and locks for shared data; be explicit about parallelism (`Promise.all` vs sequential) and limits (`p-limit`).
- **Memory Leaks:** caches with no bound, global arrays of sockets, listeners not removed, large closures retained. Heap snapshots in staging under load.
- **Profiling:** measure before rewriting. CPU and heap profiles, query plans, and traces beat guesswork.

**Common vibe-coding mistakes:** `fire-and-forget` promises that fail silently; `Promise.all` on 10,000 outbound calls; a module-level cache `Map` that grows forever; "optimize" without a profile.

**Quick verification:** a load test with a heap snapshot that is stable after GC; unhandledRejection / asyncio exception hooks count at zero; a profile attached to the slow route.

## Feature Flags and A/B Testing

**Why it matters:** Feature Flags let you ship dark and turn on in production. A/B Testing is an experiment with a hypothesis, not a random `Math.random()` in the render path.

**Checklist for the agent**

- Flags have a default, an owner, and a removal date. Evaluate flags server-side for security-sensitive behavior (the client can lie).
- Do not nest flags into an untestable matrix. Clean up flags after rollout.
- A/B Testing: stable assignment (user id hash), a documented metric, a start/stop time, and enough sample size to matter. Do not test and "just ship the winner" from 20 users.
- Keep experiment assignment out of the CDN cache key unless you intend to (layer 10).

**Common vibe-coding mistakes:** a flag left on in the code for a year; using flags as a half-finished config system; A/B based on IP so a user flips variants each request.

**Quick verification:** flip a flag without a deploy; a security-sensitive flag cannot be forced from the client; experiment assignment is sticky in a test.
