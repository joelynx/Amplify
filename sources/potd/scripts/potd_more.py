import csv, sys, re, collections, datetime
rows = [r for r in csv.DictReader(open(sys.argv[1], encoding='utf-8')) if r['Problem Statement'].strip()]
fig = [r for r in rows if re.search(r'\b(figure|diagram|shown below|picture|as shown|image)\b', r['Problem Statement'], re.I)]
print('mentions figure', len(fig), collections.Counter(r['G'] for r in fig).most_common(4))
proofy = sum(1 for r in rows if re.search(r'\b(prove|show that|determine all|find all)\b', r['Problem Statement'], re.I))
print('prove/show/find all', proofy)
ans_ok = [r['Answer'] for r in rows if r['Answer'].strip()]
junk = [a for a in ans_ok if re.search(r'blud|lol|solved by|qed|xd|bruh', a, re.I)]
print('answers', len(ans_ok), 'junk-looking', len(junk))
today = datetime.date(2026, 11, 11)
fut = [r for r in rows if datetime.datetime.strptime(r['Date'].strip(), '%d %b %Y').date() > today]
print('future-dated', len(fut))
yr = collections.Counter(r['Date'].strip()[-4:] for r in rows); print(sorted(yr.items()))
both = sum(1 for r in rows if r['Hint 1'].strip() and (r['Solution'].strip() or r['Solution Link'].strip()))
none = sum(1 for r in rows if not (r['Hint 1'].strip() or r['Solution'].strip() or r['Solution Link'].strip() or r['Answer'].strip()))
print('hint+solution/link', both, 'nothing but statement', none)
hasref = sum(1 for r in rows if r['Solution'].strip() or r['Solution Link'].strip())
print('solution text or link', hasref)
imo_off = sum(1 for r in rows if 'imo-official' in r['Solution Link'])
aops = sum(1 for r in rows if 'artofproblemsolving' in r['Solution Link'])
print('imo-official links', imo_off, 'aops links', aops)
dd = collections.defaultdict(list)
for r in rows:
    try: d = int(r['D'])
    except: continue
    fam = re.sub(r'^\s*\d{4}\S*\s*', '', r['Source']); fam = re.split(r',| P\d', fam)[0].strip()
    dd[fam].append(d)
for f in ['BMO1','AIME I','EGMO','USAMO','IMO','IMOSL','Putnam','ISL']:
    if dd[f]: v = sorted(dd[f]); print(f, len(v), 'median D', v[len(v)//2])
print('hint sample:', [(r['Source'], r['Hint 1'][:120]) for r in rows[100:103]])
