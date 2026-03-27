"""
将旧格式 JSON（含 MathML）转换为 mock-data 格式，完整保留 HTML + MathML

用法:
  python convert_old_to_mockdata.py

功能:
  1. 扫描 database/01_raw/json/ 下所有根目录旧格式 JSON
  2. 将 choiceQuestionContent (HTML+MathML) 写入 prompt
  3. 将 optionList[].optionContent (HTML+MathML) 写入 options
  4. 保留 answer、analysis (explanation)
  5. 生成 section 结构（按 type 和 specialSort 分组）
  6. 写入 mock-data/
  7. 重建 exam-catalog.json
"""

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_JSON = ROOT / "database" / "01_raw" / "json"
MOCK_DATA = ROOT / "mock-data"

sys.stdout.reconfigure(encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def make_numeric_id(seed: str) -> str:
    h = hashlib.md5(seed.encode()).hexdigest()[:15]
    return "9" + str(int(h, 16))[:17]


SUBJECT_NAMES = {
    "calculus-bc": "微积分BC",
    "csa": "计算机科学A",
    "statistics": "统计学",
    "psychology": "心理学",
    "macroeconomics": "宏观经济",
    "microeconomics": "微观经济",
    "physics-c-em": "物理C电磁",
    "physics-c-mechanics": "物理C力学",
}


def extract_year_and_type(exam_id: str) -> tuple:
    year = "??"
    paper_type = "未知"
    m = re.search(r"(20\d{2}|19\d{2})", exam_id)
    if m:
        year = m.group(1)
    eid = exam_id.lower()
    if "naset1" in eid:
        paper_type = "北美卷Set1"
    elif "naset2" in eid:
        paper_type = "北美卷Set2"
    elif "na" in eid:
        paper_type = "北美卷"
    elif "intl" in eid:
        paper_type = "国际卷"
    elif "sq" in eid or "pe" in eid:
        paper_type = "样题"
    return year, paper_type


def clean_html(html) -> str:
    """清理 HTML，保留 MathML，移除多余空白"""
    if not html:
        return ""
    html = str(html)
    # &nbsp; → 空格
    html = html.replace("&nbsp;", " ")
    # 多个空格合并
    html = re.sub(r"\s+", " ", html)
    return html.strip()


def extract_answer(question: dict) -> str:
    """从旧格式提取答案"""
    # correctQuestionAnswerStr 通常是答案
    ans = question.get("correctQuestionAnswerStr", "")
    if ans:
        return ans
    # singleQuestionAnswer
    ans = question.get("singleQuestionAnswer", "")
    if ans:
        return ans
    # correctSingleQuestionAnswer
    ans = question.get("correctSingleQuestionAnswer", "")
    if ans:
        return ans
    return ""


def extract_explanation(question: dict) -> str:
    """提取解析"""
    analysis = question.get("analysis", "")
    if analysis and analysis.strip() and "不能对 Null" not in analysis:
        return clean_html(analysis)
    return "Answer key not available yet for this imported exam."


def convert_question(old_q: dict, index: int) -> dict:
    """转换单个题目"""
    q_type = old_q.get("type", 1)

    # 题目类型映射
    if q_type == 1:
        type_str = "single"
    elif q_type == 2:
        type_str = "free-response"
    else:
        type_str = "single"

    # Prompt: 使用 choiceQuestionContent（含 MathML）或 subjectiveQuestionContent
    prompt = ""
    cqc = old_q.get("choiceQuestionContent")
    if cqc:
        prompt = clean_html(cqc)
    sq_list = old_q.get("subjectiveQuestionList")
    if not prompt and sq_list and isinstance(sq_list, list) and sq_list:
        prompt = clean_html(sq_list[0].get("subjectiveQuestionContent", ""))

    # Options: 从 optionList 提取
    options = []
    option_list = old_q.get("optionList") or []
    if option_list:
        for opt in option_list:
            key = opt.get("optionNo", "")
            content = clean_html(opt.get("optionContent", ""))
            if content:  # 只添加有内容的选项
                options.append({"key": key, "content": content})

    # Answer
    answer = extract_answer(old_q)

    # Explanation
    explanation = extract_explanation(old_q)

    # Question ID
    q_id = str(old_q.get("questionId", index))

    return {
        "id": q_id,
        "type": type_str,
        "prompt": prompt,
        "options": options,
        "answer": answer,
        "explanation": explanation,
    }


def group_into_sections(questions: list, exam_data: dict) -> list:
    """将题目按 section 分组"""
    # 旧格式的 section 信息在 questionList 的 specialSort 中
    # 但更简单的方式是按 type 分组：MCQ 一个 section，FRQ 一个 section

    mcq_questions = [q for q in questions if q["type"] == "single"]
    frq_questions = [q for q in questions if q["type"] == "free-response"]

    sections = []

    if mcq_questions:
        sections.append(
            {
                "id": "section-mcq",
                "title": "Section 1",
                "partTitle": "Multiple Choice",
                "limitMinutes": exam_data.get("limitTime", 3600) // 60 // 2,
                "directions": "",
                "questions": mcq_questions,
            }
        )

    if frq_questions:
        sections.append(
            {
                "id": "section-frq",
                "title": "Section 2",
                "partTitle": "Free Response",
                "limitMinutes": exam_data.get("limitTime", 3600) // 60 // 2,
                "directions": "",
                "questions": frq_questions,
            }
        )

    # 如果只有一种类型，合并为一个 section
    if not sections and questions:
        sections.append(
            {
                "id": "section-all",
                "title": "Section 1",
                "partTitle": "Questions",
                "limitMinutes": exam_data.get("limitTime", 3600) // 60,
                "directions": "",
                "questions": questions,
            }
        )

    return sections


def normalize_subject_name(subject_name: str) -> str:
    """标准化科目名称"""
    mapping = {
        "CSA": "计算机科学A",
        "心理": "心理学",
    }
    return mapping.get(subject_name, subject_name)


def main() -> int:
    # 扫描根目录旧格式 JSON
    old_files = sorted(
        [
            f
            for f in RAW_JSON.glob("*.json")
            if f.name != "mokao_capture_index.json"
            and "(1)" not in f.name
            and f.stat().st_size > 1000
        ]
    )

    print(f"找到 {len(old_files)} 个旧格式 JSON\n")

    converted = 0
    errors = 0
    used_ids = set()

    # 收集已有 mock-data 的 examId
    for f in MOCK_DATA.glob("ap-exam-*.json"):
        try:
            d = load_json(f)
            used_ids.add(d.get("examId", ""))
        except Exception:
            pass

    catalog_items = []

    for old_file in old_files:
        try:
            data = load_json(old_file)
        except Exception as e:
            print(f"ERROR 读取 {old_file.name}: {e}")
            errors += 1
            continue

        exam_data = data.get("data", {})
        exam_id = str(exam_data.get("id", ""))
        exam_name = exam_data.get("examName", "")
        subject_name = normalize_subject_name(exam_data.get("subjectName", ""))

        if not exam_id:
            print(f"SKIP {old_file.name}: no exam ID")
            continue

        # 检查是否已有（跳过已存在的）
        if exam_id in used_ids:
            # 已经有 mock-data 文件，但可能是旧版（无 MathML），需要覆盖
            pass

        # 转换题目
        old_questions = exam_data.get("questionList", [])
        converted_questions = []
        mathml_count = 0

        for idx, old_q in enumerate(old_questions):
            cq = old_q.get("choiceQuestionContent") or ""
            if "<math" in cq:
                mathml_count += 1

            # 检查选项中的 MathML
            for opt in (old_q.get("optionList") or []):
                oc = (opt or {}).get("optionContent") or ""
                if "<math" in oc:
                    mathml_count += 1

            converted_questions.append(convert_question(old_q, idx))

        # 按 section 分组
        sections = group_into_sections(converted_questions, exam_data)

        # 使用原始 examId 作为文件名（覆盖旧文件）
        numeric_id = exam_id

        # 构建 mock-data 格式
        mock_exam = {
            "examId": exam_id,
            "title": exam_name,
            "subjectName": subject_name,
            "yearLabel": "",
            "description": f"AP {exam_name}",
            "answerKeyAvailable": bool(exam_data.get("questionAnswer")),
            "scoring": {
                "answerKeyAvailable": False,
                "apBands": [],
                "note": "Scoring unavailable until answer keys are imported.",
            },
            "sections": sections,
        }

        # 写入 mock-data
        out_path = MOCK_DATA / f"ap-exam-{numeric_id}.json"
        write_json(out_path, mock_exam)

        # Catalog item
        year, ptype = extract_year_and_type(exam_id)
        catalog_items.append(
            {
                "examId": numeric_id,
                "title": exam_name,
                "subject": subject_name,
                "year": year,
                "paperType": ptype,
                "questionCount": len(converted_questions),
                "sectionCount": len(sections),
            }
        )

        converted += 1
        print(
            f"OK {old_file.name} -> {exam_name} | {len(converted_questions)} Q | "
            f"{mathml_count} MathML | {len(sections)} sections"
        )

    # 合并已有 mock-data 中不在旧格式的文件（新格式导入的）
    for f in sorted(MOCK_DATA.glob("ap-exam-*.json")):
        try:
            d = load_json(f)
            eid = d.get("examId", "")
            # 检查是否已在 catalog_items 中
            already = any(item["examId"] == f.stem.replace("ap-exam-", "") for item in catalog_items)
            if not already:
                numeric_id = f.stem.replace("ap-exam-", "")
                year, ptype = extract_year_and_type(eid)
                q_count = sum(len(s.get("questions", [])) for s in d.get("sections", []))
                catalog_items.append(
                    {
                        "examId": numeric_id,
                        "title": d.get("title", ""),
                        "subject": d.get("subjectName", ""),
                        "year": year,
                        "paperType": ptype,
                        "questionCount": q_count,
                        "sectionCount": len(d.get("sections", [])),
                    }
                )
        except Exception:
            pass

    # 重建 catalog
    catalog_items.sort(key=lambda x: (x["subject"], x["year"], x["title"]))
    subjects = sorted(set(i["subject"] for i in catalog_items))
    years = sorted(set(i["year"] for i in catalog_items if i["year"] != "??"), reverse=True)
    paper_types = sorted(set(i["paperType"] for i in catalog_items))

    catalog = {
        "generatedAt": "2026-03-27",
        "total": len(catalog_items),
        "subjects": subjects,
        "years": years,
        "paperTypes": paper_types,
        "items": catalog_items,
    }

    write_json(MOCK_DATA / "exam-catalog.json", catalog)

    print(f"\n{'='*50}")
    print(f"Converted from old format: {converted}")
    print(f"Errors: {errors}")
    print(f"Total in catalog: {len(catalog_items)}")
    print(f"Subjects: {', '.join(subjects)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
