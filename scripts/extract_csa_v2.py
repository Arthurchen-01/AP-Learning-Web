#!/usr/bin/env python3
"""Extract AP CSA exam PDFs to structured JSON - Final version."""
import fitz
import re
import json
import sys
import os

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

PDF_DIR = r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\pdfs\csa'
OUT_DIR = r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json\csa'
SKIP_PDFS = {'2021NA.pdf', '2025NA.pdf', '2014Intl.pdf'}  # 2014Intl = duplicate of 2008PE

TYPE_MAP = {
    'Intl': '国际卷',
    'NA': '北美卷',
    'NASet1': '北美卷Set1',
    'SQ1': '题集1',
    'PE': '练习卷',
}

def parse_filename(name):
    base = name.replace('.pdf', '')
    m = re.match(r'^(\d{4})(.+)$', base)
    if m:
        return m.group(1), m.group(2)
    return base, ''

def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ''
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def is_text_based(pdf_path):
    doc = fitz.open(pdf_path)
    total = 0
    for i in range(min(3, len(doc))):
        total += len(doc[i].get_text())
    doc.close()
    return total > 300

def clean_page_markers(text):
    """Remove page numbers, headers, footers, copyright lines."""
    # Remove page numbers on their own line (standalone digits)
    text = re.sub(r'\n\s*\d{1,3}\s*\n', '\n', text)
    # Remove "GO ON TO THE NEXT PAGE." markers
    text = re.sub(r'GO ON TO THE NEXT PAGE\.\s*', '', text)
    # Remove copyright lines
    text = re.sub(r'©\s*\d{4}\s*(?:The\s+)?College Board\.?\s*(?:Visit.*?collegeboard\.org\.?\s*)?', '', text)
    # Remove page headers like "Sample Questions for Computer Science A"
    text = re.sub(r'\n\s*(?:Sample Questions|AP\s*(?:®\s*)?Computer Science A)\s*(?:\d{4}\s*)?(?:Free-Response Questions)?\s*\n', '\n', text)
    return text

def detect_sections(text):
    """Detect if MCQ and/or FRQ sections exist. Return (has_mcq, has_frq)."""
    has_frq = bool(re.search(r'Free[- ]?Response\s+Questions', text, re.IGNORECASE))
    has_frq = has_frq or bool(re.search(r'SECTION\s+II', text))
    
    # MCQ: look for "SECTION I" that is NOT followed by "I" (i.e., not "SECTION II")
    # Also look for "Multiple-Choice" as a section title
    has_mcq = bool(re.search(r'SECTION\s+I\s*[:\n]', text))
    has_mcq = has_mcq or bool(re.search(r'SECTION\s+I\b(?!I)\s*(?:Time|—|\n)', text))
    has_mcq = has_mcq or bool(re.search(r'Multiple[- ]Choice\s+(?:Questions|Section)', text, re.IGNORECASE))
    
    # Special case: if only FRQ is in title, it's FRQ only
    title_area = text[:1000]
    if re.search(r'Free[- ]?Response\s+Questions', title_area) and not re.search(r'Multiple[- ]Choice', title_area):
        # Check if there's actually an MCQ section deeper in the text
        if not re.search(r'SECTION\s+I\s*[:\n]', text[1000:]):
            has_mcq = False
    
    return has_mcq, has_frq

