# Seniors of NY, working notes (read before every change)

Seniors of NY (seniorsofny.com) is an independent guide for New York State residents 60+ and the adult children and spouses who help them. It runs on the same static engine as Seniors of NJ (github.com/areznik17/seniorsofnj); treat NJ as the gold standard for quality and copy how it works.

Live site is published by Netlify from the `site/` folder on every push to `main`. No build runs on Netlify.

## How to make a change
1. Edit the source in `src/`: `index.html` holds all design, page templates, the benefits checker and calculators; `content/*.json` holds guides (benefits, health, caregiving, living, home, todo, local), `counties.json` (all 62 counties; NYC boroughs use slugs bronx, brooklyn, manhattan, queens, staten-island), `extras.json` (key dates, steps, checklists, glossary, season, phone directory, spotlight) and `nymap.json` (county map); `img/` holds photos (`img/sm/` are 640px copies).
2. Writing and checking: `src/content/STYLE.md` is the writer brief, `src/content/FACTCHECK.md` the fact-checker brief. Every page goes through a writer, then a separate independent fact-checker who re-opens the sources. Nothing ships on the writer's word.
3. Merge with the gate script `scripts/merge.py` (`--counties` and `--extras` modes; county data still awaiting fact-check lives in `data/pending/`, brief in `src/content/COUNTY_BRIEF.md`): it blocks em/en dashes, banned words, duplicate slugs, links to missing pages, missing fields and guides not marked `checked` by a fact-checker.
4. Run `scripts/build.sh` to regenerate `site/` (pre-renders every page with Playwright, writes sitemap.xml, robots.txt, llms.txt, 404.html, favicons and a 1200x630 share card per page). Set `GA_ID=G-...` to include Google Analytics.
5. Crawl for broken internal links and check every sitemap page at 360px and 390px for sideways scroll (`scripts/check.js`). Then commit `src/` and `site/` and push to `main`, one push per batch.

## Owner's rules (non-negotiable)
- 100% accuracy. Every figure, phone number, date, income limit, address and rule comes from an official source opened that day (ny.gov, aging.ny.gov, health.ny.gov, otda.ny.gov, tax.ny.gov, dfs.ny.gov, nyc.gov, county .gov, nycourts.gov, ssa.gov, medicare.gov, cms.gov). If it can't be verified, leave it out. Every guide lists sources and an updated date.
- Depth: guides of 1,400 to 2,400 words, question-style H2s, the answer in the first two sentences, fact tables, a steps block, 5 key facts, 6 FAQs (at least two phrased the way an adult child searches, with a NY place), FAQ and Article schema, internal links.
- Voice: plain, warm, human, short sentences. No em or en dashes anywhere. No "elderly" (say older adults). No hype, no "Whether you're", no "navigate", no colon reveals, no "not X, it's Y". No invented people, quotes, stats or reviews.
- Listings (nursing homes, hospice, home care, adult day, senior centers, funeral homes): every place confirmed on an official source (CMS Care Compare, NY DOH, NYSOFA, county or NYC sites) AND on its own website, with the phone from its own site. No rankings, no "best". Say it is not an endorsement. Never name private individuals.
- Mobile: nothing may ever scroll sideways. Tables stack into cards on phones, filter buttons wrap.
- SEO: every page has its own share card, a title under 65 characters, a description of 130 to 160 characters, a canonical tag, and is in the sitemap and llms.txt. No broken internal links.
- No email signup, no contact form, never ask readers for corrections.
- Images: square or horizontal crops only, real photos.

## Home Happenings (owner's rule)
- Seniors of NY and Home Happenings have the same owner. Home Happenings only serves New Jersey, so NOTHING about Home Happenings appears on Seniors of NY: no ads, no mentions, no links. The header button and footer links were removed from this template.
- `HH_LIVE=false` and `HH_COUNTIES=[]` in `src/index.html` stay that way. If Home Happenings ever expands to New York and the owner says so, it may show only as a clearly labeled paid ad with "Paid ad. Home Happenings and Seniors of NY have the same owner." (HH_DISC) and rel="sponsored", never in guide text.
- Do not cover in-home lessons, hobbies, activities or companionship visits as a service category.
- Do not list Connections Care Management unless the owner says so.
- Seniors of NJ and Seniors of NY may link to each other only where it truly helps a reader (a family split across both states). The footer has one line pointing to Seniors of NJ.

## Page plan (mirror NJ, adapted to New York)
Region pages (/region/<id>/) group counties: nyc, long-island, hudson-valley, capital, north-country, mohawk-valley, central, southern-tier, finger-lakes, western. County pages also render optional services, howto and faq fields.
Hubs: Benefits, Health, Caregiving, Housing & Legal, Living Well, Things to Do; plus Find care help, Tools, Key dates, Glossary, Directory, Spanish (Chinese and Russian pending owner's answer).
Build in waves, biggest search demand first. Local pages: county pages for all 62 counties, then per-county senior centers, nursing homes (CMS stars), hospice, home care, adult day, assisted living and memory care, funeral homes and caring-for-an-aging-parent guides where enough verified listings exist. Start with the five boroughs, Nassau, Suffolk, Westchester, Rockland, Erie, Monroe, Onondaga, Albany. Town and neighborhood pages after. County guide slugs end in `-<county-slug>-county-ny` (boroughs: `-<borough>-ny`) so county pages pick them up.

## After each wave
Give the owner up to 10 URLs a day to index by hand in Search Console, most important first. IndexNow (`.github/workflows/indexnow.yml`, key file `src/<key>.txt`) pings Bing on every push.

## Time-sensitive updates (weekly scheduled task)
- Spotlight on the home page comes from `spotlight` in `extras.json`; the first item whose `until` hasn't passed is shown. Keep at least two future items.
- Watch: EPIC income limits and rules, STAR and Enhanced STAR income limits and deadlines, SCHE/DHE and SCRIE/DRIE limits and the March 15 NYC deadline, HEAP season open and close dates and benefit amounts, Medicare Part B/D figures (CMS mid November), Social Security and SSI/SSP figures (October), NY estate tax exclusion (January), NY Paid Family Leave rates (January), CDPAP fiscal intermediary news, county Office for the Aging program changes.
- Update every page that uses a changed figure and its `updated` date; cite the official source. Validate, rebuild, check, push.

## Scheduled tasks (approved by the owner Nov 25 2026)
- Seniors of NY weekly upkeep: Mondays, refreshes figures and dates, publishes.
- Seniors of NY new pages: Tue/Thu/Sat, one batch of 6 to 10 fact-checked pages, priority on places near Essex and Bergen County NJ (Rockland, Westchester, Orange, Bronx, Manhattan, Staten Island), then everything else. Publishes and sends the owner up to 10 URLs to index.
- Google Search Console: domain property seniorsofny.com verified by DNS TXT in Squarespace; the meta tag is also in scripts/build.sh. Submit https://seniorsofny.com/sitemap.xml once the domain is attached in Netlify (project seniorsofny).
