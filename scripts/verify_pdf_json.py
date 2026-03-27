"""
PDF vs JSON 全量校验脚本

功能：
1. 读取 PDF（用 PyMuPDF 提取文本）
2. 与对应 JSON 的 prompt 进行对比
3. 检查：题目数量是否匹配、关键数学符号是否丢失、文本是否被截断
4. 生成校验报告
"""

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
RAW_JSON = ROOT / "database" / "01_raw" / "json"
PDFS = ROOT / "database" / "01_raw" / "pdfs"
REPORT = ROOT / "database" / "07_logs" / "pdf_json_verification.txt"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def extract_pdf_text(pdf_path, max_pages=20):
    """用 PyMuPDF 提取 PDF 文本"""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(pdf_path))
        text = ""
        for page in doc[:max_pages]:
            text += page.get_text()
        doc.close()
        return text
    except ImportError:
        return None


def extract_json_text(json_path):
    """从 JSON 提取所有 prompt 文本"""
    try:
        data = load_json(json_path)
        texts = []
        for section in data.get("sections", []):
            for q in section.get("questions", []):
                prompt = q.get("prompt", "")
                # 去掉 HTML 标签，只留纯文本
                clean = re.sub(r"<[^>]+>", " ", prompt)
                clean = re.sub(r"\s+", " ", clean).strip()
                if clean:
                    texts.append(clean)
        return texts
    except Exception as e:
        return None


def verify_exam(pdf_path, json_path):
    """校验单个 PDF vs JSON"""
    issues = []

    # 1. 提取 PDF 文本
    pdf_text = extract_pdf_text(pdf_path)
    if not pdf_text:
        return ["SKIP: PyMuPDF not available or PDF unreadable"]

    # 2. 提取 JSON 文本
    json_texts = extract_json_text(json_path)
    if json_texts is None:
        return ["ERROR: Cannot parse JSON"]
    if not json_texts:
        return ["WARNING: JSON has no question texts (empty sections)"]

    # 3. 检查 JSON 题目数 vs PDF 中的题目数
    # PDF 中题目通常以 "1." 或 "Question 1" 开头
    pdf_questions = len(re.findall(r"(?:^|\n)\s*(?:\d+\.|Question\s+\d+)", pdf_text))
    json_questions = len(json_texts)

    if pdf_questions > 0 and json_questions > 0:
        ratio = json_questions / pdf_questions
        if ratio < 0.5:
            issues.append(f"QUESTION COUNT MISMATCH: PDF~{pdf_questions}, JSON={json_questions} (ratio={ratio:.2f})")

    # 4. 抽样对比：检查 JSON 中的前3个 prompt 是否能在 PDF 中找到对应文本
    for i, json_text in enumerate(json_texts[:3]):
        # 取 json_text 的前50个字符，看是否在 PDF 中出现
        sample = json_text[:50].strip()
        if len(sample) < 10:
            continue
        # 转义正则特殊字符
        escaped = re.escape(sample[:30])
        if not re.search(escaped, pdf_text, re.IGNORECASE):
            issues.append(f"TEXT NOT FOUND IN PDF: Q{i+1} starts with '{sample[:40]}...'")

    # 5. 检查数学符号丢失
    math_symbols = "∫∑∏√πθαβγ²³′≤≥≠≈±"
    json_math_count = sum(1 for t in json_texts for c in t if c in math_symbols)
    pdf_math_count = sum(1 for c in pdf_text if c in math_symbols)

    if json_math_count == 0 and pdf_math_count > 5:
        issues.append(f"MATH SYMBOLS LOST: PDF has {pdf_math_count}, JSON has 0")

    # 6. 检查 JSON 是否有明显截断
    for i, text in enumerate(json_texts):
        if len(text) < 20 and json_questions > 5:
            issues.append(f"TRUNCATED: Q{i+1} only {len(text)} chars")
            if len(issues) > 5:
                break

    return issues


def main():
    dirs = [
        "calculus-bc", "csa", "statistics", "psychology",
        "macroeconomics", "microeconomics", "physics-c-em", "physics-c-mechanics"
    ]

    log_lines = []
    total = 0
    ok_count = 0
    issue_count = 0
    skip_count = 0

    for dir_name in dirs:
        pdf_dir = PDFS / dir_name
        json_dir = RAW_JSON / dir_name

        if not pdf_dir.exists():
            continue

        log_lines.append(f"\n### {dir_name}")
        print(f"\n📁 {dir_name}")

        for pdf_file in sorted(pdf_dir.glob("*.pdf")):
            stem = pdf_file.stem
            # 找对应 JSON
            json_file = json_dir / f"{stem}.json"
            if not json_file.exists():
                # 尝试其他可能的命名
                candidates = list(json_dir.glob(f"*{stem}*.json"))
                if candidates:
                    json_file = candidates[0]
                else:
                    total += 1
                    skip_count += 1
                    msg = f"  {stem}.pdf -> NO JSON"
                    log_lines.append(msg)
                    print(msg)
                    continue

            total += 1
            issues = verify_exam(pdf_file, json_file)

            if not issues:
                ok_count += 1
                log_lines.append(f"  ✅ {stem}.pdf")
                print(f"  ✅ {stem}.pdf")
            elif all(i.startswith("SKIP") for i in issues):
                skip_count += 1
                log_lines.append(f"  ⏭ {stem}.pdf: {issues[0]}")
                print(f"  ⏭ {stem}.pdf")
            else:
                issue_count += 1
                log_lines.append(f"  ❌ {stem}.pdf: {len(issues)} issues")
                for issue in issues:
                    log_lines.append(f"      {issue}")
                    print(f"    - {issue}")

    # 汇总
    summary = [
        f"\n{'='*50}",
        f"PDF vs JSON Verification Report",
        f"{'='*50}",
        f"Total: {total}",
        f"OK: {ok_count}",
        f"Issues: {issue_count}",
        f"Skipped: {skip_count}",
        f"Accuracy: {ok_count/max(total-skip_count,1)*100:.1f}%",
    ]

    log_lines = summary + log_lines
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(log_lines), encoding="utf-8")

    print(f"\n{'='*50}")
    for s in summary:
        print(s)
    print(f"\nReport: {REPORT}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
