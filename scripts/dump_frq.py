import fitz
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

base = r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\pdfs\csa\\'
# Dump full text for analysis of 2018NA, 2020Intl, 2022NA, 2024NA
for name in ['2018NA.pdf', '2022NA.pdf', '2024NA.pdf']:
    doc = fitz.open(base + name)
    full = ''
    for page in doc:
        full += page.get_text()
    doc.close()
    with open(rf'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json\csa\{name.replace(".pdf","_raw.txt")}', 'w', encoding='utf-8') as f:
        f.write(full)
    print(f'{name}: {len(full)} chars saved')
