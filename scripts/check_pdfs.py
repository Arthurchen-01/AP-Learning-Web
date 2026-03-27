import fitz
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

pdfs = ['2008PE.pdf', '2009Intl.pdf', '2018NA.pdf', '2020Intl.pdf', '2022NA.pdf', '2024NA.pdf', '2020SQ1.pdf']
base = r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\pdfs\csa\\'

for name in pdfs:
    doc = fitz.open(base + name)
    text = ''
    for i in range(min(3, len(doc))):
        text += doc[i].get_text()
    print(f'=== {name} ({len(doc)} pages, first 3 pages: {len(text)} chars) ===')
    print(text[:2000])
    print('---END PREVIEW---')
    print()
    doc.close()