def extract_mcq_questions(text):
    """Extract MCQ questions. Returns list of question dicts."""
    questions = []
    
    # Find MCQ section boundaries
    # Look for "SECTION I" start and "SECTION II" end
    s1_match = re.search(r'SECTION\s+I\s*[:\n]', text)
    s2_match = re.search(r'SECTION\s+II', text)
    
    if s1_match:
        mcq_start = s1_match.start()
    else:
        mcq_start = 0
    
    if s2_match:
        mcq_end = s2_match.start()
    else:
        mcq_end = len(text)
    
    # If section boundaries not clear, try finding first question
    if not s1_match:
        # Look for "1. " followed by typical question text
        q1_match = re.search(r'\n1\.\s+(?=Consider|The |Which|What |In |A |An |At |Assume)', text)
        if q1_match:
            mcq_start = max(0, q1_match.start() - 100)
    
    mcq_text = text[mcq_start:mcq_end]
    
    # Detect option format: uppercase (A)-(E) or lowercase (a)-(e)
    uppercase_opts = len(re.findall(r'\([A-E]\)', mcq_text[:5000]))
    lowercase_opts = len(re.findall(r'\([a-e]\)', mcq_text[:5000]))
    use_uppercase = uppercase_opts > lowercase_opts
    
    if use_uppercase:
        opt_pattern = r'\(([A-E])\)'
        opt_split = r'\([A-E]\)'
    else:
        opt_pattern = r'\(([a-e])\)'
        opt_split = r'\([a-e]\)'
    
    # Find question starts
    # Pattern: number followed by period and space, at start of line or after newline
    # Also handle tab-separated format: \t1.\t
    question_boundaries = []
    
    # Try standard format first: "1. " at line start
    for m in re.finditer(r'(?:^|\n)\s*(\d{1,2})\.\s+[A-Z]', mcq_text):
        question_boundaries.append((m.start(), int(m.group(1)), m.end()))
    
    if not question_boundaries:
        # Try tab format: "\t1.\t"
        for m in re.finditer(r'(?:^|\n)\t(\d{1,2})\.\t', mcq_text):
            question_boundaries.append((m.start(), int(m.group(1)), m.end()))
    
    if not question_boundaries:
        # Try "1.\n" format
        for m in re.finditer(r'(?:^|\n)(\d{1,2})\.\s*\n', mcq_text):
            question_boundaries.append((m.start(), int(m.group(1)), m.end()))
    
    if not question_boundaries:
        return questions
    
    # Sort and deduplicate by question number
    seen = set()
    unique_boundaries = []
    for start, qnum, end in question_boundaries:
        if qnum not in seen and 1 <= qnum <= 40:
            seen.add(qnum)
            unique_boundaries.append((start, qnum, end))
    question_boundaries = sorted(unique_boundaries, key=lambda x: x[0])
    
    for idx, (start, qnum, content_start) in enumerate(question_boundaries):
        if idx + 1 < len(question_boundaries):
            end = question_boundaries[idx + 1][0]
        else:
            end = len(mcq_text)
        
        q_text = mcq_text[content_start:end].strip()
        
        # Clean page markers
        q_text = clean_page_markers(q_text)
        
        # Find options
        option_matches = list(re.finditer(opt_pattern, q_text))
        
        if option_matches:
            prompt_end = option_matches[0].start()
            prompt = q_text[:prompt_end].strip()
            
            options = []
            for k, om in enumerate(option_matches):
                label = om.group(1).lower()
                opt_start = om.end()
                if k + 1 < len(option_matches):
                    opt_end = option_matches[k + 1].start()
                else:
                    opt_end = len(q_text)
                opt_text = q_text[opt_start:opt_end].strip()
                options.append({'label': label, 'text': opt_text})
        else:
            prompt = q_text
            options = []
        
        # Validate: prompt should not be empty and should have reasonable length
        if len(prompt) < 5:
            continue
        
        questions.append({
            'id': f'q{qnum}',
            'type': 'multiple-choice',
            'number': qnum,
            'prompt': prompt,
            'options': options,
            'answer': None,
            'explanation': 'Answer key not available yet for this imported exam.'
        })
    
    return questions

