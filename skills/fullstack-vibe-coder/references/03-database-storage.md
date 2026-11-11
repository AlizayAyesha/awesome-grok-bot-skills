# Layer 3 — Database & Storage

Use this file when designing schema, queries, migrations, or file storage. Pair with [08-security-rls.md](08-security-rls.md) for Row-Level Security and SQL Injection, and [13-availability-recovery.md](13-availability-recovery.md) for backups.

## Schema Design, Normalization, and Denormalization

**Why it matters:** Schema Design is the long-term shape of the product. Guessing it from a mock JSON blob usually produces a table that cannot answer the second feature's questions.

**Checklist for the agent**

- Model the real entities and relationships first. Choose **Normalization** (typically 3NF) as the default so each fact lives in one place.
- **Denormalization** is a measured cache (a count column, a materialized path) with a documented update path — not "we also store the whole user on every row because GraphQL wanted it."
- Avoid generic `json` columns for data you will filter or enforce. JSONB is fine for genuine extension attributes.
- Plan uniqueness, lifecycle (draft/published), and multi-tenant boundaries (`tenant_id` on every tenant-owned table) up front.

**Common vibe-coding mistakes:** one `data` JSON blob for the whole app; copying a TypeScript type 1:1 into tables; denormalized names that go stale.

**Quick verification:** list tables, keys, and the questions the UI asks; every question has a plausible query with constraints.

