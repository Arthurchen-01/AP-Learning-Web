#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch convert AP exam PDFs to JSON format.
Extracts text with PyMuPDF, parses MCQ/FRQ questions, outputs structured JSON.
"""
import os
import re
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

import fitz  # PyMuPDF

# === CONFIG ===
BASE_PDFS = r"C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\pdfs"
BASE_JSON = r"C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json"

SUBJECTS = {
    "statistics":        {"cn": "统计学",   "mcq_min": 90, "frq_min": 90},
    "psychology":        {"cn": "心理学",   "mcq_min": 90, "frq_min": 70},
    "macroeconomics":    {"cn": "宏观经济", "mcq_min": 70, "frq_min": 60},
    "microeconomics":    {"cn": "微观经济", "mcq_min": 70, "frq_min": 60},
    "physics-c-mechanics": {"cn": "物理C力学", "mcq_min": 45, "frq_min": 45},
    "physics-c-em":      {"cn": "物理C电磁", "mcq_min": 45, "frq_min": 45},
}

TYPE_MAP = {
    "Intl": "国际卷",
    "NA": "北美卷",
    "NASet1": "北美卷Set1",
    "NASet2": "北美卷Set2",
    "SQ": "特殊卷",
    "SQ1": "特殊卷",
    "PE": "预发布卷",
}

# AP subject display names
SUBJECT_DISPLAY = {
    "statistics": "AP Statistics",
    "psychology": "AP Psychology",
    "macroeconomics": "AP Macroeconomics",
    "microeconomics": "AP Microeconomics",
    "physics-c-mechanics": "AP Physics C: Mechanics",
    "physics-c-em": "AP Physics C: E&M",
}


def parse_filename(fname):
    """Parse e.g. '2019NASet1.pdf' -> (year='2019', type='NASet1')"""
    name = fname.replace(".pdf", "")
    # Try longest match first
    for t in ["NASet2", "NASet1", "Intl", "SQ1", "SQ", "NA", "PE"]:
        if name.endswith(t):
            year = name[:-len(t)]
            return year, TYPE_MAP.get(t, t)
    # Fallback
    m = re.match(r'(\d{4})(.*)', name)
    if m:
        return m.group(1), TYPE_MAP.get(m.group(2), m.group(2) or "未知")
    return name, "未知"


def is_text_pdf(pdf_path, threshold=300):
    """Check if first 3 pages have enough text (not image-only)."""
    doc = fitz.open(pdf_path)
    total = 0
    for i in range(min(3, len(doc))):
        total += len(doc[i].get_text())
    doc.close()
    return total >= threshold


def extract_full_text(pdf_path):
    """Extract text from all pages of a PDF."""
    doc = fitz.open(pdf_path)
    pages = []
    for i in range(len(doc)):
        pages.append(doc[i].get_text())
    doc.close()
    return pages


def find_section_boundaries(pages):
    """
    Find where Section I (MCQ) and Section II (FRQ) start/end.
    Returns (frq_start_page, answer_key_pages).
    """
    full_text = "\n".join(pages)

    # Find FRQ section start
    # Strategy: use answer key and scoring guidelines as anchors
    # FRQ content is between the last MCQ answer key/student answer sheet
    # and the first scoring guideline page.
    frq_start = None

    # Collect all boundary markers
    last_mcq_material = -1  # Last page of MCQ materials (answer sheet, answer key)
    first_scoring = -1      # First scoring guideline page
    first_section_ii_content = -1  # First page that looks like actual FRQ content

    for i, page_text in enumerate(pages):
        pt = page_text.lower()
        raw = page_text

        # Student answer sheet or MCQ answer key
        if 'student answer sheet' in pt and ('multiple-choice' in pt or 'multiple choice' in pt):
            last_mcq_material = max(last_mcq_material, i)
            continue
        if ('answer key' in pt or 'correct answer' in pt) and re.search(r'\d+\s+[A-E]\s+\d+', raw):
            last_mcq_material = max(last_mcq_material, i)
            continue

        # Scoring guidelines
        if 'scoring guideline' in pt[:300] or 'scoring criteria' in pt[:300]:
            if first_scoring < 0:
                first_scoring = i
            continue

        # Detect pages that contain actual FRQ question content
        # Look for "Part A" / "Part B" patterns typical of FRQ
        if i > last_mcq_material + 2 and first_scoring < 0:
            part_matches = re.findall(r'\bPart\s+[AB]\b', raw)
            if len(part_matches) >= 2 and len(pt.strip()) > 300:
                if first_section_ii_content < 0:
                    first_section_ii_content = i

    # Determine frq_start
    if first_section_ii_content > 0:
        # Found FRQ content by Part A/B pattern - go back to find the section header page
        frq_start = first_section_ii_content
        # Check if there's a header page right before
        if frq_start > 0 and len(pages[frq_start - 1].strip()) < 500:
            # Check if previous page is a section header or cover
            prev = pages[frq_start - 1].lower()
            if 'section ii' in prev or 'free-response' in prev:
                frq_start -= 1
    elif first_scoring > 0 and last_mcq_material >= 0:
        # Use scoring guidelines as anchor: FRQ is between last MCQ material and scoring
        # Start just after last MCQ material
        frq_start = last_mcq_material + 1
        # Skip blank/short pages
        while frq_start < first_scoring and len(pages[frq_start].strip()) < 100:
            frq_start += 1
    elif first_scoring > 0:
        # Have scoring guidelines but no MCQ material found
        # FRQ is a few pages before scoring
        frq_start = max(0, first_scoring - 5)  # Rough estimate
        # Find actual FRQ start by looking for "Part A/B"
        for i in range(first_scoring - 1, max(0, first_scoring - 10), -1):
            if i >= 0 and re.search(r'\bPart\s+[AB]\b', pages[i]):
                frq_start = i
                break

    # Fallback: search for Part A/B pattern in later half of document
    if frq_start is None:
        for i in range(len(pages) // 2, len(pages)):
            pt = pages[i].lower()
            if 'scoring guideline' in pt or 'answer key' in pt or 'contents' in pt:
                continue
            if re.search(r'part\s+[ab]\b', pt) and len(pt.strip()) > 200:
                frq_start = i
                break

    # Find answer key pages (to exclude)
    answer_key_pages = set()
    for i, page_text in enumerate(pages):
        pt = page_text.lower()
        if ('answer key' in pt or 'correct answer' in pt) and \
           re.search(r'\d+\s+[A-E]\s+\d+', page_text):
            answer_key_pages.add(i)
        # Scoring guidelines are not questions
        if 'scoring guideline' in pt and 'section ii' not in pt[:200]:
            answer_key_pages.add(i)

    # Also find "Student Answer Sheet" pages (not questions)
    for i, page_text in enumerate(pages):
        pt = page_text.lower()
        if 'student answer sheet' in pt and 'no.' in pt and 'answer' in pt:
            answer_key_pages.add(i)

    return frq_start, answer_key_pages


def parse_mcq_questions(pages, start_page, end_page):
    """Parse MCQ questions from extracted page texts."""
    # Combine relevant pages
    text_parts = []
    for i in range(start_page, end_page):
        if i < len(pages):
            text_parts.append(pages[i])

    full_text = "\n".join(text_parts)

    # Clean up common artifacts
    full_text = full_text.replace('\x00', '')
    # Remove "GO ON TO THE NEXT PAGE" markers
    full_text = re.sub(r'GO ON TO THE NEXT PAGE\.?\s*', '', full_text, flags=re.IGNORECASE)

    questions = []

    # Pattern: question number at start of line or after whitespace, followed by text
    # Match "1." or " 1." at beginning of a logical question block
    # We look for patterns like: "\n 1. text... (A) option..."

    # Split by question number pattern
    # Question numbers can be 1-100+ for some subjects
    pattern = r'(?:^|\n)\s*(\d{1,3})\.\s+'

    splits = re.split(pattern, full_text)

    # splits[0] is before first question (directions etc)
    # Then alternating: number, text, number, text...
    i = 1
    while i < len(splits) - 1:
        qnum = splits[i]
        qtext = splits[i + 1]

        # Validate qnum
        try:
            num = int(qnum)
            if num < 1 or num > 150:
                i += 2
                continue
        except ValueError:
            i += 2
            continue

        # Extract options from qtext
        # Options are (A), (B), (C), (D), (E) etc.
        options = []
        # Find where options start
        opt_pattern = r'\(([A-E])\)\s*'
        opt_matches = list(re.finditer(opt_pattern, qtext))

        if opt_matches:
            # Prompt is everything before first option
            prompt = qtext[:opt_matches[0].start()].strip()

            for j, match in enumerate(opt_matches):
                key = match.group(1)
                start = match.end()
                if j + 1 < len(opt_matches):
                    end = opt_matches[j + 1].start()
                else:
                    # Text until next question number or end
                    # Look ahead in splits for next question
                    end = len(qtext)
                opt_text = qtext[start:end].strip()
                # Clean: remove trailing question text
                # If there's a new question starting, cut there
                next_q = re.search(r'\n\s*\d{1,3}\.\s', opt_text)
                if next_q:
                    opt_text = opt_text[:next_q.start()].strip()
                    # Trim qtext processing
                # Clean whitespace
                opt_text = re.sub(r'\s+', ' ', opt_text).strip()
                options.append({"key": key, "text": opt_text})
        else:
            # No options found - might be a different format or the question continues
            prompt = qtext.strip()
            # Trim at next question
            next_q = re.search(r'\n\s*\d{1,3}\.\s', prompt)
            if next_q:
                prompt = prompt[:next_q.start()].strip()
            prompt = re.sub(r'\s+', ' ', prompt).strip()

        # Clean prompt
        prompt = re.sub(r'\s+', ' ', prompt).strip()
        # Remove common trailing artifacts
        prompt = re.sub(r'GO ON TO THE NEXT PAGE\.?\s*$', '', prompt, flags=re.IGNORECASE).strip()

        if prompt and len(prompt) > 5:  # Filter out very short/non-question matches
            q = {
                "id": str(num),
                "type": "single",
                "prompt": prompt,
                "options": options,
                "answer": None,
                "explanation": "Answer key not available yet for this imported exam."
            }
            questions.append(q)

        i += 2

    return questions


def parse_frq_questions(pages, start_page, end_page):
    """Parse FRQ questions from extracted page texts."""
    text_parts = []
    for i in range(start_page, end_page):
        if i < len(pages):
            text_parts.append(pages[i])

    full_text = "\n".join(text_parts)
    full_text = full_text.replace('\x00', '')
    full_text = re.sub(r'GO ON TO THE NEXT PAGE\.?\s*', '', full_text, flags=re.IGNORECASE)

    questions = []

    # FRQ questions typically start with "1." "2." etc at the top level
    # Parts within questions use "A." "B." or "(a)" "(b)"
    # We want top-level questions

    # Split by top-level question numbers (standalone "1." "2." etc)
    pattern = r'(?:^|\n)\s*(\d{1,2})\.\s+'
    splits = re.split(pattern, full_text)

    i = 1
    while i < len(splits) - 1:
        qnum = splits[i]
        qtext = splits[i + 1]

        try:
            num = int(qnum)
            if num < 1 or num > 20:
                i += 2
                continue
        except ValueError:
            i += 2
            continue

        # Trim at next top-level question
        next_q = re.search(r'\n\s*\d{1,2}\.\s', qtext)
        if next_q:
            qtext = qtext[:next_q.start()]

        # Also trim at "STOP" or "END OF EXAM"
        stop_match = re.search(r'\bSTOP\b|END OF EXAM', qtext)
        if stop_match:
            qtext = qtext[:stop_match.start()]

        qtext = re.sub(r'\s+', ' ', qtext).strip()
        qtext = re.sub(r'-\d+-\s*$', '', qtext).strip()  # Remove page numbers like -18-

        if qtext and len(qtext) > 10:
            q = {
                "id": f"q{num}",
                "type": "free-response",
                "prompt": qtext,
                "options": [],
                "answer": None,
                "explanation": "Answer key not available yet for this imported exam."
            }
            questions.append(q)

        i += 2

    return questions


def build_exam_json(subject_key, year, exam_type, mcq_questions, frq_questions, cfg):
    """Build the final JSON structure."""
    exam_id = f"{subject_key}-{year}"
    title = f"{SUBJECT_DISPLAY[subject_key]} {year}年{exam_type}"

    sections = []

    # MCQ section
    mcq_directions = "Each of the questions or incomplete statements below is followed by several suggested answers or completions. Select the one that is best in each case."
    if mcq_questions:
        sections.append({
            "id": "section-mcq",
            "title": "Section I - Multiple Choice",
            "partTitle": "Part MCQ - Multiple Choice",
            "limitMinutes": cfg["mcq_min"],
            "directions": mcq_directions,
            "questions": mcq_questions
        })

    # FRQ section
    frq_directions = "You have the indicated time to answer the following free response questions. It is not enough to answer a question by merely listing facts. You should present a cogent argument based on your critical analysis."
    if frq_questions:
        sections.append({
            "id": "section-frq",
            "title": "Section II - Free Response",
            "partTitle": "Part FRQ - Free Response",
            "limitMinutes": cfg["frq_min"],
            "directions": frq_directions,
            "questions": frq_questions
        })

    return {
        "examId": exam_id,
        "title": title,
        "subjectName": cfg["cn"],
        "yearLabel": year,
        "description": "Practice mode only.",
        "answerKeyAvailable": False,
        "scoring": {
            "answerKeyAvailable": False,
            "apBands": [],
            "note": "Scoring unavailable until answer keys are imported."
        },
        "sections": sections
    }


def process_pdf(pdf_path, subject_key, cfg):
    """Process a single PDF file, return JSON dict or None."""
    fname = os.path.basename(pdf_path)
    year, exam_type = parse_filename(fname)

    print(f"  Processing {fname}...", end=" ", flush=True)

    # Check if text-based
    if not is_text_pdf(pdf_path):
        print("SKIPPED (image-only)")
        return None

    # Extract text
    pages = extract_full_text(pdf_path)

    # Find section boundaries
    frq_start, answer_key_pages = find_section_boundaries(pages)

    # Determine MCQ page range (skip first 2 pages which are usually cover/directions)
    mcq_start = 2  # Skip cover and directions pages
    # Find actual MCQ start by looking for "SECTION I" or first question
    for i, pt in enumerate(pages):
        if 'section i' in pt.lower() and ('multiple choice' in pt.lower() or 'multiple-choice' in pt.lower()):
            mcq_start = i
            break

    if frq_start is None:
        # No FRQ found - everything after directions is MCQ
        # Find where answer keys / scoring guidelines start
        mcq_end = len(pages)
        for ap in sorted(answer_key_pages):
            if ap > mcq_start:
                mcq_end = ap
                break
        frq_end = 0
    else:
        mcq_end = frq_start
        frq_end = len(pages)
        # Trim FRQ at scoring guidelines
        for i in range(frq_start, len(pages)):
            if 'scoring guideline' in pages[i].lower() and i > frq_start + 1:
                frq_end = i
                break

    # Parse questions
    mcq_questions = parse_mcq_questions(pages, mcq_start, mcq_end)
    frq_questions = parse_frq_questions(pages, frq_start, frq_end) if frq_start else []

    if not mcq_questions and not frq_questions:
        print(f"SKIPPED (no questions found)")
        return None

    print(f"OK: {len(mcq_questions)} MCQ, {len(frq_questions)} FRQ")

    return build_exam_json(subject_key, year, exam_type, mcq_questions, frq_questions, cfg)


def main():
    stats = {"total": 0, "processed": 0, "skipped": 0, "errors": 0}
    all_results = []  # (subject, fname, json_data)

    for subject_key, cfg in SUBJECTS.items():
        pdf_dir = os.path.join(BASE_PDFS, subject_key)
        json_dir = os.path.join(BASE_JSON, subject_key)

        if not os.path.isdir(pdf_dir):
            print(f"[{subject_key}] PDF directory not found, skipping")
            continue

        os.makedirs(json_dir, exist_ok=True)

        pdfs = sorted([f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')])
        print(f"\n[{subject_key}] Found {len(pdfs)} PDFs")

        for fname in pdfs:
            stats["total"] += 1
            pdf_path = os.path.join(pdf_dir, fname)

            try:
                result = process_pdf(pdf_path, subject_key, cfg)
                if result:
                    stats["processed"] += 1
                    all_results.append((subject_key, fname, result))
                else:
                    stats["skipped"] += 1
            except Exception as e:
                stats["errors"] += 1
                print(f"  ERROR on {fname}: {e}")

    # Now save all JSON files using write tool approach - we'll write them directly
    # since we're in a Python script context
    print(f"\n{'='*60}")
    print(f"SAVING {len(all_results)} JSON FILES")
    print(f"{'='*60}")

    for subject_key, fname, json_data in all_results:
        json_dir = os.path.join(BASE_JSON, subject_key)
        json_fname = fname.replace('.pdf', '.json')
        json_path = os.path.join(json_dir, json_fname)

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"  Saved: {subject_key}/{json_fname}")

    print(f"\n{'='*60}")
    print(f"STATISTICS")
    print(f"{'='*60}")
    print(f"Total PDFs:  {stats['total']}")
    print(f"Processed:   {stats['processed']}")
    print(f"Skipped:     {stats['skipped']} (image-only or no questions)")
    print(f"Errors:      {stats['errors']}")

    # Breakdown by subject
    print(f"\nBy subject:")
    from collections import Counter
    subj_counts = Counter(s for s, _, _ in all_results)
    for subj in SUBJECTS:
        c = subj_counts.get(subj, 0)
        print(f"  {subj} ({SUBJECTS[subj]['cn']}): {c} exams")


if __name__ == "__main__":
    main()
