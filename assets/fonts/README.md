Self-hosted Google Fonts (Inter + Newsreader), latin subset only.

Re-fetch with:
curl -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36" \
  "https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500&family=Inter:wght@400;450;500;600&display=swap"

Both are variable fonts: Google serves the *same* woff2 file for every static weight
declared in that request, so there are only 3 unique files to keep, not 9 -- Inter
(400-600), Newsreader normal (400-600), Newsreader italic (400-500).
