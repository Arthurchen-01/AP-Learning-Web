import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Check 2008PE for option format
with open(r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json\csa\2008PE_raw.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Find first question
for m in re.finditer(r'\n\t1\.\t', text):
    print(f'=== 2008PE Q1 at {m.start()} ===')
    print(text[m.start():m.start()+1000])
    break

# Check option format
opts = re.findall(r'\([A-Ea-e]\)', text[:10000])
print(f'\nOption markers in first 10000 chars: {opts[:20]}')

# Check 2020SQ1
with open(r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json\csa\2020SQ1_raw.txt', 'r', encoding='utf-8') as f:
    text2 = f.read()

# Find MCQ section
s1 = text2.find('SECTION I')
if s1 >= 0:
    s2 = text2.find('SECTION II', s1)
    if s2 >= 0:
        mcq = text2[s1:s2]
        opts2 = re.findall(r'\([A-Ea-e]\)', mcq[:5000])
        print(f'\n2020SQ1 MCQ option markers: {opts2[:20]}')
        
        # Find first question
        for m in re.finditer(r'\n\d+\.\s', mcq):
            print(f'\n=== 2020SQ1 MCQ first Q at {m.start()} ===')
            print(mcq[m.start():m.start()+800])
            break
