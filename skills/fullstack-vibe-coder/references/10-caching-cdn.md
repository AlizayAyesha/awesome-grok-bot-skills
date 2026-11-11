# Layer 10 — Caching & CDN

Use this file when speeding up reads, static assets, or repeated queries. Pair with [01-frontend.md](01-frontend.md) for images and [11-load-balancing-scaling.md](11-load-balancing-scaling.md) if cache nodes are part of the fleet.

## Caching

**Why it matters:** A cache can make a page feel instant — or serve yesterday's prices, or leak one user's data to another. Caching is a correctness problem first.

**Checklist for the agent**

- Cache only after you can name the **key**, the **TTL**, who is allowed to see the value, and how it becomes invalid.
- Do not cache personalized or permissioned HTML/JSON on a shared public cache unless the key includes the user/tenant and the response is marked private.
- Prefer caching expensive, read-heavy, slowly changing data (config, rendered public pages, computed reports).
- Keep the database as the source of truth for records that must be right (orders, balances).

**Common vibe-coding mistakes:** "just wrap Redis around the query" with a key of the path only; caching 403/500 responses; no plan for stampede when a hot key expires.

**Quick verification:** log cache hit/miss for one endpoint; confirm a permission change is visible within the documented invalidation window; two users never share a private response.

## CDNs

**Why it matters:** A CDN (Content Delivery Network) moves bytes closer to users and absorbs a lot of traffic, but a misconfigured CDN is a worldwide cache-poisoning or privacy bug.

**Checklist for the agent**

- Put static assets (hashed JS/CSS/images) on a CDN with long cache times. Keep HTML or API responses conservative unless they are truly public and versioned.
- Enable TLS at the edge. Restrict origin access so clients cannot easily bypass the CDN if that is part of your security model.
- Set a cache key that includes the headers that actually change the response (e.g. `Accept-Encoding`, and **not** cookies unless you intend to).
- Use the CDN for Image Optimization and large media when you can.

**Common vibe-coding mistakes:** `Cache-Control: public` on a page that reads a session cookie; forwarding all cookies, which defeats the cache; origin left world-open.

**Quick verification:** request an asset twice from a far region and compare `Age` / `CF-Cache-Status` / equivalent; curl with and without auth and confirm private content is not stored publicly.

