import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Check 2020SQ1 structure
with open(r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json\csa\2020SQ1_raw.txt', 'r', encoding='utf-8') as f:
    text = f.read()

print(f'Total length: {len(text)}')
print(f'First 2000 chars:')
print(text[:2000])
print('\n=== Looking for MCQ section ===')

# Check for 'Multiple' or 'multiple-choice'
for term in ['multiple-choice', 'Multiple Choice', 'Multiple-Choice', 'SECTION I']:
    idx = text.lower().find(term.lower())
    if idx >= 0:
        print(f'Found "{term}" at {idx}')
        print(text[max(0,idx-100):idx+300])
        print()

# Check for 'Contents' section
contents_idx = text.find('Contents')
if contents_idx >= 0:
    print(f'\n=== Contents at {contents_idx} ===')
    print(text[contents_idx:contents_idx+1500])
