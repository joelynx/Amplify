"""Build the POTD competition lookup table.
usage: python -I build_map.py <sheet2.csv> <out_dir> [cutoff] [asof]

cutoff (default 15, the owner's choice of 2026-11-12): a competition with at least this many
problems is its own source; row_assignments.csv gets each row's source and subsource at it.
asof (YYYY-MM-DD, default today): rows dated after it are scheduled, not yet posted, and skipped.
<out_dir>/duplicates.csv (reviewed by hand) lists rows already in the bank or posted twice.
Skipped rows (programming and school exams, duplicates, scheduled) are left out of the counts.
"""
import csv, re, sys, os, collections, json, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ns = {}
exec(open(os.path.join(HERE, 'canon.py'), encoding='utf-8').read(), ns)
exec(open(os.path.join(HERE, 'rules.py'), encoding='utf-8').read(), ns)
CANON, RULES, SKIP_GROUPS = ns['CANON'], ns['RULES'], ns['SKIP_GROUPS']
MODS = ns['MODS']
sys.stdout.reconfigure(encoding='utf-8')

src, outdir = sys.argv[1], sys.argv[2]
CUTOFF = int(sys.argv[3]) if len(sys.argv) > 3 else 15
ASOF = datetime.date.fromisoformat(sys.argv[4]) if len(sys.argv) > 4 else datetime.date.today()
rows = [r for r in csv.DictReader(open(src, encoding='utf-8')) if r['Problem Statement'].strip()]

DUPS = {}
dup_path = os.path.join(outdir, 'duplicates.csv')
if os.path.exists(dup_path):
    DUPS = {d['potd_number']: d['duplicate_of'] for d in csv.DictReader(open(dup_path, encoding='utf-8'))}

def held_back(r):
    """Why a row is left out whatever its competition: '' when it is not."""
    if r['/f'] in DUPS:
        return 'duplicate of ' + DUPS[r['/f']]
    if datetime.datetime.strptime(r['Date'].strip(), '%d %b %Y').date() > ASOF:
        return 'scheduled'
    return ''

# Filed under another competition, with a label at the head of the subsource (owner, 2026-11-12:
# the Shortlist is one source with the IMO).
MERGED = {'IMOSL': ('IMO', 'Shortlist'), 'IMO_LL': ('IMO', 'Longlist')}

def target(k):
    return MERGED[k][0] if k in MERGED else k

# Competitions the bank already has as a source: their own source whatever the cut-off, under the
# bank's name (the bank's "AIME" is renamed to the full name on import; owner, 2026-11-12).
IN_BANK = {'AIME': 'American Invitational Mathematics Examination', 'TRIPOS': 'Cambridge Tripos'}

COMPILED = [(k, re.compile(p), lead) for k, p, lead in RULES]
for k, _, _ in RULES:
    assert k in CANON, k

