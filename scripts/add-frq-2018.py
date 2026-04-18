#!/usr/bin/env python3
"""
Script to add FRQ entries to questions.json for 2018 Calc BC exam.
"""
import json
import os
from pathlib import Path

# Paths
PROJECT_PATH = r"C:\Users\25472\projects\AP-Learning-Web"
QUESTIONS_FILE = os.path.join(PROJECT_PATH, "v2", "data", "calc-bc-2018-intl", "questions.json")
MAPPING_FILE = os.path.join(PROJECT_PATH, "v2", "data", "calc-bc-2018-intl", "question-branch-mapping.json")

# FRQ Questions extracted from text (simplified)
FRQ_QUESTIONS = [
    {
        "id": "frq-2018-1",
        "seq": 46,
        "title": "Grain silo problem",
        "parts": [
            {"part": "a", "text": "Using the data in the table, approximate g'(3). Using correct units, interpret the meaning of g'(3) in the context of the problem."},
            {"part": "b", "text": "Write an integral expression that represents the total amount of grain added to the silo from time t = 0 to time t = 8. Use a right Riemann sum with the four subintervals indicated by the data in the table to approximate the integral."},
            {"part": "c", "text": "The grain in the silo is spoiling at a rate modeled by w(t) = 32√(sin(πt/74)), where w(t) is measured in cubic feet per minute for 0 ≤ t ≤ 8. Using the result from part (b), approximate the amount of unspoiled grain remaining in the silo at time t = 8."},
            {"part": "d", "text": "Based on the model in part (c), is the amount of unspoiled grain in the silo increasing or decreasing at time t = 6? Show the work that leads to your answer."}
        ]
    },
    {
        "id": "frq-2018-2",
        "seq": 50,
        "title": "Particle motion problem",
        "parts": [
            {"part": "a", "text": "Find the position of the particle at time t = 2."},
            {"part": "b", "text": "Find the slope of the line tangent to the particle's path at time t = 2."},
            {"part": "c", "text": "Find the speed of the particle at time t = 2. Find the acceleration vector of the particle at time t = 2."},
            {"part": "d", "text": "Consider a rectangle with vertices at points (0, 0), (x(t), 0), (x(t), y(t)), and (0, y(t)) at time t ≥ 0. For 0 ≤ t ≤ 2, at what time t is the perimeter of the rectangle a maximum? Justify your answer."}
        ]
    },
    {
        "id": "frq-2018-3",
        "seq": 54,
        "title": "Function g with graph",
        "parts": [
            {"part": "a", "text": "Find f(7) and f'(7)."},
            {"part": "b", "text": "Find the value of x in the closed interval [-4, 3] at which f attains its maximum value. Justify your answer."},
            {"part": "c", "text": "For each of lim(x→0⁻) g'(x) and lim(x→0⁺) g'(x), find the value or state that it does not exist."},
            {"part": "d", "text": "Find lim(x→-2) (f(x) + 7)/(e^(3x+6) - 1)."}
        ]
    },
    {
        "id": "frq-2018-4",
        "seq": 58,
        "title": "Function g with g'(x) = 2|x|",
        "parts": [
            {"part": "a", "text": "Find expressions for g(x) and g''(x)."},
            {"part": "b", "text": "Find the x-coordinate, if any, of each point of inflection of the graph of y = g(x). Explain your reasoning."},
            {"part": "c", "text": "Let h(x) = ∫₀ˣ √(1 + 4t²) dt. For x ≥ 0, h(x) is the length of the graph of g from t = 0 to t = x. Use Euler's method, starting at x = 0 with two steps of equal size, to approximate h(4)."},
            {"part": "d", "text": "Find the value of ∫(π/2 to π) g'(x) cos(x) dx."}
        ]
    },
    {
        "id": "frq-2018-5",
        "seq": 62,
        "title": "Chemical reaction differential equation",
        "parts": [
            {"part": "a", "text": "Use the line tangent to the graph of y = f(t) at t = 0 to approximate the amount of the substance remaining at time t = 2 seconds."},
            {"part": "b", "text": "Using the given differential equation, determine whether the graph of f could resemble the given graph. Give a reason for your answer."},
            {"part": "c", "text": "Find an expression for y = f(t) by solving the differential equation dy/dt = -0.02y² with the initial condition f(0) = 10."},
            {"part": "d", "text": "Determine whether the amount of the substance is changing at an increasing or a decreasing rate. Explain your reasoning."}
        ]
    },
    {
        "id": "frq-2018-6",
        "seq": 66,
        "title": "Taylor polynomial problem",
        "parts": [
            {"part": "a", "text": "Write the second-degree Taylor polynomial for f about x = 0 and use it to approximate f(0.2)."},
            {"part": "b", "text": "Let g be a function such that g(x) = f(x³). Write the fifth-degree Taylor polynomial for g', the derivative of g, about x = 0."},
            {"part": "c", "text": "Write the third-degree Taylor polynomial for f about x = 1."},
            {"part": "d", "text": "It is known that |f⁴(x)| ≤ 300 for 0 ≤ x ≤ 1.125. The third-degree Taylor polynomial for f about x = 1, found in part (c), is used to approximate f(1.1). Use the Lagrange error bound along with the information about f⁴(x) to find an upper bound on the error of the approximation."}
        ]
    }
]

