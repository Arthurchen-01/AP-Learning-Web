#!/usr/bin/env python3
"""
Script to add FRQ entries to questions.json for 2016 and 2017 Calc BC exams.
Based on extracted text from pdftotext and the 2018 script pattern.
"""
import json
import os

PROJECT_PATH = r"C:\Users\25472\projects\AP-Learning-Web"

# ===== 2016 FRQ Questions =====
FRQ_2016 = [
    {
        "id": "frq-2016-1",
        "seq": 46,
        "title": "Parametric curve C in the xy-plane",
        "parts": [
            {"part": "a", "text": "Find the slope of the line tangent to the curve C at the point where t = 3."},
            {"part": "b", "text": "For 1 <= t <= 6, what is the value of t at which the line tangent to the curve C is vertical?"},
            {"part": "c", "text": "Find the length of the curve C for 1 <= t <= 6."},
            {"part": "d", "text": "Given y(1) = 2, find y(3)."}
        ]
    },
    {
        "id": "frq-2016-2",
        "seq": 50,
        "title": "Board game sales rate",
        "parts": [
            {"part": "a", "text": "Approximate the value of G'(8) using the data in the table. Show the computations that lead to your answer."},
            {"part": "b", "text": "Approximate the value of the integral from 0 to 12 of G(t) dt using a right Riemann sum with the four subintervals indicated by the table. Explain the meaning of the integral in the context of this problem."},
            {"part": "c", "text": "One salesperson believes that, starting with 2400 games per week at time 12, the rate at which games are being sold will increase at a constant rate of 100 games per week per week. Based on this model, how many total games will be sold in the 8 weeks between time t = 12 and t = 20?"},
            {"part": "d", "text": "Another salesperson believes the best model for the rate at which games will be sold in the 8 weeks between t = 12 and t = 20 is M(t) = 2400 * e^(-0.01*(t-12)^2) games per week. Based on this model, how many total games, to the nearest whole number, will be sold during this period?"}
        ]
    },
    {
        "id": "frq-2016-3",
        "seq": 54,
        "title": "Function f with graph (quarter circle and line segments)",
        "parts": [
            {"part": "a", "text": "Find the average rate of change of f over the interval [-5, 0]. Show the computations that lead to your answer."},
            {"part": "b", "text": "For -5 <= x <= c, let g be the function defined by g(x) = integral from -1 to x of f(t) dt. Find the x-coordinate of each point of inflection of the graph of g. Justify your answer."},
            {"part": "c", "text": "Find the value of c for which the average value of f over the interval [-5, c] is one-half."},
            {"part": "d", "text": "Assume c > 3. The function h is defined by h(x) = f(x/2). Find h'(6) in terms of c."}
        ]
    },
    {
        "id": "frq-2016-4",
        "seq": 58,
        "title": "Region R bounded by y = e^(-x)",
        "parts": [
            {"part": "a", "text": "Find the area of R in terms of m."},
            {"part": "b", "text": "Region R is revolved around the horizontal line y = 3 to form a solid. Write, but do not evaluate, an expression involving one or more integrals that gives the volume of the solid."},
            {"part": "c", "text": "Find the value of the real number k such that the integral from 0 to infinity of k*e^(-x) dx = 2, or show that no such k exists."}
        ]
    },
    {
        "id": "frq-2016-5",
        "seq": 61,
        "title": "Differential equation with slope field",
        "parts": [
            {"part": "a", "text": "Let y = f(x) be the particular solution to the differential equation with initial condition f(1) = 2. Write an equation for the line tangent to the graph of f at the point (1, 2)."},
            {"part": "b", "text": "On the axes provided, sketch a slope field for the differential equation at the twelve points indicated."},
            {"part": "c", "text": "Find the particular solution y = f(x) to the differential equation with initial condition f(1) = 2."}
        ]
    },
    {
        "id": "frq-2016-6",
        "seq": 64,
        "title": "Maclaurin series for f(x) = 1/(1+x^2)",
        "parts": [
            {"part": "a", "text": "Write the third-degree Taylor polynomial for f about x = 0."},
            {"part": "b", "text": "Use your answer from part (a) to find an approximation for the integral from 0 to 1/2 of f(x) dx."},
            {"part": "c", "text": "The Maclaurin series for f(x) = 1/(1+x^2) converges to f(x) for |x| < 1. Determine whether the approximation found in part (b) is greater than, less than, or equal to the actual value of the integral. Give a reason for your answer."},
            {"part": "d", "text": "Let g be the function defined by g(x) = integral from 0 to x of f(t) dt. Write the third-degree Taylor polynomial for g about x = 0."}
        ]
    }
]

