#!/usr/bin/env python3
"""Download the official New York facility lists into data/raw/ (needs network access to
health.data.ny.gov, profiles.health.ny.gov and data.cms.gov, which the owner allowed).

  python3 scripts/fetch_facilities.py          # everything
  python3 scripts/fetch_facilities.py --only nys,profiles,cms

Writes:
  data/raw/nys_facilities.json   NYS DOH Health Facility General Information (vn5v-hh5r), long term care types
  data/raw/profiles_home_care.json  NYS Health Profiles home care offices: profile id, name, city, type, counties served
  data/raw/profiles_<kind>.json  same for hospice, nursing_home, acf when the listing exists
  data/raw/cms_nursing_homes.json  CMS Care Compare nursing home provider info for NY (star ratings)
  data/raw/cms_home_health.json    CMS Care Compare home health agencies for NY (star ratings)
  data/raw/fetched.txt            date and counts
Then run scripts/make_facilities.py to build src/content/facilities.json.
"""
import json, os, re, sys, time, html, urllib.request, urllib.parse, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'data', 'raw')
os.makedirs(RAW, exist_ok=True)
UA = {'User-Agent': 'SeniorsOfNY-data/1.0 (+https://seniorsofny.com/about/)'}

# DOH county names as Health Profiles spells them
DOH_COUNTIES = ["Albany","Allegany","Bronx","Broome","Cattaraugus","Cayuga","Chautauqua","Chemung","Chenango","Clinton",
 "Columbia","Cortland","Delaware","Dutchess","Erie","Essex","Franklin","Fulton","Genesee","Greene","Hamilton","Herkimer",
 "Jefferson","Kings","Lewis","Livingston","Madison","Monroe","Montgomery","Nassau","New York","Niagara","Oneida","Onondaga",
 "Ontario","Orange","Orleans","Oswego","Otsego","Putnam","Queens","Rensselaer","Richmond","Rockland","Saint Lawrence",
 "Saratoga","Schenectady","Schoharie","Schuyler","Seneca","Steuben","Suffolk","Sullivan","Tioga","Tompkins","Ulster",
 "Warren","Washington","Wayne","Westchester","Wyoming","Yates"]

TYPES = ["Licensed Home Care Services Agency", "Certified Home Health Agency", "Hospice",
         "Residential Health Care Facility - SNF", "Adult Home", "Enriched Housing Program",
         "Adult Day Health Care Program - Offsite", "Long Term Home Health Care Program"]


def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def nys():
    out = []
    for t in TYPES:
        q = urllib.parse.urlencode({'$where': f"description='{t}'", '$limit': '50000', '$order': 'fac_id'})
        rows = json.loads(get('https://health.data.ny.gov/resource/vn5v-hh5r.json?' + q))
        print(f'nys {t}: {len(rows)}')
        out += rows
    json.dump(out, open(os.path.join(RAW, 'nys_facilities.json'), 'w'), indent=0)
    return len(out)


ROW = re.compile(r'<tr><td[^>]*>.*?<a href="/(\w+)/view/(\d+)">(.*?)</a></td><td>(.*?)</td><td[^>]*>(.*?)</td><td[^>]*>(.*?)</td></tr>', re.S)
ROW3 = re.compile(r'<tr><td[^>]*>.*?<a href="/(\w+)/view/(\d+)">(.*?)</a></td><td>(.*?)</td><td[^>]*>(.*?)</td></tr>', re.S)


def clean(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s)).strip()


def profiles(kind):
    """kind: home_care, hospice, nursing_home, acf. Walk the counties_served listing for every county."""
    seen = {}
    for c in DOH_COUNTIES:
        url = f'https://profiles.health.ny.gov/{kind}/counties_served/' + urllib.parse.quote(c.replace(' ', '+'), safe='+')
        try:
            page = get(url)
        except Exception as e:
            print(f'  {kind} {c}: failed {e}')
            continue
        n = 0
        for m in ROW.finditer(page):
            k, pid, name, city, typ, serves = m.groups()
            rec = seen.setdefault(pid, {'pid': int(pid), 'kind': k, 'name': clean(name), 'city': clean(city),
                                        'type': clean(typ), 'serves': set()})
            rec['serves'].update(x.strip() for x in clean(serves).split(',') if x.strip())
            n += 1
        if not n:
            for m in ROW3.finditer(page):
                k, pid, name, city, extra = m.groups()
                rec = seen.setdefault(pid, {'pid': int(pid), 'kind': k, 'name': clean(name), 'city': clean(city),
                                            'type': clean(extra), 'serves': set()})
                rec['serves'].add(c)
                n += 1
        print(f'  {kind} {c}: {n}')
        time.sleep(0.5)
    out = [{**r, 'serves': sorted(r['serves'])} for r in seen.values()]
    if out:
        json.dump(out, open(os.path.join(RAW, f'profiles_{kind}.json'), 'w'), indent=0)
    print(f'profiles {kind}: {len(out)} unique')
    return len(out)


def cms(dataset, name):
    rows, off = [], 0
    while True:
        q = urllib.parse.urlencode({'conditions[0][property]': 'state', 'conditions[0][value]': 'NY',
                                    'conditions[0][operator]': '=', 'limit': 500, 'offset': off})
        d = json.loads(get(f'https://data.cms.gov/provider-data/api/1/datastore/query/{dataset}/0?' + q))
        res = d.get('results', [])
        rows += res
        if len(res) < 500:
            break
        off += 500
    json.dump(rows, open(os.path.join(RAW, name), 'w'), indent=0)
    print(f'cms {name}: {len(rows)}')
    return len(rows)


if __name__ == '__main__':
    only = sys.argv[sys.argv.index('--only') + 1].split(',') if '--only' in sys.argv else ['nys', 'profiles', 'cms']
    log = [datetime.date.today().isoformat()]
    if 'nys' in only:
        log.append(f'nys_facilities {nys()}')
    if 'profiles' in only:
        for k in ['home_care', 'hospice', 'nursing_home', 'acf']:
            log.append(f'profiles_{k} {profiles(k)}')
    if 'cms' in only:
        # 4pq5-n9py: Nursing homes Provider Information; 6jpm-sxkc: Home Health Care Agencies
        for ds, nm in [('4pq5-n9py', 'cms_nursing_homes.json'), ('6jpm-sxkc', 'cms_home_health.json')]:
            try:
                log.append(f'{nm} {cms(ds, nm)}')
            except Exception as e:
                log.append(f'{nm} FAILED {e}')
                print(nm, 'failed', e)
    open(os.path.join(RAW, 'fetched.txt'), 'w').write('\n'.join(log) + '\n')
    print('\n'.join(log))