# country -> (country group, region)
COUNTRY = {
    'United States': ('United States Competitions', 'North America'),
    'Canada': ('Canadian Olympiads', 'North America'),
    'United Kingdom': ('British Olympiads', 'Europe'), 'Ireland': ('Irish Olympiads', 'Europe'),
    'China': ('Chinese Olympiads', 'Asia'), 'Hong Kong': ('Hong Kong Olympiads', 'Asia'),
    'Taiwan': ('Taiwanese Olympiads', 'Asia'), 'Japan': ('Japanese Olympiads', 'Asia'),
    'South Korea': ('Korean Olympiads', 'Asia'), 'North Korea': ('North Korean Olympiads', 'Asia'),
    'Singapore': ('Singaporean Olympiads', 'Asia'), 'Malaysia': ('Malaysian Olympiads', 'Asia'),
    'Indonesia': ('Indonesian Olympiads', 'Asia'), 'Philippines': ('Philippine Olympiads', 'Asia'),
    'Thailand': ('Thai Olympiads', 'Asia'), 'Vietnam': ('Vietnamese Olympiads', 'Asia'),
    'India': ('Indian Olympiads', 'Asia'), 'Bangladesh': ('Bangladeshi Olympiads', 'Asia'),
    'Nepal': ('Nepali Olympiads', 'Asia'), 'Iran': ('Iranian Olympiads', 'Asia'),
    'Israel': ('Israeli Olympiads', 'Asia'), 'Saudi Arabia': ('Saudi Olympiads', 'Asia'),
    'Kazakhstan': ('Kazakh Olympiads', 'Asia'), 'Mongolia': ('Mongolian Olympiads', 'Asia'),
    'Turkey': ('Turkish Olympiads', 'Europe'), 'Armenia': ('Armenian Olympiads', 'Europe'),
    'Azerbaijan': ('Azerbaijani Olympiads', 'Europe'),
    'Russia': ('Russian Olympiads', 'Europe'), 'Soviet Union': ('Russian Olympiads', 'Europe'),
    'Ukraine': ('Ukrainian Olympiads', 'Europe'), 'Belarus': ('Belarusian Olympiads', 'Europe'),
    'Moldova': ('Moldovan Olympiads', 'Europe'), 'Romania': ('Romanian Olympiads', 'Europe'),
    'Bulgaria': ('Bulgarian Olympiads', 'Europe'), 'Serbia': ('Serbian Olympiads', 'Europe'),
    'Yugoslavia': ('Serbian Olympiads', 'Europe'), 'Croatia': ('Croatian Olympiads', 'Europe'),
    'Slovenia': ('Slovenian Olympiads', 'Europe'), 'Bosnia and Herzegovina': ('Bosnian Olympiads', 'Europe'),
    'Kosovo': ('Kosovar Olympiads', 'Europe'), 'Albania': ('Albanian Olympiads', 'Europe'),
    'Greece': ('Greek Olympiads', 'Europe'), 'Cyprus': ('Cypriot Olympiads', 'Europe'),
    'Poland': ('Polish Olympiads', 'Europe'), 'Hungary': ('Hungarian Olympiads', 'Europe'),
    'Austria': ('Austrian Olympiads', 'Europe'), 'Germany': ('German Olympiads', 'Europe'),
    'Netherlands': ('Dutch Olympiads', 'Europe'), 'Belgium': ('Belgian Olympiads', 'Europe'),
    'France': ('French Olympiads', 'Europe'), 'Switzerland': ('Swiss Olympiads', 'Europe'),
    'Italy': ('Italian Olympiads', 'Europe'), 'Spain': ('Spanish Olympiads', 'Europe'),
    'Portugal': ('Portuguese Olympiads', 'Europe'), 'Finland': ('Finnish Olympiads', 'Europe'),
    'Sweden': ('Swedish Olympiads', 'Europe'), 'Norway': ('Norwegian Olympiads', 'Europe'),
    'Lithuania': ('Lithuanian Olympiads', 'Europe'), 'Latvia': ('Latvian Olympiads', 'Europe'),
    'Mexico': ('Mexican Olympiads', 'Latin America'), 'Brazil': ('Brazilian Olympiads', 'Latin America'),
    'Argentina': ('Argentine Olympiads', 'Latin America'), 'Chile': ('Chilean Olympiads', 'Latin America'),
    'Costa Rica': ('Costa Rican Olympiads', 'Latin America'), 'Ecuador': ('Ecuadorian Olympiads', 'Latin America'),
    'Paraguay': ('Paraguayan Olympiads', 'Latin America'),
    'South Africa': ('South African Olympiads', 'Africa'), 'Morocco': ('Moroccan Olympiads', 'Africa'),
    'Nigeria': ('Nigerian Olympiads', 'Africa'),
    'Australia': ('Australian Olympiads', 'Oceania'), 'New Zealand': ('New Zealand Olympiads', 'Oceania'),
}
REGION_GROUP = {'Europe': 'Other European Olympiads', 'Asia': 'Other Asian Olympiads',
                'Latin America': 'Latin American Olympiads', 'Africa': 'African Olympiads',
                'Oceania': 'Oceanian Olympiads', 'North America': 'Other North American Olympiads'}

YEAR = re.compile(r'^(\d{4})(?:\s*[/–-]\s*(\d{1,4}))?,?\s+(.*)$')
ORD = re.compile(r'^(?:The )?(\d+(?:st|nd|rd|th))(?:\s+(.*))?$')
EMB_YEAR = re.compile(r'(?<![\d/])((?:19|20)\d{2})()(?![\d])')

def fmt_year(y1, y2):
    if not y2:
        return y1
    full = y1[:4 - len(y2)] + y2 if len(y2) < 4 else y2
    return f'{y1}/{full[2:]}'

def norm(s):
    s = s.replace('\n', ' | ')
    return re.sub(r'\s+', ' ', s).strip()

TAIL = re.compile(r'\s+(?:P\s?\d|Q\s?\d|#\d|Problem\s*\d|[AB]\d\b|[ACGN]\d+\b|\d+\.\d+|S\d\b|I-?\d|M\d{3,}|E\d).*$')

