import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open(r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json\csa\2018NA_raw.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Search for MCQ indicators
for ind in ['multiple-choice', 'Multiple Choice', 'Multiple-Choice', 'SECTION I', 'Multiple-Choice Questions']:
    idx = text.lower().find(ind.lower())
    if idx >= 0:
        print(f'Found "{ind}" at {idx}: ...{text[max(0,idx-50):idx+100]}...')
