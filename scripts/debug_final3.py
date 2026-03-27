import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

base = r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json\csa'

# Check 2008PE - find answer key / solutions section
print('=== 2008PE structure ===')
with open(f'{base}\\2008PE_raw.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Find "Answer Key" or solutions section
for term in ['Answer Key', 'answer key', 'Solutions', 'Question 1\n', 'Question 1 ']:
    idx = text.find(term)
    if idx >= 0:
        print(f'Found "{term}" at {idx}')
        ctx = text[max(0,idx-200):idx+500]
        print(ctx.replace('\n', '\\n')[:400])
        print()

# Show last 500 chars to see if there's a clear boundary
print('\n=== LAST 500 chars of 2008PE ===')
print(text[-500:].replace('\n', '\\n'))

# Also check what comes before "Question 1" solutions section
q1_sol = text.find('Question 1\n(a)')
if q1_sol < 0:
    q1_sol = text.find('Question 1\n(a)')
if q1_sol < 0:
    q1_sol = text.find('Question 1 \n(a)')
if q1_sol > 0:
    print(f'\n=== Before solutions at {q1_sol} ===')
    print(text[max(0,q1_sol-500):q1_sol].replace('\n', '\\n')[:500])

# Check 2020Intl - Q4 detection issue
print('\n\n=== 2020Intl Q4 context ===')
with open(f'{base}\\2020Intl_raw.txt', 'r', encoding='utf-8') as f:
    text = f.read()
s2 = re.search(r'SECTION\s+II', text)
frq = text[s2.start():]
q4_match = re.search(r'\n\s*4\.\s', frq)
if q4_match:
    print(f'Q4 found at {q4_match.start()}: {repr(frq[q4_match.start():q4_match.start()+100])}')
else:
    # Search for "4." more broadly
    for m in re.finditer(r'4\.', frq):
        ctx = frq[max(0,m.start()-30):m.end()+100].replace('\n', '\\n')
        if 'school' in ctx or 'district' in ctx:
            print(f'  Found "4." at {m.start()}: {ctx}')