def raw_name(s):
    t = s
    m = YEAR.match(t)
    if m:
        t = m.group(3)
    m = ORD.match(t)
    if m:
        t = m.group(2) or ''
    mpf = re.search(r'CMO, (Pascal|Fermat)', s)
    if mpf:
        return 'CMO, ' + mpf.group(1)
    head = re.split(r',(?![^()]*\))', t)[0].strip()
    h2 = TAIL.sub('', head).strip()
    if h2 and h2.count('(') == h2.count(')'):
        head = h2
    head = re.sub(r'\s+\(\d+(?:st|nd|rd|th)\)$', '', head)
    head = re.sub(r'\s+(?:19|20)\d{2}$', '', head).strip()
    return head

# ---------- subsource ----------
FLAG_RX = re.compile(r'(?i)\(?\b(adapted|modified|generali[sz]ed|skipped)\b\)?')
SUBS = [
    (re.compile(r'(?i)\bp\s*(\d+[a-z]?)\s*(?:of|ot)\s*p?\s*\d+'), r'Problem \1'),
    (re.compile(r'(?i)\bproblem\s*(\d+[a-z]?)\s*of\s*\d+'), r'Problem \1'),
    (re.compile(r'(?i)\bproblem\s*(\d+[a-z]?)'), r'Problem \1'),
    (re.compile(r'(?i)\bq\s?(\d+[a-z]?)(?:\s*of\s*\d+)?\b'), r'Problem \1'),
    (re.compile(r'\bP\s?(\d+[a-z]?)\b'), r'Problem \1'),
    (re.compile(r'\bP\?\s*of\s*\d+'), r'Problem ?'),
    (re.compile(r'#(\d+)'), r'Problem \1'),
    (re.compile(r'\b([A-Z]-?\d+)\s*of\s*\d+'), r'\1'),
    (re.compile(r'(?i)\bday\s*(\d)'), r'Day \1'),
    (re.compile(r'(?i)\btest\s*(\d+)'), r'Test \1'),
    (re.compile(r'(?i)\b(?:round|rnd\.?)\s*(\d)'), r'Round \1'),
    (re.compile(r'\bR(\d)\b'), r'Round \1'),
    (re.compile(r'(?i)\bgrades?\s*(\d+)'), r'Grade \1'),
    (re.compile(r'\b(\d+)(?:st|nd|rd|th) (?:Grade|Form)\b'), r'Grade \1'),
    (re.compile(r'\bJnr\.?'), 'Junior'),
    (re.compile(r'(?i)\bof\s+\d+\b'), ''),
    (re.compile(r'\b(?:MO|Maths? Olympiad|Mathematical Olympiad)\b'), ''),
]

def clean_label(text):
    flags = []
    def grab(m):
        w = m.group(1).lower()
        w = {'generalized': 'generalised'}.get(w, w)
        flags.append(w)
        return ''
    text = FLAG_RX.sub(grab, text)
    text = re.sub(r'\(\s*\d+(?:st|nd|rd|th)\s*\)', '', text)
    for rx, rep in SUBS:
        text = rx.sub(rep, text)
    # put a comma before a trailing problem label glued to other text (e.g. 'Day 1 Problem 2')
    text = re.sub(r'(\S)\s+(Problem \S+)', r'\1, \2', text)
    text = re.sub(r'\b((?:Round|Test|Day) \d+) (?=[A-Z])', r'\1, ', text)
    toks = []
    for tok in re.split(r'[,|]', text):
        t = re.sub(r'\s+', ' ', tok).strip(' .;:-')
        if t.count('(') > t.count(')'):
            t = t + ')' if not t.startswith('(') else t[1:]
        if t.count(')') > t.count('('):
            t = t.rstrip(')') if not t.endswith(')') or '(' not in t else t
        t = t.strip(' .;:-').lstrip(') ')
        if t and t not in ('Some',):
            toks.append(t)
    return toks, flags

def ordinal(n):
    n = int(n)
    suf = 'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f'{n}{suf}'

ARROW = re.compile(r'(AUS|UNK)\s*(?:→|->)\s*(UNK|AUS)')
CODES = {'AUS': 'Australia', 'UNK': 'UK'}