# ===== 2017 FRQ Questions =====
FRQ_2017 = [
    {
        "id": "frq-2017-1",
        "seq": 46,
        "title": "Pottery wheel temperature",
        "parts": [
            {"part": "a", "text": "Use the data in the table to approximate W'(3). Using correct units, interpret the meaning of W'(3) in the context of the problem."},
            {"part": "b", "text": "Use a left Riemann sum with the four subintervals indicated by the table to approximate the integral from 0 to 24 of W(t) dt. Using correct units, interpret the meaning of the integral in the context of the problem."},
            {"part": "c", "text": "The temperature of the water in the pot at time t is modeled by the differentiable function W. Is there a time t, 0 < t < 24, at which W'(t) = 0? Give a reason for your answer."},
            {"part": "d", "text": "The rate at which water is being added to the pot is modeled by R(t) = 2 + sin(t^2/200) liters per hour for 0 <= t <= 24. Is the amount of water in the pot increasing or decreasing at time t = 12 hours? Give a reason for your answer."}
        ]
    },
    {
        "id": "frq-2017-2",
        "seq": 50,
        "title": "Continuous function f with graph",
        "parts": [
            {"part": "a", "text": "Find the average rate of change of f over the interval -4 <= x <= -2."},
            {"part": "b", "text": "Write an equation for the line tangent to the graph of f at x = 1."},
            {"part": "c", "text": "For -4 <= x <= 4, find the value of x at which f has a relative maximum. Justify your answer."},
            {"part": "d", "text": "For -4 <= x <= 4, find the x-coordinates of all points of inflection of f. Give a reason for your answer."}
        ]
    },
    {
        "id": "frq-2017-3",
        "seq": 54,
        "title": "Function f defined by integral",
        "parts": [
            {"part": "a", "text": "Find g(4) and g'(4)."},
            {"part": "b", "text": "On what open intervals is the graph of g concave up? Justify your answer."},
            {"part": "c", "text": "Find the value of x in the interval 0 <= x <= 8 at which g has an absolute minimum. Justify your answer."},
            {"part": "d", "text": "Find the value of x in the interval 0 <= x <= 8 at which the graph of g has a point of inflection. Give a reason for your answer."}
        ]
    },
    {
        "id": "frq-2017-4",
        "seq": 58,
        "title": "Fish population modeled by differential equation",
        "parts": [
            {"part": "a", "text": "Find dP/dt in terms of P. Use this equation to determine whether the population is increasing or decreasing at time t = 3."},
            {"part": "b", "text": "Find the value of P for which the population is neither increasing nor decreasing."},
            {"part": "c", "text": "Use Euler's method, starting at t = 0 with two steps of equal size, to approximate P(2)."},
            {"part": "d", "text": "Find the particular solution P = f(t) to the differential equation with initial condition P(0) = 3."}
        ]
    },
    {
        "id": "frq-2017-5",
        "seq": 62,
        "title": "Region R bounded by curves",
        "parts": [
            {"part": "a", "text": "Find the area of R."},
            {"part": "b", "text": "Region R is the base of a solid. For the solid, each cross section perpendicular to the x-axis is a square. Write, but do not evaluate, an expression involving one or more integrals that gives the volume of the solid."},
            {"part": "c", "text": "The vertical line x = k divides R into two regions with equal areas. Write, but do not evaluate, an equation involving one or more integrals whose solution gives the value of k."}
        ]
    },
    {
        "id": "frq-2017-6",
        "seq": 65,
        "title": "Function f with Taylor polynomial",
        "parts": [
            {"part": "a", "text": "Write the second-degree Taylor polynomial for f about x = 2."},
            {"part": "b", "text": "Let g be the function defined by g(x) = integral from 2 to x of f(t) dt. Write the third-degree Taylor polynomial for g about x = 2."},
            {"part": "c", "text": "Let h be the function defined by h(x) = f(x^2). Write the fourth-degree Taylor polynomial for h about x = 0."},
            {"part": "d", "text": "Write the third-degree Taylor polynomial for the function k defined by k(x) = integral from 0 to x of sin(t^2) dt about x = 0."}
        ]
    }
]

