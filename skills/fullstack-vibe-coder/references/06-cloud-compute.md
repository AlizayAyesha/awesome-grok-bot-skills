# Layer 6 — Cloud & Compute

Use this file when choosing runtimes, regions, containers, or serverless platforms. Pair with [05-hosting-deployment.md](05-hosting-deployment.md) and [11-load-balancing-scaling.md](11-load-balancing-scaling.md).

## Containers vs VMs

**Why it matters:** Containers vs VMs is a trade between packaging speed and isolation. The wrong one (or mixing them without a boundary) shows up as noisy neighbors or a painful ops story.

**Checklist for the agent**

- Use containers for app units you want to build once and run many times. Use VMs (or a managed platform) when you need a different OS, stronger isolation, or lift-and-shift software that assumes a machine.
- Do not treat a container as a VM: no important state on the local disk, no hand-patched packages in a running container.
- Know who patches the host and the base image. Schedule rebuilds.
- Size CPU/memory requests honestly so the scheduler can pack work without throttling surprises.

**Common vibe-coding mistakes:** SSHing into containers to "fix prod"; one giant VM running 15 processes you cannot deploy independently; no resource limits.

**Quick verification:** a fresh container/VM from the image boots without manual steps; disk is empty of user data after replace; limits are visible in the platform UI or manifests.

## Kubernetes

**Why it matters:** Kubernetes is a powerful orchestrator and an easy way to run a more complex system than the app needs.

**Checklist for the agent**

- Use Kubernetes when you have multiple services, need standard deploy/rollout/health semantics, and have people who can operate it (or a managed offering you understand).
- Define requests/limits, probes, PodDisruptionBudgets, and rolling update strategy. Run at least two replicas of public services.
- Store secrets in a secret store or sealed secrets, not plaintext in the repo. RBAC the cluster. Network policies for sensitive namespaces.
- Keep manifests in git (Infrastructure as Code). Watch upgrade policy for the control plane.

**Common vibe-coding mistakes:** a side-project cluster with no backup of etcd/state, `latest` tags, and a single replica Deployment; kubectl edit in production as the workflow.

**Quick verification:** `kubectl rollout` a change and a rollback in staging; kill a pod and confirm the service stays up; secrets are not in ConfigMaps.

**Links:** [Kubernetes documentation](https://kubernetes.io/docs/home/)

## Serverless Functions and Cold Starts

**Why it matters:** Serverless Functions scale to zero and per request, but Cold Starts, time limits, and connection pooling behave unlike a long-lived server.

**Checklist for the agent**

- Use serverless for bursty, short work and glue (webhooks, image transforms, cron). Be careful for low-latency, always-on APIs unless you keep warm instances or accept the tail latency.
- Reuse database connections carefully (global client, pool of 1, or a proxy). Do not open a new TCP connection to Postgres on every invocation without a plan.
- Timeouts, package size, and memory settings are part of the design. Log the cold-start path.
- Idempotency matters even more; at-least-once invocation is common.

**Common vibe-coding mistakes:** a 30s cold start on login; 1000 concurrent functions opening 1000 database connections; hiding a 15-minute job in a 10-second function.

**Quick verification:** invoke after 15 minutes idle and measure latency; watch connection counts under concurrency; confirm timeout + retry behavior.

## Edge Computing

**Why it matters:** Edge Computing runs code close to users. It is great for routing, auth checks, and lightweight personalization — not for heavy business logic or a fat SDK.

**Checklist for the agent**

- Keep edge handlers small and fast. Know the runtime limits (CPU, no arbitrary native modules, regional storage consistency).
- Do not put the primary database behind a global edge function without thinking about latency and connection limits. Use caches or regional origins.
- Be explicit about which region owns writes. Read [10-caching-cdn.md](10-caching-cdn.md) for cache keys at the edge.

**Common vibe-coding mistakes:** bundling an ORM into every edge request; assuming edge KV is strongly consistent worldwide; leaking secrets to a log at the edge.

**Quick verification:** measure origin vs edge latency; test a write then a read from another region; inspect bundle size.

## Regions and Availability Zones

**Why it matters:** A single data center is one outage. Regions and Availability Zones are how you survive a building, rack, or regional failure — if the app is actually deployed that way.

**Checklist for the agent**

- Know which region user data lives in (latency and sometimes Data Privacy rules). Document the primary and any failover region.
- Use multiple availability zones for load balancers, app tasks, and the database if the platform supports it.
- Data replication across regions is a product decision (RPO/RTO). "Multi-region" on the CDN is not the same as a multi-region database.
- Test DNS and data failover; do not assume they work.

**Common vibe-coding mistakes:** all instances in one AZ; a "global" frontend talking to a DB in one region 200ms away; no idea where backups live.

**Quick verification:** platform map of instances and the database; simulate an AZ loss in a drill if you can; ping times from a second region.

## Cost Monitoring

**Why it matters:** Cloud bills fail silently until the invoice. Cost Monitoring is part of reliability.

**Checklist for the agent**

- Enable billing alerts and budgets on day one (absolute and anomaly). Tag resources by environment and service.
- Watch the usual surprise meters: egress, logs/traces ingested, NAT, idle load balancers, unattached volumes, LLM tokens, and orphan snapshots.
- Right-size instances and turn off unused staging at night if appropriate.
- Review the bill after the first real traffic, not after a quarter.

**Common vibe-coding mistakes:** debug logging at 100% sample in production; a public bucket with terabytes of egress; no account-level cap.

**Quick verification:** a budget alarm exists and a test email/Slack arrives; a weekly 10-minute bill review is on the calendar.

## VPCs

**Why it matters:** VPCs (virtual private clouds) and private networks keep databases and internal admin tools off the public internet.

**Checklist for the agent**

- Place data stores, internal queues, and admin dashboards in private subnets. Public subnets only for load balancers or bastions.
- Use security groups / firewall rules that allow the minimum ports from the minimum sources. No `0.0.0.0/0` to SSH or Postgres.
- If you need human access, use a bastion, VPN, or cloud SSO tunnel — not an open SSH port. See SSH Keys in [08-security-rls.md](08-security-rls.md).
- Plan NAT and egress costs. Document network diagrams.

**Common vibe-coding mistakes:** RDS or Postgres with a public IP "so the laptop can connect"; security group inherited from a tutorial that allows the world.

**Quick verification:** from the public internet, database ports time out; the app still connects from inside the VPC; review inbound rules for every data store.
