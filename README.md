# Seniors of NY

The home for older adults in New York State.

- `src/` is the source: `index.html` (design and pages), `content/*.json` (all guides, counties, dates, glossary) and `img/` (photos).
- `site/` is the finished website, with one pre-rendered page per guide, county and topic, plus `sitemap.xml` and `robots.txt`.
- `scripts/build.sh` rebuilds `site/` from `src/`. Read CLAUDE.md before any change.

Netlify is connected to this repository and publishes `site/` automatically on every push to `main`.
