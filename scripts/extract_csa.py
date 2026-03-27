#!/usr/bin/env python3
"""Extract AP CSA exam PDFs to structured JSON."""
import fitz
import re
import json
import sys
import os

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

PDF_DIR = r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\pdfs\csa'
OUT_DIR = r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json\csa'
SKIP = {'2021NA.pdf', '2025NA.pdf'}

# Type mapping
TYPE_MAP = {
    'Intl': '国际卷',
    'NA': '北美卷',
    'NASet1': '北美卷Set1',
    'SQ1': '题集1',
    'PE': '练习卷',
}

def parse_filename(name):
    """Parse '2020Intl.pdf' -> (year='2020', type_key='Intl')"""
    base = name.replace('.pdf', '')
    # Try patterns: YYYYType
    m = re.match(r'^(\d{4})(.+)$', base)
    if m:
        return m.group(1), m.group(2)
    return base, ''

def get_type_label(type_key):
    return TYPE_MAP.get(type_key, type_key)

def extract_text(pdf_path):
    """Extract full text from PDF."""
    doc = fitz.open(pdf_path)
    text = ''
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def is_text_based(pdf_path):
    """Check if first 3 pages have > 300 chars."""
    doc = fitz.open(pdf_path)
    total = 0
    for i in range(min(3, len(doc))):
        total += len(doc[i].get_text())
    doc.close()
    return total > 300

def has_mcq(text):
    """Check if text contains MCQ section indicators."""
    indicators = [
        'multiple-choice',
        'Multiple Choice',
        'Multiple-Choice',
        'SECTION I',
        'Multiple-Choice Questions',
        'Sample Multiple-Choice',
    ]
    return any(ind.lower() in text.lower() for ind in indicators)

def has_frq(text):
    """Check if text contains FRQ section indicators."""
    indicators = [
        'free-response',
        'Free Response',
        'Free-Response',
        'SECTION II',
        'Free-Response Questions',
    ]
    return any(ind.lower() in text.lower() for ind in indicators)

def extract_mcq_questions(text):
    """Extract MCQ questions from text. Returns list of question dicts."""
    questions = []
    # MCQ format: question number followed by question text, then options (a)-(e)
    # Pattern: look for numbered questions starting with digits followed by period
    
    # Split by question numbers - pattern like "1." or "\n1.\n" at start
    # The MCQ questions have format:
    # 1.\n[question text]\n(a) ...\n(b) ...\n(c) ...\n(d) ...\n(e) ...
    
    # Find all question starts
    # Look for pattern: number followed by period at start of line or after newline
    parts = re.split(r'\n\s*(\d{1,2})\.\s*\n', text)
    
    # parts[0] is text before first question (directions etc)
    # parts[1] = '1', parts[2] = question1_text, parts[3] = '2', parts[4] = question2_text, etc.
    
    i = 1
    while i < len(parts) - 1:
        q_num = parts[i]
        q_text = parts[i + 1]
        
        # Validate q_num is an integer
        try:
            num = int(q_num)
        except ValueError:
            i += 2
            continue
        
        # Parse options from q_text
        # Options are (a), (b), (c), (d), (e)
        option_pattern = r'\([a-eA-E]\)\s*'
        option_splits = re.split(option_pattern, q_text)
        
        if len(option_splits) >= 2:
            # First part is the question prompt
            prompt = option_splits[0].strip()
            # Remaining parts are options
            options = []
            for j in range(1, len(option_splits)):
                opt_text = option_splits[j].strip()
                # Remove trailing text that belongs to next question or end
                options.append(opt_text)
            
            # Clean options - remove trailing content after last option
            # Find option labels in original text
            option_matches = list(re.finditer(r'\(([a-eA-E])\)', q_text))
            
            if option_matches:
                options = []
                for k, match in enumerate(option_matches):
                    opt_label = match.group(1).lower()
                    start = match.end()
                    if k + 1 < len(option_matches):
                        end = option_matches[k + 1].start()
                    else:
                        end = len(q_text)
                    opt_text = q_text[start:end].strip()
                    # Clean up - remove page markers etc
                    opt_text = re.sub(r'\n\s*\d+\s*\n.*?(?:©|College Board).*?\n', '\n', opt_text)
                    options.append({'label': opt_label, 'text': opt_text})
            
            questions.append({
                'id': f'q{num}',
                'type': 'multiple-choice',
                'number': num,
                'prompt': prompt,
                'options': options,
                'answer': None,
                'explanation': 'Answer key not available yet for this imported exam.'
            })
        
        i += 2
    
    return questions