def extract_frq_questions(text):
    """Extract FRQ questions. Returns list of question dicts."""
    questions = []
    
    # Find FRQ section
    s2_match = re.search(r'SECTION\s+II', text)
    if s2_match:
        frq_text = text[s2_match.start():]
    else:
        frq_text = text
    
    # Clean page markers
    frq_text = clean_page_markers(frq_text)
    
    # Find question boundaries
    # FRQ questions: "1. This question involves..." or "1.This question..."
    # Look for pattern: number followed by period and description
    question_starts = []
    
    # Primary pattern: "1. " followed by typical FRQ starters
    for m in re.finditer(r'(?:^|\n)\s*(\d)\.\s*(?=This question|The class|A |In this|Consider|The following|A high|At a|The method)', frq_text):
        qnum = int(m.group(1))
        if 1 <= qnum <= 4:
            question_starts.append((m.start(), qnum))
    
    if not question_starts:
        # Fallback: any "N. " at start of line where N is 1-4
        for m in re.finditer(r'(?:^|\n)\s*(\d)\.\s+[A-Z]', frq_text):
            qnum = int(m.group(1))
            if 1 <= qnum <= 4 and (m.start(), qnum) not in question_starts:
                question_starts.append((m.start(), qnum))
    
    if not question_starts:
        return questions
    
    # Sort by position
    question_starts.sort(key=lambda x: x[0])
    
    # Deduplicate by question number (take first occurrence)
    seen = set()
    unique_starts = []
    for pos, qnum in question_starts:
        if qnum not in seen:
            seen.add(qnum)
            unique_starts.append((pos, qnum))
    question_starts = unique_starts
    
    for idx, (start, qnum) in enumerate(question_starts):
        if idx + 1 < len(question_starts):
            end = question_starts[idx + 1][0]
        else:
            end = len(frq_text)
        
        q_text = frq_text[start:end].strip()
        
        # Clean remaining artifacts
        q_text = re.sub(r'The code presented consists of.*?lines\.?\s*', '', q_text)
        q_text = re.sub(r'END OF EXAMINATION\.\s*', '', q_text)
        
        # Find parts: "Part (a)", "(a)", or just "a."
        parts = []
        
        # Try "Part (a)" pattern
        part_matches = list(re.finditer(r'Part\s*\(([a-d])\)', q_text, re.IGNORECASE))
        
        if not part_matches:
            # Try standalone "(a)" at start of line
            part_matches = list(re.finditer(r'(?:^|\n)\s*\(([a-d])\)', q_text))
        
        if part_matches:
            main_prompt = q_text[:part_matches[0].start()].strip()
            
            for k, pm in enumerate(part_matches):
                part_letter = pm.group(1).upper()
                p_start = pm.end()
                if k + 1 < len(part_matches):
                    p_end = part_matches[k + 1].start()
                else:
                    p_end = len(q_text)
                
                part_text = q_text[p_start:p_end].strip()
                parts.append({
                    'part': part_letter,
                    'prompt': part_text
                })
        else:
            # No explicit parts - might be a "write the complete class" question
            main_prompt = q_text
        
        # Clean up whitespace
        main_prompt = re.sub(r'\n{3,}', '\n\n', main_prompt)
        
        questions.append({
            'id': f'q{qnum}',
            'type': 'free-response',
            'prompt': main_prompt,
            'parts': parts,
            'options': [],
            'answer': None,
            'explanation': 'Answer key not available yet for this imported exam.'
        })
    
    return questions

def make_mcq_directions():
    return (
        "Section I has 40 multiple-choice questions and lasts 1 hour and 30 minutes.\n"
        "No points are deducted for incorrect answers. Points are not awarded for unanswered questions.\n"
        "Determine the answer to each of the following questions or incomplete statements.\n"
        "Then decide which is the best of the choices given.\n"
        "Assume that the classes listed in the Java Quick Reference have been imported where appropriate.\n"
        "Assume that declarations of variables and methods appear within the context of an enclosing class.\n"
        "Assume that method calls that are not prefixed by an object or class name and are not shown within a complete class definition appear within the context of an enclosing class.\n"
        "Unless otherwise noted in the question, assume that parameters in method calls are not null and that methods are called only when their preconditions are satisfied."
    )

