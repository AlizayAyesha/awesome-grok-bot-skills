---
name: seo-audit
description: When auditing a public site or page for technical and on-page SEO — titles, crawlability, headings, previews, and obvious blockers — and recommending fixes.
---

# SEO Audit

Use this skill when the user wants an SEO review of a URL, a site, or page HTML. Stick to observable facts. This is not a promise of ranking.

## Steps

1. Identify the page type (home, article, product, app shell) and the intended query in plain language if the user gave one.
2. Check, with evidence:
   - Unique `<title>` and meta description (length, not "React App").
   - Heading structure (one `h1`, logical `h2`s).
   - Canonical URL, language, and whether the page is `noindex` or blocked in `robots.txt` / meta robots.
   - Status codes (`404` vs `200` for missing), redirects, HTTP vs HTTPS.
   - Whether important content is in the initial HTML or only appears after a client render.
   - Image `alt`, Open Graph / preview tags, sitemap mention if you can see one.
   - Mobile and performance notes only when they clearly affect crawl or UX (huge LCP image, blocked JS).
3. Do not invent backlink or keyword-volume numbers. If you cannot fetch the page, say so and audit from provided HTML.
4. Prioritize fixes: blocking (not indexable), high (missing titles, 200-on-404), then polish.

## Output

A short table or list: **Finding**, **Why it matters**, **Fix**. End with a suggested title and meta description the user can edit — clearly labeled as drafts.

## Rules

- Do not set up hidden text, doorway pages, or other deceptive tactics.
- Separate "crawlers may not see this" from "this will rank #1."
