# Extras — production needs beyond the original topic list

These items were not in the vibe-coder topic list, but most production apps need them. Mention them in reviews even when the 14 layers already look "green."

## Transactional email deliverability (SPF, DKIM, and DMARC)

**Why it matters:** Password resets, magic links, invoices, and "confirm your email" messages that land in spam are an auth and revenue outage.

**Checklist for the agent**

- Send transactional mail through a real provider, not a random SMTP port on the app server.
- Publish **SPF**, sign mail with **DKIM**, and set a **DMARC** policy (start with `p=none` and reporting, then tighten). Align the From domain with these records.
- Use a dedicated sending domain or subdomain (`mail.example.com`). Warm it if volume is high.
- Monitor bounces and complaints. Stop sending to hard bounces. Authenticate unsubscribe for marketing, and never mix marketing and auth mail blindly on one messy domain.
- Templates should have a plain-text part, a correct From name, and no typo-ridden link domains.

**Common vibe-coding mistakes:** `nodemailer` via the developer's Gmail; no SPF/DKIM; "works in my inbox" (which is not a deliverability test); password reset links that expire before a delayed mail arrives.

**Quick verification:** mail-tester or the provider's dashboard shows SPF/DKIM/DMARC pass; a test reset reaches a mailbox that is not the developer's usual allow-list.

**Links:** [Cloudflare Learning: SPF, DKIM, and DMARC](https://www.cloudflare.com/learning/email-security/dmarc-dkim-spf/)

## Payments and webhook idempotency

**Why it matters:** Payment providers retry webhooks. If your handler is not idempotent, you will double-fulfill or double-email, or miss a state change.

**Checklist for the agent**

- Verify webhook signatures. Reject unsigned or stale events. Use the provider's official SDK when you can.
- Store the event id and process **Idempotency** keys so retries do not repeat side effects. The same applies to your own "create charge" APIs.
- Fulfill on the events the provider documents (e.g. `payment_intent.succeeded`, invoice paid), not only on the browser redirect (the user may close the tab).
- Test failure modes: duplicate events, out-of-order events, refunds, disputes. Log a Correlation ID that includes the event id.
- Never log full card numbers or raw bank data. Keep PCI scope small (hosted checkout / tokenized elements).

**Common vibe-coding mistakes:** trusting the success URL as proof of payment; no signature check; a unique index missing on `event_id` so two workers fulfill twice.

**Quick verification:** replay a staging webhook twice and confirm one fulfillment; a tampered signature is rejected; the success page still reconciles if the redirect is skipped.

**Links:** [Stripe: Webhooks](https://docs.stripe.com/webhooks)

## Internationalization (i18n)

**Why it matters:** Hard-coded English strings, `toLocaleString()` without a locale, and concatenated sentences break as soon as you add a second language or a new currency.

**Checklist for the agent**

- Externalize user-visible strings. Use ICU or equivalent for pluralization and interpolation — do not concatenate `"1 " + noun`.
- Format numbers, currencies, and dates with an explicit locale and time zone (see Time Zones in [01-frontend.md](01-frontend.md)).
- Plan layout for longer text and RTL languages if you will need them. Store user locale as a preference, not only from `Accept-Language`.
- Translate legal and email templates too, not just the SPA.

**Common vibe-coding mistakes:** keys like `error1` with English inside the code path only; assuming every name has a first/last order; currency rounded with float.

## SEO basics

**Why it matters:** Public marketing and content pages that are client-rendered only, title-less, or `noindex` by accident will not be found.

**Checklist for the agent**

- Unique `<title>` and meta description per public page. Canonical URLs. Correct status codes (`404` not `200` for missing content).
- Server-render or prerender content you want indexed. Provide a sitemap and `robots.txt` you meant to ship.
- Open Graph / social preview tags. Structured data only when it is accurate.
- Fast, mobile-usable pages (layers 1 and 10) are part of SEO. Do not block critical resources.

**Common vibe-coding mistakes:** a global `noindex` left on from staging; empty `index.html` for crawlers; 30 pages titled "React App."

**Links:** [Google Search Central](https://developers.google.com/search/docs)

## Analytics and cookie consent

**Why it matters:** Shipping a marketing pixel on every page without consent can violate Data Privacy (GDPR) and similar laws. Analytics also often leaks PII into a third party.

**Checklist for the agent**

- Inventory every tracker, tag, and SDK. Load non-essential analytics only after consent where required.
- Do not send names, emails, or tokens as event properties. IP truncation and a data-processing agreement may be required.
- Provide a way to withdraw consent. Document what you collect in the privacy policy (see legal pages).
- Prefer first-party, privacy-respecting setups when they meet the need.

**Common vibe-coding mistakes:** pasting four pixels "from the ads team" into `index.html`; using user email as the analytics user id; consent banner that does not actually block scripts.

## Legal pages

**Why it matters:** Privacy policy, terms of service, and a cookie/consent notice are expected for most production apps that have accounts, payments, or trackers. This is not legal advice — get a professional to draft or review them — but the product must have a place for them and links in signup, footer, and checkout.

**Checklist for the agent**

- Ship linked Privacy Policy and Terms. If you use cookies or similar trackers, explain them and honor the consent path.
- Include contact details for privacy requests. Note international transfer and retention at a high level consistent with what the app *actually* does.
- Do not copy another company's policy wholesale. Keep the pages under version control and update them when you add a vendor.
- Age restrictions, refund terms, and acceptable-use should match real enforcement.

**Common vibe-coding mistakes:** lorem-ipsum legal links; a policy that claims "we never share data" while a pixel fires; no link from the signup checkbox.

## Environment-specific config

**Why it matters:** Dev, staging, and production must not share API keys, webhooks, payment modes, or databases. Environment-specific config is how you prevent "I tested a refund on a live customer."

**Checklist for the agent**

- Separate cloud accounts or at least strictly separate projects and credentials per environment.
- Production payment keys, SMS, and email domains only in production. Use provider sandbox/test modes elsewhere.
- Feature flags and URLs (callback, CORS origins, cookie domains) are explicit per env. See Configuration Management in [05-hosting-deployment.md](05-hosting-deployment.md).
- A failed deploy should never fall back to a default production secret "so it boots."

**Common vibe-coding mistakes:** one Stripe live key in a shared `.env`; webhook endpoint pointing at localhost in prod or at prod from a laptop; `NODE_ENV=production` on a developer's machine with prod credentials.

**Quick verification:** grep config for live keys in non-prod; a staging purchase cannot touch prod customers; callback URLs match the environment hostname.