# Mapping trunk/branch based on FRQ content analysis
FRQ_MAPPING = {
    "frq-2018-1": {  # Grain silo - accumulation/riemann
        "trunkId": "trunk-integrals",
        "branchId": "branch-accumulation-riemann",
        "primarySkillId": "skill-accumulation-context-modeling",
        "confidence": "high"
    },
    "frq-2018-2": {  # Particle motion - derivatives/integrals
        "trunkId": "trunk-derivatives",
        "branchId": "branch-derivative-interpretation",
        "primarySkillId": "skill-rate-of-change-interpretation",
        "confidence": "high"
    },
    "frq-2018-3": {  # Function with graph - integrals/ftc
        "trunkId": "trunk-integrals",
        "branchId": "branch-fundamental-theorem-modeling",
        "primarySkillId": "skill-ftc-evaluation",
        "confidence": "high"
    },
    "frq-2018-4": {  # g'(x) = 2|x| - derivatives/curve analysis
        "trunkId": "trunk-derivatives",
        "branchId": "branch-curve-analysis",
        "primarySkillId": "skill-second-derivative-concavity",
        "confidence": "high"
    },
    "frq-2018-5": {  # Differential equation - derivatives
        "trunkId": "trunk-derivatives",
        "branchId": "branch-derivative-interpretation",
        "primarySkillId": "skill-rate-of-change-interpretation",
        "confidence": "medium"
    },
    "frq-2018-6": {  # Taylor polynomial - series
        "trunkId": "trunk-series",
        "branchId": "branch-taylor-approximation",
        "primarySkillId": "skill-taylor-series",
        "confidence": "high"
    }
}

def load_json(filepath):
    """Load JSON file with UTF-8 encoding."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    """Save JSON file with UTF-8 encoding."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def generate_question_html(question):
    """Generate HTML for FRQ question."""
    html = f"<p>{question['title']}</p>"
    for part in question['parts']:
        html += f"<p>({part['part']}) {part['text']}</p>"
    return html

def create_frq_entry(question, seq_start):
    """Create FRQ question entries for each part."""
    entries = []
    
    # Create one entry per part (a, b, c, d)
    for i, part in enumerate(question['parts']):
        entry = {
            "question_id": f"{question['id']}-{part['part']}",
            "exam_id": "calc-bc-2018-intl",
            "section_id": "frq",
            "sequence_in_exam": seq_start + i,
            "question_type": "free_response",
            "question_html": f"<p>{question['title']} - Part ({part['part']})</p><p>{part['text']}</p>",
            "options": [],
            "correct_answer": "",
            "unit": "",
            "metadata": {
                "source_priority_used": "extracted",
                "source_refs": [
                    "C:\\Users\\25472\\projects\\AP-Learning-Web\\AP-Learning-Web-01\\database\\02_staging\\reviews\\calculus-bc\\2018Intl_text.txt"
                ],
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

def main():
    print("Loading questions.json...")
    questions = load_json(QUESTIONS_FILE)
    
    print("Loading question-branch-mapping.json...")
    mapping_data = load_json(MAPPING_FILE)
    
    # Generate FRQ entries
    print("Generating FRQ entries...")
    new_entries = []
    seq_counter = 46
    
    for question in FRQ_QUESTIONS:
        entries = create_frq_entry(question, seq_counter)
        new_entries.extend(entries)
        seq_counter += len(question['parts'])
    
    print(f"Generated {len(new_entries)} FRQ entries (seq 46-{45 + len(new_entries)})")
    
    # Add FRQ entries to questions.json
    questions.extend(new_entries)
    
    # Save updated questions.json
    print("Saving updated questions.json...")
    save_json(QUESTIONS_FILE, questions)
    
    # Update mapping confidence for FRQ entries
    print("Updating mapping confidence...")
    updated_count = 0
    
    for mapping in mapping_data['mappings']:
        seq = mapping['sequenceInExam']
        if 46 <= seq <= 69:
            # Find corresponding FRQ question
            for question in FRQ_QUESTIONS:
                for part in question['parts']:
                    expected_seq = question['seq'] + ord(part['part']) - ord('a')
                    if seq == expected_seq:
                        mapping_info = FRQ_MAPPING[question['id']]
                        mapping['trunkId'] = mapping_info['trunkId']
                        mapping['branchId'] = mapping_info['branchId']
                        mapping['branchIds'] = [mapping_info['branchId']]
                        mapping['primarySkillId'] = mapping_info['primarySkillId']
                        mapping['skillIds'] = [mapping_info['primarySkillId']]
                        mapping['mappingConfidence'] = mapping_info['confidence']
                        mapping['questionId'] = f"{question['id']}-{part['part']}"
                        updated_count += 1
                        break
    
    print(f"Updated {updated_count} mapping entries")
    
    # Save updated mapping
    print("Saving updated question-branch-mapping.json...")
    save_json(MAPPING_FILE, mapping_data)
    
    print("Done!")
    print(f"Summary:")
    print(f"  - Added {len(new_entries)} FRQ entries to questions.json")
    print(f"  - Updated {updated_count} mapping entries in question-branch-mapping.json")
    print(f"  - FRQ sequences: 46-{45 + len(new_entries)}")

if __name__ == "__main__":
    main()