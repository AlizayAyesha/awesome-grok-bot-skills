# Layer 4 — Auth & Permissions

Use this file when adding login, sessions, tokens, or protected routes. Pair with [08-security-rls.md](08-security-rls.md) for Row-Level Security and headers, and [09-rate-limiting.md](09-rate-limiting.md) for Brute Force Protection.

## Authentication and Authorization

**Why it matters:** Authentication answers "who is this?" Authorization answers "may they do this?" A logged-in user is not allowed to do everything.

**Checklist for the agent**

- Every route that is not explicitly public requires Authentication on the **server**. UI hiding is not Authorization.
- Authorization checks the resource and the action (`can(user, 'transfer', account)`), including IDOR-sensitive IDs in the path.
- Default deny. New endpoints inherit auth middleware, not "remember to add it."
- Distinguish `401` (no/invalid credentials) from `403` (authenticated but not allowed).
- Admin tools need the same or stricter rules, plus extra step-up auth for dangerous actions.

**Common vibe-coding mistakes:** `if (user.role === 'admin')` only in React; a wildcard API route left public; "internal" endpoints with no auth because they are not in the docs.

**Quick verification:** `curl` each new route without cookies/tokens (expect 401); as a normal user on another user's id (expect 403 or 404); as the owner (expect 200).

**Links:** [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html), [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)

## Password Hashing, Salting, and Hashing vs Encryption

**Why it matters:** If the password database leaks, Hashing vs Encryption decides whether attackers get passwords or get to start a long offline attack. Encryption is reversible with a key; password storage must not be reversible.

**Checklist for the agent**

- Hash passwords with a slow, memory-hard (or well-supported slow) algorithm: Argon2id preferred, or bcrypt/scrypt with a modern cost. Never MD5, SHA-1, or a single SHA-256.
- **Salting:** a unique salt per password, usually handled by the algorithm/library. Do not invent a single global salt. Do not "add pepper" in a home-grown way unless you know where the pepper is stored.
- Never log or return passwords. Never store them encrypted "so we can email it back."
- Tune work factor for ~100ms+ on the server, and watch CPU under a burst (combine with Rate Limiting).
- On login, use a constant-time compare provided by the library.

**Common vibe-coding mistakes:** `hashlib.sha256(password)`; bcrypt with cost 4; storing a reversible "encrypted password"; writing your own salt scheme.

**Quick verification:** a dumped hash is not recognizable as the password; two identical passwords produce different hashes; the library and cost are documented.

