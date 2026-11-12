import csv, sys
sys.stdout.reconfigure(encoding='utf-8')
rows = list(csv.DictReader(open(sys.argv[1], encoding='utf-8-sig')))
want = ['2024 IMOSL, C5', '2019 China TST Test 4, P2 of 6', '2017 Irish MO, Day 1, P1 of 5', '2008 Putnam, A5',
        '2002 AIME II, P7 OF 15', '2001/02 BMO1, P1 of 5', '2015 UK IMOK, C6', '2016 ToT Fall, Senior A-6',
        '2025 MEMO, I2 of 4', '2023 AUS → UNK F3, P2 of 3', '2024 CMO, Pascal P20', '2014 Taiwan TST1 Quiz 2, P1',
        '2017 Serbia MO, P4 of 6 (Modified)', '4th AGO, P5 of 6', 'PST 10.0.11', 'Broken Chord Theorem', 'Folklore',
        '2010 AMC 10A, P24 of 25', '2023 ICMC Round 1, P3 of 6', '2025 IGO Advanced, P3 of 5']
seen = set()
for w in want:
    for r in rows:
        if r['source_as_in_sheet'].strip() == w and w not in seen:
            seen.add(w)
            print(f"{w}\t{r['source'] or '(' + r['skip'] + ')'}\t{r['subsource']}")
print('missing', [w for w in want if w not in seen])

