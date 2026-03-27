#!/usr/bin/env python3
"""Extract AP Statistics 2024 NA from PDF via EasyOCR and convert to JSON."""
import sys, os, json, time
sys.stdout.reconfigure(encoding='utf-8')

import fitz
import easyocr

BASE = r"C:\Users\25472\projects\methods\mokaoai.com\database\01_raw"
PDF_PATH = os.path.join(BASE, "pdfs", "statistics", "2024NA.pdf")
IMG_DIR = os.path.join(BASE, "pdfs", "statistics", "pages")
OUT_DIR = os.path.join(BASE, "json", "statistics")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Step 1: Get text pages (formulas, tables) ──
doc = fitz.open(PDF_PATH)
text_pages = {}
for i in [1, 17, 18, 19, 20]:  # pages 2, 18-21
    text_pages[i+1] = doc[i].get_text()
doc.close()

# ── Step 2: OCR image pages ──
print("Loading EasyOCR reader...")
reader = easyocr.Reader(['en'], gpu=False)

ocr_pages = {}
for pg_num in range(3, 18):  # pages 3-17
    img_path = os.path.join(IMG_DIR, f"page_{pg_num}.png")
    if not os.path.exists(img_path):
        print(f"  Page {pg_num}: image not found, skipping")
        continue
    print(f"  OCR page {pg_num}...", end=" ", flush=True)
    t0 = time.time()
    results = reader.readtext(img_path, detail=0, paragraph=True)
    text = '\n'.join(results)
    ocr_pages[pg_num] = text
    print(f"{len(text)} chars ({time.time()-t0:.1f}s)")

# ── Step 3: Save raw combined text ──
all_pages = {}
all_pages.update(text_pages)
all_pages.update(ocr_pages)

combined_path = os.path.join(OUT_DIR, "2024NA_combined.txt")
with open(combined_path, 'w', encoding='utf-8') as f:
    for pg in sorted(all_pages.keys()):
        f.write(f"=== PAGE {pg} ===\n{all_pages[pg]}\n\n")
print(f"\nCombined text saved to {combined_path}")

# Print summary
total = sum(len(t) for t in all_pages.values())
print(f"Total text: {total} chars from {len(all_pages)} pages")
print("OCR extraction complete.")
