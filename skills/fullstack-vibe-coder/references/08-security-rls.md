# Layer 8 — Security & RLS

Use this file when handling untrusted input, secrets, policies, or headers. Pair with [04-auth-permissions.md](04-auth-permissions.md). When in doubt, walk the OWASP Top 10.

## OWASP Top 10

**Why it matters:** The OWASP Top 10 is a widely used map of frequent, high-impact web risks. It is not a complete audit checklist, but if you cannot speak to each item, you are not ready to store real user data.

**Checklist for the agent**

- Review the current Top 10 and note how this app handles each (or why it does not apply). Common guests: broken access control, injection, crypto failures, insecure design, misconfig, vulnerable components, auth failures, integrity (supply chain), logging failures, SSRF.
- Use it as a review agenda before launch, then again after major features (payments, file uploads, multi-tenant).
- Prefer official cheat sheets over random blog posts when you implement controls.

**Common vibe-coding mistakes:** "we use a framework so we are safe"; a one-time exam at the start of the project and never again.

**Links:** [OWASP Top 10](https://owasp.org/www-project-top-ten/), [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)

## Row-Level Security

**Why it matters:** Row-Level Security (RLS) enforces "this tenant can only see their rows" **inside the database**. Application filters get skipped by a raw query, a new endpoint, or a buggy ORM include.

**Checklist for the agent**

- In multi-tenant Postgres (and similar), enable RLS on tenant-owned tables and write policies for `SELECT/INSERT/UPDATE/DELETE` using a session setting (`SET app.tenant_id = ...`) or a tightly controlled role.
- The database role the app uses should not be a superuser and should not bypass RLS (`BYPASSRLS`).
- Test with two tenants: a leaked id from tenant A must return no row for tenant B, including through joins, views, and admin exceptions (which should be explicit).
- Combine RLS with application Authorization; RLS is a backstop, not an excuse for a messy API.
- Migrations must grant policies on new tables. A new table without RLS is a hole.

```sql
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders FORCE ROW LEVEL SECURITY;
CREATE POLICY orders_tenant ON orders
  USING (tenant_id = current_setting('app.tenant_id')::uuid);
```

**Common vibe-coding mistakes:** RLS designed but disabled in the connection "to get the dashboard working"; policies only on `SELECT`; the app connects as a bypass role; `FORCE ROW LEVEL SECURITY` not set so table owners skip policies.

**Quick verification:** integration test: as tenant B, `SELECT` by tenant A's uuid returns 0 rows even with a raw query; a new table in a migration review is checked for policies.

**Links:** [PostgreSQL RLS](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)

## SQL Injection, XSS, CSRF, SSRF, Path Traversal, Command Injection, and Open Redirects

**Why it matters:** These classic injection and request-abuse bugs are still how apps get popped — often from a concatenated string an AI model generated.

**Checklist for the agent**

- **SQL Injection:** parameterized queries or a bound ORM only. No f-strings, no `+ userInput` in SQL, no unsanitized `$query.raw()`. Watch order-by and identifier interpolation (whitelist column names).
- **XSS:** encode untrusted data at the HTML/JS/attribute boundary. Avoid `dangerouslySetInnerHTML` / `innerHTML` unless sanitized with a vetted library and a strict policy. Set a Content Security Policy.
- **CSRF:** for cookie-based sessions, require SameSite plus an anti-CSRF token or double-submit on state-changing requests. Be careful with `SameSite=None`. Token-in-header APIs are less exposed but not if cookies are also used.
- **SSRF:** do not fetch user-supplied URLs without an allow list (scheme, host, no link-local/metadata IPs like `169.254.169.254`). Disable surprising redirects.
- **Path Traversal:** join user filenames to a base directory only after resolving and checking the prefix (`..`, encoded slashes). Prefer generated names in Object Storage.
- **Command Injection:** do not pass user input to the shell. Use argument arrays (`subprocess.run(["ffmpeg", path])`, never `shell=True`).
- **Open Redirects:** only redirect to relative paths or an allow list of origins. Do not `redirect(req.query.next)`.

**Common vibe-coding mistakes:** `query(f"SELECT * FROM users WHERE id = {id}")`; rendering a comment field as HTML; CSRF off because "we have a SPA"; a screenshot-of-URL feature that hits the cloud metadata IP; `open("/uploads/" + filename)`.

**Quick verification:** payload tests (`' OR 1=1`, `<script>alert(1)</script>`, `../../etc/passwd`, `http://127.0.0.1`, `//evil.test`); CSRF: a cross-site POST without a token fails; redirects only to allow-listed hosts.

**Links:** [OWASP SQL Injection](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html), [OWASP XSS](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html), [MDN CSP](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)

## File Upload Security

**Why it matters:** Uploads are a path into your disk, your users' browsers, and your bill.

**Checklist for the agent**

- Authorize, size-limit, and inspect content type (magic bytes, not only `Content-Type` or extension). Store outside the web root or in a private bucket.
- Randomize keys. Do not serve user files as `text/html` from your origin (MIME sniffing — set `X-Content-Type-Options: nosniff` and a safe content type).
- Image pipelines should strip dangerous payloads or transcode. Do not pass filenames to the shell (Command Injection).
- Scan when the risk warrants it. See also Presigned URLs in layer 3.

**Common vibe-coding mistakes:** accepting any file into `public/uploads` and serving it with the original MIME type; a `.html` upload that steals cookies; unbounded size.

**Quick verification:** a rejected huge or `.html`/`.exe` upload; stored object is not publicly listable; download uses a safe content type.

## Content Security Policy, Security Headers, and Clickjacking

**Why it matters:** Security Headers are cheap defenses that stop entire classes of bugs, or at least shrink them. Clickjacking is your site in someone else's iframe, tricking a click.

**Checklist for the agent**

- **Content Security Policy:** default to tight (`default-src 'self'`, no wild `unsafe-inline` unless you have a nonce/hash plan). Raise reports in `Report-Only` first if needed, then enforce.
- **Security Headers:** `Content-Security-Policy`, `Strict-Transport-Security` (when HTTPS is solid), `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy`, and a frame policy (below). Review `CORS` in layer 2.
- **Clickjacking:** `Content-Security-Policy: frame-ancestors 'self'` (or `'none'`) and/or `X-Frame-Options: DENY` / `SAMEORIGIN` unless you must be framed by a named partner.

**Common vibe-coding mistakes:** no CSP; CSP with `'unsafe-inline' 'unsafe-eval'` everywhere; HSTS on a host that still has an HTTP subdomain; missing frame-ancestors on the login page.

**Quick verification:** [securityheaders.com](https://securityheaders.com/) or `curl -I` on production-like staging; a test page cannot iframe the login form.

**Links:** [MDN CSP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy), [MDN X-Frame-Options](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options)

## Secrets Management, Secret Rotation, Encryption at Rest, and Encryption in Transit

**Why it matters:** Secrets in git or in the client are gone. Encryption in Transit (TLS) and Encryption at Rest protect data on the wire and on disks/backups — they do not fix a public bucket or a leaked key.

**Checklist for the agent**

- **Secrets Management:** store keys in a secret manager or the platform's vault, not in source, chat, or tickets. Least privilege to read them. Different values per environment (see extras).
- **Secret Rotation:** you can rotate DB passwords, API keys, and JWT signing keys (with overlap). If a secret leaked, rotate immediately and purge caches. Scan git history.
- **Encryption in Transit:** HTTPS everywhere, TLS to the database and Redis (or a private network plus a documented exception). No `rejectUnauthorized: false`.
- **Encryption at Rest:** use the cloud provider's disk/S3/database encryption and protect the KMS keys. Extra application-level encryption for especially sensitive fields (with a real key story — not a key next to the data).
- Hashing vs Encryption is covered in layer 4 for passwords; do not "encrypt" passwords.

**Common vibe-coding mistakes:** `SECRET_KEY` committed; the same JWT secret for five years and all environments; Postgres on the public internet without TLS; a "encrypted" field with the key in the same row.

**Quick verification:** secret scanner clean; `sslmode=require` or equivalent; bucket default encryption on; a rotation drill documented.

## Dependency Vulnerabilities and Supply Chain Attacks

**Why it matters:** Most of your code is other people's code. Dependency Vulnerabilities and Supply Chain Attacks (typosquats, hijacked packages, poisoned build tools) land in your repo through a single install.

**Checklist for the agent**

- Install from lockfiles. Review new packages (maintainer, age, downloads, typo). Disable auto-merge of dependency PRs you do not look at.
- Run `npm audit` / `pip-audit` / OS image scans in CI and triage high/critical issues (layer 7).
- Pin GitHub Actions and build images by digest when you can. Do not run unreviewed `curl | bash` in CI.
- Treat install scripts and postinstall hooks as untrusted code. For AI-generated imports, verify the package exists and is the one you meant (layer 14, Hallucinated APIs/packages).

**Common vibe-coding mistakes:** adding a package because an AI suggested a plausible name; `latest` tags on Actions; ignoring a critical RCE because "it's only devDependencies" (often it still runs).

**Quick verification:** CI audit job exists; a deliberate typo package is not in the lockfile; Actions are pinned.

## Bot Protection, CAPTCHA, WAF, Firewalls, and DDoS Protection

**Why it matters:** Public forms and APIs will be hit by bots and floods. These controls buy time; they are not a substitute for Rate Limiting and auth.

**Checklist for the agent**

- **Firewalls / security groups:** default deny, least ports, no public SSH or DB (layers 5–6).
- **WAF:** useful for common probes and some injection/XSS patterns at the edge. Tune to reduce false positives; do not assume it sanitizes everything.
- **DDoS Protection:** usually a CDN or cloud offering in front of origin; origin should not be easy to bypass. Combine with autoscaling caps and rate limits so a bill is not the failure mode.
- **Bot Protection and CAPTCHA:** put friction on signup, login after failures, and scrapers of expensive pages. Offer accessible alternatives. Do not CAPTCHA every page load if you can avoid it.

**Common vibe-coding mistakes:** a WAF with default rules and a public origin IP; no DDoS plan except "the host will handle it"; CAPTCHA that blocks all real users on mobile.

**Quick verification:** origin IP is not trivially in DNS for bypass if you rely on the edge; security groups are tight; a bot score or CAPTCHA path exists on auth routes.

## SSH Keys

**Why it matters:** SSH Keys are often root-equivalent to production. A leftover laptop key is a breach.

**Checklist for the agent**

- Prefer SSO/bastion or session-based access over a garden of standing keys. If you use keys: unique per person, passphrases, no shared `prod.pem` in Slack, disable password auth, and no `PermitRootLogin`.
- Rotate and revoke on offboarding immediately. Audit `authorized_keys`. Prefer short-lived certificates if the platform supports them.
- Never embed a deploy key that can also push unless you meant to; use read-only where that is the need.

**Common vibe-coding mistakes:** `chmod 777` on a `.pem` in the repo; one key for the whole company; SSH open to `0.0.0.0/0`.

**Quick verification:** `sshd` config and security group; a list of who can SSH and when it was last reviewed.

## Audit Logs and Data Privacy (GDPR)

**Why it matters:** Audit Logs tell you who did something after a breach or a support dispute. Data Privacy (GDPR) and similar laws constrain what you collect, why, how long, and how people exercise rights. This is not legal advice.

**Checklist for the agent**

- Log security-relevant events: login (success/fail), logout, password/email change, permission change, admin access, exports, and payment/account deletion. Include actor, time, IP/device lightly, and Correlation IDs — not raw secrets.
- Protect audit logs (append-only or a separate store). Retain per policy.
- Data Privacy (GDPR): know a lawful basis for what you collect, minimize it, publish a privacy policy (see [extras.md](extras.md)), honor access/deletion/export requests, be careful with processors and international transfers, and do not hide trackers in a way that contradicts consent.
- Children's data, health, and financial data have extra rules — do not collect them casually.

**Common vibe-coding mistakes:** no audit trail for admin impersonation; logs that are also PII dumps; "GDPR" as a banner only; deletion that does not cover backups or logs (document this honestly).

**Quick verification:** an admin action is visible in the audit log; a written process exists for an export/delete request; analytics is covered in [extras.md](extras.md).

**Links:** [GDPR official text / EU site](https://gdpr.eu/)

## Penetration Testing

**Why it matters:** Penetration Testing is a skilled human (or a structured paid program) trying to break the live system. It finds the issues scanners miss.

**Checklist for the agent**

- Before handling serious money, health, or large PII sets, schedule a test and fix the findings. Even a lightweight external review is better than none.
- Scope it (staging vs prod), do not block the testers with surprise WAFs you forgot, and budget time to remediate — a PDF nobody reads is not the goal.
- Bug bounty is optional and needs a policy so "testers" are not just abusing you.

**Common vibe-coding mistakes:** "the intern ran ZAP once"; a 40-finding report with no owners; testing only after a breach.