def subsource(key, s, m):
    """s is the normalised source, m the rule match."""
    t = s
    year = ''
    my = YEAR.match(t)
    if my:
        year = fmt_year(my.group(1), my.group(2))
    edition = ''
    pre, post = s[:m.start()], s[m.end():]
    matched = m.group(0)
    if my:
        cut = len(s) - len(my.group(3))
        if m.start() >= cut:
            pre = s[cut:m.start()]
        else:
            pre = ''
    mo = ORD.match(pre.strip())
    if mo:
        edition = mo.group(1) + ' edition'
        pre = mo.group(2) or ''
    elif ORD.match(s) and m.start() > 0:
        mo = ORD.match(s)
        edition = mo.group(1) + ' edition'
        pre = s[len(s) - len(mo.group(2) or ''):m.start()]
    extra_flags = []
    for word, flag in (('Generalization of', 'generalised'), ('Adapted from', 'adapted'), ('Stronger', 'strengthened'), ('Mock', None)):
        if word in pre:
            pre = pre.replace(word, '')
            if flag:
                extra_flags.append(flag)
    if not year:
        me = EMB_YEAR.search(s)
        if me:
            year = fmt_year(me.group(1), me.group(2))
            pre = EMB_YEAR.sub('', pre)
            post = EMB_YEAR.sub('', post)
    pre_toks, f1 = clean_label(pre)
    post_toks, f2 = clean_label(post)
    toks = pre_toks + post_toks
    flags = extra_flags + f1 + f2
    lead = dict((k, l) for k, _, l in RULES).get(key)
    if lead and toks and re.match(r'\d+\b', toks[0]):
        toks[0] = re.sub(r'^((?:Round|Test|Day) \d+) (?=[A-Z])', r'\1, ', f'{lead} {toks[0]}')
    if key == 'ACPS' and 'Paul Zeitz, 1999' in s:
        year = ''
        toks = [x for x in toks if x != '1999']
    if key == 'AGO':
        toks = [ordinal(x) + ' edition' if re.fullmatch(r'\d+', x) else x for x in toks]
    if key == 'IMO_LL' and 'West German proposal' in s:
        toks.insert(0, 'West German proposal')
    # key-specific touches
    if key == 'AIME':
        toks = ['AIME ' + x if x in ('I', 'II') else x for x in toks]
    if key == 'AMC':
        toks = ['AMC ' + x if re.fullmatch(r'1[02][AB]?', x) else x for x in toks]
    if key == 'KMO' and matched == 'FKMO':
        toks.insert(0, 'Final Round')
    if key == 'AMC' and matched == 'AHSME':
        toks.insert(0, 'AHSME')
    if key == 'IMOK':
        toks = [re.sub(r'^(Maclaurin|Cayley) Olympiad$', r'\1', x) for x in toks]
        toks = [re.sub(r'^([CHM])(\d)$', lambda q: {'C': 'Cayley', 'H': 'Hamilton', 'M': 'Maclaurin'}[q.group(1)] + ', Problem ' + q.group(2), x) for x in toks]
    if key == 'MEMO':
        toks = [re.sub(r'^I-?(\d+)$', r'Individual, Problem \1', x) for x in toks]
        toks = [re.sub(r'^T-?(\d+)$', r'Team, Problem \1', x) for x in toks]
    if key == 'F3':
        new = []
        for x in toks:
            ma = ARROW.search(x)
            new.append(f'set by {CODES[ma.group(1)]} for {CODES[ma.group(2)]}' if ma else x)
        toks = new
    if re.search(r'SL\b|Shortlist', matched) and 'Shortlist' not in CANON[key]['full']:
        toks.insert(0, 'Shortlist')
    if key in MERGED:
        toks.insert(0, MERGED[key][1])
    parts = [p for p in [year, edition] if p] + toks
    out = ', '.join(parts)
    if flags:
        out += ' (' + ', '.join(dict.fromkeys(flags)) + ')'
    return out

# ---------- assign ----------
assign = []
unmatched = collections.Counter()
for i, r in enumerate(rows):
    s = norm(r['Source'])
    key, m = None, None
    for k, rx, _ in COMPILED:
        m = rx.search(s)
        if m:
            key = k
            break
    if key is None:
        key = 'MODS_ATTR'
        unmatched[s] += 1
        sub = s
        rn = s
    else:
        sub = subsource(key, s, m)
        rn = raw_name(s)
    assign.append(dict(idx=i, num=r['/f'], date=r['Date'], source=r['Source'].replace('\n', ' | '),
                       key=target(key), ckey=key, raw=rn, sub=sub, held=held_back(r)))

