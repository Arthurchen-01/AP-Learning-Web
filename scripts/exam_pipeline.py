#!/usr/bin/env python3
"""
AP真题 PDF → JSON 转换 + 三审查员系统
Architecture:
  1. PDF Text Extractor (PyMuPDF)
  2. AI Parser (将文本转为JSON格式)
  3. Three Reviewers (独立审核，投票决定)
  4. Orchestrator (协调以上所有)
"""

import fitz  # PyMuPDF
import json
import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
BASE_DIR = Path(r"C:\Users\25472\projects\methods\mokaoai.com")
PDF_DIR = BASE_DIR / "database" / "01_raw" / "pdfs"
OUTPUT_DIR = BASE_DIR / "database" / "02_staging" / "questions"
REVIEW_DIR = BASE_DIR / "database" / "02_staging" / "reviews"
CURATED_DIR = BASE_DIR / "database" / "03_curated" / "ap" / "subjects"

# Subject mapping
SUBJECT_MAP = {
    "csa": {"zh": "计算机科学A", "en": "CSA", "folder": "csa"},
    "statistics": {"zh": "统计学", "en": "Statistics", "folder": "statistics"},
    "psychology": {"zh": "心理学", "en": "Psychology", "folder": "psychology"},
    "physics-c-mechanics": {"zh": "物理C力学", "en": "Physics C Mechanics", "folder": "physics-c-mechanics"},
    "physics-c-em": {"zh": "物理C电磁", "en": "Physics C E&M", "folder": "physics-c-em"},
    "calculus-bc": {"zh": "微积分BC", "en": "Calculus BC", "folder": "calculus-bc"},
    "macroeconomics": {"zh": "宏观经济", "en": "Macroeconomics", "folder": "macroeconomics"},
    "microeconomics": {"zh": "微观经济", "en": "Microeconomics", "folder": "microeconomics"},
}

# JSON Template for exam output
EXAM_TEMPLATE = {
    "examId": "",
    "title": "",
    "subjectName": "",
    "yearLabel": "",
    "description": "",
    "answerKeyAvailable": False,
    "scoring": {
        "answerKeyAvailable": False,
        "apBands": [],
        "note": "Scoring unavailable until answer keys are imported."
    },
    "sections": []
}

SECTION_TEMPLATE = {
    "id": "",
    "title": "",
    "partTitle": "",
    "limitMinutes": 0,
    "directions": "",
    "questions": []
}

QUESTION_TEMPLATE = {
    "id": "",
    "type": "single",  # single, multiple, free-response
    "prompt": "",
    "options": [],
    "answer": None,
    "explanation": "Answer key not available yet for this imported exam."
}

# ============================================================
# PDF TEXT EXTRACTOR
# ============================================================
def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF. Returns (text, is_image_based, page_count)"""
    doc = fitz.open(str(pdf_path))
    pages_text = []
    total_chars = 0
    
    for page in doc:
        text = page.get_text()
        pages_text.append(text)
        total_chars += len(text)
    
    page_count = len(doc)
    doc.close()
    
    is_image_based = total_chars < 100 * page_count  # Less than 100 chars per page = likely image
    
    return "\n\n--- PAGE BREAK ---\n\n".join(pages_text), is_image_based, page_count

# ============================================================
# PROMPT BUILDER
# ============================================================
SYSTEM_PROMPT = """You are an AP exam data parser. Your job is to convert raw PDF text from AP exam papers into structured JSON.

Output ONLY valid JSON matching this exact schema. No explanations, no markdown, just JSON.

SCHEMA:
{
  "examId": "<generate-from-title-hash>",
  "title": "<Chinese title like 'AP 微观经济 2017年国际卷'>",
  "subjectName": "<Chinese subject name>",
  "yearLabel": "<year string>",
  "description": "Practice mode only.",
  "answerKeyAvailable": <true if answers found, else false>,
  "scoring": {
    "answerKeyAvailable": <bool>,
    "apBands": [],
    "note": ""
  },
  "sections": [
    {
      "id": "section-<number>",
      "title": "Section <I/II>, Part <A/B>",
      "partTitle": "Part <A/B> - Multiple Choice/Free Response",
      "limitMinutes": <time in minutes>,
      "directions": "<directions text from exam>",
      "questions": [
        {
          "id": "<number>",
          "type": "single|multiple|free-response",
          "prompt": "<question text>",
          "options": [{"key": "A", "text": "..."}, ...],
          "answer": "<correct key if available, else null>",
          "explanation": "<if available, else default message>"
        }
      ]
    }
  ]
}

RULES:
1. Parse ALL questions from the text
2. For MCQ: extract prompt, all options (A-E), and answer if present
3. For FRQ: type="free-response", no options array needed
4. If answer key is present in the PDF, extract it
5. Generate a unique examId by hashing the title
6. Keep all original formatting in question text (code, formulas)
7. If text is garbled or unclear, do your best but note it in description
"""

def build_parser_prompt(pdf_text, subject_info, filename):
    """Build the prompt for the AI parser"""
    year = ''.join(c for c in filename if c.isdigit())[:4]
    year = year if year else "Unknown"
    
    return f"""Parse this AP exam PDF into JSON format.

Subject: {subject_info['en']} ({subject_info['zh']})
Filename: {filename}
Year: {year}

PDF TEXT:
{pdf_text[:50000]}  

