import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open(r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json\csa\2020SQ1_raw.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Find actual MCQ section start - look for "SECTION I" with "Multiple Choice" nearby
# or "Multiple-Choice" directions
s1_idx = text.find('SECTION I: Multiple Choice')
if s1_idx < 0:
    s1_idx = text.find('SECTION I \nTime')
if s1_idx < 0:
    # Look for "Multiple-Choice Section" in notes
    s1_idx = text.find('Multiple-Choice Section')

print(f'SECTION I found at: {s1_idx}')

# Find "AP Computer Science A Practice Exam" followed by page number 7 and question 1
# The actual exam starts after the answer sheet
exam_start = text.find('AP\u00ae Computer Science A Practice Exam', 4000)
print(f'Exam section found at: {exam_start}')

# Look for question 1
q1_idx = text.find('1.', exam_start if exam_start > 0 else 4000)
while q1_idx > 0:
    context = text[q1_idx:q1_idx+200]
    # Check if this looks like a real question (not a page number or answer sheet)
    if re.match(r'1\.\s+[A-Z]', text[q1_idx:q1_idx+20]):
        print(f'\nQ1 at {q1_idx}:')
        print(text[q1_idx:q1_idx+800])
        break
    q1_idx = text.find('1.', q1_idx + 2)

# Find answer sheet section
ans_idx = text.find('Answer Sheet')
print(f'\nAnswer Sheet at: {ans_idx}')
if ans_idx > 0:
    print(text[ans_idx:ans_idx+500])
