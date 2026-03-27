import fitz
import json
import os
import re

BASE_DIR = r"C:\Users\25472\projects\methods\mokaoai.com\database\01_raw"
PDF_DIR = os.path.join(BASE_DIR, "pdfs", "calculus-bc")
JSON_DIR = os.path.join(BASE_DIR, "json", "calculus-bc")
os.makedirs(JSON_DIR, exist_ok=True)

FILES = [
    ("2025NA", "AP 微积分BC 2025年真题北美卷", "2025"),
    ("2023NA", "AP 微积分BC 2023年真题北美卷", "2023"),
    ("2022NA", "AP 微积分BC 2022年真题北美卷", "2022"),
    ("2021NA", "AP 微积分BC 2021年真题北美卷", "2021"),
]

def check_text_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    total = ""
    for i in range(min(3, len(doc))):
        total += doc[i].get_text()
    doc.close()
    return len(total) > 300

def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    doc.close()
    return full_text

def clean_text(text):
    """Remove headers, footers, page numbers, and common noise."""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        ls = line.strip()
        # Skip common header/footer patterns
        if re.match(r'^(Visit College Board|AP Central|© \d{4} College Board|GO ON TO THE NEXT PAGE|STOP\s*$|END OF EXAM|END OF PART [AB])', ls):
            continue
        if re.match(r'^\d+\s*$', ls):  # lone page numbers
            continue
        if re.match(r'^AP[®\u00ae].*Free-Response Questions\s*$', ls):
            continue
        if re.match(r'^AP CALCULUS BC \d{4}.*FREE-RESPONSE', ls):
            continue
        if 'College Board' in ls and ('trademark' in ls.lower() or 'registered' in ls.lower()):
            continue
        if ls.startswith('©') and 'College Board' in ls:
            continue
        # Line of underscores (separator)
        if re.match(r'^_{10,}$', ls):
            continue
        cleaned.append(line)  # Keep original (with leading whitespace) for spacing
    return '\n'.join(cleaned)

def extract_questions(text):
    """Extract all 6 FRQ questions from cleaned text."""
    questions = []
    
    # Find question starts: "1. " at start of line or after newline
    # Pattern: digit(s) followed by period and whitespace
    q_markers = list(re.finditer(r'(?:^|\n)(\d+)\.\s+', text))
    
    # Filter to actual question numbers (1-6)
    q_starts = []
    for m in q_markers:
        qnum = int(m.group(1))
        if 1 <= qnum <= 6:
            # Check this isn't a table value or random number
            # Look at what follows - should start with capital letter (question text)
            after = text[m.end():m.end()+50].strip()
            if after and after[0].isupper():
                q_starts.append((qnum, m.start(), m.end()))
    
    # Remove duplicates by qnum (keep first occurrence for each)
    seen = {}
    unique_starts = []
    for qnum, start, end in q_starts:
        if qnum not in seen:
            seen[qnum] = True
            unique_starts.append((qnum, start, end))
    
    unique_starts.sort(key=lambda x: x[1])
    
    for i, (qnum, start, content_start) in enumerate(unique_starts):
        # End = start of next question, or END OF PART, or end of text
        if i + 1 < len(unique_starts):
            end = unique_starts[i+1][1]
        else:
            end_match = re.search(r'\n(?:END OF PART|STOP)', text[start:])
            end = start + end_match.start() if end_match else len(text)
        
        # Extract body - skip the "1. " prefix
        body = text[content_start:end].strip()
        
        # Clean up any trailing noise
        body = re.split(r'\n(?:Write your responses|AP[®\u00ae]\s*Calculus|Visit College Board)', body)[0].strip()
        
        if len(body) < 30:
            continue
        
        questions.append({
            "id": f"q{qnum}",
            "type": "free-response",
            "prompt": body,
            "options": [],
            "answer": None,
            "explanation": "Answer key not available yet for this imported exam."
        })
    
    return questions

def build_json(exam_id, title, year, questions):
    return {
        "examId": f"calculus-bc-{exam_id}",
        "title": title,
        "subjectName": "微积分BC",
        "yearLabel": year,
        "description": "Practice mode only.",
        "answerKeyAvailable": False,
        "scoring": {
            "answerKeyAvailable": False,
            "apBands": [],
            "note": "Scoring unavailable until answer keys are imported."
        },
        "sections": [
            {
                "id": "section-frq",
                "title": "Section II - Free Response",
                "partTitle": "Part FRQ",
                "limitMinutes": 90,
                "directions": "CALCULUS BC SECTION II, Part A — Time: 30 minutes, 2 Questions. A GRAPHING CALCULATOR IS REQUIRED FOR THESE QUESTIONS. SECTION II, Part B — Time: 1 hour, 4 Questions. NO CALCULATOR IS ALLOWED FOR THESE QUESTIONS. Write your responses to each question only on the designated pages in the separate Free Response booklet. Write your solution to each part in the space provided for that part.",
                "questions": questions
            }
        ]
    }

for exam_id, title, year in FILES:
    pdf_path = os.path.join(PDF_DIR, f"{exam_id}.pdf")
    json_path = os.path.join(JSON_DIR, f"{exam_id}.json")
    
    if not os.path.exists(pdf_path):
        print(f"[SKIP] {exam_id}.pdf not found")
        continue
    
    if not check_text_pdf(pdf_path):
        print(f"[SKIP] {exam_id}.pdf is image-based")
        continue
    
    print(f"[OK] {exam_id}.pdf extracting...")
    raw_text = extract_text(pdf_path)
    text = clean_text(raw_text)
    
    questions = extract_questions(text)
    
    if len(questions) < 6:
        print(f"  [WARN] Only {len(questions)} questions from cleaned text, trying raw...")
        questions = extract_questions(raw_text)
    
    if not questions:
        print(f"  [ERROR] No questions parsed for {exam_id}")
        continue
    
    exam_json = build_json(exam_id, title, year, questions)
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(exam_json, f, ensure_ascii=False, indent=2)
    
    print(f"  Saved {json_path} with {len(questions)} questions")
    for q in questions:
        subs_upper = re.findall(r'\n([A-D])\.', q['prompt'])
        subs_lower = re.findall(r'\n\(([a-d])\)', q['prompt'])
        all_subs = subs_upper + subs_lower
        print(f"    {q['id']}: {len(q['prompt'])} chars, sub-parts found: {len(all_subs)} {all_subs}")

print("\nDone!")
