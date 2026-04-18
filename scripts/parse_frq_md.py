"""
Parse FRQ .md files from Desktop/AP to extract:
- Question number and stem
- Sub-parts (a)(b)(c)(d) text
- Image URLs (mathpix)

Output: structured JSON for each FRQ question.

Reads from Desktop/AP (read-only), writes to project local dirs.
"""
import json, os, re, sys, shutil
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

AP_BASE = Path(r"C:\Users\25472\Desktop\AP\01 A 真题")
OUT_DIR = Path(__file__).resolve().parent.parent / "mock-data"
IMG_DIR = Path(__file__).resolve().parent.parent / "assets" / "frq-images"

# Subject mapping: (desktop_folder, json_suffix, subject)
SUBJECTS = [
    ("06 微积分", "_CALC", "calculus_bc"),
]

def parse_frq_markdown(md_text):
    """Parse a markdown FRQ file into structured questions."""
    questions = []
    
    # Split by question numbers: "1.", "2.", "3.", etc.
    # Pattern: start of line, number, period, space
    parts = re.split(r'\n+(\d+)\.\s+', md_text)
    
    # parts[0] is header text before first question
    # Then alternating: question_number, question_text, question_number, question_text...
    i = 1
    while i < len(parts) - 1:
        qnum = parts[i]
        qtext = parts[i + 1]
        i += 2
        
        # Skip if not a digit
        if not qnum.isdigit():
            continue
        
        # Extract images
        images = re.findall(r'!\[\]\((https://cdn\.mathpix\.com/[^\)]+)\)', qtext)
        
        # Remove image references from text for cleaner display
        clean_text = re.sub(r'!\[\]\(https://cdn\.mathpix\.com/[^\)]+\)', '', qtext)
        
        # Split into stem and sub-parts
        # The stem is everything before the first (a)
        # Sub-parts start with (a), (b), (c), etc.
        
        stem = ""
        parts_list = []
        
        # Find first (a) marker
        first_part = re.search(r'\n?\(a\)\s', clean_text)
        if first_part:
            stem = clean_text[:first_part.start()].strip()
            remaining = clean_text[first_part.start():]
            
            # Split by part markers: (a), (b), (c), etc.
            part_splits = re.split(r'\n?\(([a-f])\)\s+', remaining)
            # part_splits[0] is empty or whitespace
            # Then alternating: letter, text, letter, text...
            j = 1
            while j < len(part_splits) - 1:
                letter = part_splits[j]
                text = part_splits[j + 1]
                j += 2
                # Clean up: remove "Write your responses..." boilerplate
                text = re.sub(r'Write your responses.*', '', text, flags=re.DOTALL).strip()
                text = re.sub(r'Show the (setup|work|calculations).*', '', text, flags=re.DOTALL).strip()
                parts_list.append({
                    "id": letter,
                    "text": text.strip(),
                })
        else:
            stem = clean_text.strip()
        
        # Remove common boilerplate from stem
        stem = re.sub(r'Write your responses.*', '', stem, flags=re.DOTALL).strip()
        stem = re.sub(r'SECTION II.*?Questions', '', stem, flags=re.DOTALL).strip()
        stem = re.sub(r'Time-\d+ minutes', '', stem).strip()
        stem = re.sub(r'CALCULUS BC', '', stem).strip()
        stem = re.sub(r'\|.*?tabular', '', stem, flags=re.DOTALL).strip()
        stem = re.sub(r'\n{3,}', '\n\n', stem).strip()
        
        # Determine question ID
        qid = f"frq-{qnum}"
        
        questions.append({
            "id": qid,
            "number": int(qnum),
            "stem": stem,
            "parts": parts_list,
            "images": images,
        })
    
    return questions

def process_subject(desktop_folder, json_suffix, subject_slug):
    """Process all .md files for a subject."""
    src_dir = AP_BASE / desktop_folder
    if not src_dir.exists():
        return
    
    for md_file in sorted(src_dir.glob("*.md")):
        # Match with corresponding JSON
        json_file = md_file.with_suffix(".json")
        if not json_file.exists():
            continue
        
        # Read JSON to get exam metadata
        try:
            with open(json_file, encoding="utf-8") as f:
                exam_data = json.load(f)
        except:
            continue
        
        # Count FRQ questions (questions with parts OR if .md has FRQ markers)
        frq_count = sum(1 for q in exam_data.get("questions", []) if q.get("parts"))
        
        # Also check if .md has (a) sub-part markers (indicates FRQ content)
        try:
            with open(md_file, encoding="utf-8") as f:
                md_text = f.read()
        except:
            continue
        
        has_frq_markers = bool(re.search(r'\(a\)\s', md_text))
        
        if frq_count == 0 and not has_frq_markers:
            continue
        
        # Parse
        frq_questions = parse_frq_markdown(md_text)
        
        if not frq_questions:
            continue
        
        exam_name = md_file.stem.replace("_CALC", "").replace("_MECH", "").replace("_EM", "").replace("_CSA", "")
        
        # Output
        out_file = OUT_DIR / f"frq-{exam_name}.json"
        output = {
            "examId": exam_name,
            "subject": subject_slug,
            "source": str(md_file),
            "questions": frq_questions,
        }
        
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"  {exam_name}: {len(frq_questions)} FRQ parsed -> {out_file.name}")

# Main
print("=== Parsing FRQ from .md files ===")
for desktop_folder, json_suffix, subject_slug in SUBJECTS:
    process_subject(desktop_folder, json_suffix, subject_slug)

print(f"\nOutput dir: {OUT_DIR}")
