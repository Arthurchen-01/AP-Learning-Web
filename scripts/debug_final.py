import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

base = r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json\csa'

# 1. Check 2008PE - why only 4 MCQ? 
print('=== 2008PE MCQ issues ===')
with open(f'{base}\\2008PE_raw.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# The MCQ format is tab-separated: \t1.\t
# Let's find all question starts
matches = list(re.finditer(r'(?:^|\n)\t(\d{1,2})\.\t', text))
print(f'Tab-separated question matches: {len(matches)}')
for m in matches[:15]:
    qnum = int(m.group(1))
    context = text[m.start():m.start()+100].replace('\n', '\\n').replace('\t', '\\t')
    print(f'  Q{qnum} at {m.start()}: {context}')

# 2. Check 2018NA FRQ - missing Q4
print('\n=== 2018NA FRQ ===')
with open(f'{base}\\2018NA_raw.txt', 'r', encoding='utf-8') as f:
    text = f.read()
for m in re.finditer(r'(?:^|\n)\s*(\d)\.\s+', text):
    print(f'  Q{m.group(1)} at {m.start()}: {repr(text[m.start():m.start()+100])}')

# 3. Check 2019NA FRQ - missing Q2-4
print('\n=== 2019NA FRQ ===')
with open(f'{base}\\2019NA_raw.txt', 'r', encoding='utf-8') as f:
    text = f.read()
for m in re.finditer(r'(?:^|\n)\s*(\d)\.\s+', text):
    ctx = text[m.start():m.start()+150].replace('\n', '\\n')
    print(f'  Q{m.group(1)} at {m.start()}: {ctx}')

# 4. Check 2022NA FRQ - missing Q3-4
print('\n=== 2022NA FRQ ===')
with open(f'{base}\\2022NA_raw.txt', 'r', encoding='utf-8') as f:
    text = f.read()
for m in re.finditer(r'(?:^|\n)\s*(\d)\.\s+', text):
    ctx = text[m.start():m.start()+150].replace('\n', '\\n')
    print(f'  Q{m.group(1)} at {m.start()}: {ctx}')

# 5. Check 2015Intl MCQ - why 0 MCQ?
print('\n=== 2015Intl MCQ section ===')
with open(f'{base}\\2015Intl_raw.txt', 'r', encoding='utf-8') as f:
    text = f.read()
s1 = re.search(r'SECTION\s+I\s*[:\n]', text)
s2 = re.search(r'SECTION\s+II', text)
if s1 and s2:
    mcq = text[s1.start():s2.start()]
    print(f'MCQ section: {s1.start()}-{s2.start()}, length={len(mcq)}')
    # Find question patterns
    for m in re.finditer(r'(?:^|\n)\s*(\d{1,2})\.\s+[A-Z]', mcq):
        print(f'  Q{m.group(1)} at {m.start()}: {repr(mcq[m.start():m.start()+100])}')