**Links:** [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

## Session Management, JWTs, Token Expiration and Refresh, and Cookie Flags (HttpOnly/Secure/SameSite)

**Why it matters:** A session or token *is* the user's identity. Loose cookies or immortal JWTs are stolen accounts.

**Checklist for the agent**

- Prefer server-side Session Management (a random session id in a cookie, data on the server) unless you have a real reason for a self-contained token.
- If you use JWTs: short-lived access tokens (minutes), a refresh token that can be revoked (stored hashed, rotated on use), an explicit `aud`/`iss`, and a signing algorithm you intended (no `alg: none`). Do not put secrets or PII you cannot leak in the payload (it is only encoded).
- Token Expiration and Refresh: access tokens expire; refresh happens over HTTPS, with rotation and reuse detection. Log out must invalidate the server-side session or refresh token, not only delete client state.
- Set Cookie Flags (HttpOnly/Secure/SameSite): `HttpOnly` (no JS access), `Secure` (HTTPS only), `SameSite=Lax` or `Strict` unless you have a documented cross-site need (`None` + `Secure`). Set `Path` and a tight `Domain`. Prefer `__Host-` prefix cookies when you can.
- Do not store access tokens in `localStorage` if you can use `HttpOnly` cookies (XSS then cannot exfiltrate them as easily).

**Common vibe-coding mistakes:** JWT valid for 30 days with no revocation; tokens in localStorage; missing `Secure` on production cookies; logout that only hits `localStorage.clear()`.

**Quick verification:** inspect the Set-Cookie header; after logout a replayed cookie/refresh token fails; an expired access token is rejected; XSS in staging cannot read the cookie.

**Links:** [MDN Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie), [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)

## OAuth, SSO, Passkeys, Magic Links, and Two-Factor Authentication

**Why it matters:** These are easy to "add" and easy to implement unsafely (open redirects, link leakage, skipped `state`).

**Checklist for the agent**

- **OAuth / SSO:** use a maintained library, `state` (and PKCE for public clients), exact redirect URI allow lists, and the official token endpoint. Map IdP subjects to local users carefully; do not trust email change from the IdP without verification. See Open Redirects in layer 8.
- **Passkeys** (WebAuthn): prefer platform authenticators, store credentials per user, and keep a recovery path. Serve them only on HTTPS and the correct origin.
- **Magic Links:** single-use, short TTL, high-entropy token hashed in the database, sent only to the claimed address. Do not leave the raw token in server logs or Referer (use a POST/intermediate page). Combine with Email Verification rules.
- **Two-Factor Authentication:** TOTP or WebAuthn for privileged users at least. Recovery codes hashed, shown once. Do not use SMS as the only 2FA if you can avoid it (SIM swap). 2FA is required again for sensitive account changes.
- After any of these succeed, rotate the session id (session fixation).

**Common vibe-coding mistakes:** `redirect_uri` from a query param; magic links that work twice for 24 hours; 2FA bypass on the "backup" code path; linking a Google account by email without verifying the IdP subject.

**Quick verification:** expired/used magic link fails; OAuth with a bad `state` or foreign redirect fails; 2FA is required on login for an enrolled user and cannot be skipped via a second endpoint.

## Email Verification and Password Reset Flows

**Why it matters:** These flows are account takeovers if tokens are guessable, reusable, or delivered to the wrong place.

**Checklist for the agent**

- Tokens: long, random, stored hashed, single use, 15–60 minute expiry. Invalidation when a new reset is requested and after a successful change.
- The form should not reveal whether an email is registered (same response and similar timing). Rate-limit both flows (layer 9).
- Email Verification before sensitive privileges (posting, paying as a trusted seller, etc.). Re-verify on email change; do not switch the address until the new one confirms.
- After Password Reset Flows, invalidate other sessions and refresh tokens. Require the current password (or a fresh reset) to change email or add a login method.
- Send a notification to the old address on email or password change.

**Common vibe-coding mistakes:** `?user_id=3&token=1234`; reset tokens in the URL that get logged by analytics; "verify later" with full access forever.

**Quick verification:** used and expired tokens fail; a second reset invalidates the first; other sessions die after reset; enumeration test on the form.

## Role-Based Access Control and Principle of Least Privilege

**Why it matters:** Role-Based Access Control (RBAC) and the Principle of Least Privilege keep a support intern from dropping the production database and a user from hitting admin APIs.

**Checklist for the agent**

- Roles and permissions are data, checked on the server. Prefer "permission to do X" over a spreading set of `isAdmin` booleans.
- New staff start with the minimum role. Production data stores, cloud keys, and CI use scoped roles (not one shared `Administrator` access key).
- Separate "can read this ticket" from "can impersonate a user." Impersonation is logged (Audit Logs in layer 8).
- Review access when people change teams. Service accounts get only the APIs they need.

**Common vibe-coding mistakes:** two roles (`user`/`admin`) with admin meaning "all queries allowed"; a shared AWS key in the mobile app; a support role that can export the whole user table unmonitored.

**Quick verification:** a non-admin token is denied on admin routes; cloud/IAM policies are scoped; a checklist exists for offboarding.

## API Keys

**Why it matters:** API Keys identify a program, not a human, and often bypass interactive login. They leak in repos, client apps, and screenshots.

**Checklist for the agent**

- Generate high-entropy keys, show them once, store only a hash (and a prefix for display). Scope and rate-limit each key. Allow revocation.
- Never ship a secret key in a mobile app or browser. That is a public client; use a backend or a publishable key that is not privileged.
- Rotate keys. Do not log them. Prefer user-based OAuth for actions on behalf of a user.
- Bind keys to IPs or audiences if the threat model needs it.

**Common vibe-coding mistakes:** a single sk-live key in the frontend; keys in git history; no revocation; treating API key = admin.

**Quick verification:** a hashed store (raw key is not in the DB); revoked key fails; frontend bundle has no secret key material.

## IDOR and Mass Assignment

**Why it matters:** IDOR (Insecure Direct Object Reference) is "change the id in the URL and see someone else's data." Mass Assignment is "send `role=admin` in the JSON and become one."

**Checklist for the agent**

- For every `GET/PATCH/DELETE /resources/:id`, load the resource **and** confirm the caller is allowed to act on it (ownership, org membership, or a grant). Do not rely on unguessable ids alone.
- Use a Deny-by-default allow list of updatable fields. Never pass `req.body` straight into `update()`. Ignore or reject `role`, `isAdmin`, `tenantId`, `price`, `verifiedAt` from clients unless this is a carefully authorized admin API.
- Add tests: user A cannot read or mutate user B's object; extra fields in a PATCH do not stick.

**Common vibe-coding mistakes:** `Items.findById(req.params.id)` with only "is logged in"; Prisma/Sequelize `update(req.body)`; UUIDs treated as a security control.

**Quick verification:** a second test user swapping ids gets 403/404; a PATCH with `"role":"admin"` does not change the role.

**Links:** [OWASP IDOR](https://owasp.org/www-community/attacks/Insecure_Direct_Object_Reference), [OWASP Mass Assignment](https://owasp.org/www-community/vulnerabilities/Mass_Assignment)

## Account Lockout

**Why it matters:** Account Lockout stops online password guessing on a single account, but it can also be used to lock a victim out. Combine with Rate Limiting and careful messaging (layer 9).

**Checklist for the agent**

- After a threshold of failed attempts, delay or lock the account and require a verified unlock (email or time delay). Do not reveal whether the username exists.
- Unlock paths must be as strong as password reset. Alert the user.
- Consider soft lock (CAPTCHA, exponential delays) before a hard lock on consumer apps, to reduce denial-of-service against a known email.
- Privileged accounts should have stricter policies and mandatory 2FA.

**Common vibe-coding mistakes:** unlimited attempts; lockout by IP only; "your account is locked" confirming a valid username to an attacker; no unlock except a silent 24h wait with no user notice.

**Quick verification:** N failures trigger the policy; a valid password during lockout does not log in; the user is notified; enumeration is not obvious.