# ===== Mapping =====
FRQ_2016_MAPPING = {
    "frq-2016-1": {"trunkId": "trunk-derivatives", "branchId": "branch-parametric-polar-vectors", "primarySkillId": "skill-parametric-motion", "confidence": "high"},
    "frq-2016-2": {"trunkId": "trunk-integrals", "branchId": "branch-accumulation-riemann", "primarySkillId": "skill-riemann-sums-approximation", "confidence": "high"},
    "frq-2016-3": {"trunkId": "trunk-integrals", "branchId": "branch-fundamental-theorem-modeling", "primarySkillId": "skill-ftc-evaluation", "confidence": "high"},
    "frq-2016-4": {"trunkId": "trunk-integrals", "branchId": "branch-area-volume-rotational", "primarySkillId": "skill-volume-rotation", "confidence": "high"},
    "frq-2016-5": {"trunkId": "trunk-derivatives", "branchId": "branch-differential-equations-slope-field", "primarySkillId": "skill-eulers-method", "confidence": "high"},
    "frq-2016-6": {"trunkId": "trunk-series", "branchId": "branch-taylor-approximation", "primarySkillId": "skill-taylor-series", "confidence": "high"}
}

FRQ_2017_MAPPING = {
    "frq-2017-1": {"trunkId": "trunk-derivatives", "branchId": "branch-derivative-interpretation", "primarySkillId": "skill-rate-of-change-interpretation", "confidence": "high"},
    "frq-2017-2": {"trunkId": "trunk-derivatives", "branchId": "branch-curve-analysis", "primarySkillId": "skill-second-derivative-concavity", "confidence": "high"},
    "frq-2017-3": {"trunkId": "trunk-integrals", "branchId": "branch-fundamental-theorem-modeling", "primarySkillId": "skill-ftc-evaluation", "confidence": "high"},
    "frq-2017-4": {"trunkId": "trunk-derivatives", "branchId": "branch-differential-equations-slope-field", "primarySkillId": "skill-eulers-method", "confidence": "medium"},
    "frq-2017-5": {"trunkId": "trunk-integrals", "branchId": "branch-area-volume-rotational", "primarySkillId": "skill-volume-rotation", "confidence": "high"},
    "frq-2017-6": {"trunkId": "trunk-series", "branchId": "branch-taylor-approximation", "primarySkillId": "skill-taylor-series", "confidence": "high"}
}

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def create_frq_entries(questions, exam_id, source_ref):
    """Create FRQ question entries for each part."""
    entries = []
    for question in questions:
        for part in question['parts']:
            seq = question['seq'] + ord(part['part']) - ord('a')
            entry = {
                "question_id": f"{question['id']}-{part['part']}",
                "exam_id": exam_id,
                "section_id": "frq",
                "sequence_in_exam": seq,
                "question_type": "free_response",
                "question_html": f"<p>{question['title']} - Part ({part['part']})</p><p>{part['text']}</p>",
                "options": [],
                "correct_answer": "",
                "unit": "",
                "metadata": {
                    "source_priority_used": "extracted",
                    "source_refs": [source_ref],
                    "review_flags": [],
                    "parent_question_id": question['id'],
                    "part_label": part['part']
                },
                "subjectiveList": [
                    {
                        "partId": part['part'],
                        "partLabel": part['part'],
                        "prompt": part['text']
                    }
                ]
            }
            entries.append(entry)
    return entries

