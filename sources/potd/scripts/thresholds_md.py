import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8'))
out = []
TS = (5, 10, 15, 20)
out.append('# Own sources vs groups at thresholds 5, 10, 15 and 20\n')
out.append('The owner chose 15 on 2026-11-12. The IMO Shortlist and Longlist are counted with the IMO.\n')
out.append(f"Generated from `competition_map.csv` / `row_assignments.csv` ({d['rows']:,} rows with a problem statement).\n")
out.append('Rule used: a competition with at least T problems is its own source. Smaller ones go to their `group_source`; '
           'a `group_source` that still pools fewer than T problems rolls up to its `regional_group` '
           '(unless that regional group would hold only that one country, in which case the country group is kept). '
           f"The {d['skip_rows']} rows of programming contests and school exams (STEP and ISI are kept) are left out of all counts, "
           f"and so are the rows held back as of {d['asof']}: "
           + ", ".join(f"{n} {k}" for k, n in d['held_back'].items()) + ". "
           f"Rows with no competition that go to the Discord server: {d['mods_attr_rows']}.\n")
out.append('| Threshold | Sources in total | Own sources (rows) | Competitions/books merged into groups (rows) | Groups |')
out.append('|---|---|---|---|---|')
for T in TS:
    t = d[f'T{T}']
    out.append(f"| {T} | {t['total_sources']} | {t['own_competitions']} ({t['own_rows']}) | {t['grouped_competitions']} ({t['grouped_rows']}) | {len(t['groups'])} |")
out.append('')
for T in TS:
    t = d[f'T{T}']
    out.append(f'## Threshold {T}\n')
    out.append('Groups (problems, competitions merged in):\n')
    for g, (n, c) in t['groups'].items():
        extra = f" + the {d['mods_attr_rows']} no-competition rows" if g == 'Math Olympiad Discord Server' else ''
        out.append(f'- {g}: {n} ({c}{extra})')
    out.append('')
    out.append('Own sources: ' + '; '.join(f'{name} ({n})' for name, n in t['own']) + '\n')
open(sys.argv[2], 'w', encoding='utf-8').write('\n'.join(out))
