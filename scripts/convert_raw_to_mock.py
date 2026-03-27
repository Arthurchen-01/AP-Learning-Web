#!/usr/bin/env python3
"""
Convert raw exam JSON from database/01_raw/json/ to mock-data format.

Usage:
    python scripts/convert_raw_to_mock.py <input_json_file>
    python scripts/convert_raw_to_mock.py --all
"""

from __future__ import annotations

import json
import re
import sys
from html import unescape
from pathlib import Path
from typing import Any


WHITESPACE_RE = re.compile(r"[ \t\r\f\v]+")
TAG_RE = re.compile(r"<[^>]+>")
BREAK_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
PARA_OPEN_RE = re.compile(r"<p[^>]*>", re.IGNORECASE)
DIV_OPEN_RE = re.compile(r"<div[^>]*>", re.IGNORECASE)
SPAN_OPEN_RE = re.compile(r"<span[^>]*>", re.IGNORECASE)


def clean_html(value: str | None) -> str:
    if not value:
        return ""

    text = unescape(value)
    text = text.replace("\xa0", " ")
    text = BREAK_RE.sub("\n", text)
    text = PARA_OPEN_RE.sub("\n\n", text)
    text = text.replace("</p>", "")
    text = DIV_OPEN_RE.sub("", text)
    text = text.replace("</div>", "")
    text = SPAN_OPEN_RE.sub("", text)
    text = text.replace("</span>", "")
    text = TAG_RE.sub("", text)
    text = WHITESPACE_RE.sub(" ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def unique_questions(question_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[Any, Any, Any]] = set()

    for question in question_list:
        key = (
            question.get("questionId"),
            question.get("questionNum"),
            question.get("questionType"),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(question)

    return unique


def extract_question_kind(question: dict[str, Any]) -> str:
    if question.get("questionType") == 2 or question.get("subjectiveQuestionList"):
        return "frq"
    if question.get("type") == 2:
        return "multi"
    return "single"


def convert_options(option_list: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    options: list[dict[str, str]] = []
    for option in option_list or []:
        options.append(
            {
                "key": str(option.get("optionSign") or "").strip(),
                "text": clean_html(option.get("optionContent")),
            }
        )
    return options


def convert_mcq_question(question: dict[str, Any], index: int) -> dict[str, Any]:
    prompt = clean_html(question.get("choiceQuestionContent")) or clean_html(question.get("questionTitle"))
    return {
        "id": str(question.get("questionId") or f"mcq-{index}"),
        "type": extract_question_kind(question),
        "prompt": prompt,
        "options": convert_options(question.get("optionList")),
        "answer": None,
        "explanation": "Answer key not available yet for this imported exam.",
    }


def convert_frq_question(question: dict[str, Any], index: int) -> dict[str, Any]:
    prompt_blocks: list[str] = []
    title = clean_html(question.get("questionTitle"))
    if title:
        prompt_blocks.append(title)

    seen_parts: set[str] = set()
    for part in question.get("subjectiveQuestionList") or []:
        label = str(part.get("questionSpecialSort") or "").strip()
        content = clean_html(part.get("questionContent"))
        part_key = f"{label}:{content}"
        if not content or part_key in seen_parts:
            continue
        seen_parts.add(part_key)
        prompt_blocks.append(f"({label}) {content}" if label else content)

    if not prompt_blocks:
        prompt_blocks.append(clean_html(question.get("choiceQuestionContent")))

    return {
        "id": str(question.get("questionId") or f"frq-{index}"),
        "type": "frq",
        "prompt": "\n\n".join(block for block in prompt_blocks if block),
        "points": max(1, len(seen_parts) or 1),
        "rubric": {"mustInclude": [], "concepts": []},
        "explanation": "Scoring rubric not available yet for this imported exam.",
    }


def convert_question(question: dict[str, Any], index: int) -> dict[str, Any]:
    if extract_question_kind(question) == "frq":
        return convert_frq_question(question, index)
    return convert_mcq_question(question, index)


def count_questions_for_part(part: dict[str, Any]) -> int:
    fields = (
        "singleChoiceAmount",
        "multiChoiceAmount",
        "frqAmount",
        "saqAmount",
        "dbqAmount",
        "leqAmount",
    )
    return sum(int(part.get(field) or 0) for field in fields)


def build_section_title(section: dict[str, Any], part: dict[str, Any], section_index: int, part_index: int) -> str:
    section_name = str(section.get("sectionName") or "").strip()
    part_name = str(part.get("partName") or "").strip()
    if section_name and part_name:
        return f"Section {section_name}, Part {part_name}"
    if section_name:
        return f"Section {section_name}"
    if part_name:
        return f"Part {part_name}"
    return f"Section {section_index + 1}, Part {part_index + 1}"


def build_part_title(part: dict[str, Any], default_label: str) -> str:
    if part.get("singleChoiceAmount"):
        return f"{default_label} - Multiple Choice"
    if part.get("multiChoiceAmount"):
        return f"{default_label} - Multiple Select"
    if part.get("frqAmount") or part.get("saqAmount") or part.get("dbqAmount") or part.get("leqAmount"):
        return f"{default_label} - Free Response"
    return default_label


def group_questions_by_template(questions: list[dict[str, Any]], template: dict[str, Any]) -> list[dict[str, Any]]:
    section_defs = template.get("sectionList") or []
    if not section_defs:
        return [
            {
                "id": "section-1",
                "title": "All Questions",
                "partTitle": "Practice",
                "limitMinutes": 60,
                "directions": "Imported from raw exam data. Answer keys are not available yet.",
                "questions": questions,
            }
        ]

    sections: list[dict[str, Any]] = []
    cursor = 0

    for section_index, section in enumerate(section_defs):
        for part_index, part in enumerate(section.get("partList") or []):
            expected_count = count_questions_for_part(part)
            if expected_count <= 0:
                continue

            part_questions = questions[cursor : cursor + expected_count]
            cursor += expected_count

            if not part_questions:
                continue

            sections.append(
                {
                    "id": f"section-{section.get('sectionId') or section_index + 1}-part-{part.get('partId') or part_index + 1}",
                    "title": build_section_title(section, part, section_index, part_index),
                    "partTitle": build_part_title(part, f"Part {part.get('partName') or part_index + 1}"),
                    "limitMinutes": int(part.get("limitTime") or 60),
                    "directions": clean_html(part.get("directionsText")) or "Imported from raw exam data.",
                    "questions": part_questions,
                }
            )

    leftovers = questions[cursor:]
    if leftovers:
        if sections:
            sections[-1]["questions"].extend(leftovers)
        else:
            sections.append(
                {
                    "id": "section-1",
                    "title": "All Questions",
                    "partTitle": "Practice",
                    "limitMinutes": 60,
                    "directions": "Imported from raw exam data. Answer keys are not available yet.",
                    "questions": leftovers,
                }
            )

    return sections


def extract_year_label(exam_name: str) -> str:
    match = re.search(r"(20\d{2})", exam_name)
    return match.group(1) if match else "Practice"


def convert_exam(input_path: Path) -> dict[str, Any]:
    raw = json.loads(input_path.read_text(encoding="utf-8"))
    data = raw.get("data") or {}

    unique_raw_questions = unique_questions(data.get("questionList") or [])
    converted_questions = [
        convert_question(question, index + 1)
        for index, question in enumerate(unique_raw_questions)
    ]

    exam_name = clean_html(data.get("examName")) or input_path.stem
    subject_name = clean_html(data.get("subjectName")) or "Unknown Subject"

    return {
        "examId": str(data.get("id") or input_path.stem),
        "title": exam_name,
        "subjectName": subject_name,
        "yearLabel": extract_year_label(exam_name),
        "description": "Practice mode only. This imported paper does not include answer keys or scoring yet.",
        "answerKeyAvailable": False,
        "scoring": {
            "answerKeyAvailable": False,
            "apBands": [],
            "note": "Scoring unavailable until answer keys are imported.",
        },
        "sections": group_questions_by_template(converted_questions, data.get("template") or {}),
    }


def write_exam(exam: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"ap-exam-{exam['examId']}.json"
    output_path.write_text(json.dumps(exam, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def iter_source_files(input_dir: Path) -> list[Path]:
    preferred: dict[str, Path] = {}
    for path in sorted(input_dir.glob("*.json")):
        if path.name == "mokao_capture_index.json":
            continue

        match = re.search(r"__(\d+)(?: \(\d+\))?\.json$", path.name)
        exam_id = match.group(1) if match else path.stem
        current = preferred.get(exam_id)

        if current is None or "(1)" in current.name and "(1)" not in path.name:
            preferred[exam_id] = path

    return list(preferred.values())


def convert_all(input_dir: Path, output_dir: Path) -> tuple[int, int]:
    success = 0
    failed = 0

    for path in iter_source_files(input_dir):
        try:
            exam = convert_exam(path)
            write_exam(exam, output_dir)
            total_questions = sum(len(section["questions"]) for section in exam["sections"])
            print(f"[ok] {path.name} -> ap-exam-{exam['examId']}.json ({total_questions} questions)")
            success += 1
        except Exception as exc:  # pragma: no cover - CLI reporting
            print(f"[fail] {path.name}: {exc}")
            failed += 1

    return success, failed


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    input_dir = project_root / "database" / "01_raw" / "json"
    output_dir = project_root / "mock-data"

    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)

    if sys.argv[1] == "--all":
        success, failed = convert_all(input_dir, output_dir)
        print(f"Converted {success} exams, {failed} failed.")
        raise SystemExit(0 if failed == 0 else 1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        raise SystemExit(f"File not found: {input_path}")

    exam = convert_exam(input_path)
    output_path = write_exam(exam, output_dir)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
