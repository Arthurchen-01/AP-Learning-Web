#!/usr/bin/env python3
"""Extract AP CSA exam PDFs to structured JSON - v3 (final)."""
import fitz
import re
import json
import sys
import os

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

PDF_DIR = r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\pdfs\csa'
OUT_DIR = r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json\csa'
SKIP_PDFS = {'2021NA.pdf', '2025NA.pdf', '2014Intl.pdf', '2009Intl.pdf', '2024Intl.pdf'}

TYPE_MAP = {
    'Intl': '国际卷', 'NA': '北美卷', 'NASet1': '北美卷Set1',
    'SQ1': '题集1', 'PE': '练习卷',
}

def parse_filename(name):
    base = name.replace('.pdf', '')
    m = re.match(r'^(\d{4})(.+)$', base)
    return (m.group(1), m.group(2)) if m else (base, '')

def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ''.join(p.get_text() for p in doc)
    doc.close()
    return text

def is_text_based(pdf_path):
    doc = fitz.open(pdf_path)
    total = sum(len(doc[i].get_text()) for i in range(min(3, len(doc))))
    doc.close()
    return total > 300

def find_real_mcq_section(text):
    """Find the actual MCQ questions section, not proctoring instructions.
    Returns (start, end) or None."""
    
    # Strategy: find "SECTION I" with "Time" or "Number of questions" nearby
    # These are the actual exam headers, not proctoring instructions
    best_start = None
    for m in re.finditer(r'SECTION\s+I\s*\n\s*Time', text):
        best_start = m.start()
        break
    
    if best_start is None:
        for m in re.finditer(r'SECTION\s+I\s*\n\s*Number of questions', text):
            best_start = m.start()
            break
    
    if best_start is None:
        # Look for "SECTION I: Multiple Choice" followed by exam content (not instructions)
        for m in re.finditer(r'SECTION\s+I:\s*Multiple\s+Choice\s*\n\d{4}', text):
            best_start = m.start()
            break
    
    if best_start is None:
        # Fallback: look for first real MCQ question "1. Consider" or "1. Which"
        q1 = re.search(r'\n1\.\s+(?=Consider|Which|What|The |A |In |At |Assume)', text)
        if q1:
            best_start = max(0, q1.start() - 200)
    
    if best_start is None:
        return None
    
    # Find end: "SECTION II" that's an actual section header
    best_end = len(text)
    for m in re.finditer(r'SECTION\s+II\s*\n\s*(?:Time|—)', text[best_start:]):
        best_end = best_start + m.start()
        break
    
    if best_end == len(text):
        for m in re.finditer(r'SECTION\s+II\s*:\s*Free', text[best_start:]):
            best_end = best_start + m.start()
            break
    
    return (best_start, best_end)

def find_real_frq_section(text):
    """Find the actual FRQ questions section. Returns (start, end) or None."""
    # Find "SECTION II" with "Time" nearby - this is the actual FRQ header
    best_start = None
    for m in re.finditer(r'SECTION\s+II\s*\n\s*Time', text):
        best_start = m.start()
        break
    
    if best_start is None:
        for m in re.finditer(r'SECTION\s+II\s*:\s*Free', text):
            best_start = m.start()
            break
    
    if best_start is None:
        # Fallback: look for FRQ title
        m = re.search(r'Free[- ]Response\s+Questions\s*\n', text)
        if m:
            best_start = m.start()
    
    if best_start is None:
        return None
    
    # Find end: "Suggested Solutions" or end of document
    remaining = text[best_start:]
    end_markers = ['Suggested Solutions', 'Answer Key', 'END OF EXAMINATION']
    best_end = len(text)
    for marker in end_markers:
        idx = remaining.find(marker)
        if idx >= 0:
            best_end = min(best_end, best_start + idx)
    
    return (best_start, best_end)

def has_mcq_section(text):
    """Check if this exam has a real MCQ section (not just proctoring notes)."""
    # Look for actual MCQ exam header
    if re.search(r'SECTION\s+I\s*\n\s*Time.*?Number of questions.*?40', text, re.DOTALL):
        return True
    if re.search(r'SECTION\s+I\s*\n\s*Number of questions.*?40', text, re.DOTALL):
        return True
    if re.search(r'SECTION\s+I:\s*Multiple\s+Choice\s*\n\d{4}', text):
        return True
    return False

def has_frq_section(text):
    """Check if this exam has a FRQ section."""
    return bool(re.search(r'SECTION\s+II', text)) or bool(re.search(r'Free[- ]Response\s+Questions', text))