Convert to the JSON schema defined in your system prompt. Output ONLY the JSON object."""

# ============================================================
# REVIEW PROMPT
# ============================================================
REVIEWER_PROMPT_TEMPLATE = """You are Reviewer #{reviewer_id} in a 3-person AP exam quality review team.

Your job: Review this parsed AP exam JSON and determine if it's accurate and complete.

CHECK:
1. Are all questions present and properly separated?
2. Are MCQ options (A-E) correctly extracted?
3. Is the section structure correct (MCQ vs FRQ)?
4. Are time limits reasonable?
5. Is the answer key extracted if present?
6. Any formatting issues or missing content?

ORIGINAL PDF TEXT (first 5000 chars):
{pdf_text}

PARSED JSON:
{parsed_json}

Respond with ONLY this JSON:
{{
  "reviewer": {reviewer_id},
  "verdict": "approve" | "revise" | "reject",
  "score": <1-10>,
  "issues": ["list of issues found"],
  "suggestions": ["list of suggestions"]
}}"""

# ============================================================
# ORCHESTRATOR
# ============================================================
class ExamProcessor:
    def __init__(self):
        self.results = []
        self.stats = {"total": 0, "success": 0, "failed": 0, "needs_review": 0}
    
    def process_exam(self, pdf_path, subject_key):
        """Process a single exam PDF through the full pipeline"""
        subject_info = SUBJECT_MAP[subject_key]
        filename = Path(pdf_path).stem
        
        print(f"\n{'='*60}")
        print(f"Processing: {subject_info['zh']} / {filename}")
        print(f"{'='*60}")
        
        # Step 1: Extract text
        print("[1/4] Extracting text from PDF...")
        text, is_image, pages = extract_text_from_pdf(pdf_path)
        
        if is_image:
            print(f"  [WARN] Image-based PDF ({pages} pages) - needs OCR")
            return {"status": "needs_ocr", "file": filename, "pages": pages}
        
        print(f"  [OK] Extracted {len(text)} chars from {pages} pages")
        
        # Step 2: Save extracted text
        text_file = REVIEW_DIR / subject_key / f"{filename}_text.txt"
        text_file.parent.mkdir(parents=True, exist_ok=True)
        text_file.write_text(text, encoding='utf-8')
        
        # Step 3: Build AI prompts
        print("[2/4] Building parser prompt...")
        parser_prompt = build_parser_prompt(text, subject_info, filename)
        
        # Save prompts for external AI processing
        prompt_file = REVIEW_DIR / subject_key / f"{filename}_parser_prompt.txt"
        prompt_file.write_text(parser_prompt, encoding='utf-8')
        
        print(f"  [OK] Prompt saved to {prompt_file}")
        print(f"[3/4] Ready for AI parsing")
        print(f"[4/4] Ready for 3-reviewer validation")
        
        return {
            "status": "ready_for_ai",
            "file": filename,
            "subject": subject_key,
            "text_chars": len(text),
            "pages": pages,
            "prompt_file": str(prompt_file),
            "text_file": str(text_file)
        }
    
    def generate_review_prompts(self, parsed_json_path, text_file_path, subject_key, filename):
        """Generate prompts for the 3 reviewers"""
        parsed_json = Path(parsed_json_path).read_text(encoding='utf-8')
        pdf_text = Path(text_file_path).read_text(encoding='utf-8')[:5000]
        
        review_prompts = []
        for i in range(1, 4):
            prompt = REVIEWER_PROMPT_TEMPLATE.format(
                reviewer_id=i,
                pdf_text=pdf_text,
                parsed_json=parsed_json
            )
            prompt_file = REVIEW_DIR / subject_key / f"{filename}_reviewer{i}_prompt.txt"
            prompt_file.write_text(prompt, encoding='utf-8')
            review_prompts.append(str(prompt_file))
        
        return review_prompts


# ============================================================
# BATCH PROCESSOR
# ============================================================
def batch_extract_all():
    """Extract text from all PDFs and prepare AI prompts"""
    processor = ExamProcessor()
    manifest = []
    
    for subject_key in SUBJECT_MAP:
        pdf_folder = PDF_DIR / subject_key
        if not pdf_folder.exists():
            continue
        
        for pdf_file in sorted(pdf_folder.glob("*.pdf")):
            result = processor.process_exam(pdf_file, subject_key)
            manifest.append(result)
            processor.stats["total"] += 1
            
            if result["status"] == "ready_for_ai":
                processor.stats["success"] += 1
            elif result["status"] == "needs_ocr":
                processor.stats["needs_review"] += 1
            else:
                processor.stats["failed"] += 1
    
    # Save manifest
    manifest_file = REVIEW_DIR / "processing_manifest.json"
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump({
            "generatedAt": datetime.now().isoformat(),
            "stats": processor.stats,
            "exams": manifest
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"BATCH COMPLETE")
    print(f"Total: {processor.stats['total']}")
    print(f"Ready for AI: {processor.stats['success']}")
    print(f"Needs OCR: {processor.stats['needs_review']}")
    print(f"Failed: {processor.stats['failed']}")
    print(f"Manifest: {manifest_file}")
    
    return manifest

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "batch":
        batch_extract_all()
    else:
        # Demo: process one exam
        demo_pdf = PDF_DIR / "csa" / "2025NA.pdf"
        if demo_pdf.exists():
            processor = ExamProcessor()
            result = processor.process_exam(demo_pdf, "csa")
            print(f"\nDemo result: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print("Demo PDF not found. Run with 'batch' to process all.")
