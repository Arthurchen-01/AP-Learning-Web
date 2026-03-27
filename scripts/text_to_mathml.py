"""
将纯文本公式 JSON 升级为模板格式（含 MathML）

策略：
1. 读取纯文本 JSON（科目目录下）
2. 检测公式内容（包含数学符号的文本）
3. 将纯文本公式转换为 MathML
4. 包裹在 HTML span 中，保留 aria-label
5. 保存为新的模板格式 JSON
6. 生成转换日志供人工校对

文本→MathML 转换使用：
- 正则匹配已知模式（三角函数、积分、导数、分数等）
- MathML 手动构建（不依赖外部库，更稳定）
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


# ── MathML 构建器 ──────────────────────────────────────────

def ml(text):
    """简写：创建 MathML 元素"""
    return text


def mrow(*children):
    return f"<mrow>{''.join(children)}</mrow>"


def mi(name):
    return f"<mi>{name}</mi>"


def mn(num):
    return f"<mn>{num}</mn>"


def mo(op):
    return f"<mo>{op}</mo>"


def mfrac(num, den):
    return f"<mfrac>{num}{den}</mfrac>"


def msqrt(content):
    return f"<msqrt>{content}</msqrt>"


def msup(base, sup):
    return f"<msup>{base}{sup}</msup>"


def msub(base, sub):
    return f"<msub>{base}{sub}</msub>"


def msubsup(base, sub, sup):
    return f"<msubsup>{base}{sub}{sup}</msubsup>"


def math_wrap(content):
    return f"<math>{content}</math>"


def span_with_mathml(mathml_content, aria_label, text_before=""):
    """创建带 MathML 和 aria-label 的 span"""
    return f'{text_before}<span aria-label="{aria_label}">{mathml_content}</span>'


# ── 公式检测 ───────────────────────────────────────────────

MATH_SYMBOLS = set("∫∑∏√πθαβγΔδεμσωΩλρτφψ≤≥≠≈±×÷′²³⅓⅔¼¾⅛")
TRIG_FUNCS = {"sin", "cos", "tan", "cot", "sec", "csc"}
MATH_FUNCS = TRIG_FUNCS | {"ln", "log", "exp"}


def has_math(text):
    """判断文本是否包含数学公式"""
    if not text:
        return False
    # 包含数学符号
    if any(c in MATH_SYMBOLS for c in text):
        return True
    # 包含三角函数或数学函数
    for func in MATH_FUNCS:
        if func in text.lower():
            return True
    # 包含导数标记
    if re.search(r"[fgh]\s*[′']\s*\(", text):
        return True
    # 包含积分符号
    if "integral" in text.lower() or "∫" in text:
        return True
    # 包含分数模式
    if re.search(r"−?\d+\s*/\s*\d+", text):
        return True
    # 包含指数
    if re.search(r"[a-zA-Z]\s*[²³]|\^\s*\d+|\{\d+\}", text):
        return True
    return False


# ── 文本→MathML 转换 ──────────────────────────────────────

def tokenize_math(text):
    """将数学文本分解为 token"""
    tokens = []
    i = 0
    while i < len(text):
        c = text[i]
        # 数字
        if c.isdigit() or (c == '.' and i + 1 < len(text) and text[i + 1].isdigit()):
            j = i
            while j < len(text) and (text[j].isdigit() or text[j] == '.'):
                j += 1
            tokens.append(("num", text[i:j]))
            i = j
        # 字母（变量或函数名）
        elif c.isalpha():
            j = i
            while j < len(text) and text[j].isalpha():
                j += 1
            word = text[i:j]
            if word.lower() in MATH_FUNCS:
                tokens.append(("func", word.lower()))
            else:
                tokens.append(("var", word))
            i = j
        # 希腊字母和特殊符号
        elif c in MATH_SYMBOLS:
            tokens.append(("sym", c))
            i += 1
        # 运算符
        elif c in "+-*/=<>!()[]{}":
            tokens.append(("op", c))
            i += 1
        # 减号/负号（Unicode）
        elif c == "−":
            tokens.append(("op", "−"))
            i += 1
        # 空格
        elif c in " \t":
            i += 1
        # 其他
        else:
            tokens.append(("other", c))
            i += 1
    return tokens


def text_to_mathml_simple(text):
    """
    简单的文本→MathML 转换
    处理常见模式，复杂的保持原文本
    """
    if not text or not has_math(text):
        return None

    # 清理
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = re.sub(r"\s+", " ", text).strip()

    # 生成 aria-label（语音描述）
    aria = text.replace("−", "negative ").replace("′", "prime ")
    aria = re.sub(r"[()]", lambda m: "open paren" if m.group() == "(" else "close paren", aria)

    # 简单模式匹配 → MathML

    # 1. 三角函数: "cos(3x−5)" → MathML
    trig_match = re.match(r"(sin|cos|tan|cot|sec|csc)\s*[\(（]\s*([^)）]+)\s*[\)）]", text)
    if trig_match:
        func = trig_match.group(1)
        arg = trig_match.group(2)
        arg_mathml = text_to_mathml_inner(arg)
        content = mrow(mi(func), mo("("), arg_mathml, mo(")"))
        return span_with_mathml(math_wrap(content), aria, "")

    # 2. 三角函数平方: "cos²(3x−5)"
    trig_sq = re.match(r"(sin|cos|tan)\s*[²]\s*[\(（]\s*([^)）]+)\s*[\)）]", text)
    if trig_sq:
        func = trig_sq.group(1)
        arg = trig_sq.group(2)
        arg_mathml = text_to_mathml_inner(arg)
        content = mrow(msup(mi(func), mn("2")), mo("("), arg_mathml, mo(")"))
        return span_with_mathml(math_wrap(content), aria, "")

    # 3. 简单表达式: "3x−5"
    if re.match(r"^[0-9a-zA-Z+\-−×÷²³\s]+$", text):
        content = text_to_mathml_inner(text)
        return span_with_mathml(math_wrap(content), aria, "")

    # 4. 复杂公式，直接包装为 MathML 文本
    content = text_to_mathml_inner(text)
    if content:
        return span_with_mathml(math_wrap(content), aria, "")

    return None


def text_to_mathml_inner(text):
    """将文本内部转换为 MathML 内容"""
    text = text.strip()
    if not text:
        return mn("0")

    parts = []
    i = 0
    while i < len(text):
        c = text[i]

        # 数字
        if c.isdigit() or (c == '.' and i + 1 < len(text) and text[i + 1].isdigit()):
            j = i
            while j < len(text) and (text[j].isdigit() or text[j] == '.'):
                j += 1
            parts.append(mn(text[i:j]))
            i = j

        # 三角函数
        elif text[i:i+3].lower() in TRIG_FUNCS or text[i:i+4].lower() in TRIG_FUNCS:
            for func in ["sin", "cos", "tan", "cot", "sec", "csc"]:
                if text[i:].lower().startswith(func):
                    parts.append(mi(func))
                    i += len(func)
                    break

        # 字母变量
        elif c.isalpha():
            parts.append(mi(c))
            i += 1

        # 减号/负号
        elif c == "−" or c == "-":
            parts.append(mo("−"))
            i += 1

        # 运算符
        elif c in "+=<>":
            parts.append(mo(c))
            i += 1

        # 乘号
        elif c == "×":
            parts.append(mo("×"))
            i += 1

        # 除号
        elif c == "÷":
            parts.append(mo("÷"))
            i += 1

        # 括号
        elif c in "()（）":
            bracket = "(" if c in "(（" else ")"
            parts.append(mo(bracket))
            i += 1

        # 平方
        elif c == "²":
            if parts:
                base = parts.pop()
                parts.append(msup(base, mn("2")))
            i += 1

        # 立方
        elif c == "³":
            if parts:
                base = parts.pop()
                parts.append(msup(base, mn("3")))
            i += 1

        # 导数
        elif c == "′":
            parts.append(mo("′"))
            i += 1

        # 希腊字母
        elif c in MATH_SYMBOLS:
            symbol_map = {
                "π": "π", "θ": "θ", "α": "α", "β": "β", "γ": "γ",
                "Δ": "Δ", "δ": "δ", "ε": "ε", "μ": "μ", "σ": "σ",
                "Σ": "Σ", "ω": "ω", "Ω": "Ω", "λ": "λ", "ρ": "ρ",
                "τ": "τ", "φ": "φ", "ψ": "ψ",
                "∫": "∫", "∑": "∑", "∏": "∏", "√": "√",
                "∞": "∞", "≤": "≤", "≥": "≥", "≠": "≠", "≈": "≈",
                "±": "±",
            }
            sym = symbol_map.get(c, c)
            if c in "∫∑∏√∞":
                parts.append(mo(sym))
            else:
                parts.append(mi(sym))
            i += 1

        # 空格
        elif c == " ":
            i += 1

        # 其他
        else:
            parts.append(mo(c))
            i += 1

    if len(parts) == 1:
        return parts[0]
    return mrow(*parts)


# ── 处理单个问题 ──────────────────────────────────────────

def process_question_content(content):
    """处理题目内容中的数学公式"""
    if not content or not has_math(content):
        return content, 0

    # 尝试整体转换
    mathml = text_to_mathml_simple(content)
    if mathml:
        return mathml, 1

    # 如果整体转换失败，保持原样
    return content, 0


def process_option_content(content):
    """处理选项内容中的数学公式"""
    if not content or not has_math(content):
        return content, 0

    mathml = text_to_mathml_simple(content)
    if mathml:
        return mathml, 1

    return content, 0


# ── 主流程 ────────────────────────────────────────────────

def process_exam(json_path):
    """处理单个考试文件"""
    data = load_json(json_path)
    mathml_count = 0
    processed = 0
    total = 0

    sections = data.get("sections", [])
    for section in sections:
        questions = section.get("questions", [])
        for question in questions:
            total += 1

            # 处理 prompt
            prompt = question.get("prompt", "")
            new_prompt, count = process_question_content(prompt)
            if count > 0:
                question["prompt"] = new_prompt
                mathml_count += count

            # 处理 options
            for option in question.get("options", []):
                content = option.get("content", "") or option.get("text", "")
                if not content:
                    continue
                new_content, count = process_option_content(content)
                if count > 0:
                    if "content" in option:
                        option["content"] = new_content
                    else:
                        option["text"] = new_content
                    mathml_count += count

            if mathml_count > 0:
                processed += 1

    return data, mathml_count, processed, total


def main():
    dirs = [
        "calculus-bc", "csa", "statistics", "psychology",
        "macroeconomics", "microeconomics", "physics-c-em", "physics-c-mechanics"
    ]

    total_mathml = 0
    total_processed = 0
    total_files = 0
    log = []

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
            try:
                data, mathml_count, processed, questions = process_exam(jf)

                if mathml_count > 0:
                    # 保存升级后的 JSON
                    write_json(jf, data)
                    total_mathml += mathml_count
                    total_processed += processed
                    log.append(f"OK {dir_name}/{jf.name}: {mathml_count} MathML in {processed}/{questions} questions")
                    print(f"  ✅ {dir_name}/{jf.name}: +{mathml_count} MathML")
                else:
                    log.append(f"SKIP {dir_name}/{jf.name}: no formulas detected")
                    print(f"  ⏭ {dir_name}/{jf.name}: no formulas")

            except Exception as e:
                log.append(f"ERROR {dir_name}/{jf.name}: {e}")
                print(f"  ❌ {dir_name}/{jf.name}: {e}")

    print(f"\n{'='*50}")
    print(f"Files processed: {total_files}")
    print(f"Files with MathML added: {total_processed}")
    print(f"Total MathML elements added: {total_mathml}")

    # 写日志
    log_path = ROOT / "database" / "07_logs" / "text_to_mathml_log.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("\n".join(log), encoding="utf-8")
    print(f"Log: {log_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
