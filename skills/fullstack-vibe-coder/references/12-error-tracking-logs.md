# Layer 12 — Error Tracking & Logs

Use this file when adding logging, traces, alerts, or debugging production. Pair with [13-availability-recovery.md](13-availability-recovery.md) for incidents and [14-ai-process.md](14-ai-process.md) for how you read failures.

## Observability, Metrics, and Dashboards

**Why it matters:** Observability means you can explain *why* the system is behaving badly from the outside — not just that CPU is "kind of high." Metrics, logs, and traces work together. Dashboards are for questions you ask every day, not a wall of charts nobody watches.

**Checklist for the agent**

- Define a few golden signals per service: latency (p50/p95/p99), traffic, errors, and saturation (CPU, queue depth, pool usage).
- Metrics should have useful labels (route, status, tenant) but not unbounded labels (raw user id, email) that explode cardinality.
- Build a default Dashboard: request rate, error rate, latency, dependency health, and one business metric (signups, checkouts).
- Monitoring should cover user-facing symptoms, not only host metrics.
- Tie Observability back to SLOs (layer 13).

**Common vibe-coding mistakes:** 40 dashboards, no "is checkout okay?" view; a metric per unique user id; watching only CPU while the thread pool is exhausted.

**Quick verification:** using only the dashboard, explain the last deploy's effect; a forced 500 appears as a spike within a minute.

## Logging, Structured Logging, Log Levels, and Log Retention

**Why it matters:** Plain string logs cannot be searched reliably. Logging without levels or retention is either noise or a compliance pile.

**Checklist for the agent**

- Use Structured Logging (JSON or equivalent) with consistent fields: timestamp, level, message, service, Correlation IDs, route, status.
- Log Levels: `error` for failures that need attention, `warn` for degraded, `info` for significant business events, `debug` off in production unless briefly enabled.
- Do not log at info on every function entry in production.
- Set Log Retention by class (e.g. 7–30 days hot, longer only if legally required). Storage cost and privacy both grow with time.
- Make logs queryable in a central system. Do not SSH and `tail` as the only plan.

**Common vibe-coding mistakes:** `console.log` of entire request objects; debug left on; no rotation; a different log format per service.

**Quick verification:** emit one request and find it by field query; confirm retention in the log vendor; production default is not debug.

## Correlation IDs

**Why it matters:** A Correlation ID (request id) is the only way to follow one user's request across API, jobs, and third parties.

**Checklist for the agent**

- Accept an incoming request id or generate one (`X-Request-Id` / `traceparent`). Return it in the response and include it in every log line and downstream header.
- Propagate the id into Background Jobs and Webhooks you enqueue.
- Prefer W3C trace context if you use Distributed Tracing so logs and traces join.

**Common vibe-coding mistakes:** an id that dies at the first HTTP client call; logs that say "payment failed" with no id; clients that cannot see the id when they file a ticket.

**Quick verification:** trigger a flow that hits two services; search one id and see both; the client response header contains it.

## PII in Logs

**Why it matters:** PII in Logs (emails, names, tokens, card numbers, messages, addresses) turns your log vendor into a second, poorly governed database and can break Data Privacy rules.

**Checklist for the agent**

- Redact or never log passwords, cookies, Authorization headers, tokens, and raw card or bank data. Truncate or hash emails if you need a lookup key.
- Be careful with request bodies and "dump the user object." Provide a denylist and a test that fails if `password` or `token` appears.
- Access to logs should be restricted and audited like production data.
- Apply the same rules to error tracker breadcrumbs and frontend analytics.

**Common vibe-coding mistakes:** logging the full HTTP request; error screenshots that include a form; support tools that search logs by raw email stored in plain text without a policy.

**Quick verification:** grep a staging log stream for `@`, `Bearer`, and `password` after running signup and login; fix anything that matches.

## Error Tracking

**Why it matters:** Error Tracking (Sentry, Rollbar, or similar) groups stack traces so you see a *new* fault, not a wall of logs.

**Checklist for the agent**

- Capture unhandled exceptions on the server and a sampled, sanitized subset on the client. Include release version and Correlation IDs.
- Do not send PII or secrets in event context. Scrub headers and form fields.
- Alert on new issues or a rate spike, not on every single event. Assign an owner.
- Source maps and symbolication should work for production builds, stored privately.

**Common vibe-coding mistakes:** no release version, so every deploy looks like new bugs; the tracker is installed but the DSN is missing in prod; 10,000 copies of the same network flake with no fingerprinting.

**Quick verification:** `throw` in a staging route and confirm an event with stack, release, and request id; a second throw groups with the first.

## Alerting

**Why it matters:** Alerting that is too noisy trains people to ignore it. Alerting that is too quiet is an outage with a delay.

**Checklist for the agent**

- Alert on symptoms (error rate, SLO burn, queue age, failed payments) and on "the pipeline is down" (no data).
- Every alert has an owner, a Runbook link, and a severity. No orphan emails to a folder nobody reads.
- Tune thresholds after a week of baseline. Page only for things that should wake a human.
- Test notifications. Include silences for planned maintenance.

**Common vibe-coding mistakes:** an email per 404; a CPU 70% page at 2am; alerts that go only to the person who left the company.

**Quick verification:** a forced failure pages the right channel; a known noisy metric is a dashboard, not a page.

## Distributed Tracing

**Why it matters:** Distributed Tracing shows where time went across services (and usually proves the slowness is a downstream call or a lock, not "the server").

**Checklist for the agent**

- Trace inbound requests, outbound HTTP, DB, and queue publish/consume. Sample in production (e.g. 1–10%, or 100% of errors).
- Use one trace id aligned with Correlation IDs. Name spans after routes, not anonymous `GET`.
- Watch tail latencies, not only averages.

**Common vibe-coding mistakes:** 100% traces at full payload in production (cost and PII); traces that stop at the first HTTP client because headers were not propagated.

**Quick verification:** one checkout or login trace shows the handler, the DB, and at least one downstream call with timings.

## Debugging and Reading Error Messages

**Why it matters:** Debugging is a process. Reading Error Messages carefully is faster than rewriting the module or pasting the stack into a model without the context.

**Checklist for the agent**

- Read the **full** message, status code, and the first frame that is *your* code. Search the Correlation ID before you change code.
- Reproduce with the smallest input. Check recent deploys, config, and dependency changes.
- Distinguish "I don't understand this error" from "there is no error message" — add the latter as a product bug.
- Keep personally identifiable production data out of tickets and chat when you paste logs.

**Common vibe-coding mistakes:** ignoring `Caused by:`; fixing a symptom in the UI when the API 500 is a missing migration; retrying blindly until the error changes.

**Quick verification:** in a drill, a teammate can go from a 500 in the dashboard to the exact line using only logs, traces, and the error tracker.
