"""
批量导入考试 JSON 数据到 mock-data 目录，并重建 exam-catalog.json

用法:
  python import_exams.py

流程:
  1. 扫描 database/01_raw/json/ 下所有科目目录的 JSON 文件
  2. 保留现有 mock-data 的 examId（不动已有文件）
  3. 为新文件生成稳定 numeric ID
  4. 写入 mock-data/ap-exam-{id}.json
  5. 重建 exam-catalog.json
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
    """从字符串生成稳定的数字 ID"""
    h = hashlib.md5(seed.encode()).hexdigest()[:15]
    return "9" + str(int(h, 16))[:17]  # 9开头区分于原始API ID


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


def normalize_exam_data(data: dict, subject_dir: str, filename: str) -> dict:
    """统一数据格式"""
    # subjectName
    if not data.get("subjectName"):
        data["subjectName"] = SUBJECT_NAMES.get(subject_dir, subject_dir)

    # examId - 如果没有或是空的，从文件名生成
    eid = data.get("examId", "").strip()
    if not eid:
        stem = Path(filename).stem
        eid = f"{subject_dir}-{stem}"
    data["examId"] = eid

    # title
    if not data.get("title"):
        data["title"] = f"AP {data['subjectName']} {eid}"

    # answerKeyAvailable
    if "answerKeyAvailable" not in data:
        data["answerKeyAvailable"] = False

    return data


def main() -> int:
    # 1. 读取现有 mock-data 的 examId 集合
    existing_exam_ids = {}  # examId -> file path
    for f in MOCK_DATA.glob("ap-exam-*.json"):
        try:
            d = load_json(f)
            eid = d.get("examId", "")
            if eid:
                existing_exam_ids[eid] = f
        except Exception:
            pass
    print(f"现有 mock-data: {len(existing_exam_ids)} 个考试\n")

    # 2. 扫描科目目录
    subject_dirs = sorted([d for d in RAW_JSON.iterdir() if d.is_dir()])
    added = 0
    skipped = 0
    errors = 0
    catalog_items = []

    # 先把现有的加进 catalog
    for eid, fpath in sorted(existing_exam_ids.items()):
        try:
            d = load_json(fpath)
            numeric_id = fpath.stem.replace("ap-exam-", "")
            year, ptype = extract_year_and_type(eid)
            q_count = sum(len(s.get("questions", [])) for s in d.get("sections", []))
            catalog_items.append({
                "examId": numeric_id,
                "title": d.get("title", ""),
                "subject": d.get("subjectName", ""),
                "year": year,
                "paperType": ptype,
                "questionCount": q_count,
                "sectionCount": len(d.get("sections", [])),
            })
        except Exception:
            pass

    # 3. 处理新文件
    used_numeric_ids = {f.stem.replace("ap-exam-", "") for f in MOCK_DATA.glob("ap-exam-*.json")}

    for sdir in subject_dirs:
        dir_name = sdir.name
        json_files = sorted([
            f for f in sdir.glob("*.json")
            if "review" not in f.name and f.stat().st_size > 100
        ])
        print(f"📁 {dir_name}: {len(json_files)} 个文件")

        for jf in json_files:
            try:
                data = load_json(jf)
            except Exception as e:
                print(f"  ❌ {jf.name}: 读取失败 - {e}")
                errors += 1
                continue

            data = normalize_exam_data(data, dir_name, jf.name)
            exam_id = data["examId"]

            # 跳过已有
            if exam_id in existing_exam_ids:
                print(f"  ⏭  {jf.name} -> {exam_id} (已存在)")
                skipped += 1
                continue

            # 生成 numeric ID
            numeric_id = make_numeric_id(exam_id)
            while numeric_id in used_numeric_ids:
                numeric_id = make_numeric_id(f"{numeric_id}-x")
            used_numeric_ids.add(numeric_id)

            # 写入
            out_path = MOCK_DATA / f"ap-exam-{numeric_id}.json"
            write_json(out_path, data)

            # 统计
            year, ptype = extract_year_and_type(exam_id)
            q_count = sum(len(s.get("questions", [])) for s in data.get("sections", []))
            s_count = len(data.get("sections", []))

            catalog_items.append({
                "examId": numeric_id,
                "title": data["title"],
                "subject": data["subjectName"],
                "year": year,
                "paperType": ptype,
                "questionCount": q_count,
                "sectionCount": s_count,
            })

            existing_exam_ids[exam_id] = out_path
            added += 1
            print(f"  ✅ {jf.name} -> {exam_id} | ID:{numeric_id} | {q_count}题 | {s_count} section(s)")

    # 4. 重建 catalog
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
    print(f"✅ 新增: {added} 个考试")
    print(f"⏭  跳过: {skipped} 个 (已存在)")
    print(f"❌ 错误: {errors} 个")
    print(f"📊 Catalog 总计: {len(catalog_items)} 个考试, {len(subjects)} 个科目")
    print(f"📁 科目: {', '.join(subjects)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