def clean_text(text):
    """Remove page markers, headers, footers."""
    # Remove standalone page numbers
    text = re.sub(r'\n\s*\d{1,3}\s*\n', '\n', text)
    # Remove "GO ON TO THE NEXT PAGE"
    text = re.sub(r'GO ON TO THE NEXT PAGE\.\s*', '', text)
    # Remove copyright lines
    text = re.sub(r'©\s*\d{4}\s*(?:The\s+)?College Board\.?\s*(?:Visit.*?collegeboard\.org\.?\s*)?', '', text)
    # Remove page headers
    text = re.sub(r'\n\s*(?:Sample Questions|AP\s*(?:®\s*)?Computer Science A)\s*(?:\d{4}\s*)?(?:Free-Response Questions)?\s*\n', '\n', text)
    return text

def extract_mcq_questions(text, start, end):
    """Extract MCQ questions from the text range [start, end]."""
    mcq_text = text[start:end]
    questions = []
    
    # Detect option format
    upper_count = len(re.findall(r'\([A-E]\)', mcq_text[:10000]))
    lower_count = len(re.findall(r'\([a-e]\)', mcq_text[:10000]))
    
    if lower_count > upper_count:
        opt_pattern = r'\(([a-e])\)'
        # Tab format for 2008PE
        q_pattern = r'(?:^|\n)\t(\d{1,2})\.\t'
    else:
        opt_pattern = r'\(([A-E])\)'
        q_pattern = r'(?:^|\n)\s*(\d{1,2})\.\s+'
    
    # Find question starts
    question_boundaries = []
    for m in re.finditer(q_pattern, mcq_text):
        qnum = int(m.group(1))
        if 1 <= qnum <= 40:
            question_boundaries.append((m.start(), qnum, m.end()))
    
    # If tab format found nothing, try standard format
    if not question_boundaries and lower_count > upper_count:
        for m in re.finditer(r'(?:^|\n)\s*(\d{1,2})\.\s+', mcq_text):
            qnum = int(m.group(1))
            if 1 <= qnum <= 40:
                question_boundaries.append((m.start(), qnum, m.end()))
    
    if not question_boundaries:
        return questions
    
    # Deduplicate by qnum, keep first occurrence
    seen = set()
    unique = []
    for item in question_boundaries:
        if item[1] not in seen:
            seen.add(item[1])
            unique.append(item)
    question_boundaries = sorted(unique, key=lambda x: x[0])
    
    for idx, (start_pos, qnum, content_start) in enumerate(question_boundaries):
        end_pos = question_boundaries[idx + 1][0] if idx + 1 < len(question_boundaries) else len(mcq_text)
        q_text = mcq_text[content_start:end_pos].strip()
        q_text = clean_text(q_text)
        
        # Find options
        option_matches = list(re.finditer(opt_pattern, q_text))
        
        if option_matches:
            prompt = q_text[:option_matches[0].start()].strip()
            options = []
            for k, om in enumerate(option_matches):
                label = om.group(1).lower()
                opt_start = om.end()
                opt_end = option_matches[k + 1].start() if k + 1 < len(option_matches) else len(q_text)
                opt_text = q_text[opt_start:opt_end].strip()
                options.append({'label': label, 'text': opt_text})
        else:
            prompt = q_text
            options = []
        
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

