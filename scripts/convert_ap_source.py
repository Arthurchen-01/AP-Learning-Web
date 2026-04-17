#!/usr/bin/env python3
"""
Convert AP source exam files (from Desktop/AP/01 A 真题/) to mock-data format.

AP source format:
  { examId, subject, questions: [{ id, type, question, options/ parts, correctAnswer }] }
  LaTeX $...$ in question and options.text

Target mock-data format:
  { examId, title, sections: [{ questions: [{ id, type, prompt, options: [{ key, content }], answer, explanation }] }] }

Usage:
  python scripts/convert_ap_source.py <input.json> <output.json>
  python scripts/convert_ap_source.py --all
"""

import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

AP_BASE = Path(r"C:\Users\25472\Desktop\AP\01 A 真题")
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "mock-data"

SUBJECT_MAP = {
    "06 微积分": {"slug": "calculus-bc", "display": "微积分BC"},
    "01 力学": {"slug": "physics-c-mechanics", "display": "物理C力学"},
    "02 电磁": {"slug": "physics-c-em", "display": "物理C电磁"},
    "07 CSA": {"slug": "csa", "display": "计算机科学A"},
}


def convert_question(q, index):
    """Convert a single AP source question to mock-data format."""
    q_type = q.get("type", "single")
    prompt = q.get("question", "") or q.get("title", "")
    parts = q.get("parts", [])
    opts = q.get("options", [])

    # Detect MCQ: has options OR has 4 parts with A/B/C/D keys
    is_mcq = bool(opts) or (
        len(parts) == 4 and
        all(p.get("partId", p.get("id", "")) in ("A", "B", "C", "D") for p in parts)
    )

    if is_mcq:
        source_list = opts if opts else parts
        options = []
        for opt in source_list:
            options.append({
                "key": opt.get("key", opt.get("partId", "")),
                "content": opt.get("text", opt.get("content", "")),
            })
        return {
            "id": str(q.get("id", f"q{index}")),
            "type": "single",
            "prompt": prompt,
            "options": options,
            "answer": q.get("correctAnswer", ""),
            "explanation": "Answer key not available yet for this imported exam.",
        }
    else:
        # True FRQ with sub-parts
        options = []
        for part in parts:
            pid = part.get("partId", part.get("id", ""))
            text = part.get("text", part.get("content", ""))
            options.append({"key": pid, "content": text})
        return {
            "id": str(q.get("id", f"q{index}")),
            "type": "frq",
            "prompt": prompt,
            "options": options,
            "answer": "",
            "explanation": "Answer key not available yet for this imported exam.",
        }


def convert_exam(input_path, output_path=None):
    """Convert one AP source JSON to mock-data format."""
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    questions = data.get("questions", [])
    if not questions:
        print(f"  SKIP: no questions in {input_path}")
        return None

    # Determine MCQ vs FRQ split
    mcq = [q for q in questions if q.get("type") != "frq"]
    frq = [q for q in questions if q.get("type") == "frq"]

    sections = []
    if mcq:
        sections.append({
            "id": "section-mcq",
            "title": "Section 1",
            "partTitle": "Multiple Choice",
            "limitMinutes": 60,
            "directions": "",
            "questions": [convert_question(q, i) for i, q in enumerate(mcq)],
        })
    if frq:
        sections.append({
            "id": "section-frq",
            "title": "Section 2",
            "partTitle": "Free Response",
            "limitMinutes": 45,
            "directions": "",
            "questions": [convert_question(q, i + len(mcq)) for i, q in enumerate(frq)],
        })

    exam_id = data.get("examId", "unknown")
    subject = data.get("subject", "unknown")
    year = data.get("year", "unknown")

    mock_data = {
        "examId": exam_id,
        "title": data.get("examName", f"AP {subject} {year}"),
        "subjectName": data.get("subjectName", subject),
        "yearLabel": data.get("year", ""),
        "description": data.get("examName", ""),
        "answerKeyAvailable": bool(data.get("questions", [{}])[0].get("correctAnswer")),
        "scoring": {
            "answerKeyAvailable": False,
            "apBands": [],
            "note": "Scoring unavailable until answer keys are imported.",
        },
        "sections": sections,
    }

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(mock_data, f, ensure_ascii=False, indent=2)
        total_q = sum(len(s["questions"]) for s in sections)
        print(f"  OK: {output_path} ({total_q} questions)")

    return mock_data


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        count = 0
        for subject_dir, info in SUBJECT_MAP.items():
            subject_path = AP_BASE / subject_dir
            if not subject_path.exists():
                print(f"SKIP {subject_dir}: not found")
                continue
            for fname in sorted(os.listdir(subject_path)):
                if not fname.endswith(".json"):
                    continue
                input_path = subject_path / fname
                # Build output filename
                exam_id = fname.replace(".json", "")
                out_name = f"ap-exam-{exam_id}.json"
                output_path = OUTPUT_DIR / out_name
                print(f"Converting {fname}...")
                result = convert_exam(str(input_path), str(output_path))
                if result:
                    count += 1
        print(f"\nDone: {count} exams converted")
    elif len(sys.argv) >= 3:
        convert_exam(sys.argv[1], sys.argv[2])
    else:
        print("Usage:")
        print("  python scripts/convert_ap_source.py <input.json> <output.json>")
        print("  python scripts/convert_ap_source.py --all")


if __name__ == "__main__":
    main()
