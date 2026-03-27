#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Batch convert text-based AP exam PDFs to JSON format.
Uses robust parsing for MCQ (via (A) markers) and FRQ sections."""

import fitz  # PyMuPDF
import json
import re
import os
import sys

FILES = [
    ("calculus-bc", "2008Intl", "微积分BC", "2008", "国际卷"),
    ("calculus-bc", "2012Intl", "微积分BC", "2012", "国际卷"),
    ("calculus-bc", "2013Intl", "微积分BC", "2013", "国际卷"),
    ("calculus-bc", "2014Intl", "微积分BC", "2014", "国际卷"),
    ("calculus-bc", "2015Intl", "微积分BC", "2015", "国际卷"),
    ("calculus-bc", "2016Intl", "微积分BC", "2016", "国际卷"),
    ("calculus-bc", "2016SQ", "微积分BC", "2016", "样题"),
    ("calculus-bc", "2017Intl", "微积分BC", "2017", "国际卷"),
    ("calculus-bc", "2018Intl", "微积分BC", "2018", "国际卷"),
    ("calculus-bc", "2018NA", "微积分BC", "2018", "北美卷"),
    ("calculus-bc", "2019Intl", "微积分BC", "2019", "国际卷"),
    ("calculus-bc", "2019NA", "微积分BC", "2019", "北美卷"),
    ("calculus-bc", "2025Intl", "微积分BC", "2025", "国际卷"),
    ("physics-c-em", "2025Intl", "物理C电磁", "2025", "国际卷"),
    ("physics-c-mechanics", "2024NASet1", "物理C力学", "2024", "北美卷Set1"),
    ("physics-c-mechanics", "2024NASet2", "物理C力学", "2024", "北美卷Set2"),
    ("statistics", "2007Intl", "统计学", "2007", "国际卷"),
    ("statistics", "2025Intl", "统计学", "2025", "国际卷"),
]

BASE_PDF = r"C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\pdfs"
BASE_JSON = r"C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json"


def extract_pages(pdf_path):
    """Extract text from all pages."""
    doc = fitz.open(pdf_path)
    pages = [doc[i].get_text() for i in range(doc.page_count)]
    doc.close()
    return pages


def parse_answer_key_page(text):
    """Parse answer key from a page. Format: alternating lines of number and letter."""
    answers = {}
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    i = 0
    while i < len(lines) - 1:
        num_str = lines[i]
        letter = lines[i + 1]
        if num_str.isdigit() and letter in 'ABCDE':
            n = int(num_str)
            if 1 <= n <= 200:
                answers[n] = letter
            i += 2
        else:
            i += 1
    return answers


def find_section_boundaries(pages):
    """Find page ranges for MCQ, FRQ, answer key, scoring guidelines.
    Returns dict with page ranges (0-indexed).
    """
    result = {
        'mcq_start': None, 'mcq_end': None,
        'frq_start': None, 'frq_end': None,
        'answer_key_pages': [],
        'scoring_pages': [],
    }
    
    toc_pages = set()  # Pages that are TOC/directions (skip)
    
    for i, page in enumerate(pages):
        pt = page
        ptl = page.lower()
        
        # TOC / directions (first few pages)
        if i < 4 and ('contents' in ptl or 'directions for administration' in ptl):
            toc_pages.add(i)
            continue
        
        # Answer key page
        if 'answer key' in ptl and 'correct' in ptl:
            result['answer_key_pages'].append(i)
            continue
        
        # Scoring guidelines
        if 'scoring guideline' in ptl or 'scoring rubric' in ptl:
            result['scoring_pages'].append(i)
            continue
        
        # Student answer sheet
        if 'student answer sheet' in ptl:
            continue
        
        # END OF SECTION I
        if re.search(r'END\s+OF\s+SECTION\s+I', pt, re.IGNORECASE):
            result['mcq_end'] = i
            continue
        
        # END OF SECTION II or END OF EXAM
        if re.search(r'END\s+OF\s+(SECTION\s+II|EXAM)', pt, re.IGNORECASE):
            result['frq_end'] = i
            continue
        
        # Section II marker (FRQ start)
        if re.search(r'SECTION\s+II', pt, re.IGNORECASE) and \
           ('free response' in ptl or 'free-response' in ptl or 'part a' in ptl):
            if result['frq_start'] is None:
                result['frq_start'] = i
            continue
        
        # Section I marker (MCQ start) - look for the actual start, not TOC
        if re.search(r'SECTION\s+I\b', pt, re.IGNORECASE) and \
           'multiple choice' in ptl and i > 3:
            if result['mcq_start'] is None:
                result['mcq_start'] = i
    
    # If no explicit end markers found, use heuristics
    if result['mcq_end'] is None:
        # Find last page with (A) options that's not an FRQ page
        for i in range(len(pages) - 1, -1, -1):
            if i in toc_pages:
                continue
            if i in result['answer_key_pages'] or i in result['scoring_pages']:
                continue
            if 'student answer sheet' in pages[i].lower():
                continue
            if re.search(r'\([A-E]\)', pages[i]) and not re.search(r'\([a-h]\)\s+(?:Find|Show|Let|For)', pages[i]):
                result['mcq_end'] = i
                break
    
    if result['frq_end'] is None and result['frq_start'] is not None:
        for i in range(result['frq_start'], len(pages)):
            if i in result['answer_key_pages'] or i in result['scoring_pages']:
                result['frq_end'] = i - 1
                break
            if 'student answer sheet' in pages[i].lower():
                result['frq_end'] = i - 1
                break
    
    return result


def extract_mcq_text(pages, boundaries):
    """Extract MCQ section text from pages."""
    start = boundaries['mcq_start']
    end = boundaries['mcq_end']
    
    if start is None or end is None:
        # Fallback: find pages with (A)/(B)/(C)/(D)/(E) but not (a)/(b)/(c) patterns
        mcq_pages = []
        for i, page in enumerate(pages):
            if i in boundaries['answer_key_pages'] or i in boundaries['scoring_pages']:
                continue
            if 'student answer sheet' in page.lower():
                continue
            if i < 4:  # skip cover/TOC
                continue
            if re.search(r'\([A-E]\)', page):
                mcq_pages.append(page)
        return '\n'.join(mcq_pages)
    
    return '\n'.join(pages[start:end + 1])


def extract_frq_text(pages, boundaries):
    """Extract FRQ section text from pages."""
    start = boundaries['frq_start']
    end = boundaries['frq_end']
    
    if start is None or end is None:
        # Fallback: find pages with (a), (b), (c) parts
        frq_pages = []
        for i, page in enumerate(pages):
            if i in boundaries['answer_key_pages'] or i in boundaries['scoring_pages']:
                continue
            if 'student answer sheet' in page.lower():
                continue
            if re.search(r'\([a-h]\)\s+(?:Find|Show|Let|For|The|A |Consider|What|Determine|Calculate|Write|On|Evaluate|Is|Does|Must)', page):
                frq_pages.append(page)
        return '\n'.join(frq_pages)
    
    return '\n'.join(pages[start:end + 1])


def clean_text(text):
    """Clean extracted text."""
    text = re.sub(r'GO ON TO THE NEXT PAGE\.\s*', '', text)
    text = re.sub(r'-\d+-\s*\n', '', text)
    text = re.sub(r'A A A A A A A A A A[ A]*\n', '', text)
    text = re.sub(r'B B B B B B B B B B[ B]*\n', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def parse_mcq_from_text(text, answer_key):
    """Parse MCQ questions by finding (A) markers.
    Each (A) marker indicates the start of options for a question.
    The question prompt is the text between the previous question's options
    and the current (A) marker.
    """
    text = clean_text(text)
    
    # Find all (A) option start positions
    a_positions = [m.start() for m in re.finditer(r'(?:^|\n)\s*\(A\)\s', text)]
    
    if not a_positions:
        return []
    
    questions = []
    
    for idx, a_pos in enumerate(a_positions):
        # Get the option chunk for this question
        if idx + 1 < len(a_positions):
            option_chunk = text[a_pos:a_positions[idx + 1]]
        else:
            option_chunk = text[a_pos:]
        
        # Parse options first - we need to know where (E) ends
        options_raw = parse_options_raw(option_chunk)
        
        # Get the prompt chunk
        if idx == 0:
            chunk_before = text[:a_pos]
            # Find question number
            m = re.search(r'(?:^|\n)\s*(\d{1,3})\.\s+(?=[A-Z\w])', chunk_before)
            if not m:
                m = re.search(r'(\d{1,3})\.\s+(?=[A-Z\w])', chunk_before)
            if m:
                qn = int(m.group(1))
                prompt = chunk_before[m.end():].strip()
            else:
                qn = 1
                prompt = chunk_before.strip()
        else:
            # From end of previous question's options to current (A)
            prev_a = a_positions[idx - 1]
            prev_chunk = text[prev_a:a_pos]
            prev_options = parse_options_raw(prev_chunk)
            
            # Find (E) end in previous chunk
            e_match = re.search(r'\(E\)\s*', prev_chunk)
            if e_match:
                after_prev_e = prev_chunk[e_match.end():]
            else:
                after_prev_e = prev_chunk
            
            # Find question number in the text after previous (E)
            m = re.search(r'(?:^|\n)\s*(\d{1,3})\.\s+(?=[A-Z\w])', after_prev_e)
            if not m:
                m = re.search(r'(\d{1,3})\.\s+(?=[A-Z\w])', after_prev_e)
            if m:
                qn = int(m.group(1))
                prompt = after_prev_e[m.end():].strip()
            else:
                qn = idx + 1
                prompt = ""
        
        # Clean prompt
        prompt = re.sub(r'\n{2,}', '\n', prompt).strip()
        
        # Clean options - trim any trailing content after the option text
        options = []
        for opt in options_raw:
            opt_text = opt["text"].strip()
            options.append({"key": opt["key"], "text": opt_text})
        
        # Ensure all 5 options
        existing = {o["key"] for o in options}
        for c in "ABCDE":
            if c not in existing:
                options.append({"key": c, "text": ""})
        options.sort(key=lambda o: o["key"])
        
        questions.append({
            "id": str(qn),
            "type": "single",
            "prompt": prompt,
            "options": options,
            "answer": answer_key.get(qn),
            "explanation": "Answer key not available yet for this imported exam."
        })
    
    return questions


def parse_options_raw(text):
    """Parse (A) through (E) options from text, returning raw list."""
    options = []
    pattern = re.compile(r'\(([A-E])\)\s*')
    matches = list(pattern.finditer(text))
    
    for i, m in enumerate(matches):
        key = m.group(1)
        start = m.end()
        # End at next option marker
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            # Last option (E) - end at double newline or end
            after_opt = text[start:]
            dbl_nl = re.search(r'\n\n', after_opt)
            if dbl_nl:
                end = start + dbl_nl.start()
            else:
                end = len(text)
        
        opt_text = text[start:end].strip()
        opt_text = re.sub(r'\n', ' ', opt_text).strip()
        # Remove trailing page numbers like "-3-"
        opt_text = re.sub(r'\s*-\d+-\s*$', '', opt_text).strip()
        options.append({"key": key, "text": opt_text})
    
    return options


def parse_options(text):
    """Parse (A) through (E) options from text - legacy wrapper."""
    return parse_options_raw(text)


def parse_frq_from_text(text):
    """Parse FRQ questions from text."""
    text = clean_text(text)
    
    # FRQ questions start with "N. " where N is 1-6 (or 1-3)
    # Look for standalone question numbers
    q_pattern = re.compile(r'(?:^|\n)\s*(\d{1,2})\.\s+([A-Z])', re.MULTILINE)
    matches = list(q_pattern.finditer(text))
    
    if not matches:
        # Try without requiring uppercase after
        q_pattern = re.compile(r'(?:^|\n)\s*(\d{1,2})\.\s', re.MULTILINE)
        matches = list(q_pattern.finditer(text))
    
    if not matches:
        return []
    
    questions = []
    
    for i, m in enumerate(matches):
        qn = int(m.group(1))
        if qn > 12:
            continue
        
        start = m.end()
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(text)
        
        prompt = text[start:end].strip()
        prompt = re.sub(r'GO ON TO THE NEXT PAGE\.\s*', '', prompt)
        prompt = re.sub(r'-\d+-\s*$', '', prompt, flags=re.MULTILINE)
        prompt = re.sub(r'END\s+OF\s+.*$', '', prompt, flags=re.DOTALL).strip()
        prompt = re.sub(r'\n{3,}', '\n\n', prompt).strip()
        
        if prompt:
            questions.append({
                "id": f"q{qn}",
                "type": "free-response",
                "prompt": prompt,
                "options": [],
                "answer": None,
                "explanation": "Answer key not available yet for this imported exam."
            })
    
    return questions


def get_directions(subject, section):
    mcq_dirs = {
        "calculus-bc": "Each of the questions or incomplete statements below is followed by five suggested answers or completions. Select the one that is best in each case.",
        "physics-c-em": "Each of the questions or incomplete statements below is followed by five suggested answers or completions. Select the one that is best in each case.",
        "physics-c-mechanics": "Each of the questions or incomplete statements below is followed by five suggested answers or completions. Select the one that is best in each case.",
        "statistics": "Each of the questions or incomplete statements below is followed by five suggested answers or completions. Select the one that is best in each case.",
    }
    frq_dirs = {
        "calculus-bc": "CALCULUS BC SECTION II, Part A — Time: 30 minutes, 2 Questions. A GRAPHING CALCULATOR IS REQUIRED FOR THESE QUESTIONS. SECTION II, Part B — Time: 1 hour, 4 Questions. NO CALCULATOR IS ALLOWED FOR THESE QUESTIONS. Write your responses to each question only on the designated pages in the separate Free Response booklet. Write your solution to each part in the space provided for that part.",
        "physics-c-em": "Directions: Answer all three questions. The suggested time is about 15 minutes for answering each of the questions, which are worth 15 points each. The parts within a question may not have equal weight.",
        "physics-c-mechanics": "Directions: Answer all three questions. The suggested time is about 15 minutes for answering each of the questions, which are worth 15 points each. The parts within a question may not have equal weight.",
        "statistics": "Directions: Show all your work. Indicate clearly the methods you use, because you will be scored on the correctness of your methods as well as on the accuracy of your results and explanation.",
    }
    if section == 'mcq':
        return mcq_dirs.get(subject, mcq_dirs["calculus-bc"])
    else:
        return frq_dirs.get(subject, frq_dirs["calculus-bc"])


def get_limits(subject):
    mcq = {"calculus-bc": 105, "physics-c-em": 45, "physics-c-mechanics": 45, "statistics": 90}
    frq = {"calculus-bc": 90, "physics-c-em": 45, "physics-c-mechanics": 45, "statistics": 90}
    return mcq.get(subject, 45), frq.get(subject, 90)


def build_json(subject_folder, filename, subject_name, year_label, title_suffix,
               mcq_questions, frq_questions):
    exam_id = f"{subject_folder}-{filename}"
    title = f"AP {subject_name} {year_label}年真题{title_suffix}"
    mcq_limit, frq_limit = get_limits(subject_folder)
    
    sections = []
    if mcq_questions:
        sections.append({
            "id": "section-mcq",
            "title": "Section I - Multiple Choice",
            "partTitle": "Part MCQ - Multiple Choice",
            "limitMinutes": mcq_limit,
            "directions": get_directions(subject_folder, 'mcq'),
            "questions": mcq_questions
        })
    if frq_questions:
        sections.append({
            "id": "section-frq",
            "title": "Section II - Free Response",
            "partTitle": "Part FRQ",
            "limitMinutes": frq_limit,
            "directions": get_directions(subject_folder, 'frq'),
            "questions": frq_questions
        })
    
    ans_avail = any(q.get("answer") for sec in sections for q in sec["questions"])
    
    return {
        "examId": exam_id,
        "title": title,
        "subjectName": subject_name,
        "yearLabel": year_label,
        "description": "Practice mode only.",
        "answerKeyAvailable": ans_avail,
        "scoring": {
            "answerKeyAvailable": ans_avail,
            "apBands": [],
            "note": "Scoring unavailable until answer keys are imported."
        },
        "sections": sections
    }


def process_pdf(subject_folder, filename, subject_name, year_label, title_suffix):
    pdf_path = os.path.join(BASE_PDF, subject_folder, f"{filename}.pdf")
    if not os.path.exists(pdf_path):
        print(f"  WARNING: PDF not found: {pdf_path}")
        return None
    
    print(f"  Reading: {pdf_path}")
    pages = extract_pages(pdf_path)
    print(f"  Pages: {len(pages)}")
    
    # Find answer key
    answer_key = {}
    for page in pages:
        if 'answer key' in page.lower():
            ak = parse_answer_key_page(page)
            answer_key.update(ak)
    if answer_key:
        print(f"  Answer key: {len(answer_key)} entries")
    
    # Find section boundaries
    boundaries = find_section_boundaries(pages)
    print(f"  MCQ: pages {boundaries['mcq_start']}-{boundaries['mcq_end']}")
    print(f"  FRQ: pages {boundaries['frq_start']}-{boundaries['frq_end']}")
    
    # Extract and parse MCQ
    mcq_text = extract_mcq_text(pages, boundaries)
    mcq_questions = parse_mcq_from_text(mcq_text, answer_key)
    
    # Deduplicate MCQ
    seen = set()
    unique_mcq = []
    for q in mcq_questions:
        if q["id"] not in seen:
            seen.add(q["id"])
            unique_mcq.append(q)
    mcq_questions = unique_mcq
    
    # Extract and parse FRQ
    frq_text = extract_frq_text(pages, boundaries)
    frq_questions = parse_frq_from_text(frq_text)
    
    # Deduplicate FRQ
    seen = set()
    unique_frq = []
    for q in frq_questions:
        if q["id"] not in seen:
            seen.add(q["id"])
            unique_frq.append(q)
    frq_questions = unique_frq
    
    answered = sum(1 for q in mcq_questions if q.get("answer"))
    print(f"  Result: {len(mcq_questions)} MCQ ({answered} w/ answers) + {len(frq_questions)} FRQ")
    
    return build_json(subject_folder, filename, subject_name, year_label,
                     title_suffix, mcq_questions, frq_questions)


def main():
    print("=" * 60)
    print("AP Exam PDF → JSON Batch Converter")
    print("=" * 60)
    
    ok = fail = 0
    for subj, fn, sname, year, suffix in FILES:
        print(f"\n[{subj}/{fn}]")
        try:
            result = process_pdf(subj, fn, sname, year, suffix)
            if result is None:
                fail += 1
                continue
            
            out = os.path.join(BASE_JSON, subj, f"{fn}.json")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            data = json.dumps(result, ensure_ascii=False, indent=2)
            with open(out, 'w', encoding='utf-8') as f:
                f.write(data)
            print(f"  → {out} ({len(data)} bytes)")
            ok += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            fail += 1
    
    print(f"\n{'='*60}")
    print(f"Done! Success: {ok}, Failed: {fail}")


if __name__ == "__main__":
    main()
