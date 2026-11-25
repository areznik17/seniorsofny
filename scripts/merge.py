#!/usr/bin/env python3
"""Merge fact-checked batch files into src/content and block anything that breaks the rules.
Usage: merge.py <batch.json>... (guides) ; counties merge with --counties; extras with --extras
Blocks: invalid JSON, em/en dashes, banned words, duplicate slugs, internal links to missing slugs,
missing fields, seo lengths, Home Happenings / Connections mentions, guides not marked checked."""
import json,re,sys,glob,os
import os
C=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','src','content')
HUBFILE={'benefits':'benefits','health':'health','caregiving':'caregiving','living':'living','home':'home','things-to-do':'todo'}
BANNED=[r'\belderly\b',r"\bwhether you're\b",r'\bnavigat',r"\bit's worth noting\b",r'home happenings',r'homehappenings',r'connections care management',r'caremanagementconnect']
DASH=re.compile('[—–]')
def load(f):
    try: return json.load(open(f))
    except FileNotFoundError: return []
def words(h): return len(re.sub(r'<[^>]+>',' ',h).split())
args=sys.argv[1:]; mode='guides'
if args and args[0].startswith('--'): mode=args.pop(0)[2:]
errs=[];warn=[]
if mode=='counties':
    # Updates the existing counties.json by slug (later files win); never drops a county.
    cur={c['slug']:c for c in load(C+'/counties.json')}
    newc=[]
    for f in args: newc+=[c for c in json.load(open(f)) if c.get('checked')]
    slugs=[c['slug'] for c in newc]
    dup={s for s in slugs if slugs.count(s)>1}
    if dup: warn.append(f'later file wins for {dup}')
    for c in newc: cur[c['slug']]=c
    allc=list(cur.values())
    for c in newc:
        t=json.dumps(c,ensure_ascii=False)
        if DASH.search(t): errs.append(f"{c['slug']}: dash")
        tt=re.sub(r'https?://\S+','',t.lower()).replace('in-home services for the elderly','')
        for b in BANNED[:3]:
            if re.search(b,tt): errs.append(f"{c['slug']}: banned {b}")
        for k in ('slug','name','region','intro','agingOffice'):
            if not c.get(k): errs.append(f"{c['slug']}: missing {k}")
    if errs: print('\n'.join(errs)); sys.exit(1)
    json.dump(sorted(allc,key=lambda c:c['name']),open(C+'/counties.json','w'),ensure_ascii=False,indent=1); print('\n'.join(warn)) if warn else None; print(len(newc),'updated,',len(allc),'counties total'); sys.exit(0)
if mode=='extras':
    x=json.load(open(args[0]))
    if DASH.search(json.dumps(x,ensure_ascii=False)): print('dash in extras'); sys.exit(1)
    json.dump(x,open(C+'/extras.json','w'),ensure_ascii=False,indent=1); print('extras merged'); sys.exit(0)
# guides
existing={}
for h,f in HUBFILE.items():
    for a in load(f'{C}/{f}.json'): existing[a['slug']]=a
new=[]
for f in args: new+=json.load(open(f))
ns=[a['slug'] for a in new]
dup={s for s in ns if ns.count(s)>1}
if dup: errs.append(f'duplicate slugs in batch {dup}')
for a in new: existing[a['slug']]=a
allslugs=set(existing)
csl={c['slug'] for c in load(C+'/counties.json')}
for a in new:
    s=a['slug'];t=json.dumps(a,ensure_ascii=False)
    for k in ('title','dek','hub','body','faq','sources','keyFacts','updated','seoDesc','photo'):
        if not a.get(k): errs.append(f'{s}: missing {k}')
    if a.get('hub') not in HUBFILE: errs.append(f'{s}: bad hub {a.get("hub")}')
    if DASH.search(t): errs.append(f'{s}: em/en dash')
    low=t.lower().replace('elderly pharmaceutical insurance coverage','epic-name').replace('in-home services for the elderly','eisep-name').replace('all-inclusive care for the elderly','pace-name')
    low=re.sub(r'https?://[^"\s<>]+','URL',low)
    if re.search(r'\bbest\b',low): warn.append(f'{s}: uses "best"')
    for b in BANNED:
        if re.search(b,low): errs.append(f'{s}: banned pattern {b}')
    if a.get('checked')!=a.get('updated'): errs.append(f'{s}: not marked checked by fact-checker')
    w=words(a.get('body',''))
    if not 1300<=w<=2600: errs.append(f'{s}: {w} words')
    d=a.get('seoDesc','')
    if not 120<=len(d)<=165: warn.append(f'{s}: seoDesc {len(d)} chars')
    if len(a.get('seoTitle') or a['title'])>65: warn.append(f'{s}: title long')
    if len(a.get('faq',[]))<5: errs.append(f'{s}: {len(a.get("faq",[]))} faqs')
    if 'class="facts"' not in a['body']: warn.append(f'{s}: no facts table')
    if 'class="steps"' not in a['body']: warn.append(f'{s}: no steps block')
    for l in re.findall(r'#/article/([\w-]+)',t):
        if l not in allslugs: errs.append(f'{s}: link to missing article {l}')
    for l in re.findall(r'#/county/([\w-]+)',t):
        if csl and l not in csl: errs.append(f'{s}: link to missing county {l}')
print('\n'.join('WARN '+w for w in warn))
if errs: print('\n'.join('BLOCK '+e for e in errs)); sys.exit(1)
by={f:[] for f in HUBFILE.values()}
for a in existing.values(): by[HUBFILE[a['hub']]].append(a)
for f,L in by.items(): json.dump(sorted(L,key=lambda a:a['slug']),open(f'{C}/{f}.json','w'),ensure_ascii=False,indent=1)
print(len(new),'guides merged;',len(existing),'total')
