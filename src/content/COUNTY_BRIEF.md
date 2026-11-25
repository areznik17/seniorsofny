# County data brief (Seniors of NY)
Read /home/claude/seniorsofny/src/content/STYLE.md first (voice, accuracy, no em/en dashes, never name private individuals).
For each assigned New York county, produce one object. Every phone, name and URL must be confirmed TODAY with WebFetch on the official county .gov site, aging.ny.gov (NYSOFA's county office list), nyc.gov, or the place's own official site. If you cannot confirm a field, omit it rather than guess.

Schema:
{
 "slug": "kebab-case county name without 'county' (e.g. "erie", "st-lawrence"); NYC boroughs use "bronx","brooklyn","manhattan","queens","staten-island",
 "name": "Erie County" (boroughs: "Brooklyn (Kings County)", "Manhattan (New York County)", "Staten Island (Richmond County)", "The Bronx (Bronx County)", "Queens (Queens County)"),
 "region": one of nyc, long-island, hudson-valley, capital, north-country, mohawk-valley, central, southern-tier, finger-lakes, western,
 "seat": county seat (boroughs: borough name),
 "towns": [6 to 8 of the larger cities/towns/villages; boroughs: well known neighborhoods],
 "intro": "3 sentences, plain and warm, specific to the county: where it is, what the Office for the Aging does there, one concrete detail (e.g. a named program or transport service). No dashes.",
 "agingOffice": {"name": official name, "phone": main phone, "url": official page},   // NYC boroughs: NYC Aging, 212-AGING (212-244-6469) if confirmed, plus 311
 "transport": {"name": senior or county paratransit / OFA transportation service, "phone": ..., "url": ...},  // NYC: Access-A-Ride
 "dss": {"name": county Department of Social Services (Medicaid, HEAP, SNAP), "phone": ..., "url": ...},  // NYC: HRA, with its info line
 "places": [4 to 5 {"name": ..., "note": one sentence why it's good for an older visitor (flat paths, benches, accessible, free days) only if confirmed on the place's official page}],
 "sources": [["Title","https://..."]],
 "verified": true
}
Write a JSON array to the output path you were given. Validate with python3 json.load and confirm no em/en dashes. Reply with a short table: county, aging phone, transport phone, dss phone, and any field you had to omit.
