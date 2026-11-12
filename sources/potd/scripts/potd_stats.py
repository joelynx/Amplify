import csv, sys, re, collections
p = sys.argv[1]
rows = list(csv.reader(open(p, encoding='utf-8')))
hdr = rows[0]; print(hdr)
data = [dict(zip(hdr, r)) for r in rows[1:]]
print('rows', len(data))
st = [d for d in data if d.get('Problem Statement','').strip()]
print('with statement', len(st))
for col in hdr:
    n = sum(1 for d in st if d.get(col,'').strip())
    print(f'  {col!r}: {n}')
print('G', collections.Counter(d['G'] for d in st).most_common())
print('D', sorted(collections.Counter(d['D'] for d in st).items(), key=lambda x: (len(x[0]), x[0])))
print('T top', collections.Counter(d['T'] for d in st).most_common(25))
print('In pdf', collections.Counter(d.get('In pdf?','') for d in st).most_common(8))
print('Solved', collections.Counter(d.get('Solved','') for d in st).most_common(8))
dates = [d['Date'] for d in st]
print('dates', dates[-1], '->', dates[0])
# sources: contest family
fam = collections.Counter()
for d in st:
    s = d['Source']
    s2 = re.sub(r'^\s*\d{4}(/\d{2,4})?\s*', '', s)
    s2 = re.split(r',| P\d| Problem| #', s2)[0].strip()
    fam[s2] += 1
print('source families', len(fam)); print(fam.most_common(60))
orig = sum(1 for d in st if re.search(r'original|mock|curator', d['Source'], re.I))
print('original/mock-ish', orig)
sl = collections.Counter(re.sub(r'(https?://[^/]+).*', r'\1', d['Solution Link']) for d in st if d['Solution Link'].strip())
print('sol link hosts', sl.most_common(10))
il = collections.Counter(re.sub(r'(https?://[^/]+).*', r'\1', d['Image Link']) for d in st if d['Image Link'].strip())
print('image hosts', il.most_common(10))
lens = sorted(len(d['Problem Statement']) for d in st); print('stmt len median', lens[len(lens)//2])
latex = sum(1 for d in st if '$' in d['Problem Statement'] or '\(' in d['Problem Statement']); print('has latex', latex)
ans = [d['Answer'] for d in st if d['Answer'].strip()]; print('answer samples', ans[:15])
sol = [d for d in st if d['Solution'].strip()]; print('solution sample len', sorted(len(d['Solution']) for d in sol)[len(sol)//2] if sol else 0)
print('disc sample', [d['Discussion'][:80] for d in st if d['Discussion'].strip()][:5])
print('sol sample', [d['Solution'][:200] for d in sol][:3])
