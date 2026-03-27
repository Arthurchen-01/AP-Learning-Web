import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Look at 2015Intl - 167K chars, check structure
for fname in ['2015Intl', '2020Intl', '2019NA', '2022NA', '2023NA']:
    path = rf'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json\csa\{fname}_raw.txt'
    try:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        continue
    
    print(f'=== {fname} ({len(text)} chars) ===')
    # Show first 500 chars
    print('FIRST 500:', repr(text[:500]))
    print()
    # Search for 'SECTION I' and 'SECTION II'
    for term in ['SECTION I ', 'SECTION II', 'Multiple-Choice', 'Free-Response', 'multiple-choice']:
        indices = [m.start() for m in re.finditer(re.escape(term), text, re.IGNORECASE)]
        if indices:
            print(f'  "{term}" at positions: {indices[:5]}')
    print()
