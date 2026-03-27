# -*- coding: utf-8 -*-
"""
OCR批量处理扫描版AP真题PDF
使用EasyOCR提取图片中的文字，然后转换为JSON
"""
import fitz  # PyMuPDF
import json
import os
import sys
import io
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PDF_DIR = r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\pdfs'
JSON_DIR = r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json'

# Image-based PDFs that need OCR
IMAGE_PDFS = [
    ('calculus-bc', '2023Intl', '微积分BC', '国际卷', '2023'),
    ('calculus-bc', '2024Intl', '微积分BC', '国际卷', '2024'),
    ('macroeconomics', '2005Intl', '宏观经济', '国际卷', '2005'),
    ('macroeconomics', '2024Intl', '宏观经济', '国际卷', '2024'),
    ('macroeconomics', '2025Intl', '宏观经济', '国际卷', '2025'),
    ('microeconomics', '2010Intl', '微观经济', '国际卷', '2010'),
    ('microeconomics', '2022Intl', '微观经济', '国际卷', '2022'),
    ('microeconomics', '2024Intl', '微观经济', '国际卷', '2024'),
    ('physics-c-em', '2024Intl', '物理C电磁', '国际卷', '2024'),
    ('physics-c-em', '2024NASet1', '物理C电磁', '北美卷Set1', '2024'),
    ('physics-c-em', '2024NASet2', '物理C电磁', '北美卷Set2', '2024'),
    ('physics-c-em', '2025Intl', '物理C电磁', '国际卷', '2025'),
    ('physics-c-mechanics', '2004Intl', '物理C力学', '国际卷', '2004'),
    ('physics-c-mechanics', '2009Intl', '物理C力学', '国际卷', '2009'),
    ('physics-c-mechanics', '2024Intl', '物理C力学', '国际卷', '2024'),
    ('physics-c-mechanics', '2025Intl', '物理C力学', '国际卷', '2025'),
    ('psychology', '2024Intl', '心理学', '国际卷', '2024'),
    ('psychology', '2024NASet1', '心理学', '北美卷Set1', '2024'),
    ('psychology', '2024NASet2', '心理学', '北美卷Set2', '2024'),
    ('psychology', '2025Intl', '心理学', '国际卷', '2025'),
]

SUBJECT_TIMES = {
    '微积分BC': (60, 90),
    '宏观经济': (70, 60),
    '微观经济': (70, 60),
    '物理C力学': (45, 45),
    '物理C电磁': (45, 45),
    '心理学': (90, 70),
}

def extract_text_ocr(pdf_path, ocr_reader):
    """Extract text from image-based PDF using EasyOCR"""
    doc = fitz.open(pdf_path)
    all_text = []
    
    for i, page in enumerate(doc):
        # Render page as image
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
        
        # Save temp image
        temp_path = f'_temp_page_{i}.png'
        with open(temp_path, 'wb') as f:
            f.write(img_bytes)
        
        # OCR
        results = ocr_reader.readtext(temp_path)
        page_text = '\n'.join([r[1] for r in results])
        all_text.append(page_text)
        
        # Cleanup
        os.remove(temp_path)
        print(f'  Page {i+1}/{len(doc)}: {len(page_text)} chars')
    
    doc.close()
    return '\n\n'.join(all_text)

