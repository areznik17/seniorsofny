#!/usr/bin/env python3
"""Build src/content/facilities.json from the official downloads in data/raw/ (see fetch_facilities.py).

Every record comes straight from NYS DOH (health.data.ny.gov and profiles.health.ny.gov) or CMS Care Compare.
Nothing is invented: a field is left out when the source does not have it. The owner approved listing
every licensed agency from the official list (Nov 25 2026). `site` and `siteChecked` are added later,
one by one, when a checker confirms the provider's own website.
"""
import json, os, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'data', 'raw')
OUT = os.path.join(ROOT, 'src', 'content', 'facilities.json')

BORO = {'New York': 'manhattan', 'Kings': 'brooklyn', 'Richmond': 'staten-island', 'Bronx': 'bronx', 'Queens': 'queens'}


def cslug(n):
    n = (n or '').replace(' County', '').strip()
    if n in BORO:
        return BORO[n]
    if n in ('Saint Lawrence', 'St. Lawrence', 'St Lawrence'):
        return 'st-lawrence'
    return re.sub(r'[^a-z0-9]+', '-', n.lower()).strip('-')


def slugify(s):
    s = s.lower().replace('&', ' and ').replace("'", '')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:70].strip('-')


def norm(s):
    s = (s or '').lower().replace('&', 'and')
    s = re.sub(r'\b(inc|llc|corp|corporation|co|ltd|pc|the|of|dba)\b', ' ', s)
    return re.sub(r'[^a-z0-9]', '', s)


def phone(p):
    d = re.sub(r'\D', '', p or '')
    return f'{d[0:3]}-{d[3:6]}-{d[6:10]}' if len(d) == 10 else None


def load(name, default=None):
    p = os.path.join(RAW, name)
    return json.load(open(p)) if os.path.exists(p) else (default if default is not None else [])


NYS_T = {'Licensed Home Care Services Agency': 'lhcsa', 'Certified Home Health Agency': 'chha', 'Hospice': 'hospice',
         'Residential Health Care Facility - SNF': 'snf', 'Adult Home': 'ah', 'Enriched Housing Program': 'eh',
         'Adult Day Health Care Program - Offsite': 'adhc', 'Long Term Home Health Care Program': 'lthhcp'}
PROF_T = {'LHCSA': 'lhcsa', 'CHHA': 'chha'}

nys = load('nys_facilities.json')
counties = {c['slug'] for c in json.load(open(os.path.join(ROOT, 'src', 'content', 'counties.json')))}
fetched = (open(os.path.join(RAW, 'fetched.txt')).read().split('\n')[0] if os.path.exists(os.path.join(RAW, 'fetched.txt')) else '')

by_name_city = collections.defaultdict(list)
for r in nys:
    by_name_city[(norm(r.get('facility_name')), (r.get('city') or '').lower())].append(r)
by_name = collections.defaultdict(list)
for r in nys:
    by_name[norm(r.get('facility_name'))].append(r)

recs, used = [], set()


def from_nys(r, t):
    return {'t': t, 'n': r.get('facility_name', '').strip(), 'a': (r.get('address1') or '').strip() or None,
            'c': (r.get('city') or '').strip() or None, 'z': r.get('fac_zip'), 'p': phone(r.get('fac_phone')),
            'co': cslug(r.get('county')), 'lic': r.get('opcert_num'), 'own': r.get('ownership_type'),
            'op': (r.get('operator_name') or '').strip() or None, 'opened': (r.get('fac_opn_dat') or '')[:10] or None,
            'fid': r.get('fac_id'),
            'lat': float(r['latitude']) if r.get('latitude') else None, 'lng': float(r['longitude']) if r.get('longitude') else None}


