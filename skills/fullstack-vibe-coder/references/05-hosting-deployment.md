# Layer 5 — Hosting & Deployment

Use this file when deploying, configuring environments, DNS, or TLS. Pair with [06-cloud-compute.md](06-cloud-compute.md) and [07-cicd-version-control.md](07-cicd-version-control.md).

## Environment Variables

**Why it matters:** Environment Variables are the usual way to inject config, and the usual way secrets leak into git, logs, and the client bundle.

**Checklist for the agent**

- Keep config in the environment (or a secret manager), not hardcoded. Provide `.env.example` with dummy values only.
- Never commit `.env`. Never prefix a secret with `NEXT_PUBLIC_`, `VITE_`, or any other client-exposed prefix.
- Fail fast at boot if required variables are missing. Validate types (URLs, booleans, integers).
- Do not bake secrets into Docker images. Inject at runtime.

**Common vibe-coding mistakes:** a real API key in `.env.example` or a screenshot; changing a var and forgetting to restart; assuming "private" env vars are invisible if they were inlined at build time.

**Quick verification:** search the built client bundle for secret prefixes and known key patterns; start the app with a var unset and confirm it refuses to boot.

**Links:** [The Twelve-Factor App: Config](https://12factor.net/config)

## Docker and Docker Compose

**Why it matters:** Docker packages the app consistently; Docker Compose describes a local or small-stack of services. A fat, root, latest-tagged image is not "done."

**Checklist for the agent**

- Use a specific base image tag, not `latest`. Prefer slim/distroless and a non-root user.
- Multi-stage builds so compilers and dev dependencies stay out of the final image. `.dockerignore` must exclude `.env`, `.git`, and `node_modules`.
- One process per container as a default. Persist data in volumes, not the container filesystem.
- Docker Compose for local parity (app, db, redis) should not be copied blindly as a production orchestrator unless you have a real plan.
- Pin compose image versions. Separate bind mounts for development from production configs.

**Common vibe-coding mistakes:** running as root; copying secrets into the image; 2GB images including the entire monorepo; compose `ports: 5432:5432` on a public VM.

**Quick verification:** `docker run --read-only` (with needed tmpfs) still boots; image is scanned; `docker compose up` in a clean checkout works from docs.

## Staging Environments and Environment Parity

**Why it matters:** If staging is a laptop and production is a cluster, you will discover failures only in production.

**Checklist for the agent**

- Maintain Staging Environments that use the same shape as production (same container, same edge, similar services) with **separate** data, keys, and payment/email modes.
- Environment Parity means similar versions, feature flags, and migrations — not a copy of production PII.
- Seed staging with realistic fake data. Practice deploys and Rollbacks there first.
- Protect staging from the public internet if it is not meant to be public (HTTP basic auth, SSO, IP allow list).

**Common vibe-coding mistakes:** "staging" that has not been updated in months; production credentials in staging; testing only on SQLite while prod is Postgres.

**Quick verification:** a checklist of services and versions prod vs staging; a dry-run migration against a staging dump (sanitized).

## Configuration Management

**Why it matters:** Configuration Management is how you know which flag, URL, or limit is live in each environment without SSHing in to guess.

**Checklist for the agent**

- Centralize config (env, feature flags, secret manager). Document every key and its default.
- Make changes auditable. Avoid snowflake edits on a single box.
- Keep environment-specific config out of application code (`if hostname == 'prod'`).
- Encrypt secrets at rest in whatever store you use; restrict who can read prod values.

**Common vibe-coding mistakes:** editing Nginx on the server by hand; three competing `.env` files; a boolean flag that is a string `"false"` and therefore truthy.

**Quick verification:** dump effective config at boot (redact secrets); change a non-secret flag through the official path and confirm it applies.

## Rollbacks, Rolling Deployments, and Blue-Green Deployments

**Why it matters:** A deploy that cannot be undone is an outage waiting to happen.

**Checklist for the agent**

- **Rollbacks:** keep the previous artifact and a one-command or one-click rollback. Database migrations must be backward compatible so the old app can still run (see Zero-Downtime Migrations).
- **Rolling Deployments:** replace instances in batches behind the load balancer with health checks and drain.
- **Blue-Green Deployments:** run the new version in parallel, switch traffic, and keep the old version warm until you are confident.
- Automate deploys in CI/CD. Record who shipped what version.

**Common vibe-coding mistakes:** `migrate` that drops a column the old instances still read; no retained images; "rollback" meaning restore a 24-hour-old database backup.

**Quick verification:** deploy a harmless change to staging, roll it back, and confirm the previous version serves health checks and a smoke test.

## Domain Names, DNS, HTTPS/TLS, and SSL Certificate Renewal

**Why it matters:** Users reach you through Domain Names and DNS; browsers will warn or block without valid HTTPS/TLS. Expired certificates are a full outage.

**Checklist for the agent**

- Use a registrar and DNS host you control. Keep TTLs reasonable. Document apex and `www` redirects. Prefer multiple nameservers.
- Force HTTPS. Enable TLS 1.2+ only. Turn on HSTS once you are sure HTTPS works on all hosts (including APIs and assets).
- Automate SSL Certificate Renewal (Let's Encrypt or your cloud cert manager) and alert on certificates that expire within 14–30 days. Cover every hostname you actually serve, including `api.` and `cdn.`.
- Do not disable certificate verification in clients "to make it work."

**Common vibe-coding mistakes:** cert on the apex but not `www`; renewal cron that silently failed; mixed-content HTTP assets; DNS still pointing at an old IP.

**Quick verification:** SSL Labs or `openssl s_client` for each hostname; calendar or monitor for expiry; HTTP requests redirect to HTTPS.

**Links:** [Let's Encrypt docs](https://letsencrypt.org/docs/), [MDN HTTPS](https://developer.mozilla.org/en-US/docs/Glossary/HTTPS), [MDN HSTS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security)

## Health Checks

**Why it matters:** Health Checks tell the balancer and your monitors whether to send traffic or page a human. A lying check is worse than none.

**Checklist for the agent**

- Split **liveness** (process is up) from **readiness** (this instance can take traffic — database and critical deps reachable).
- Keep checks cheap and authenticated or internal-only if they leak stack details.
- Do not mark the app unready because a non-critical optional service is down, unless you mean to drop all traffic.
- Graceful Shutdown should stop passing readiness first, then drain.

**Common vibe-coding mistakes:** `/health` that always prints `ok`; a check that runs a heavy query and becomes the outage; exposing internal versions publicly if that is not intended.

**Quick verification:** stop the database in staging and confirm readiness fails while the orchestrator stops routing; liveness does not flap.

## Graceful Shutdown

**Why it matters:** Without Graceful Shutdown, deploys and crashes cut in-flight requests and leave half-written jobs.

**Checklist for the agent**

- Listen for `SIGTERM`. Stop accepting new work, finish in-flight requests within a deadline, close the HTTP server, then close DB pools.
- Push incomplete jobs back to the queue. Do not `process.exit(0)` immediately on signal.
- Align proxy idle timeouts, orchestrator `terminationGracePeriodSeconds`, and the app's shutdown deadline.

**Common vibe-coding mistakes:** the process dies on SIGTERM with 50 open requests; Kubernetes kills the pod at 30s while the app waits 60s.

**Quick verification:** start a slow request, send SIGTERM, confirm the request completes (or is cleanly 502 after drain) and no new request is accepted.

## Infrastructure as Code

**Why it matters:** If the real infrastructure lives only in a console, you cannot review, reproduce, or recover it.

**Checklist for the agent**

- Describe cloud resources in Infrastructure as Code (Terraform, CloudFormation, Pulumi, or the host's file format). Review diffs in pull requests.
- Remote state with locking. No manual drift, or detect it. Separate state per environment.
- Never commit state files or cloud secret keys. Use a least-privilege deploy role.

**Common vibe-coding mistakes:** "just click a bucket in the dashboard"; committing `terraform.tfstate`; one state file for all environments.

**Quick verification:** a clean apply from CI in staging; `plan` shows no unexpected drift; secrets are not in the repo.

## Vendor Lock-In

**Why it matters:** Vendor Lock-In is a trade, not a moral failure — but you should know the exit cost before you store all user data in a proprietary API.

**Checklist for the agent**

- Prefer open formats and standard protocols (SQL, S3-compatible APIs, OIDC) at the boundaries that would be painful to move.
- Isolate vendor SDKs behind a small module. Keep exports of customer data you are obliged to release.
- Document what would be hard to migrate (queues, auth, search, AI APIs) and accept or mitigate that risk.

**Common vibe-coding mistakes:** business logic written as proprietary workflow glue with no export; assuming "we can switch later" with no dump path.
