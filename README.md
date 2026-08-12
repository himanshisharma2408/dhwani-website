# Dhwani RIS website — static mockup

A ground-up rebuild of www.dhwaniris.com: 52 static HTML pages (35 top-level + 17
`insights/`), one design system, no build step. This is a **source to migrate into a
Frappe CMS**, not the long-term architecture — see "Known limitations" below.

## Structure

- Every top-level `*.html` page is self-contained: inline `<style>`, inline `<script>`,
  no shared CSS/JS file. `insights/*.html` are blog posts, one directory level down, so
  their internal links carry a `../` prefix.
- `assets/img/` — logos, client marks, case-study photos, self-hosted stock photography
  (`assets/img/stock/`, one file per photo-id/width pair actually used on the site).
- `assets/fonts/` — self-hosted Inter + Newsreader (latin subset, 3 files — both are
  variable fonts, so every static weight the CSS asks for maps onto one of the three).
- `assets/docs/` — downloadable PDFs/decks.
- `tools/check.py` and `tools/set_domain.py` — see below.

## Previewing

No server needed — open any `.html` file directly, or for a full-page screenshot:

```
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$CHROME" --headless --disable-gpu --hide-scrollbars --window-size=1320,4000 \
  --screenshot=out.png --virtual-time-budget=7000 "file://$PWD/index.html"
```

Headless resolves `width=device-width` to ~500px; for a mobile shot use
`--window-size=500,…` (430px crops the right edge).

## `tools/`

- `check.py snapshot` / `check.py verify` — run `snapshot` before a bulk edit across many
  pages, `verify` after, to catch CSS rules a regex silently ate or moved, dead internal
  links, and unbalanced tags. Known blind spots: it globs the top level only (misses
  `insights/`), and its duplicate-rule and moved-rule detection both have false-negative/
  false-positive failure modes on this codebase specifically — see the review below. Not
  worth hardening further; retire it with the rest of this fork when the CMS migration
  lands.
- `set_domain.py <url>` — re-points every canonical, `og:url`, `og:image`,
  `twitter:image`, sitemap, and robots entry at a new base URL in one pass. Run this
  before launch if the domain differs from what's currently baked in.

## Known limitations (as of 12 Aug 2026)

A strict external review (`../dhwani-website-review-2026-08-12.html`, one level up) is
the fullest account of this. In short:

- **No template layer.** Chrome (nav/footer/chat widget) is duplicated across all 52
  pages. This is the root cause of most drift bugs so far, and the CMS migration is the
  real fix — hand-extracting a shared stylesheet now would be wasted effort on an
  architecture about to be replaced.
- **Forms report success without sending anything.** `window.DHWANI_FORMS.FORM_ENDPOINT`
  and `NEWSLETTER_ACTION` are empty on every page; until real endpoint URLs are wired in,
  every contact/newsletter/deck-download form falls back to opening the visitor's mail
  client, but the UI always shows a success state regardless of whether that actually
  happened. **Before wiring the endpoint:** delete the second, unconditional submit
  listener on `contact.html` and `404.html` (search for `addEventListener('submit'` —
  there are two per page) or fetch failures become invisible.
- **Two decks are unresolved.** `mgrant-donors.html` and `mgrant-nonprofits.html` both
  hand over the generic organisation profile instead of a dedicated deck (none exists
  yet). See `../docs/PENDING-FROM-YOU.md` one level up for what's still needed and from
  whom.

## Contact-form / deck-gate config

Every page carries the same config block in `<head>`:

```js
window.DHWANI_FORMS = {
  WHATSAPP_URL: '…',
  BOOKING_URL: '…',
  FORM_ENDPOINT: '',      // <- a URL that accepts a JSON POST (Zoho Form recommended)
  FORM_ENCODING: 'json',
  NEWSLETTER_ACTION: '',  // <- Zoho Campaigns signup form action URL
  NEWSLETTER_FIELD: 'CONTACT_EMAIL',
  NEWSLETTER_ARCHIVE: '',
  NOTIFY_EMAIL: 'partnerships@dhwaniris.com'
};
```

Both empty strings are the two things standing between this site and a working form.
