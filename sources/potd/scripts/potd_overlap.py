import csv, sys, re, sqlite3, collections
def norm(s):
    s = re.sub(r'\[a-zA-Z]+', ' ', s.lower())
    return re.sub(r'[^a-z0-9]+', '', s)
rows = list(csv.DictReader(open(sys.argv[1], encoding='utf-8')))
st = [r for r in rows if r['Problem Statement'].strip()]
c = sqlite3.connect(f'file:{sys.argv[2]}?mode=ro', uri=True)
db = [(norm(t or ''), s) for t, s in c.execute('select latexcode, source from questions')]
# shingle index on 40-char windows
idx = collections.defaultdict(set)
for i, (t, s) in enumerate(db):
    for k in range(0, max(1, len(t) - 40), 20):
        idx[t[k:k+40]].add(i)
hits = collections.Counter(); n = 0
self_dup = collections.Counter(norm(r['Problem Statement'])[:150] for r in st)
for r in st:
    t = norm(r['Problem Statement'])
    cand = collections.Counter()
    for k in range(0, max(1, len(t) - 40), 7):
        for i in idx.get(t[k:k+40], ()): cand[i] += 1
    if cand:
        i, m = cand.most_common(1)[0]
        if m >= 3:
            n += 1; hits[db[i][1]] += 1
print('POTD problems', len(st), 'likely already in DB', n)
print(hits.most_common(20))
print('internal repeats', sum(v - 1 for v in self_dup.values() if v > 1))
