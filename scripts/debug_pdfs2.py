import fitz, os
BASE_PDF = r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\pdfs'

# Check more pages of the problematic PDFs
for path, page_range in [
    ('calculus-bc/2025Intl.pdf', range(0, 10)),
    ('physics-c-em/2025Intl.pdf', range(0, 15)),
    ('physics-c-mechanics/2024NASet1.pdf', range(0, 16)),
    ('statistics/2007Intl.pdf', range(0, 38)),
    ('statistics/2025Intl.pdf', range(0, 3)),
]:
    fp = os.path.join(BASE_PDF, path)
    doc = fitz.open(fp)
    print(f'\n=== {path} ({doc.page_count} pages) ===')
    for i in page_range:
        if i >= doc.page_count:
            break
        text = doc[i].get_text().strip()
        if text:
            clean = text.replace('\n', '|')[:300]
            print(f'  Page {i}: {clean}')
        else:
            print(f'  Page {i}: [EMPTY]')
    doc.close()
