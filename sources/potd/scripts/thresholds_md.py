import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8'))
out = []
out.append('# Own sources vs groups at thresholds 5, 10 and 20\n')
out.append('Generated from `competition_map.csv` / `row_assignments.csv` (2,792 rows with a problem statement).\n')
out.append('Rule used: a competition with at least T problems is its own source. Smaller ones go to their `group_source`; '
           'a `group_source` that still pools fewer than T problems rolls up to its `regional_group` '
           '(unless that regional group would hold only that one country, in which case the country group is kept). '
           f"The {d['skip_rows']} rows flagged skip? (programming and school/admission exams) are left out of all counts. "
           f"Rows with no competition that go to the Discord server: {d['mods_attr_rows']}.\n")
out.append('| Threshold | Sources in total | Own sources (rows) | Competitions/books merged into groups (rows) | Groups |')
out.append('|---|---|---|---|---|')
for T in (5, 10, 20):
    t = d[f'T{T}']
    out.append(f"| {T} | {t['total_sources']} | {t['own_competitions']} ({t['own_rows']}) | {t['grouped_competitions']} ({t['grouped_rows']}) | {len(t['groups'])} |")
out.append('')
for T in (5, 10, 20):
    t = d[f'T{T}']
    out.append(f'## Threshold {T}\n')
    out.append('Groups (problems, competitions merged in):\n')
    for g, (n, c) in t['groups'].items():
        extra = ' + the 240 no-competition rows' if g == 'Math Olympiad Discord Server' else ''
        out.append(f'- {g}: {n} ({c}{extra})')
    out.append('')
    out.append('Own sources: ' + '; '.join(f'{name} ({n})' for name, n in t['own']) + '\n')
open(sys.argv[2], 'w', encoding='utf-8').write('\n'.join(out))
