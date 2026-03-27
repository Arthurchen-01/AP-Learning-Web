"""
修复 OCR 空格伪影：去除字母/数字间多余空格

规则：
1. "W h e n" → "When"（连续单字符+空格→合并）
2. 保留运算符周围的合法空格："3 x − 5" 保持
3. "2 0 2 4" → "2024"（纯数字序列）
4. 保留句尾标点前的空格
"""

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
RAW_JSON = ROOT / "database" / "01_raw" / "json"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def fix_spaced_letters(text):
    """
    修复字母间空格伪影
    "W h e n a s k e d" → "When asked"
    "T h e s i z e s , i n s q u a r e" → "The sizes, in square"
    """
    if not text:
        return text

    # 核心修复：匹配连续 "单字符+空格" 模式（至少2个字符）
    # 这会匹配 "W h e n", "T h e", "i n", "o f" 等
    # 但不会匹配正常单词 "cos" 或 "the"（因为没有空格）
    def merge_spaced_chars(match):
        return match.group(0).replace(" ", "")

    # 匹配 2+ 个连续的 "单字母+空格"（到非字母为止）
    # 这是最关键的规则，覆盖 "T h e s i z e s" 这种长序列
    text = re.sub(
        r"(?<![a-zA-Z])([a-zA-Z]\s)+[a-zA-Z](?![a-zA-Z])",
        merge_spaced_chars,
        text,
    )

    # 单数字空格也合并: "2 0 2 4" → "2024"
    text = re.sub(
        r"(?<!\d)(\d\s)+\d(?!\d)",
        lambda m: m.group(0).replace(" ", ""),
        text,
    )

    # 修复常见函数名（如果还有残留）
    math_funcs = ["sin", "cos", "tan", "cot", "sec", "csc", "ln", "log", "exp"]
    for func in math_funcs:
        spaced = " ".join(func)
        text = text.replace(spaced, func)

    # 清理多余空格
    text = re.sub(r"  +", " ", text)

    return text


def fix_math_spacing(text):
    """
    修复数学表达式中的空格
    "c o s" → "cos"（如果之前没修复）
    "s i n" → "sin"
    """
    if not text:
        return text

    # 修复常见函数名的空格
    math_funcs = ["sin", "cos", "tan", "cot", "sec", "csc", "ln", "log", "exp"]
    for func in math_funcs:
        # "s i n" → "sin" (每个字母间有空格)
        spaced = " ".join(func)
        text = text.replace(spaced, func)

    return text


def process_question(question, stats):
    """处理单个题目的文本"""
    changed = False

    # Prompt
    prompt = question.get("prompt", "")
    if prompt:
        new_prompt = fix_spaced_letters(prompt)
        new_prompt = fix_math_spacing(new_prompt)
        if new_prompt != prompt:
            question["prompt"] = new_prompt
            stats["prompt_fixed"] += 1
            changed = True

    # Options
    for opt in question.get("options", []):
        for field in ["content", "text"]:
            val = opt.get(field, "")
            if val:
                new_val = fix_spaced_letters(val)
                new_val = fix_math_spacing(new_val)
                if new_val != val:
                    opt[field] = new_val
                    stats["option_fixed"] += 1
                    changed = True

    if changed:
        stats["questions_fixed"] += 1

    return changed


def process_exam(json_path):
    """处理单个考试文件"""
    stats = {
        "prompt_fixed": 0,
        "option_fixed": 0,
        "questions_fixed": 0,
    }

    try:
        data = load_json(json_path)
    except Exception as e:
        return None, f"ERROR: {e}"

    total_questions = 0
    for section in data.get("sections", []):
        for question in section.get("questions", []):
            total_questions += 1
            process_question(question, stats)

    return data, stats


def main():
    dirs = [
        "calculus-bc", "csa", "statistics", "psychology",
        "macroeconomics", "microeconomics", "physics-c-em", "physics-c-mechanics"
    ]

    total_files = 0
    fixed_files = 0
    total_prompts = 0
    total_options = 0
    total_questions_fixed = 0

    for dir_name in dirs:
        dir_path = RAW_JSON / dir_name
        if not dir_path.exists():
            continue

        json_files = sorted([
            f for f in dir_path.glob("*.json")
            if "review" not in f.name and f.stat().st_size > 100
        ])

        for jf in json_files:
            total_files += 1
            result, info = process_exam(jf)

            if result is None:
                print(f"  ❌ {dir_name}/{jf.name}: {info}")
                continue

            if isinstance(info, dict):
                if info["questions_fixed"] > 0:
                    write_json(jf, result)
                    fixed_files += 1
                    total_prompts += info["prompt_fixed"]
                    total_options += info["option_fixed"]
                    total_questions_fixed += info["questions_fixed"]
                    print(f"  ✅ {dir_name}/{jf.name}: {info['questions_fixed']} Q fixed (P:{info['prompt_fixed']}, O:{info['option_fixed']})")
                else:
                    print(f"  ⏭ {dir_name}/{jf.name}: no changes needed")

    print(f"\n{'='*50}")
    print(f"Files scanned: {total_files}")
    print(f"Files fixed: {fixed_files}")
    print(f"Prompts fixed: {total_prompts}")
    print(f"Options fixed: {total_options}")
    print(f"Questions affected: {total_questions_fixed}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
