import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open(r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json\csa\2020Intl_raw.txt', 'r', encoding='utf-8') as f:
    text = f.read()

mcq_text = text[5711:32006]

# Find "1. " (question 1)
for m in re.finditer(r'\n1\. ', mcq_text):
    print(f'=== Q1 at {m.start()} ===')
    print(mcq_text[m.start():m.start()+1500])
    print('=== END ===')
    break

# Find "(a)" option pattern
opt_matches = list(re.finditer(r'\([a-e]\)', mcq_text))
print(f'\nTotal option markers found: {len(opt_matches)}')
if opt_matches:
    for om in opt_matches[:10]:
        print(f'  {om.group()} at {om.start()}: context: {repr(mcq_text[max(0,om.start()-20):om.end()+50])}')
