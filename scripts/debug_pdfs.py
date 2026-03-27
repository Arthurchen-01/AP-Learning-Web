import fitz, os
BASE_PDF = r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\pdfs'

for path in [
    'calculus-bc/2025Intl.pdf',
    'physics-c-em/2025Intl.pdf', 
    'physics-c-mechanics/2024NASet1.pdf',
    'statistics/2007Intl.pdf',
    'statistics/2025Intl.pdf',
]:
    fp = os.path.join(BASE_PDF, path)
    doc = fitz.open(fp)
    print(f'\n=== {path} ({doc.page_count} pages) ===')
    for i in range(min(5, doc.page_count)):
        text = doc[i].get_text()
        clean = text.replace('\n', '|')[:250]
        print(f'  Page {i}: {clean}')
    doc.close()