def extract_frq_questions(text):
    """Extract FRQ questions from text. Returns list of question dicts."""
    questions = []
    
    # FRQ format varies. Common patterns:
    # "1. This question involves..." or "1.This question involves..."
    # Parts are labeled "Part (a)", "Part (b)" etc
    
    # Split text by question numbers
    # Look for patterns like "1.\n" or "1. " at the start of a line
    # But be careful not to split on page numbers
    
    # Try to find question boundaries
    # FRQ questions start with "1.", "2.", "3.", "4." followed by description
    # They're typically separated by page breaks or "GO ON TO THE NEXT PAGE"
    
    # More robust: split on "GO ON TO THE NEXT PAGE" or page markers first,
    # then identify question starts
    
    # Let's try a different approach: find each question's start position
    question_starts = []
    for m in re.finditer(r'(?:^|\n)\s*(\d)\.\s+(?=This question|The class|A |In this|Consider|The following)', text):
        question_starts.append((m.start(), int(m.group(1))))
    
    if not question_starts:
        # Fallback: look for numbered items at line start
        for m in re.finditer(r'(?:^|\n)\s*(\d)\.\s+[A-Z]', text):
            question_starts.append((m.start(), int(m.group(1))))
    
    if not question_starts:
        return questions
    
    # Extract each question's text
    for idx, (start, q_num) in enumerate(question_starts):
        if idx + 1 < len(question_starts):
            end = question_starts[idx + 1][0]
        else:
            end = len(text)
        
        q_text = text[start:end].strip()
        
        # Remove page markers and copyright notices
        q_text = re.sub(r'-\d+-\s*\n©.*?College Board.*?\n', '\n', q_text)
        q_text = re.sub(r'\n\d+\s*\n(?:AP.*?QUESTIONS|Computer Science A.*?Free-Response Questions)\s*\n', '\n', q_text)
        q_text = re.sub(r'GO ON TO THE NEXT PAGE\.\s*', '', q_text)
        q_text = re.sub(r'END OF EXAMINATION\.\s*', '', q_text)
        q_text = re.sub(r'©\s*\d{4}\s*College Board\.?\s*(?:Visit.*?collegeboard\.org\.?\s*)?', '', q_text)
        q_text = re.sub(r'The code presented consists of.*?lines\.?\s*', '', q_text)
        
        # Find parts: "Part (a)", "Part (b)", etc.
        parts = []
        part_pattern = r'Part\s*\(([a-z])\)'
        part_matches = list(re.finditer(part_pattern, q_text, re.IGNORECASE))
        
        if part_matches:
            # First part's prompt is everything before first "Part (X)"
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
            # No explicit parts, full text is the prompt
            main_prompt = q_text
            parts = []
        
        # Clean up main prompt
        main_prompt = re.sub(r'\s+', ' ', main_prompt).strip()
        
        questions.append({
            'id': f'q{q_num}',
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

def build_json(year, type_key, type_label, text, mcq_questions, frq_questions):
    """Build the final JSON structure."""
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
    
    # Build description
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
    
    for fname in files:
        if not fname.endswith('.pdf') or fname in SKIP:
            continue
        
        pdf_path = os.path.join(PDF_DIR, fname)
        year, type_key = parse_filename(fname)
        type_label = get_type_label(type_key)
        
        print(f'\n=== Processing {fname} ===')
        
        # Check if text-based
        if not is_text_based(pdf_path):
            print(f'  SKIP: Image-based PDF (< 300 chars in first 3 pages)')
            continue
        
        # Extract text
        text = extract_text(pdf_path)
        print(f'  Extracted {len(text)} chars')
        
        # Check for MCQ and FRQ
        mcq_present = has_mcq(text)
        frq_present = has_frq(text)
        print(f'  MCQ: {mcq_present}, FRQ: {frq_present}')
        
        mcq_questions = []
        frq_questions = []
        
        if mcq_present:
            mcq_questions = extract_mcq_questions(text)
            print(f'  MCQ questions found: {len(mcq_questions)}')
        
        if frq_present:
            frq_questions = extract_frq_questions(text)
            print(f'  FRQ questions found: {len(frq_questions)}')
        
        if not mcq_questions and not frq_questions:
            print(f'  WARNING: No questions extracted, saving raw text reference')
            # Still save for manual review
        
        # Build JSON
        exam_json = build_json(year, type_key, type_label, text, mcq_questions, frq_questions)
        
        # Save
        out_name = f'{year}{type_key}.json'
        out_path = os.path.join(OUT_DIR, out_name)
        
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(exam_json, f, ensure_ascii=False, indent=2)
        
        print(f'  Saved: {out_name}')
        
        # Also save raw text for reference
        raw_path = os.path.join(OUT_DIR, f'{year}{type_key}_raw.txt')
        with open(raw_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'  Raw text saved: {year}{type_key}_raw.txt')

if __name__ == '__main__':
    main()