def build_json(exam_id, title, subject_name, year, text):
    """Build JSON from OCR text"""
    mcq_time, frq_time = SUBJECT_TIMES.get(subject_name, (70, 60))
    
    sections = []
    
    # Try to detect MCQ section
    mcq_match = re.search(r'SECTION\s+I|Multiple\s+Choice|MCQ', text, re.IGNORECASE)
    frq_match = re.search(r'SECTION\s+II|Free\s+Response|FRQ', text, re.IGNORECASE)
    
    if mcq_match and frq_match:
        # Both sections present
        mcq_text = text[:frq_match.start()]
        frq_text = text[frq_match.start():]
        
        sections.append({
            "id": "section-mcq",
            "title": "Section I - Multiple Choice",
            "partTitle": "Part MCQ - Multiple Choice",
            "limitMinutes": mcq_time,
            "directions": mcq_text[:500] if len(mcq_text) > 500 else mcq_text,
            "questions": parse_mcq_questions(mcq_text)
        })
        sections.append({
            "id": "section-frq",
            "title": "Section II - Free Response",
            "partTitle": "Part FRQ - Free Response",
            "limitMinutes": frq_time,
            "directions": frq_text[:500] if len(frq_text) > 500 else frq_text,
            "questions": parse_frq_questions(frq_text)
        })
    else:
        # Single section (likely FRQ only)
        sections.append({
            "id": "section-frq",
            "title": "Section II - Free Response",
            "partTitle": "Free Response Questions",
            "limitMinutes": frq_time,
            "directions": text[:500] if len(text) > 500 else text,
            "questions": parse_frq_questions(text)
        })
    
    return {
        "examId": exam_id,
        "title": title,
        "subjectName": subject_name,
        "yearLabel": year,
        "description": "Practice mode only. OCR-extracted from scanned PDF.",
        "answerKeyAvailable": False,
        "scoring": {
            "answerKeyAvailable": False,
            "apBands": [],
            "note": "Scoring unavailable until answer keys are imported."
        },
        "sections": sections
    }

def parse_mcq_questions(text):
    """Parse MCQ questions from text"""
    questions = []
    # Find question patterns: "1." followed by text and A/B/C/D/E options
    pattern = r'(\d+)\.\s+(.*?)(?=\d+\.\s|$)'
    matches = re.findall(pattern, text, re.DOTALL)
    
    for num, content in matches:
        if int(num) > 200:  # Skip page numbers
            continue
        options = re.findall(r'([A-E])\)\s*(.*?)(?=[A-E]\)|\d+\.|$)', content, re.DOTALL)
        prompt = re.split(r'[A-E]\)', content)[0].strip()
        
        questions.append({
            "id": num,
            "type": "single",
            "prompt": prompt[:500],
            "options": [{"key": k, "text": v.strip()[:200]} for k, v in options],
            "answer": None,
            "explanation": "Answer key not available yet for this imported exam."
        })
    
    return questions

def parse_frq_questions(text):
    """Parse FRQ questions from text"""
    questions = []
    # Find "1." or "Question 1" patterns
    parts = re.split(r'(?:(?:Question|Q)\s*|^)(\d+)\.\s', text)
    
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            qnum = parts[i]
            content = parts[i + 1]
            questions.append({
                "id": f"q{qnum}",
                "type": "free-response",
                "prompt": content[:2000],
                "options": [],
                "answer": None,
                "explanation": "Answer key not available yet for this imported exam."
            })
    
    if not questions:
        # Fallback: just put the whole text as one question
        questions.append({
            "id": "q1",
            "type": "free-response",
            "prompt": text[:5000],
            "options": [],
            "answer": None,
            "explanation": "Answer key not available yet for this imported exam."
        })
    
    return questions

def main():
    print("Initializing EasyOCR...")
    import easyocr
    reader = easyocr.Reader(['en'], gpu=False)
    print("EasyOCR ready.")
    
    success = 0
    failed = 0
    
    for subj, filename, zh_name, paper_type, year in IMAGE_PDFS:
        pdf_path = os.path.join(PDF_DIR, subj, f'{filename}.pdf')
        json_path = os.path.join(JSON_DIR, subj, f'{filename}.json')
        
        # Skip if already done
        if os.path.exists(json_path) and os.path.getsize(json_path) > 100:
            print(f'[SKIP] {subj}/{filename} - already exists')
            success += 1
            continue
        
        if not os.path.exists(pdf_path):
            print(f'[MISS] {subj}/{filename} - PDF not found')
            failed += 1
            continue
        
        print(f'\n[OCR] {subj}/{filename}...')
        try:
            text = extract_text_ocr(pdf_path, reader)
            title = f'AP {zh_name} {year}年{paper_type}'
            exam_id = f'{subj}-{filename}'
            
            data = build_json(exam_id, title, zh_name, year, text)
            
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            size_kb = os.path.getsize(json_path) / 1024
            print(f'  -> Saved {size_kb:.0f}KB')
            success += 1
        except Exception as e:
            print(f'  -> ERROR: {e}')
            failed += 1
    
    print(f'\n=== DONE: {success} success, {failed} failed ===')

if __name__ == '__main__':
    main()
