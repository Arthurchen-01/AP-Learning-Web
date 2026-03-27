import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Examine 2015Intl and 2020Intl - full exams
for fname in ['2015Intl', '2020Intl']:
    path = rf'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json\csa\{fname}_raw.txt'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f'=== {fname} ===')
    
    # Find SECTION I boundary (MCQ) and SECTION II boundary (FRQ)
    # Look for explicit "SECTION I" that is NOT part of "SECTION II"
    # Pattern: "SECTION I\n" followed by "Multiple" or "Time"
    s1_matches = list(re.finditer(r'SECTION\s+I\b(?!I)', text))
    s2_matches = list(re.finditer(r'SECTION\s+II\b', text))
    
    print(f'SECTION I matches: {[(m.start(), text[m.start():m.start()+80]) for m in s1_matches[:3]]}')
    print(f'SECTION II matches: {[(m.start(), text[m.start():m.start()+80]) for m in s2_matches[:3]]}')
    
    # Find question patterns in MCQ section
    if s1_matches and s2_matches:
        mcq_start = s1_matches[0].start()
        mcq_end = s2_matches[0].start()
        mcq_text = text[mcq_start:mcq_end]
        
        # Find question numbers
        q_patterns = re.findall(r'\n\s*(\d{1,2})\.\s', mcq_text)
        print(f'MCQ section: {mcq_start}-{mcq_end}, question numbers found: {q_patterns[:20]}...')
    
    print()