**Links:** [PostgreSQL data definition](https://www.postgresql.org/docs/current/ddl.html)

## SQL vs NoSQL

**Why it matters:** SQL vs NoSQL is about access patterns, transactions, and operations, not fashion.

**Checklist for the agent**

- Prefer a relational database when you have interrelated records, reporting, and strong consistency needs (the common SaaS case).
- Consider a document or key-value store when the unit of access is a mostly-isolated document and you accept weaker ad-hoc query/join support.
- Many apps are "SQL plus Redis plus object storage," not a single bet. Do not add a second primary store without a reason.

**Common vibe-coding mistakes:** Mongo "because it's JSON"; using Postgres as a blob dump; two sources of truth for the same entity.

## Primary Keys, Foreign Keys, UUIDs vs Auto-Increment IDs, Unique Constraints, and Database Constraints

**Why it matters:** If the database does not enforce integrity, a bug will eventually insert nonsense.

**Checklist for the agent**

- Every table has a Primary Key. Prefer stable, unique, never-reused identifiers.
- **UUIDs vs Auto-Increment IDs:** auto-increment is simple and small but leaks volume and is hard to merge across systems; UUIDv4 is easy to generate client-side but fragments indexes; UUIDv7/ULID-style time-ordered ids often balance the two. Do not expose raw sequential ids if they become an IDOR shortcut — but also do not treat "UUID" as authorization.
- Foreign Keys for every real relationship, with an explicit `ON DELETE` (`RESTRICT`/`CASCADE`/`SET NULL`) you meant.
- Unique Constraints for natural uniqueness (email per tenant, one default payment method). Use partial unique indexes when uniqueness is conditional (`WHERE deleted_at IS NULL`).
- Database Constraints (`NOT NULL`, `CHECK`, exclusion constraints) belong in the database, not only in TypeScript. The ORM will be bypassed someday (or already is, by jobs and console).

```sql
-- email unique among live rows, tenant-scoped
CREATE UNIQUE INDEX users_tenant_email_live
  ON users (tenant_id, lower(email)) WHERE deleted_at IS NULL;
```

**Common vibe-coding mistakes:** no foreign keys "for flexibility"; string ids with no uniqueness; unique email without a tenant scope; trusting the app to enforce `amount >= 0`.

**Quick verification:** try to insert an orphan FK, a duplicate email, and a negative amount — all should fail in the database.

## Database Indexing and Query Plans (EXPLAIN)

**Why it matters:** Database Indexing is how lists stay fast. Query Plans (EXPLAIN) tell you whether the database agrees with your guess.

**Checklist for the agent**

- Index columns used in `WHERE`, `JOIN`, and `ORDER BY` that filter or sort large tables — especially foreign keys.
- Prefer composite indexes that match left-to-right query patterns. Avoid indexing everything (writes and storage suffer).
- Use `EXPLAIN (ANALYZE, BUFFERS)` on slow or high-volume queries in a realistic data size, not on an empty dev DB.
- Watch sequential scans on large tables, sort/hash memory spills, and "Row Remove" from missing predicates.
- Partial and expression indexes (e.g. `lower(email)`) should match the query exactly.

**Common vibe-coding mistakes:** indexing every column "just in case"; an index that does not match `ORDER BY`; celebrating an index you never confirmed with EXPLAIN.

**Quick verification:** `EXPLAIN ANALYZE` the top 5 API queries against production-like data; each has a sensible plan.

**Links:** [PostgreSQL EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html), [PostgreSQL indexes](https://www.postgresql.org/docs/current/indexes.html)

## Transactions, ACID, Isolation Levels, Database Locks, Deadlocks, and Race Conditions

**Why it matters:** Two requests will hit the same row. Without Transactions and a clear Isolation Level, money and inventory drift. ACID is the contract you are relying on; know when you left it (e.g. Eventual Consistency across services).

**Checklist for the agent**

- Put multi-step writes (create order + decrement stock + enqueue payment) in **one** transaction, or use an explicit outbox pattern if they cannot share one.
- Know Isolation Levels (`READ COMMITTED` vs `REPEATABLE READ` vs `SERIALIZABLE`). If you check-then-update, you need a lock (`SELECT … FOR UPDATE`) or a single `UPDATE … WHERE quantity >= 1` that you inspect.
- Keep transactions short. Do not hold a transaction open across an HTTP call to a third party.
- Understand Database Locks (row vs table, advisory locks for crons). On Deadlocks, retry the transaction a small number of times and fix the lock order.
- Race Conditions in "read, compute, write" without a constraint or lock will pass tests and fail in production.

```sql
UPDATE products SET stock = stock - 1
 WHERE id = $1 AND stock >= 1;
-- 0 rows updated means "out of stock," not an exception to ignore
```

**Common vibe-coding mistakes:** `GET` stock in the app, then `SET` stock = n-1; a transaction around a 5-second Stripe call; catching deadlock and giving up with a 500 to the user every time.

**Quick verification:** two concurrent "buy last item" requests — only one succeeds; a deadlock test retries; pg/mysql logs do not show frequent lock waits.

**Links:** [PostgreSQL transactions](https://www.postgresql.org/docs/current/tutorial-transactions.html), [PostgreSQL concurrency](https://www.postgresql.org/docs/current/mvcc.html)

## Connection Pooling

**Why it matters:** Each app instance opening dozens of connections will exhaust the database faster than it exhausts CPU.

**Checklist for the agent**

- Use a pool (and often a pooler like PgBouncer) with a cap per process times instance count **below** `max_connections`.
- Serverless: do not open a new pool of 10 on every cold start without a proxy; hold a small global client.
- Set idle timeouts. Watch pool wait time as a metric. Close pools on Graceful Shutdown.

**Common vibe-coding mistakes:** no cap; `max_connections` raised "to fix" an incident; opening a connection per request and leaking it on error.

**Quick verification:** under a load test, connections plateau; killing the app releases them; a third instance does not push the database over the limit.

## N+1 Queries, Joins, ORMs, and Raw SQL

**Why it matters:** N+1 Queries (one query plus one per row) feel fine with 10 rows and die at 500. ORMs make this easy. Raw SQL is not a failure — unreviewed string concatenation is.

**Checklist for the agent**

- List then batch-load associations (`IN`, join, or a dataloader). Look at the query log in development (Prisma/Django debug, `DEBUG=knex`, etc.).
- **Joins:** use them, but avoid joining huge unbounded sets; paginate first or filter early. Select only the columns you need.
- **ORMs:** keep them for ordinary CRUD. Know what SQL they emit. Disable or be careful with implicit lazy loads in request handlers.
- **Raw SQL:** parameterized always (`$1`, `%s`, never f-strings). Use for reports, updates, and CTEs the ORM mangles. Put raw queries in versioned files when they are non-trivial.

**Common vibe-coding mistakes:** `for (const u of users) await posts.find({userId: u.id})`; `SELECT *` everywhere; string-built `WHERE id IN (${ids})`.

**Quick verification:** a list page of 50 parents should not issue 50+ queries; `EXPLAIN` a join; grep for raw queries that interpolate variables.

## Soft Deletes and Seed Data

**Why it matters:** Soft Deletes (`deleted_at`) are easy to get wrong: unique constraints, unique emails, and forgotten `WHERE deleted_at IS NULL` resurrect ghosts. Seed Data should be repeatable and fake.

**Checklist for the agent**

- If you soft-delete, index and filter consistently, and use partial unique indexes so a new row can reuse a unique value. Decide what FKs do.
- Hard-delete or anonymize when Data Retention Policies require it (see below). Soft delete is not a privacy program.
- Seed Data: scripted, idempotent, no production PII, useful for tests and staging. Do not seed by hand in prod.

**Common vibe-coding mistakes:** unique `email` blocks re-registration after "delete"; queries that mix live and deleted rows; production dump used as seed.

## Eventual Consistency and Read Replicas

**Why it matters:** Eventual Consistency means a read may not see the write yet (replicas, search indexes, caches, other regions). Read Replicas scale reads; they are not instant copies of the primary.

**Checklist for the agent**

- After a write, read from the primary (or "read-your-writes") for the response the user will immediately see.
- Route heavy reporting to replicas knowingly. Monitor replica lag and stop routing if lag exceeds a budget.
- Tell the product when a search result or count may be slightly behind.

**Common vibe-coding mistakes:** the new profile page 404s because it hit a lagging replica; using a replica for a read-modify-write.

**Quick verification:** measure replica lag; a test that writes then immediately reads through the same path the UI uses.

## Full-Text Search

**Why it matters:** `LIKE '%term%'` will not scale and will not rank. Full-Text Search needs indexes (Postgres `tsvector`, or an external engine) and a plan for freshness.

**Checklist for the agent**

- Use a real FTS index or a search engine when users search text. Handle stemming/language, unaccent if needed, and pagination of results.
- Sanitize input (`websearch_to_tsquery` or equivalent) so user typings cannot form illegal queries or huge scanners.
- Keep the index updated (trigger, generated column, or async indexer). Know the lag.

**Common vibe-coding mistakes:** leading-wildcard `LIKE` on the main table in production; no limit on search results; exposing internal document IDs without auth.

**Links:** [PostgreSQL full-text search](https://www.postgresql.org/docs/current/textsearch.html)

## Cursor-Based Pagination

**Why it matters:** Offset pagination gets slower and less stable as the table grows (see also Pagination in [02-apis-backend.md](02-apis-backend.md)). Cursor-Based Pagination (keyset) uses a unique sort key as the cursor.

**Checklist for the agent**

- Order by a unique, indexed tuple (`(created_at, id)`). Cursor is an opaque encoding of that tuple, not a raw SQL string.
- `WHERE (created_at, id) < ($1, $2) ORDER BY created_at DESC, id DESC LIMIT N`.
- Do not skip the unique tie-breaker or pages will drop/dupe rows with the same timestamp.

**Common vibe-coding mistakes:** cursor = offset; sortable by a non-unique column; leaking internal keys you did not mean to.

**Quick verification:** walk pages while inserting at the head; no duplicates or holes; `EXPLAIN` shows an index range, not `OFFSET 100000`.

## Database Migrations, Data Migration Scripts, and Zero-Downtime Migrations

**Why it matters:** Schema changes on a live database can lock tables or break old app instances still running during a deploy.

**Checklist for the agent**

- All schema change goes through versioned Database Migrations in git, applied by CI/CD or a controlled job — never "quick ALTER in prod."
- Data Migration Scripts (backfills) should be batched, resumable, and idempotent. Do not run a 20-million-row rewrite in one transaction if it will lock for an hour.
- Zero-Downtime Migrations: expand/contract. Add a nullable column, deploy code that writes both, backfill, then add constraints and stop writing the old column. Do not drop or rename in the same release the old code still needs.
- Rehearse against a production-sized copy. Set lock timeouts so a migration fails instead of waiting forever on a busy table.

**Common vibe-coding mistakes:** `ALTER COLUMN … NOT NULL` without a default or backfill; dropping a column in the same deploy as the code change; migrations applied from a laptop.

**Quick verification:** migrate up/down in staging; a rolling deploy with mixed versions still works after an expand-only migration.

## Object Storage and Presigned URLs

**Why it matters:** User files in the app repo or container disk will not survive deploys and will not scale. Object Storage (S3-compatible or similar) plus Presigned URLs is the usual pattern.

**Checklist for the agent**

- Store objects in a private bucket by default. The app issues short-lived Presigned URLs for upload/download after Authorization.
- Do not make the bucket world-readable "so the `<img>` works." Use signed URLs or a controlled proxy.
- Virus/type/size checks, unique keys (`tenant/user/uuid`), and lifecycle rules. See File Upload Security in layer 8.
- Versioning or a trash prefix helps recovery. Back up or replicate unique objects (layer 13).

**Common vibe-coding mistakes:** `public-read` on everything; 24-hour upload URLs that allow overwrite of any key; files committed to git.

**Quick verification:** a public `curl` of a raw object URL without a signature fails; an authorized user can upload and read; keys are not predictable admin paths.

## Data Retention Policies

**Why it matters:** Keeping everything forever increases breach impact and can violate Data Privacy (GDPR) and your own privacy policy.

**Checklist for the agent**

- Define how long each class of data lives (accounts, logs, support tickets, backups, exports). Automate deletion or anonymization.
- "Soft deleted" is not deleted. Include backups and logs in the policy (you may not be able to surgically delete one user from an old backup — document that).
- Legal holds (disputes, finance) should be an explicit exception, not "we never delete."

**Common vibe-coding mistakes:** promising deletion in the UI that only sets `deleted_at`; logs with PII kept "forever because storage is cheap."

**Quick verification:** a staging script can anonymize or remove a test subject across tables and object keys; the policy is written and linked from legal pages.
