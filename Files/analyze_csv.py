import csv

with open(r'Files/Terms.csv', encoding='utf-8') as f:
    reader = csv.reader(f)
    rows = list(reader)

print('Row 0 (types):', rows[0])
print('Row 1 (headers):', rows[1])
print('Total rows (including header rows):', len(rows))
print()

headers = rows[1]
empties = {h: 0 for h in headers}
filled = {h: 0 for h in headers}

for r in rows[2:]:
    dict_r = dict(zip(headers, r))
    for k, v in dict_r.items():
        if v.strip():
            filled[k] += 1
        else:
            empties[k] += 1

print('Column stats:')
for h in headers:
    print(f'  {h}: {filled[h]} filled, {empties[h]} empty')

# Check how many questions reference images
image_refs = 0
for r in rows[2:]:
    dict_r = dict(zip(headers, r))
    latex = dict_r.get('latexcode', '')
    if 'includegraphics' in latex or '.jpg' in latex or '.png' in latex or '.jpeg' in latex:
        image_refs += 1
        
print(f'\nQuestions referencing images: {image_refs}')

# Show a few rows with image references
print('\nSample rows with image references:')
count = 0
for i, r in enumerate(rows[2:]):
    dict_r = dict(zip(headers, r))
    latex = dict_r.get('latexcode', '')
    if 'includegraphics' in latex or '.jpg' in latex or '.png' in latex:
        print(f'  Row {i+2}: Source={dict_r.get("Source","")}, latex snippet: ...{latex[max(0,latex.find(".jpg")-40):latex.find(".jpg")+20]}...')
        count += 1
        if count >= 5:
            break

# Check Solution column for image references
sol_img = 0
for r in rows[2:]:
    dict_r = dict(zip(headers, r))
    sol = dict_r.get('Solution', '')
    if 'includegraphics' in sol or '.jpg' in sol or '.png' in sol:
        sol_img += 1
print(f'\nSolutions referencing images: {sol_img}')

# Check Hints column for image references
hint_img = 0
for r in rows[2:]:
    dict_r = dict(zip(headers, r))
    hints = dict_r.get('Hints', '')
    if 'includegraphics' in hints or '.jpg' in hints or '.png' in hints:
        hint_img += 1
print(f'Hints referencing images: {hint_img}')