# ---------- groups ----------
count = collections.Counter(a['key'] for a in assign if not a['held'])
country_total = collections.Counter()
for k, n in count.items():
    c = CANON[k]
    if c['group'] is None:
        country_total[c['country']] += n

EXPLICIT_REGIONAL = {'British Olympiads': 'Other European Olympiads', 'Russian Olympiads': 'Other European Olympiads'}

def group_of(k):
    """first-level group: the country group, or an explicit group for international/mock/etc."""
    c = CANON[k]
    if c['group']:
        return c['group']
    return COUNTRY[c['country']][0]

def regional_of(k):
    """fallback group when the first-level group is itself too small at a given threshold"""
    c = CANON[k]
    if c['group']:
        return EXPLICIT_REGIONAL.get(c['group'], c['group'])
    return REGION_GROUP[COUNTRY[c['country']][1]]

OWNER_RULE = re.compile(r'^(Folklore|Original|Unknown)\b')
PERSONAL_WEB = {'A conversation with my sister', 'Algebra class day 1', 'AoPS (actual source unknown)', 'Assignment from last week',
                'Ben Green', "Catriona Shearer's Twitter", 'David Monk', 'Dr Barker', 'Instagram reels', 'Mathematics Stack Exchange',
                'My Friend', 'My homework', 'OEIS', 'One of those "99% cannot solve" quizzes | (??)', 'Romantics of Geometry, Post 8700, adapted',
                "Tony Wang's friend", 'X+Y (2014 Movie)'}
JOKE = {'Lore', 'F01K10R3', 'Typo', 'RAZING THUNDER', 'BF'}

def mods_attr_detail(raw):
    if OWNER_RULE.match(raw):
        return 'high', 'Owner rule (Folklore/Original/Unknown).'
    if raw in PERSONAL_WEB:
        return 'medium', 'Proposed: person, class or web source with no competition, so attributed to the server; label kept as subsource.'
    if raw in JOKE:
        return 'medium', 'Proposed: joke/pun label ("Lore", "F01K10R3" = FOLKLORE, "Typo"...) for a folklore-type problem.'
    return 'medium', 'Proposed: named classic/theorem with no competition, attributed to the server; label kept as subsource.'

# ---------- competition_map.csv ----------
pairs = collections.Counter((a['raw'], a['ckey']) for a in assign)
out_rows = []
for (raw, k), n in pairs.items():
    c = CANON[k]
    note = c['note']
    conf = c['conf']
    if k == 'MODS_ATTR':
        conf, note = mods_attr_detail(raw)
    if c['group'] in SKIP_GROUPS and not note.startswith('SKIP?'):
        note = 'SKIP? ' + note
    out_rows.append(dict(raw_name=raw, count=n, full_name=CANON[target(k)]['full'], group_source=group_of(k),
                         country_or_region=c['country'], kind=c['kind'], existing_bank_source=c['bank'],
                         confidence=conf, note=note, regional_group=regional_of(k), competition_total=count[target(k)]))
LOWRAW = {  # raw names that drop a mapping's confidence to low
    'Russia', 'Iran', 'Sweden', 'Bosnia and Herzegovina', 'Some Australian TST', 'New Zealand MO',
}
for o in out_rows:
    if o['raw_name'] in LOWRAW and o['confidence'] != 'low':
        o['confidence'] = 'low'
        o['note'] = (o['note'] + ' ' if o['note'] else '') + f'[This raw name: low confidence, no round/paper given.]'
