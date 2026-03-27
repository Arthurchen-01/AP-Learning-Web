import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Examine 2020Intl MCQ section in detail
with open(r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json\csa\2020Intl_raw.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# MCQ section: 5711-32006
mcq_text = text[5711:32006]

# Find question patterns
# Try different patterns
q_patterns = list(re.finditer(r'\n\s*(\d{1,2})\.\s*\n', mcq_text))
print(f'Pattern \\n N. \\n: {len(q_patterns)} matches')
if q_patterns:
    for p in q_patterns[:5]:
        print(f'  Q{p.group(1)} at {p.start()}: {repr(mcq_text[p.start():p.start()+200])}')

q_patterns2 = list(re.finditer(r'\n(\d{1,2})\.\s*\n', mcq_text))
print(f'\nPattern \\nN.\\n: {len(q_patterns2)} matches')

# Try: number on its own line
q_patterns3 = list(re.finditer(r'\n(\d{1,2})\n', mcq_text))
print(f'Pattern \\nN\\n: {len(q_patterns3)} matches')
if q_patterns3:
    for p in q_patterns3[:5]:
        print(f'  At {p.start()}: {repr(mcq_text[p.start():p.start()+100])}')

# Show the text around question 1
idx1 = mcq_text.find('1.\n')
if idx1 < 0:
    idx1 = mcq_text.find('\n1\n')
if idx1 < 0:
    # Try tab
    idx1 = mcq_text.find('\t1.\t')
    
print(f'\n\n=== Around Q1 (idx={idx1}) ===')
if idx1 >= 0:
    print(mcq_text[idx1:idx1+800])
