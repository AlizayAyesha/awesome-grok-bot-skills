# Layer 13 — Availability & Recovery

Use this file when planning backups, uptime, incidents, or failover. Pair with [03-database-storage.md](03-database-storage.md) and [12-error-tracking-logs.md](12-error-tracking-logs.md).

## Backups, Point-in-Time Recovery, and Testing Backup Restores

**Why it matters:** Backups that have never been restored are a story you tell yourself. Point-in-Time Recovery (PITR) is how you undo an "oops, I deleted the table" at 14:07, not just last night's dump.

**Checklist for the agent**

- Automate Backups of the primary database and any object storage that is unique (user uploads). Store them in a different account/region from the primary.
- Encrypt backups at rest. Restrict who can read them. They contain everything.
- Enable Point-in-Time Recovery (WAL / binlog / vendor PITR) where a short RPO matters.
- Testing Backup Restores is mandatory: on a schedule, restore to a scratch instance, run a smoke query, and time how long it took. Write the steps in a Runbook.
- Define RPO (how much data you can lose) and RTO (how long you can be down). Check that the backup frequency and restore drill match those numbers.
- Do not keep the only backup on the same disk as the database.

**Common vibe-coding mistakes:** `pg_dump` in a cron that has been failing for months; backups in `./backups` on the web server; never restoring; no upload-bucket backup.

**Quick verification:** date of last *successful restore drill* (not last backup job); a restored instance answers `SELECT COUNT(*)` on a core table; object storage versioning or a replica exists.

**Links:** [PostgreSQL backup and restore](https://www.postgresql.org/docs/current/backup.html)

## Disaster Recovery

**Why it matters:** Disaster Recovery is the plan for "the region is gone," "the account is locked," or "someone ransomed the bucket" — not a failed deploy (that is a Rollback).

**Checklist for the agent**

- Write a short DR plan: what is "disaster," who decides, where the backups live, how DNS moves, and what you tell users.
- Know dependencies (IdP, DNS, email, payments, the cloud account itself). A second region does not help if DNS is the single point.
- Practice a tabletop once. After a real incident, update the plan.
- Keep offline copies of the plan and credentials path (a password manager, not only a wiki that is down).

**Common vibe-coding mistakes:** "we are on a big cloud so we are fine"; both prod and backups in one AZ; the only person who knows the registrar left.

**Quick verification:** someone who did not write the plan can find the restore steps and the DNS login path; backup location is a different failure domain.

## Uptime Monitoring

**Why it matters:** Uptime Monitoring from *outside* the cluster is how you learn you are down when logs are not coming in.

**Checklist for the agent**

- Probe HTTPS on the real hostname from more than one region. Check a page or endpoint that exercises the database, not only a static `/health` that never talks to it.
- Alert when probes fail twice (or similar) to avoid single-blip pages, but do not wait 20 minutes.
- Monitor TLS expiry, domain expiry, and the status of critical vendors.
- Track uptime as a complement to SLOs, not a vanity 100% badge.

**Common vibe-coding mistakes:** a monitor on the raw load-balancer IP that misses a DNS or cert problem; monitoring only staging; a probe that hits a cached CDN page in front of a dead origin.

**Quick verification:** temporarily fail staging's readiness and confirm an external monitor fires; cert expiry is also monitored.

## SLOs and SLAs

**Why it matters:** An SLO is a target you operate to (e.g. 99.9% successful checkouts over 30 days). An SLA is a contractual promise, usually weaker than the SLO, with consequences.

**Checklist for the agent**

- Pick one or two SLOs on user-facing journeys, not 40 internal metrics. Use error budgets to decide when to ship vs stabilize.
- Do not publish an SLA you cannot measure or survive. If you have no contract, you may have only SLOs — say so.
- Report SLOs on a Dashboard. Review them when you change architecture.

**Common vibe-coding mistakes:** marketing "five nines" on a single VM; an SLA with no measurement; SLO on CPU instead of user success.

**Quick verification:** the SLO number, window, and data source are written down; a week of data exists.

## Incident Response, On-Call, Runbooks, Postmortems, and Status Pages

**Why it matters:** Incidents are inevitable. The difference is whether anyone knows, can act, and learns afterwards.

**Checklist for the agent**

- **Incident Response:** define severity, a commander, a comms person, and a working channel. Record a timeline.
- **On-Call:** a rotation, an escalation, and a handoff. Compensate and constrain hours. The pager must reach a human, not a dead email.
- **Runbooks:** short, actionable pages for the top failures (db full, cert expired, queue stuck, auth vendor down). Link them from alerts.
- **Postmortems:** blameless, written, with root cause and follow-up tickets. Schedule them for anything user-visible or pager-worthy.
- **Status Pages:** a place to tell users the truth, preferably on a different provider than the app. Do not wait until you have a perfect design.

**Common vibe-coding mistakes:** the founder is the unofficial 24/7 on-call forever; a 20-page postmortem with no actions; updating Twitter but not the people mid-checkout; no status page because "we won't go down."

**Quick verification:** a game-day: who gets the page, which runbook they open, how they post a status update, and what ticket is filed after.
