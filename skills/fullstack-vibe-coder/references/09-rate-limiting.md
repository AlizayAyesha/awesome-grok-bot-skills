# Layer 9 — Rate Limiting

Use this file whenever you expose a public HTTP API, a login or password-reset form, a search endpoint, or any expensive job (including LLM calls). Pair with [04-auth-permissions.md](04-auth-permissions.md) for Account Lockout and [08-security-rls.md](08-security-rls.md) for Bot Protection and CAPTCHA.

## Rate Limiting

**Why it matters:** Without limits, one script can lock users out, run up a cloud bill, or knock the database over. Rate Limiting is a production control, not an optimization.

**Checklist for the agent**

- Limit by **user id** when authenticated, and by **IP plus a fingerprint** when not. Also limit by **route class** (auth, read, write, expensive).
- Use a shared store (Redis or the platform's limiter) so limits work across instances. In-memory maps fail as soon as you have two processes.
- Return `429 Too Many Requests` with a `Retry-After` (or equivalent) header. Do not return `500` or a generic HTML page.
- Choose an algorithm on purpose: token bucket or sliding window are usual; a naive fixed window stampedes at the reset second.
- Give tighter limits to login, signup, password reset, one-time codes, and AI/search endpoints than to ordinary reads.
- Add a higher ceiling or a separate quota for trusted service accounts so one customer cannot starve others (per-tenant quotas).
- Log when limits fire (with Correlation IDs, no PII) so you can tell abuse from a too-tight threshold.
- Document the published limits in API Documentation.

Example shape (Node/TS, conceptual):

```ts
// 5 login attempts / 15 min / IP, plus 10 / 15 min / account
await rateLimit({ key: `login:ip:${ip}`, limit: 5, windowSec: 900 });
await rateLimit({ key: `login:user:${emailHash}`, limit: 10, windowSec: 900 });
```

**Common vibe-coding mistakes:** a limiter only in React; one global bucket for the whole API; no limit on `/forgot-password`; failing open when Redis is down (prefer fail-closed or a conservative local fallback on auth routes).

**Quick verification:** a tight loop of 20 login or search requests should yield `429` after the threshold, with `Retry-After`; a second app instance should share the same count; unauthenticated and authenticated keys are distinct.

**Links:** [MDN 429](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/429), [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

## Brute Force Protection

**Why it matters:** Rate Limiting slows a spray; Brute Force Protection stops credential stuffing and OTP guessing from succeeding even when distributed across many IPs.

**Checklist for the agent**

- Count failed Authentication attempts per account and per IP. After a threshold, delay responses, require CAPTCHA or an email challenge, or start Account Lockout with a clear, non-enumerating message.
- Do not reveal whether the email exists ("invalid email or password" for both cases). Apply similar timing to reduce user enumeration.
- Protect one-time codes, Magic Links, and password-reset tokens with short expiry, single use, and their own attempt limits.
- Alert on unusual failure rates (new country, many accounts from one IP, one account from many IPs).
- Consider known-breached password checks on signup and login, and MFA for privileged roles.
- After a lockout, only an already-verified channel (email/2FA) or time delay should reopen the account — not a second easily guessed form.

**Common vibe-coding mistakes:** locking only by IP (easy to rotate); lockout messages that confirm valid usernames; unlimited 6-digit OTP attempts (`10^6` is guessable); CAPTCHA as the only control on login.

**Quick verification:** N failed logins to one account trigger the slower path or lockout; attempts from a second IP still increment the account counter; OTP endpoint rejects further guesses after the limit; no user-enumeration difference in responses.