# 1. Home care offices from Health Profiles (one record per office, with counties served)
for p in load('profiles_home_care.json'):
    t = PROF_T.get(p['type'])
    if not t:
        continue
    m = by_name_city.get((norm(p['name']), p['city'].lower())) or [x for x in by_name.get(norm(p['name']), []) if NYS_T.get(x.get('description')) == t]
    m = [x for x in m if NYS_T.get(x.get('description')) == t]
    rec = from_nys(m[0], t) if len(m) == 1 else {'t': t, 'n': p['name'], 'c': p['city']}
    if len(m) == 1:
        used.add(m[0].get('fac_id'))
    rec['n'] = p['name']
    rec['c'] = p['city'] or rec.get('c')
    rec['pid'] = p['pid']
    rec['pr'] = f"https://profiles.health.ny.gov/home_care/view/{p['pid']}"
    rec['sv'] = sorted({cslug(x) for x in p['serves']} & counties)
    recs.append(rec)

# 2. Everything else (and any home care license not matched above) from the NYS facility list
prof_kind = {'hospice': 'hospice', 'snf': 'nursing_home', 'ah': 'acf', 'eh': 'acf'}
plists = {k: load(f'profiles_{k}.json') for k in ('hospice', 'nursing_home', 'acf')}
pidx = {k: collections.defaultdict(list) for k in plists}
for k, L in plists.items():
    for p in L:
        pidx[k][(norm(p['name']), p['city'].lower())].append(p)
for r in nys:
    t = NYS_T.get(r.get('description'))
    if not t or r.get('fac_id') in used or t == 'lthhcp':
        continue
    if t in ('lhcsa', 'chha') and load('profiles_home_care.json'):
        continue  # offices already listed from Health Profiles
    rec = from_nys(r, t)
    k = prof_kind.get(t)
    if k:
        hit = pidx[k].get((norm(rec['n']), (rec['c'] or '').lower()))
        if hit and len(hit) == 1:
            rec['pid'] = hit[0]['pid']
            rec['pr'] = f"https://profiles.health.ny.gov/{hit[0]['kind']}/view/{hit[0]['pid']}"
            if t == 'hospice':
                rec['sv'] = sorted({cslug(x) for x in hit[0]['serves']} & counties)
    recs.append(rec)

# 3. CMS star ratings (nursing homes by name+city+zip; home health by name+zip)
def cms_idx(rows, name_keys, city_keys, zip_keys):
    idx = {}
    for x in rows:
        nm = next((x[k] for k in name_keys if x.get(k)), '')
        z = next((str(x[k])[:5] for k in zip_keys if x.get(k)), '')
        idx[(norm(nm), z)] = x
    return idx

nh = cms_idx(load('cms_nursing_homes.json'), ['provider_name'], ['citytown', 'city'], ['zip_code'])
hh = cms_idx(load('cms_home_health.json'), ['provider_name'], ['citytown', 'city'], ['zip_code'])
for rec in recs:
    key = (norm(rec['n']), (rec.get('z') or '')[:5])
    if rec['t'] == 'snf' and key in nh:
        x = nh[key]
        rec['ccn'] = x.get('cms_certification_number_ccn') or x.get('federal_provider_number')
        for src, dst in [('overall_rating', 'st'), ('health_inspection_rating', 'sti'), ('staffing_rating', 'sts'),
                         ('qm_rating', 'stq'), ('number_of_certified_beds', 'beds')]:
            if str(x.get(src, '')).strip().isdigit():
                rec[dst] = int(x[src])
    if rec['t'] == 'chha' and key in hh:
        x = hh[key]
        rec['ccn'] = x.get('cms_certification_number_ccn')
        v = str(x.get('quality_of_patient_care_star_rating', '')).strip()
        if re.fullmatch(r'\d(\.\d)?', v):
            rec['st'] = float(v)

# 4. Slugs, county check, drop empty
out, seen = [], set()
for rec in sorted(recs, key=lambda r: (r['t'], r['n'], r.get('c') or '')):
    if not rec.get('n'):
        continue
    if rec.get('co') and rec['co'] not in counties:
        rec.pop('co')
    base = slugify(f"{rec['n']} {rec.get('c') or ''}")
    s, i = base, 2
    while s in seen:
        s, i = f'{base}-{i}', i + 1
    seen.add(s)
    rec['slug'] = s
    out.append({k: v for k, v in rec.items() if v not in (None, '', [])})

json.dump({'asof': fetched, 'items': out}, open(OUT, 'w'), separators=(',', ':'), ensure_ascii=False)
print(len(out), 'facilities', collections.Counter(r['t'] for r in out))
