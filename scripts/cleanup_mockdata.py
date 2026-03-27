"""
清理并重建 mock-data：用旧格式 JSON（含 MathML）覆盖，保留其他新格式文件
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_JSON = ROOT / "database" / "01_raw" / "json"
MOCK_DATA = ROOT / "mock-data"

sys.stdout.reconfigure(encoding="utf-8")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    # 1. 收集旧格式 examId
    old_files = [
        f
        for f in RAW_JSON.glob("*.json")
        if f.name != "mokao_capture_index.json"
        and "(1)" not in f.name
        and f.stat().st_size > 1000
    ]

    old_exam_ids = set()
    for f in old_files:
        try:
            d = load_json(f)
            eid = str(d.get("data", {}).get("id", ""))
            if eid:
                old_exam_ids.add(eid)
        except Exception:
            pass

    print(f"Old-format exam IDs: {len(old_exam_ids)}")

    # 2. 删除 mock-data 中对应旧格式的文件（它们是昨天导入的无 MathML 版本）
    removed = 0
    for f in sorted(MOCK_DATA.glob("ap-exam-*.json")):
        try:
            d = load_json(f)
            eid = d.get("examId", "")
            if eid in old_exam_ids:
                # 这是旧格式考试的 mock-data 文件，需要删除重做
                f.unlink()
                removed += 1
                print(f"  Removed: {f.name} (examId={eid})")
        except Exception:
            pass

    print(f"\nRemoved {removed} old mock-data files")
    remaining = len(list(MOCK_DATA.glob("ap-exam-*.json")))
    print(f"Remaining: {remaining} files")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