out_rows.sort(key=lambda o: (-o['competition_total'], o['full_name'], -o['count'], o['raw_name'].lower()))
cols = ['raw_name', 'count', 'full_name', 'group_source', 'country_or_region', 'kind', 'existing_bank_source', 'confidence', 'note', 'regional_group']
with open(os.path.join(outdir, 'competition_map.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=cols + ['competition_total'], extrasaction='ignore')
    w.writeheader()
    for o in out_rows:
        w.writerow(o)

# ---------- summary ----------
summary = {}
nonskip = {k: n for k, n in count.items() if CANON[k]['group'] not in SKIP_GROUPS}
comp_kinds = {'national', 'international', 'TST', 'mock', 'community', 'university', 'other'}
competitions = [k for k in nonskip if CANON[k]['kind'] in comp_kinds and k != 'MODS_ATTR']
summary['rows'] = len(assign)
summary['held_back'] = dict(collections.Counter(a['held'].split(':')[0] for a in assign if a['held']))
summary['asof'] = ASOF.isoformat()
summary['skip_rows'] = sum(n for k, n in count.items() if CANON[k]['group'] in SKIP_GROUPS)
summary['skip_keys'] = {CANON[k]['full']: n for k, n in count.items() if CANON[k]['group'] in SKIP_GROUPS}
summary['distinct_competitions'] = len(competitions)
summary['distinct_books_journals'] = len([k for k in nonskip if CANON[k]['kind'] == 'book'])
summary['mods_attr_rows'] = count['MODS_ATTR']
summary['country_total'] = dict(country_total.most_common())
def resolve(T):
    """own source if count >= T; else first-level group; a first-level group that pools < T rows rolls up to its regional group."""
    own = [k for k, n in nonskip.items() if (n >= T or k in IN_BANK) and k != 'MODS_ATTR']
    small = [k for k in nonskip if k not in own]
    pool = collections.Counter()
    for k in small:
        pool[MODS if k == 'MODS_ATTR' else group_of(k)] += nonskip[k]
    final = {}
    for k in small:
        g = MODS if k == 'MODS_ATTR' else group_of(k)
        final[k] = g if (pool[g] >= T or g == regional_of(k)) else regional_of(k)
    # a regional group fed by a single country group is just a rename: keep the country group
    feeders = collections.defaultdict(set)
    for k, g in final.items():
        first = MODS if k == 'MODS_ATTR' else group_of(k)
        if g != first:
            feeders[g].add(first)
    for k, g in list(final.items()):
        first = MODS if k == 'MODS_ATTR' else group_of(k)
        if g != first and len(feeders[g]) == 1 and not any(group_of(j) == g for j in small if j != 'MODS_ATTR'):
            final[k] = first
    return own, final

for T in sorted({5, 10, 15, 20, CUTOFF}):
    own, final = resolve(T)
    grouped, gcomps = collections.Counter(), collections.Counter()
    for k, g in final.items():
        grouped[g] += nonskip[k]
        if k != 'MODS_ATTR':
            gcomps[g] += 1
    own_names = {IN_BANK.get(k, CANON[k]['full']) for k in own}
    srcs = len(own_names | set(grouped))
    summary[f'T{T}'] = dict(
        own_competitions=len(own), own_rows=sum(nonskip[k] for k in own),
        grouped_competitions=sum(gcomps.values()), grouped_rows=sum(grouped.values()),
        total_sources=srcs,
        groups={g: [grouped[g], gcomps[g]] for g in sorted(grouped, key=lambda g: -grouped[g])},
        own=sorted([(IN_BANK.get(k, CANON[k]['full']), nonskip[k]) for k in own], key=lambda x: -x[1]))
summary['competition_counts'] = sorted([(CANON[k]['full'], n, group_of(k), CANON[k]['conf']) for k, n in count.items()], key=lambda x: -x[1])
with open(os.path.join(HERE, 'summary.json'), 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=1, ensure_ascii=False)

# ---------- per-row assignment, at the cut-off ----------
# A row whose competition is merged into a group keeps the competition's full name at the head of
# its subsource, so the group does not lose it.
own, final = resolve(CUTOFF)
with open(os.path.join(outdir, 'row_assignments.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['potd_number', 'date', 'source_as_in_sheet', 'full_name', 'group_source', 'regional_group',
                'source', 'subsource', 'confidence', 'skip'])
    for a in assign:
        k = a['key']
        c = CANON[a['ckey']]
        conf = c['conf']
        if k == 'MODS_ATTR':
            conf = mods_attr_detail(a['raw'])[0]
        if a['raw'] in LOWRAW:
            conf = 'low'
        full = CANON[k]['full']
        skip = a['held'] or ('not an olympiad problem' if CANON[k]['group'] in SKIP_GROUPS else '')
        if skip:
            source, sub = '', a['sub']
        elif k in own:
            source, sub = IN_BANK.get(k, full), a['sub']
        else:
            source = final[k]
            sub = a['sub'] if full == source else ', '.join(p for p in (full, a['sub']) if p)
        w.writerow([a['num'], a['date'], a['source'], full, group_of(k), regional_of(k), source, sub, conf, skip])
print('rows', len(assign), 'keys', len(count), 'competitions', len(competitions), 'map rows', len(out_rows))
print('unmatched -> MODS_ATTR:', sum(unmatched.values()), 'distinct', len(unmatched))
for s, n in sorted(unmatched.items()):
    print(f'  {n}  {s}')
unused = [k for k in CANON if k not in count]
print('unused keys:', unused)