def extract_frq_questions(text, start, end):
    """Extract FRQ questions from the text range [start, end]."""
    frq_text = text[start:end]
    frq_text = clean_text(frq_text)
    
    questions = []
    
    # Find question starts: "1. " followed by typical FRQ starters
    question_starts = []
    for m in re.finditer(r'(?:^|\n)\s*(\d)\.\s*(?:This question|The |A |In this|Consider|A high|At a|The method|Many |Users)', frq_text):
        qnum = int(m.group(1))
        if 1 <= qnum <= 4:
            question_starts.append((m.start(), qnum))
    
    if not question_starts:
        # More relaxed: "1. " at start of line with uppercase following
        for m in re.finditer(r'(?:^|\n)\s*(\d)\.\s+[A-Z]', frq_text):
            qnum = int(m.group(1))
            if 1 <= qnum <= 4:
                question_starts.append((m.start(), qnum))
    
    if not question_starts:
        return questions
    
    # Deduplicate
    seen = set()
    unique = []
    for pos, qnum in question_starts:
        if qnum not in seen:
            seen.add(qnum)
            unique.append((pos, qnum))
    question_starts = sorted(unique, key=lambda x: x[0])
    
    for idx, (start_pos, qnum) in enumerate(question_starts):
        end_pos = question_starts[idx + 1][0] if idx + 1 < len(question_starts) else len(frq_text)
        q_text = frq_text[start_pos:end_pos].strip()
        
        # Clean artifacts
        q_text = re.sub(r'The code presented consists of.*?lines\.?\s*', '', q_text)
        q_text = re.sub(r'END OF EXAMINATION\.\s*', '', q_text)
        q_text = re.sub(r'\n{3,}', '\n\n', q_text)
        
        # Find parts
        parts = []
        part_matches = list(re.finditer(r'Part\s*\(([a-d])\)', q_text, re.IGNORECASE))
        if not part_matches:
            part_matches = list(re.finditer(r'(?:^|\n)\s*\(([a-d])\)', q_text))
        
        if part_matches:
            main_prompt = q_text[:part_matches[0].start()].strip()
            for k, pm in enumerate(part_matches):
                part_letter = pm.group(1).upper()
                p_start = pm.end()
                p_end = part_matches[k + 1].start() if k + 1 < len(part_matches) else len(q_text)
                part_text = q_text[p_start:p_end].strip()
                parts.append({'part': part_letter, 'prompt': part_text})
        else:
            main_prompt = q_text
        
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
            'id': 'section-mcq', 'title': 'Section I - Multiple Choice',
            'partTitle': 'Multiple-Choice Questions', 'limitMinutes': 90,
            'directions': make_mcq_directions(), 'questions': mcq_questions
        })
    if frq_questions:
        sections.append({
            'id': 'section-frq', 'title': 'Section II - Free Response',
            'partTitle': 'Free Response Questions', 'limitMinutes': 90,
            'directions': make_frq_directions(), 'questions': frq_questions
        })
    
    desc_parts = []
    if mcq_questions: desc_parts.append('Multiple-Choice')
    if frq_questions: desc_parts.append('Free-Response')
    
    return {
        'examId': f'csa-{year}{type_key}',
        'title': f'AP 计算机科学A {year}年{type_label}',
        'subjectName': '计算机科学A', 'yearLabel': year,
        'description': f"AP CSA {year} {' & '.join(desc_parts)} Questions",
        'answerKeyAvailable': False,
        'scoring': {'answerKeyAvailable': False, 'apBands': [],
                    'note': 'Scoring unavailable until answer keys are imported.'},
        'sections': sections
    }

def main():
    files = sorted(f for f in os.listdir(PDF_DIR) if f.endswith('.pdf'))
    results = []
    
    for fname in files:
        if fname in SKIP_PDFS:
            print(f'SKIP: {fname}')
            continue
        
        pdf_path = os.path.join(PDF_DIR, fname)
        year, type_key = parse_filename(fname)
        type_label = TYPE_MAP.get(type_key, type_key)
        
        print(f'\n=== {fname} ===')
        
        if not is_text_based(pdf_path):
            print('  SKIP: Image-based')
            results.append(f'{fname}: image-based')
            continue
        
        text = extract_text(pdf_path)
        print(f'  Text: {len(text)} chars')
        
        # Detect sections
        mcq_present = has_mcq_section(text)
        frq_present = has_frq_section(text)
        print(f'  Sections: MCQ={mcq_present}, FRQ={frq_present}')
        
        mcq_questions = []
        frq_questions = []
        
        if mcq_present:
            mcq_range = find_real_mcq_section(text)
            if mcq_range:
                print(f'  MCQ range: {mcq_range[0]}-{mcq_range[1]} ({mcq_range[1]-mcq_range[0]} chars)')
                mcq_questions = extract_mcq_questions(text, *mcq_range)
            else:
                print('  MCQ section header found but could not determine range')
        
        if frq_present:
            frq_range = find_real_frq_section(text)
            if frq_range:
                print(f'  FRQ range: {frq_range[0]}-{frq_range[1]} ({frq_range[1]-frq_range[0]} chars)')
                frq_questions = extract_frq_questions(text, *frq_range)
            else:
                # Fallback: use full text
                frq_questions = extract_frq_questions(text, 0, len(text))
        
        print(f'  Extracted: {len(mcq_questions)} MCQ + {len(frq_questions)} FRQ')
        
        if not mcq_questions and not frq_questions:
            results.append(f'{fname}: WARNING no questions')
            # Save raw for debugging
            with open(os.path.join(OUT_DIR, f'{year}{type_key}_raw.txt'), 'w', encoding='utf-8') as f:
                f.write(text)
            continue
        
        exam_json = build_json(year, type_key, type_label, mcq_questions, frq_questions)
        
        out_path = os.path.join(OUT_DIR, f'{year}{type_key}.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(exam_json, f, ensure_ascii=False, indent=2)
        
        with open(os.path.join(OUT_DIR, f'{year}{type_key}_raw.txt'), 'w', encoding='utf-8') as f:
            f.write(text)
        
        total = len(mcq_questions) + len(frq_questions)
        print(f'  SAVED: {fname} -> {total} questions')
        results.append(f'{fname}: {len(mcq_questions)} MCQ + {len(frq_questions)} FRQ')
    
    print('\n========== SUMMARY ==========')
    for r in results:
        print(r)

if __name__ == '__main__':
    main()
