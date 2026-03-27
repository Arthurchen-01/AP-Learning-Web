import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

base = r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json\csa'

# Check 2020Intl FRQ
print('=== 2020Intl FRQ ===')
with open(f'{base}\\2020Intl_raw.txt', 'r', encoding='utf-8') as f:
    text = f.read()
s2 = re.search(r'SECTION\s+II', text)
if s2:
    frq = text[s2.start():]
    print(f'FRQ section starts at {s2.start()}')
    for m in re.finditer(r'(?:^|\n)\s*(\d)\.\s+', frq):
        ctx = frq[m.start():m.start()+150].replace('\n', '\\n')
        print(f'  Q{m.group(1)} at {m.start()}: {ctx[:120]}')

# Check 2020SQ1 MCQ
print('\n=== 2020SQ1 MCQ ===')
with open(f'{base}\\2020SQ1_raw.txt', 'r', encoding='utf-8') as f:
    text = f.read()
s1 = re.search(r'SECTION\s+I\s*[:\n]', text)
s2 = re.search(r'SECTION\s+II', text)
if s1 and s2:
    mcq = text[s1.start():s2.start()]
    print(f'MCQ section: {s1.start()}-{s2.start()}, length={len(mcq)}')
    # Find Q1
    q1 = re.search(r'\n1\.\s+[A-Z]', mcq)
    if q1:
        print(f'Q1 found at {q1.start()}')
        print(mcq[q1.start():q1.start()+500])
    else:
        # Show first 2000 chars of MCQ section
        print('Q1 not found. MCQ section start:')
        print(mcq[:2000])

# Check 2015Intl - actual MCQ location
print('\n=== 2015Intl actual MCQ ===')
with open(f'{base}\\2015Intl_raw.txt', 'r', encoding='utf-8') as f:
    text = f.read()
# Look for all "SECTION I" occurrences
for m in re.finditer(r'SECTION\s+I\b(?!I)', text):
    ctx = text[m.start():m.start()+200].replace('\n', '\\n')
    print(f'  SECTION I at {m.start()}: {ctx[:150]}')
    print()