def make_frq_directions():
    return (
        "Section II has 4 free-response questions and lasts 1 hour and 30 minutes.\n"
        "All program segments must be written in Java. Show all your work. Credit for partial solutions will be given.\n"
        "Assume that the classes listed in the Java Quick Reference have been imported where appropriate.\n"
        "Unless otherwise noted in the question, assume that parameters in method calls are not null and that methods are called only when their preconditions are satisfied.\n"
        "In writing solutions for each question, you may use any of the accessible methods that are listed in classes defined in that question. Writing significant amounts of code that can be replaced by a call to one of these methods will not receive full credit."
    )

def build_json(year, type_key, type_label, mcq_questions, frq_questions):
    sections = []
    
    if mcq_questions:
        sections.append({
            'id': 'section-mcq',
            'title': 'Section I - Multiple Choice',
            'partTitle': 'Multiple-Choice Questions',
            'limitMinutes': 90,
            'directions': make_mcq_directions(),
            'questions': mcq_questions
        })
    
    if frq_questions:
        sections.append({
            'id': 'section-frq',
            'title': 'Section II - Free Response',
            'partTitle': 'Free Response Questions',
            'limitMinutes': 90,
            'directions': make_frq_directions(),
            'questions': frq_questions
        })
    
    exam_id = f'csa-{year}{type_key}'
    
    desc_parts = []
    if mcq_questions:
        desc_parts.append('Multiple-Choice')
    if frq_questions:
        desc_parts.append('Free-Response')
    desc = f"AP CSA {year} {' & '.join(desc_parts)} Questions"
    
    return {
        'examId': exam_id,
        'title': f'AP 计算机科学A {year}年{type_label}',
        'subjectName': '计算机科学A',
        'yearLabel': year,
        'description': desc,
        'answerKeyAvailable': False,
        'scoring': {
            'answerKeyAvailable': False,
            'apBands': [],
            'note': 'Scoring unavailable until answer keys are imported.'
        },
        'sections': sections
    }

def main():
    files = sorted(os.listdir(PDF_DIR))
    
    results = []
    for fname in files:
        if not fname.endswith('.pdf') or fname in SKIP_PDFS:
            if fname.endswith('.pdf'):
                print(f'SKIP (duplicate/skip): {fname}')
            continue
        
        pdf_path = os.path.join(PDF_DIR, fname)
        year, type_key = parse_filename(fname)
        type_label = TYPE_MAP.get(type_key, type_key)
        
        print(f'\n=== {fname} ===')
        
        if not is_text_based(pdf_path):
            print(f'  SKIP: Image-based PDF')
            results.append(f'{fname}: SKIPPED (image-based)')
            continue
        
        text = extract_text(pdf_path)
        print(f'  Text: {len(text)} chars')
        
        has_mcq, has_frq = detect_sections(text)
        print(f'  Detected: MCQ={has_mcq}, FRQ={has_frq}')
        
        mcq_questions = extract_mcq_questions(text) if has_mcq else []
        frq_questions = extract_frq_questions(text) if has_frq else []
        
        print(f'  Extracted: {len(mcq_questions)} MCQ, {len(frq_questions)} FRQ')
        
        if not mcq_questions and not frq_questions:
            print(f'  WARNING: No questions extracted!')
            results.append(f'{fname}: WARNING - no questions')
            # Save raw text for debugging
            raw_path = os.path.join(OUT_DIR, f'{year}{type_key}_raw.txt')
            with open(raw_path, 'w', encoding='utf-8') as f:
                f.write(text)
            continue
        
        exam_json = build_json(year, type_key, type_label, mcq_questions, frq_questions)
        
        out_name = f'{year}{type_key}.json'
        out_path = os.path.join(OUT_DIR, out_name)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(exam_json, f, ensure_ascii=False, indent=2)
        
        # Save raw text
        raw_path = os.path.join(OUT_DIR, f'{year}{type_key}_raw.txt')
        with open(raw_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        q_count = len(mcq_questions) + len(frq_questions)
        print(f'  SAVED: {out_name} ({q_count} questions)')
        results.append(f'{fname}: OK ({len(mcq_questions)} MCQ + {len(frq_questions)} FRQ)')
    
    print('\n=== SUMMARY ===')
    for r in results:
        print(r)

if __name__ == '__main__':
    main()