**Links:** [MDN CDN](https://developer.mozilla.org/en-US/docs/Glossary/CDN)

## Cache Invalidation

**Why it matters:** Stale data is often worse than a slower query. Cache Invalidation must be designed, not hoped for.

**Checklist for the agent**

- Prefer **immutable URLs** for builds (`app.abc123.js`) so you rarely need to purge them.
- For data, pick one strategy and document it: short TTLs, explicit purge on write, or tag/surrogate-key invalidation (`product:42`).
- After a write, invalidate every cache that could show the old value (list + detail + CDN + application Redis).
- Have a manual purge path for emergencies. Protect that path; it is a denial-of-service button.

**Common vibe-coding mistakes:** TTL of 24 hours on inventory; invalidating the detail page but not the search cache; "users can hard-refresh" as the strategy.

**Quick verification:** update a record and watch each cached surface; measure how long the old value can survive; test a purge.

## HTTP Caching Headers

**Why it matters:** Browsers and CDNs will do whatever your HTTP Caching Headers say — including storing a session page.

**Checklist for the agent**

- Use `Cache-Control` as the source of truth: `public` vs `private`, `max-age`, `s-maxage`, `no-store` for sensitive responses, `must-revalidate` when needed.
- Fingerprint static assets and use long `max-age` plus `immutable` when the filename changes on every build.
- For HTML that must be fresh, prefer `no-cache` (revalidate) or a short max-age, not "hope they reload."
- ETags or `Last-Modified` help conditional requests; do not invent weak validators that never change.
- `Vary` on headers that change the body (`Accept-Encoding`, `Accept-Language` if you serve different languages). Do not `Vary: Cookie` unless you mean to.

**Common vibe-coding mistakes:** `no-cache` on every hashed asset (wastes the CDN); missing `Vary: Accept-Encoding`; default framework headers left on authenticated JSON.

**Quick verification:** `curl -I` on HTML, API, and hashed assets; confirm `Cache-Control` matches the table you documented.

**Links:** [MDN Cache-Control](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control)

## TTLs

**Why it matters:** A TTL (time to live) is a safety bound, not a complete invalidation plan. Too long is stale; too short is a database tax.

**Checklist for the agent**

- Set TTLs per class of data: seconds for volatile counts, minutes for profiles, hours or more for rarely changed public content.
- Document what the user might see during the TTL window after a write.
- For Redis and HTTP, make sure TTL and `max-age` are not accidentally "never" (0 vs missing vs -1, depending on the client).
- Add jitter to aligned TTLs on hot keys so they do not all expire together.

**Common vibe-coding mistakes:** a default TTL of 0 or "forever"; one TTL for every key; session TTL longer than your security policy.

**Quick verification:** read the TTL of a written key (`TTL key` in Redis, `max-age` on the wire); wait past it and confirm a miss + refresh.

## Compression (Gzip/Brotli)

**Why it matters:** Compression (Gzip/Brotli) cuts transfer time for text assets cheaply, but compressing things twice or compressing already-encrypted tiny payloads wastes CPU.

**Checklist for the agent**

- Compress HTML, CSS, JS, JSON, and SVG at the reverse proxy or CDN. Prefer Brotli for modern browsers with Gzip fallback.
- Do not compress already-compressed images, video, or zip files. Do not compress responses so small that CPU costs dominate.
- Set `Content-Encoding` correctly and include `Accept-Encoding` in `Vary`.
- Enable compression in production; some dev servers leave it off — measure the prod path.

**Common vibe-coding mistakes:** gzip at both the app and the CDN (double-encoding bugs); compressing JPEG; forgetting Brotli on the CDN while the origin only does Gzip.

**Quick verification:** `curl -H 'Accept-Encoding: br, gzip' -I` and look for `Content-Encoding`; compare transferred vs decoded size.

**Links:** [MDN Content-Encoding](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Encoding)

## Redis

**Why it matters:** Redis is fast and easy to misuse as a second database you never back up.

**Checklist for the agent**

- Use Redis for ephemeral or derived data: sessions, rate counters, locks, caches, pub/sub. Persistence and eviction policy must match that use (do you accept loss on restart?).
- Namespace keys (`prod:session:`). Set TTLs on almost everything. Avoid unbounded `KEYS *` in production.
- Treat Redis like production infrastructure: auth, TLS, network isolation, memory limits, and an eviction policy (`allkeys-lru` vs `noeviction`).
- Do not store the only copy of an order or a user record only in Redis unless you have a durability design.

**Common vibe-coding mistakes:** no password and open `0.0.0.0`; keys without TTL filling RAM; using Redis lists as an unbounded job queue with no dead-letter plan.

**Quick verification:** `INFO memory`; confirm TTLs; restart Redis in staging and confirm the app still has a source of truth for durable data.

## Key-Value Stores

**Why it matters:** Key-Value Stores (Redis, Memcached, Dynamo-style tables, worker KV) have different durability, query, and consistency properties than your primary SQL store.

**Checklist for the agent**

- Pick a KV store for lookup-by-key, not for ad-hoc relational queries.
- Model keys carefully (tenant, environment, version). Document consistency (eventual vs single-key atomicity).
- Watch size limits per value (edge KV often has them). Compress or split large blobs; prefer Object Storage for files.
- Have a migration/invalidation story when the value schema changes (version prefix in the key).

**Common vibe-coding mistakes:** stuffing a whole user profile blob that you then need to query by email; assuming a global KV replica is instantly consistent everywhere.

**Quick verification:** write, read from a second region if you use one, and document how stale it can be; test a schema version bump.