def process_exam(year, exam_id, frq_questions, frq_mapping, questions_file, mapping_file, source_ref):
    print(f"\n=== Processing {year} ===")
    
    # Load existing files
    questions = load_json(questions_file)
    mapping_data = load_json(mapping_file)
    
    print(f"Existing questions: {len(questions)}")
    
    # Generate FRQ entries
    new_entries = create_frq_entries(frq_questions, exam_id, source_ref)
    print(f"Generated {len(new_entries)} FRQ entries")
    
    # Add to questions.json
    questions.extend(new_entries)
    save_json(questions_file, questions)
    print(f"Saved questions.json: {len(questions)} total entries")
    
    # Update mapping confidence
    updated = 0
    for mapping in mapping_data['mappings']:
        seq = mapping['sequenceInExam']
        for question in frq_questions:
            for part in question['parts']:
                expected_seq = question['seq'] + ord(part['part']) - ord('a')
                if seq == expected_seq:
                    info = frq_mapping[question['id']]
                    mapping['trunkId'] = info['trunkId']
                    mapping['branchId'] = info['branchId']
                    mapping['branchIds'] = [info['branchId']]
                    mapping['primarySkillId'] = info['primarySkillId']
                    mapping['skillIds'] = [info['primarySkillId']]
                    mapping['mappingConfidence'] = info['confidence']
                    mapping['questionId'] = f"{question['id']}-{part['part']}"
                    updated += 1
                    break
    
    save_json(mapping_file, mapping_data)
    print(f"Updated {updated} mapping entries")
    
    # Verification
    questions_final = load_json(questions_file)
    frq_final = [q for q in questions_final if q.get('sequence_in_exam', 0) >= 46]
    print(f"Verification: {len(frq_final)} FRQ entries in questions.json")
    mapping_final = load_json(mapping_file)
    frq_mappings = [m for m in mapping_final['mappings'] if m['sequenceInExam'] >= 46]
    low_conf = [m for m in frq_mappings if m.get('mappingConfidence') == 'low']
    print(f"Verification: {len(frq_mappings)} FRQ mappings, {len(low_conf)} still low confidence")

def main():
    # 2016
    process_exam(
        year="2016",
        exam_id="calc-bc-2016-intl",
        frq_questions=FRQ_2016,
        frq_mapping=FRQ_2016_MAPPING,
        questions_file=os.path.join(PROJECT_PATH, "v2", "data", "calc-bc-2016-intl", "questions.json"),
        mapping_file=os.path.join(PROJECT_PATH, "v2", "data", "calc-bc-2016-intl", "question-branch-mapping.json"),
        source_ref=r"C:\Users\25472\projects\AP-Learning-Web\AP-Learning-Web-01\database\02_staging\reviews\calculus-bc\2016Intl_text.txt"
    )
    
    # 2017
    process_exam(
        year="2017",
        exam_id="calc-bc-2017-intl",
        frq_questions=FRQ_2017,
        frq_mapping=FRQ_2017_MAPPING,
        questions_file=os.path.join(PROJECT_PATH, "v2", "data", "calc-bc-2017-intl", "questions.json"),
        mapping_file=os.path.join(PROJECT_PATH, "v2", "data", "calc-bc-2017-intl", "question-branch-mapping.json"),
        source_ref=r"C:\Users\25472\projects\AP-Learning-Web\AP-Learning-Web-01\database\02_staging\reviews\calculus-bc\2017Intl_text.txt"
    )
    
    print("\n=== Done ===")

if __name__ == "__main__":
    main()
