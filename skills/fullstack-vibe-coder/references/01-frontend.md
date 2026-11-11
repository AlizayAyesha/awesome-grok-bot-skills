# Layer 1 — Frontend

Use this file when building or reviewing UI, styling, media, accessibility, or client-side performance. Pair with [10-caching-cdn.md](10-caching-cdn.md) for asset delivery and [08-security-rls.md](08-security-rls.md) for XSS and CSP.

## Accessibility

**Why it matters:** An interface that only works with a mouse and perfect vision excludes users and often fails procurement or legal review.

**Checklist for the agent**

- Use semantic elements (`button`, `nav`, `main`, `label`, headings in order). Do not make a `div` clickable without a real button or link.
- Every input has a visible `<label>` (or `aria-label` only when the design truly has no visible text).
- Keyboard: all actions reachable, focus order matches the visual order, a visible focus ring, and a skip link to main content.
- Images that convey meaning have `alt` text; decorative images have empty `alt`. Icon-only buttons have an accessible name.
- Color is not the only signal. Check contrast (WCAG AA as a default: 4.5:1 for normal text).
- Honor `prefers-reduced-motion`. Announce dynamic updates with live regions when needed.
- If you ship video, include captions.

**Common vibe-coding mistakes:** pretty components with no labels; click handlers on `<div>`; focus outline removed "for design"; contrast that only looks fine on the author's monitor.

**Quick verification:** keyboard-only pass through the main flows; an axe or Lighthouse accessibility audit on key pages; screen-reader spot check on forms and errors.

**Links:** [WCAG 2.2 Quick Reference](https://www.w3.org/WAI/WCAG22/quickref/), [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)

## Mobile Responsiveness

**Why it matters:** Most users will not see your desktop layout first. A "responsive" page that overflows or has 16px tap targets still fails on a phone.

**Checklist for the agent**

- Include a correct viewport meta tag. Start from a 320px-wide layout, not from desktop and shrinking.
- Tap targets at least ~44×44px, with spacing so adjacent controls are not hit together.
- Do not rely on hover for essential actions. Show menus and tooltips in a touch-friendly way.
- Avoid horizontal scroll unless the content is a table or canvas that is explicitly scrollable.
- Test forms with a virtual keyboard (fixed footers must not cover the submit button).
- Prefer responsive typography and fluid images (`max-width: 100%`) over device-specific pages unless you truly have a native app.

**Common vibe-coding mistakes:** breakpoints copied from a template but a 400px-wide modal; `hover:`-only dropdowns; `100vh` mobile bars covering content.

**Quick verification:** resize to 320, 375, 768, and 1280px; check with device mode and a real phone if possible.

## Performance Budgets

**Why it matters:** Unbounded JavaScript and layout shift feel like downtime. A budget makes performance a failing check, not a wish.

**Checklist for the agent**

- Set numeric Performance Budgets: e.g. max compressed JS/CSS on first load, max image weight above the fold, LCP / INP / CLS targets.
- Code-split routes. Defer non-critical scripts. Measure the *real* first-load bundle, not the dev build.
- Avoid shipping the entire icon or animation library for two icons.
- Fail CI when the budget is exceeded (Lighthouse CI, webpack/vite bundle analyzer, or similar).
- Prefer server-rendered or streamed HTML for content pages when SEO or first paint matters.

**Common vibe-coding mistakes:** "it's fine on localhost"; importing a 200KB date library to format one timestamp; measuring performance with React Strict Mode noise and no throttling.

**Quick verification:** production build + Lighthouse (mobile); record LCP element; print bundle sizes per route.

**Links:** [web.dev Core Web Vitals](https://web.dev/articles/vitals), [MDN Performance](https://developer.mozilla.org/en-US/docs/Web/Performance)

## Image Optimization

**Why it matters:** Images are often the heaviest bytes on the page and the usual LCP element.

**Checklist for the agent**

- Serve modern formats (AVIF/WebP) with a fallback. Compress and resize to the largest size you actually display — not the 4000px original.
- Set `width` and `height` (or CSS aspect-ratio) to prevent layout shift. Use `srcset` and `sizes` for responsive images.
- Lazy-load below-the-fold images (`loading="lazy"`); do **not** lazy-load the LCP image. Use `fetchpriority="high"` for the hero.
- Prefer a CDN or image pipeline for transforms rather than committing uncompressed assets.

**Common vibe-coding mistakes:** a 4MB PNG logo; lazy-loading the hero; no dimensions; background images that cannot be alt-texted or srcset.

**Quick verification:** Network panel: image weight and format; no CLS from images; LCP is not an oversized bitmap.

## Video Streaming

**Why it matters:** A raw MP4 in `<video src>` will buffer, waste bandwidth, and fail on slow networks. Video also has accessibility requirements.

**Checklist for the agent**

- For anything longer than a short UI clip, use adaptive streaming (HLS/DASH) or a video platform, not a single huge file on the app server.
- Provide a poster image, captions/subtitles, and a transcript when the video carries information.
- Do not autoplay with sound. Honor reduced-motion and data-saver expectations.
- Support range requests if you self-host. Cache video on a CDN. Keep the player out of the critical JS path when possible.

**Common vibe-coding mistakes:** committing 200MB videos to git; autoplay muted videos that still stall LCP; no captions; serving one 1080p file to every phone.

**Quick verification:** throttle the network and confirm playback starts; captions toggle works; the origin is not your app dyno/container.

## Character Encoding

**Why it matters:** Mixed encodings silently corrupt names, languages, and emoji — often only after the first non-English user arrives.

**Checklist for the agent**

- Use UTF-8 end to end: source files, HTTP `Content-Type` with `charset=utf-8`, HTML `<meta charset="utf-8">`, database client and columns.
- Do not guess encodings when reading CSVs or uploads; declare or detect them, then store UTF-8.
- Normalize Unicode where identity matters (usernames, emails) so visually identical strings compare consistently.
- APIs should not mojibake on the way through a proxy or email template.

**Common vibe-coding mistakes:** default Latin-1 database collation; opening a CSV in a locale-default editor and re-saving; assuming "the frontend will fix it."

**Quick verification:** save and render the string `Iñtërnâtiônàlizætiøn 😀`; check response headers for `charset=utf-8`.

## Time Zones

**Why it matters:** "Tomorrow at 9am" is meaningless without a zone. Server-local time will be wrong for someone as soon as you leave one office.

**Checklist for the agent**

- Store timestamps in UTC (or a proper timestamptz). Convert to the user's Time Zone only at the edges (UI, emails, reports).
- Never build calendar dates from `new Date().getDate()` on a UTC instant without a zone. Be explicit about date-only vs instant values.
- For scheduling (bookings, cron "in the user's morning"), persist the IANA zone (`America/Karachi`, not `UTC+5`, which misses DST rules elsewhere).
- Show the zone on receipts and admin tools so support can reason about events.

**Common vibe-coding mistakes:** `datetime` without time zone in Postgres; formatting with the server locale; comparing "today" in local time to a UTC date column and dropping rows at the boundary.

**Quick verification:** set the OS or browser to a far-away zone and repeat a create/display/filter flow; inspect stored values (they should be UTC/offset-aware).

**Links:** [MDN Date time format](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/DateTimeFormat)
