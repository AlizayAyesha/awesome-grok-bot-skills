# Layer 11 — Load Balancing & Scaling

Use this file when running more than one instance, planning for traffic growth, or placing a proxy in front of the app. Pair with [05-hosting-deployment.md](05-hosting-deployment.md), [06-cloud-compute.md](06-cloud-compute.md), and [13-availability-recovery.md](13-availability-recovery.md).

## Load Balancing

**Why it matters:** Load Balancing spreads traffic and, if health checks are honest, takes sick instances out of rotation. A balancer with sticky, lying health checks just hides outages.

**Checklist for the agent**

- Put at least two app instances behind a load balancer in production once you have real users.
- Health checks should hit a dedicated `/health` (or similar) that verifies critical dependencies you are willing to fail on — or a shallow liveness plus a deeper readiness probe. Do not use a heavy homepage as the check.
- Decide the algorithm (round robin, least connections). Use connection draining on deploy.
- Terminate TLS at the balancer or a Reverse Proxy and forward protocol/client IP headers carefully (`X-Forwarded-For`, `X-Forwarded-Proto`) only from trusted hops.
- For WebSockets or long requests, set idle timeouts that match the app.

**Common vibe-coding mistakes:** one instance "behind" a balancer; health checks that always return 200; trusting `X-Forwarded-For` from the public internet; leaving an instance in the pool during a crash loop.

**Quick verification:** stop one instance and confirm traffic moves; deploy with drain and no dropped in-flight requests; spoofed forwarded headers are ignored unless from the proxy.

**Links:** [MDN Load balancing](https://developer.mozilla.org/en-US/docs/Glossary/Load_balancing)

## Horizontal vs Vertical Scaling

**Why it matters:** Vertical scaling (bigger box) is simple until you run out of a bigger box. Horizontal scaling (more boxes) requires Stateless Services and shared storage.

**Checklist for the agent**

- Know which parts of the system scale horizontally (app servers, many workers) and which usually scale vertically or by sharding first (a single primary database).
- Measure the real bottleneck (CPU, RAM, I/O, locks, downstream APIs) before you "scale."
- For Horizontal vs Vertical Scaling decisions, write down cost, failover, and how sessions and jobs behave with N instances.
- Scale the database with indexes, read replicas, and connection pools before you multiply app servers that all stampede the same primary.

**Common vibe-coding mistakes:** adding app instances that each open 100 DB connections; paying for a huge VM because the query is O(n) with no index; assuming the database will "just scale" like the web tier.

**Quick verification:** load test with 1 vs 2 app instances; watch DB connections and latency; record the first upgrade you would buy and why.

## Stateless Services

**Why it matters:** If an instance stores unique state in memory, Load Balancing randomly logs people out and deploys drop work.

**Checklist for the agent**

- Keep app servers as Stateless Services: session data in a shared store (Redis/DB), uploads in Object Storage, job state in a queue.
- Any in-memory cache must be a performance hint, not the only copy.
- Cron and scheduled jobs should run once per cluster (a leader lock or a dedicated worker), not once per instance.
- Local disk is ephemeral. Do not write durable files to the container filesystem.

**Common vibe-coding mistakes:** `Map` of sessions in the Node process; file uploads to `./uploads` on the web box; a `setInterval` invoice job on every replica.

**Quick verification:** log in, then kill the instance you hit; the next request on another instance should still be authenticated. Run two instances and confirm a scheduled job fires once.

## Reverse Proxies

**Why it matters:** Reverse Proxies (Nginx, Caddy, Envoy, a managed load balancer) are where TLS, compression, request size limits, and routing usually belong.

**Checklist for the agent**

- Use a reverse proxy to terminate TLS, serve static assets or pass them to a CDN, and route `/api` to the app.
- Set max body size, header size, and timeouts. Buffer or stream based on the endpoint (uploads vs SSE).
- Hide internal ports. Do not expose the app container directly to the world if the proxy is the security boundary.
- Preserve WebSocket upgrade headers. Strip hop-by-hop headers correctly.
- Rate Limiting and WAF rules often live here — keep them consistent with the app.

**Common vibe-coding mistakes:** app listening on `0.0.0.0:3000` on a public VM "temporarily"; proxy timeouts shorter than file uploads; forgotten `Upgrade` headers breaking WebSockets.

**Quick verification:** only 443/80 open publicly; a large rejected body returns `413`; WebSockets still connect; `curl -I` shows expected security and cache headers from the proxy.

## Autoscaling

**Why it matters:** Autoscaling adds and removes instances as load changes. Bad metrics make it oscillate or scale too late to help.

**Checklist for the agent**

- Scale on a metric that matches pain (event-loop lag, queue depth, RPS vs p95 latency), not only average CPU.
- Set min and max counts. Min ≥ 2 if you need failover. Max is a cost and safety cap.
- Account for warmup (Cold Starts, JIT, cache fill). A scale-up that takes five minutes will miss a spike.
- Scale workers by queue depth. Scale the database independently; autoscale of app servers can overwhelm it.
- Test scale-down: connections drain, in-flight jobs finish, no lost sessions.

**Common vibe-coding mistakes:** min=0 on a latency-sensitive API; max unset (bill shock); scaling on CPU when the app is I/O bound; no cooldown, so the fleet flaps.

**Quick verification:** in staging, generate load and watch a new instance join and receive traffic; drain and scale in without 5xx; confirm cost alerts still make sense at max.
