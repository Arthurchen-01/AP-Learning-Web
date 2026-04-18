#!/usr/bin/env python3
"""
Convert AP exam sources into canonical v2 exam data.

Supported source priority:
1. Structured raw JSON in database/01_raw/json
2. Backup JSON in _AP_RAW_DATA_BACKUP/json-exams
3. Legacy Desktop OCR JSON in Desktop/AP/01 A 真题

Canonical output:
  v2/data/<exam-id>/exam_packet.json
  v2/data/<exam-id>/questions.json

Legacy compatibility:
  python scripts/convert_ap_source.py <input.json> <output.json>
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
RAW_JSON_DIR = ROOT / "database" / "01_raw" / "json"
BACKUP_DIR = Path(r"C:\Users\25472\projects\_AP_RAW_DATA_BACKUP\json-exams")
DESKTOP_BASE = Path(r"C:\Users\25472\Desktop\AP\01 A 真题")
V2_DATA_DIR = ROOT / "v2" / "data"

try:
    from fix_ocr_spaces import fix_math_spacing, fix_spaced_letters
except Exception:
    def fix_spaced_letters(text):
        return text

    def fix_math_spacing(text):
        return text


SUBJECT_MAP = {
    "06 微积分": {"slug": "calculus-bc", "display": "微积分BC"},
    "01 力学": {"slug": "physics-c-mechanics", "display": "物理C力学"},
    "02 电磁": {"slug": "physics-c-em", "display": "物理C电磁"},
    "07 CSA": {"slug": "csa", "display": "计算机科学A"},
}

CANONICAL_EXAMS = [
    {
        "exam_id": "calc-bc-2017-intl",
        "exam_title": "AP Calculus BC 2017 国际卷",
        "subject": "calculus_bc",
        "subject_display": "微积分BC",
        "year": 2017,
        "form": "international",
        "raw_file": "微积分BC__AP 微积分BC 2017年国际卷__1902622411338911744.json",
        "desktop_file": ("06 微积分", "2017Intl_CALC.json"),
        "legacy_exam_ids": ["1902622411338911744", "2017Intl"],
        "sections": [
            {
                "section_id": "mcq-1",
                "section_type": "mcq",
                "part_label": "Part A",
                "time_limit_minutes": 60,
                "calculator_allowed": False,
                "question_count": 30,
            },
            {
                "section_id": "mcq-2",
                "section_type": "mcq",
                "part_label": "Part B",
                "time_limit_minutes": 45,
                "calculator_allowed": True,
                "question_count": 15,
            },
        ],
    },
    {
        "exam_id": "calc-bc-2018-intl",
        "exam_title": "AP Calculus BC 2018 国际卷",
        "subject": "calculus_bc",
        "subject_display": "微积分BC",
        "year": 2018,
        "form": "international",
        "raw_file": "微积分BC__AP 微积分BC 2018年国际卷__1902622411800285184.json",
        "desktop_file": ("06 微积分", "2018Intl_CALC.json"),
        "legacy_exam_ids": ["1902622411800285184", "2018Intl"],
        "sections": [
            {
                "section_id": "mcq-1",
                "section_type": "mcq",
                "part_label": "Part A",
                "time_limit_minutes": 60,
                "calculator_allowed": False,
                "question_count": 30,
            },
            {
                "section_id": "mcq-2",
                "section_type": "mcq",
                "part_label": "Part B",
                "time_limit_minutes": 45,
                "calculator_allowed": True,
                "question_count": 15,
            },
        ],
    },
    {
        "exam_id": "statistics-2017-intl",
        "exam_title": "AP Statistics 2017 国际卷",
        "subject": "statistics",
        "subject_display": "统计学",
        "year": 2017,
        "form": "international",
        "raw_file": "统计学__AP 统计 2017年国际卷__1902622413180211200.json",
        "legacy_exam_ids": ["1902622413180211200"],
        "sections": [
            {
                "section_id": "mcq-1",
                "section_type": "mcq",
                "part_label": "Multiple Choice",
                "time_limit_minutes": 90,
                "calculator_allowed": False,
                "question_count": 40,
            }
        ],
    },
    {
        "exam_id": "statistics-2018-intl",
        "exam_title": "AP Statistics 2018 国际卷",
        "subject": "statistics",
        "subject_display": "统计学",
        "year": 2018,
        "form": "international",
        "raw_file": "统计学__AP 统计 2018年国际卷__1902622413633196032.json",
        "backup_file": "ap-statistics-2018.json",
        "legacy_exam_ids": ["1902622413633196032"],
        "sections": [
            {
                "section_id": "mcq-1",
                "section_type": "mcq",
                "part_label": "Multiple Choice",
                "time_limit_minutes": 90,
                "calculator_allowed": False,
                "question_count": 40,
            }
        ],
    },
    {
        "exam_id": "statistics-2019-intl",
        "exam_title": "AP Statistics 2019 国际卷",
        "subject": "statistics",
        "subject_display": "统计学",
        "year": 2019,
        "form": "international",
        "raw_file": "统计学__AP 统计 2019年国际卷__1902622414081986560.json",
        "backup_file": "ap-statistics-2019.json",
        "legacy_exam_ids": ["1902622414081986560"],
        "sections": [
            {
                "section_id": "mcq-1",
                "section_type": "mcq",
                "part_label": "Multiple Choice",
                "time_limit_minutes": 90,
                "calculator_allowed": False,
                "question_count": 40,
            }
        ],
    },
    {
        "exam_id": "statistics-2021-intl",
        "exam_title": "AP Statistics 2021 国际卷",
        "subject": "statistics",
        "subject_display": "统计学",
        "year": 2021,
        "form": "international",
        "raw_file": "统计学__AP 统计 2021年国际卷__1902622414539165696.json",
        "backup_file": "ap-statistics-2021.json",
        "legacy_exam_ids": ["1902622414539165696"],
        "sections": [
            {
                "section_id": "mcq-1",
                "section_type": "mcq",
                "part_label": "Multiple Choice",
                "time_limit_minutes": 90,
                "calculator_allowed": False,
                "question_count": 40,
            }
        ],
    },
    {
        "exam_id": "microeconomics-2017-intl",
        "exam_title": "AP Microeconomics 2017 国际卷",
        "subject": "microeconomics",
        "subject_display": "微观经济",
        "year": 2017,
        "form": "international",
        "raw_file": "微观经济__AP 微观经济 2017年国际卷__1902622410416164864.json",
        "legacy_exam_ids": ["1902622410416164864"],
        "sections": [
            {
                "section_id": "mcq-1",
                "section_type": "mcq",
                "part_label": "Multiple Choice",
                "time_limit_minutes": 70,
                "calculator_allowed": False,
                "question_count": 60,
            }
        ],
    },
    {
        "exam_id": "microeconomics-2018-intl",
        "exam_title": "AP Microeconomics 2018 国际卷",
        "subject": "microeconomics",
        "subject_display": "微观经济",
        "year": 2018,
        "form": "international",
        "raw_file": "微观经济__AP 微观经济 2018年国际卷__1902622410881732608.json",
        "backup_file": "microeconomics-2018.json",
        "legacy_exam_ids": ["1902622410881732608"],
        "sections": [
            {
                "section_id": "mcq-1",
                "section_type": "mcq",
                "part_label": "Multiple Choice",
                "time_limit_minutes": 70,
                "calculator_allowed": False,
                "question_count": 60,
            }
        ],
    },
    {
        "exam_id": "microeconomics-2019-intl",
        "exam_title": "AP Microeconomics 2019 国际卷",
        "subject": "microeconomics",
        "subject_display": "微观经济",
        "year": 2019,
        "form": "international",
        "raw_file": "微观经济__AP 微观经济 2019年国际卷__1902622418683138048.json",
        "backup_file": "ap-microeconomics-2019.json",
        "legacy_exam_ids": ["1902622418683138048"],
        "sections": [
            {
                "section_id": "mcq-1",
                "section_type": "mcq",
                "part_label": "Multiple Choice",
                "time_limit_minutes": 70,
                "calculator_allowed": False,
                "question_count": 60,
            }
        ],
    },
    {
        "exam_id": "microeconomics-2021-intl",
        "exam_title": "AP Microeconomics 2021 国际卷",
        "subject": "microeconomics",
        "subject_display": "微观经济",
        "year": 2021,
        "form": "international",
        "raw_file": "微观经济__AP 微观经济 2021年国际卷__1902622419140317184.json",
        "backup_file": "ap-microeconomics-2021.json",
        "legacy_exam_ids": ["1902622419140317184"],
        "sections": [
            {
                "section_id": "mcq-1",
                "section_type": "mcq",
                "part_label": "Multiple Choice",
                "time_limit_minutes": 70,
                "calculator_allowed": False,
                "question_count": 60,
            }
        ],
    },
]

EXAMS_BY_ID = {exam["exam_id"]: exam for exam in CANONICAL_EXAMS}


def load_json(path: Path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def clean_plain_text(value):
    text = str(value or "").replace("\xa0", " ")
    text = re.sub(r"MathType@MTEF@\S+", "", text)
    text = fix_spaced_letters(text)
    text = fix_math_spacing(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_html_fragment(value):
    text = str(value or "").replace("\xa0", " ")
    text = re.sub(r"<annotation\b[^>]*>.*?</annotation>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"MathType@MTEF@[^<]+", "", text)
    text = re.sub(r">\s+<", "><", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def plain_text_to_html(value):
    text = clean_plain_text(value)
    return html.escape(text) if text else ""


def letter_for_index(index):
    return chr(ord("A") + index)


def build_review_flags(*values):
    return [value for value in values if value]


def convert_legacy_question(question, index):
    q_type = question.get("type", "single")
    prompt = question.get("question", "") or question.get("title", "")
    parts = question.get("parts", [])
    options = question.get("options", [])
    # Detect MCQ: has options OR has 4-5 parts with A/B/C/D(/E) keys
    is_mcq = bool(options) or (
        len(parts) in (4, 5) and
        all(p.get("partId", p.get("id", "")) in ("A", "B", "C", "D", "E") for p in parts)
    )
    if not is_mcq:
        return None

    source_list = options if options else parts
    normalized_options = []
    for option_index, option in enumerate(source_list):
        normalized_options.append(
            {
                "key": option.get("key") or option.get("partId") or letter_for_index(option_index),
                "html": plain_text_to_html(option.get("text") or option.get("content") or ""),
            }
        )

    return {
        "question_id": str(question.get("id", f"q{index}")),
        "question_type": "single_choice",
        "question_html": plain_text_to_html(prompt),
        "options": normalized_options,
        "correct_answer": str(question.get("correctAnswer") or ""),
        "unit": "",
        "source_priority_used": "desktop",
        "source_refs": [],
        "review_flags": build_review_flags("desktop_ocr_fallback"),
    }


def convert_exam(input_path, output_path=None):
    data = load_json(Path(input_path))
    questions = []
    for index, question in enumerate(data.get("questions", []), start=1):
        converted = convert_legacy_question(question, index)
        if converted:
            questions.append(converted)

    mock_data = {
        "examId": data.get("examId", "unknown"),
        "title": data.get("examName", "AP Practice Test"),
        "subjectName": data.get("subjectName", data.get("subject", "unknown")),
        "yearLabel": data.get("year", ""),
        "description": data.get("examName", ""),
        "answerKeyAvailable": False,
        "scoring": {
            "answerKeyAvailable": False,
            "apBands": [],
            "note": "Scoring unavailable until answer keys are imported.",
        },
        "sections": [
            {
                "id": "section-mcq",
                "title": "Section 1",
                "partTitle": "Multiple Choice",
                "limitMinutes": 60,
                "directions": "",
                "questions": [
                    {
                        "id": question["question_id"],
                        "type": "single",
                        "prompt": question["question_html"],
                        "options": [
                            {"key": option["key"], "content": option["html"]}
                            for option in question["options"]
                        ],
                        "answer": question["correct_answer"],
                        "explanation": "Answer key not available yet for this imported exam.",
                    }
                    for question in questions
                ],
            }
        ],
    }

    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8") as handle:
            json.dump(mock_data, handle, ensure_ascii=False, indent=2)

    return mock_data


def parse_backup_source(path: Path):
    data = load_json(path)
    questions = []
    for raw_question in data.get("questions", []):
        if str(raw_question.get("type", "")).lower() == "frq":
            continue
        options = raw_question.get("options", [])
        if not options:
            continue

        review_flags = []
        prompt = str(raw_question.get("question") or raw_question.get("title") or "")
        if "MathType@MTEF@" in prompt:
            review_flags.append("mathtype_plaintext_removed")

        normalized_options = []
        for index, option in enumerate(options):
            option_text = str(option.get("text") or option.get("content") or "")
            if "MathType@MTEF@" in option_text:
                review_flags.append("mathtype_plaintext_removed")
            normalized_options.append(
                {
                    "key": option.get("id") or option.get("key") or letter_for_index(index),
                    "html": plain_text_to_html(option_text),
                }
            )

        questions.append(
            {
                "question_id": str(raw_question.get("id") or len(questions) + 1),
                "question_type": "single_choice",
                "question_html": plain_text_to_html(prompt),
                "options": normalized_options,
                "correct_answer": str(raw_question.get("correctAnswer") or ""),
                "unit": str(raw_question.get("unit") or ""),
                "source_priority_used": "backup",
                "source_refs": [str(path)],
                "review_flags": sorted(set(review_flags)),
            }
        )

    return questions


def parse_raw_source(path: Path):
    payload = load_json(path)
    exam = payload.get("data", {})
    questions = []
    for raw_question in exam.get("questionList", []):
        option_list = raw_question.get("optionList") or []
        if not option_list:
            continue

        prompt_html = str(raw_question.get("choiceQuestionContent") or "")
        review_flags = []
        if "MathType@MTEF@" in prompt_html:
            review_flags.append("mathtype_annotation_removed")

        normalized_options = []
        for option in option_list:
            option_html = str(option.get("optionContent") or "")
            if "MathType@MTEF@" in option_html:
                review_flags.append("mathtype_annotation_removed")
            normalized_options.append(
                {
                    "key": option.get("optionSign") or letter_for_index(len(normalized_options)),
                    "html": clean_html_fragment(option_html),
                }
            )

        questions.append(
            {
                "question_id": str(raw_question.get("questionId") or len(questions) + 1),
                "question_type": "single_choice",
                "question_html": clean_html_fragment(prompt_html) or plain_text_to_html(raw_question.get("questionTitle") or ""),
                "options": normalized_options,
                "correct_answer": str(raw_question.get("correctQuestionAnswerStr") or ""),
                "unit": str(raw_question.get("tableUnit") or ""),
                "source_priority_used": "raw",
                "source_refs": [str(path)],
                "review_flags": sorted(set(review_flags)),
            }
        )

    return questions


def parse_desktop_source(path: Path):
    data = load_json(path)
    questions = []
    for index, raw_question in enumerate(data.get("questions", []), start=1):
        question = convert_legacy_question(raw_question, index)
        if question:
            question["source_refs"] = [str(path)]
            questions.append(question)
    return questions


def fill_missing_from_backup(primary_questions, backup_questions):
    for index, question in enumerate(primary_questions):
        if index >= len(backup_questions):
            break
        backup_question = backup_questions[index]
        if not question.get("question_html") and backup_question.get("question_html"):
            question["question_html"] = backup_question["question_html"]
            question.setdefault("review_flags", []).append("backup_prompt_fill")
            question.setdefault("source_refs", []).extend(backup_question.get("source_refs", []))

        backup_options = backup_question.get("options", [])
        for option_index, option in enumerate(question.get("options", [])):
            if option_index >= len(backup_options):
                break
            if not option.get("html") and backup_options[option_index].get("html"):
                option["html"] = backup_options[option_index]["html"]
                question.setdefault("review_flags", []).append("backup_option_fill")
                question.setdefault("source_refs", []).extend(backup_question.get("source_refs", []))

        question["review_flags"] = sorted(set(question.get("review_flags", [])))
        question["source_refs"] = sorted(set(question.get("source_refs", [])))

    return primary_questions


def assign_sections(questions, section_specs):
    packet_sections = []
    assigned_questions = []
    cursor = 0

    for section in section_specs:
        count = int(section.get("question_count", 0))
        section_questions = questions[cursor:cursor + count]
        for question in section_questions:
            question["section_id"] = section["section_id"]
            question["sequence_in_exam"] = len(assigned_questions) + 1
            assigned_questions.append(question)
        packet_sections.append(
            {
                "section_id": section["section_id"],
                "section_type": section["section_type"],
                "part_label": section["part_label"],
                "time_limit_minutes": section["time_limit_minutes"],
                "calculator_allowed": section["calculator_allowed"],
                "question_count": len(section_questions),
            }
        )
        cursor += count

    if cursor < len(questions):
        overflow = questions[cursor:]
        section_id = "mcq-overflow"
        for question in overflow:
            question["section_id"] = section_id
            question["sequence_in_exam"] = len(assigned_questions) + 1
            question.setdefault("review_flags", []).append("unexpected_question_overflow")
            question["review_flags"] = sorted(set(question["review_flags"]))
            assigned_questions.append(question)
        packet_sections.append(
            {
                "section_id": section_id,
                "section_type": "mcq",
                "part_label": "Overflow Review",
                "time_limit_minutes": 0,
                "calculator_allowed": False,
                "question_count": len(overflow),
            }
        )

    return packet_sections, assigned_questions


def build_source_candidates(exam_spec):
    candidates = []
    raw_file = exam_spec.get("raw_file")
    if raw_file:
        candidates.append(("raw", RAW_JSON_DIR / raw_file))

    backup_file = exam_spec.get("backup_file")
    if backup_file:
        candidates.append(("backup", BACKUP_DIR / backup_file))

    desktop_file = exam_spec.get("desktop_file")
    if desktop_file:
        subject_dir, filename = desktop_file
        candidates.append(("desktop", DESKTOP_BASE / subject_dir / filename))

    return candidates


def load_primary_questions(exam_spec):
    source_refs = []
    backup_questions = []
    primary_kind = None
    primary_questions = None

    for source_kind, source_path in build_source_candidates(exam_spec):
        if not source_path.exists():
            continue
        source_refs.append(f"{source_kind}:{source_path}")
        if source_kind == "backup":
            backup_questions = parse_backup_source(source_path)
            if primary_questions is None:
                primary_kind = "backup"
                primary_questions = backup_questions
            continue
        if source_kind == "raw":
            primary_kind = "raw"
            primary_questions = parse_raw_source(source_path)
            continue
        if source_kind == "desktop" and primary_questions is None:
            primary_kind = "desktop"
            primary_questions = parse_desktop_source(source_path)

    if primary_questions is None:
        raise FileNotFoundError(f"No source files found for {exam_spec['exam_id']}")

    if primary_kind != "backup" and backup_questions:
        primary_questions = fill_missing_from_backup(primary_questions, backup_questions)

    return primary_kind, primary_questions, source_refs


def build_canonical_exam(exam_spec):
    primary_kind, questions, source_refs = load_primary_questions(exam_spec)
    packet_sections, assigned_questions = assign_sections(questions, exam_spec["sections"])

    packet_review_flags = []
    expected_questions = sum(section["question_count"] for section in exam_spec["sections"])
    if len(assigned_questions) != expected_questions:
        packet_review_flags.append("question_count_mismatch")
    if primary_kind != "raw":
        packet_review_flags.append(f"{primary_kind}_primary_source")

    packet = {
        "exam_id": exam_spec["exam_id"],
        "exam_title": exam_spec["exam_title"],
        "subject": exam_spec["subject"],
        "subject_display": exam_spec["subject_display"],
        "year": exam_spec["year"],
        "form": exam_spec.get("form", "international"),
        "total_questions": len(assigned_questions),
        "sections": packet_sections,
        "metadata": {
            "converted_at": date.today().isoformat(),
            "source_priority_used": primary_kind,
            "source_refs": source_refs,
            "legacy_exam_ids": exam_spec.get("legacy_exam_ids", []),
            "review_flags": packet_review_flags,
        },
    }

    canonical_questions = []
    for question in assigned_questions:
        canonical_questions.append(
            {
                "question_id": question["question_id"],
                "exam_id": exam_spec["exam_id"],
                "section_id": question["section_id"],
                "sequence_in_exam": question["sequence_in_exam"],
                "question_type": question["question_type"],
                "question_html": question["question_html"],
                "options": question["options"],
                "correct_answer": question.get("correct_answer", ""),
                "unit": question.get("unit", ""),
                "metadata": {
                    "source_priority_used": question.get("source_priority_used", primary_kind),
                    "source_refs": sorted(set(question.get("source_refs", []))),
                    "review_flags": sorted(set(question.get("review_flags", []))),
                },
            }
        )

    return packet, canonical_questions


def write_canonical_exam(exam_spec, output_root: Path):
    packet, questions = build_canonical_exam(exam_spec)
    target_dir = output_root / exam_spec["exam_id"]
    write_json(target_dir / "exam_packet.json", packet)
    write_json(target_dir / "questions.json", questions)
    print(f"OK {exam_spec['exam_id']}: {len(questions)} questions -> {target_dir}")


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Build canonical AP exam data")
    parser.add_argument("legacy_input", nargs="?", help="Legacy input JSON path")
    parser.add_argument("legacy_output", nargs="?", help="Legacy output JSON path")
    parser.add_argument("--all", action="store_true", help="Build all configured canonical exams")
    parser.add_argument("--exam", action="append", dest="exam_ids", default=[], help="Build one canonical exam by exam_id")
    parser.add_argument("--list", action="store_true", help="List supported canonical exam ids")
    parser.add_argument("--output-root", default=str(V2_DATA_DIR), help="Canonical output root")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])

    if args.legacy_input and args.legacy_output and not args.all and not args.exam_ids and not args.list:
        convert_exam(args.legacy_input, args.legacy_output)
        print(f"OK legacy mock-data: {args.legacy_output}")
        return 0

    if args.list:
        for exam_id in EXAMS_BY_ID:
            print(exam_id)
        return 0

    output_root = Path(args.output_root)
    selected_exam_ids = []
    if args.all:
        selected_exam_ids = list(EXAMS_BY_ID.keys())
    else:
        selected_exam_ids = args.exam_ids

    if not selected_exam_ids:
        print("Usage:")
        print("  python scripts/convert_ap_source.py --list")
        print("  python scripts/convert_ap_source.py --exam calc-bc-2018-intl")
        print("  python scripts/convert_ap_source.py --all")
        print("  python scripts/convert_ap_source.py <input.json> <output.json>")
        return 1

    exit_code = 0
    for exam_id in selected_exam_ids:
        exam_spec = EXAMS_BY_ID.get(exam_id)
        if not exam_spec:
            print(f"SKIP unknown exam_id: {exam_id}")
            exit_code = 1
            continue
        try:
            write_canonical_exam(exam_spec, output_root)
        except Exception as error:
            print(f"ERROR {exam_id}: {error}")
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
