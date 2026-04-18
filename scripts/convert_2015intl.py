# -*- coding: utf-8 -*-
"""Convert 2015 Intl CALC source data to v2 format."""
import json, os

PROJECT = r"C:\Users\25472\projects\AP-Learning-Web"
SRC = os.path.join(PROJECT, "mock-data", "ap-exam-2015Intl_CALC.json")
OUT_DIR = os.path.join(PROJECT, "v2", "data", "calc-bc-2015-intl")

with open(SRC, encoding="utf-8") as f:
    raw = json.load(f)

# --- exam_packet.json ---
exam_packet = {
    "examId": "calc-bc-2015-intl",
    "exam_id": "calc-bc-2015-intl",
    "exam_title": "AP Calculus BC 2015 Intl",
    "subjectName": "微积分BC",
    "subject": "微积分BC",
    "subject_display": "Calculus BC",
    "year": "2015",
    "yearLabel": "2015年国际卷",
    "description": "AP Calculus BC 2015 Intl",
    "answerKeyAvailable": False,
    "scoring": {
        "answerKeyAvailable": False,
        "apBands": [],
        "note": "Scoring unavailable until answer keys are imported."
    },
    "sections": []
}

# --- questions.json ---
questions_out = []

# --- question-branch-mapping.json ---
mapping = {
    "version": "1.0.0",
    "subjectSlug": "ap_calculus_bc",
    "examId": "calc-bc-2015-intl",
    "mainModelId": "calc-bc-breakthrough-core",
    "modelType": "single-route",
    "breakthroughVersion": "2026-04-18-v1",
    "mappingSource": "manual-builder-v1",
    "coverage": {
        "mappedQuestionCount": 0,
        "totalQuestionCount": 0,
        "mappedSequenceRanges": []
    },
    "mappings": []
}

# Trunk/branch/skill cycling for MCQ (reuse existing strategy)
TRUNK_CYCLE = [
    ("trunk-limits", "branch-limit-evaluation", "skill-limit-one-sided"),
    ("trunk-derivatives", "branch-derivative-rules", "skill-derivative-basic-rules"),
    ("trunk-integrals", "branch-antiderivative-techniques", "skill-antiderivative-basic-forms"),
    ("trunk-series", "branch-sequence-series-convergence", "skill-convergence-classification"),
    ("trunk-limits", "branch-limit-continuity-analysis", "skill-continuity-classification"),
    ("trunk-derivatives", "branch-derivative-interpretation", "skill-rate-of-change-interpretation"),
    ("trunk-integrals", "branch-accumulation-riemann", "skill-riemann-sum-setup"),
    ("trunk-series", "branch-power-series-representation", "skill-power-series-identification"),
    ("trunk-limits", "branch-limit-evaluation", "skill-limit-algebraic-simplification"),
    ("trunk-derivatives", "branch-curve-analysis", "skill-first-derivative-sign"),
    ("trunk-integrals", "branch-fundamental-theorem-modeling", "skill-ftc-evaluation"),
    ("trunk-series", "branch-taylor-approximation", "skill-taylor-polynomial-construction"),
]

seq_counter = 0

for section in raw.get("sections", []):
    section_id = section.get("id", "section-mcq")
    is_mcq = "mcq" in section_id.lower() or "multiple" in section.get("partTitle", "").lower()
    
    exam_packet_section = {
        "id": section_id,
        "title": section.get("title", "Section 1"),
        "partTitle": section.get("partTitle", "Multiple Choice"),
        "limitMinutes": section.get("limitMinutes", 60),
        "directions": section.get("directions", ""),
        "questions": []
    }
    
    for q in section.get("questions", []):
        seq_counter += 1
        q_id = str(q.get("id", seq_counter))
        
        # exam_packet question (same format as source)
        exam_packet_section["questions"].append(q)
        
        # questions.json entry
        q_entry = {
            "question_id": q_id,
            "exam_id": "calc-bc-2015-intl",
            "section_id": section_id,
            "sequence_in_exam": seq_counter,
            "question_type": "single_choice" if q.get("type") == "single" else ("multiple_select" if q.get("type") == "multi" else "free_response"),
            "question_html": q.get("prompt", ""),
            "options": [
                {"key": opt.get("key", ""), "html": opt.get("content", "")}
                for opt in q.get("options", [])
            ],
            "correct_answer": q.get("answer", ""),
            "unit": ""
        }
        questions_out.append(q_entry)
        
        # mapping entry (MCQ only)
        if is_mcq and q.get("type") in ("single", "multi"):
            trunk, branch, skill = TRUNK_CYCLE[(seq_counter - 1) % len(TRUNK_CYCLE)]
            mapping["mappings"].append({
                "questionId": q_id,
                "sequenceInExam": seq_counter,
                "trunkId": trunk,
                "branchId": branch,
                "branchIds": [branch],
                "primarySkillId": skill,
                "skillIds": [skill],
                "mappingConfidence": "low"
            })
    
    exam_packet["sections"].append(exam_packet_section)

mcq_count = len(mapping["mappings"])
mapping["coverage"]["mappedQuestionCount"] = mcq_count
mapping["coverage"]["totalQuestionCount"] = seq_counter
mapping["coverage"]["mappedSequenceRanges"] = [f"1-{mcq_count}"] if mcq_count > 0 else []

# Write files
os.makedirs(OUT_DIR, exist_ok=True)

with open(os.path.join(OUT_DIR, "exam_packet.json"), "w", encoding="utf-8") as f:
    json.dump(exam_packet, f, ensure_ascii=False, indent=2)

with open(os.path.join(OUT_DIR, "questions.json"), "w", encoding="utf-8") as f:
    json.dump(questions_out, f, ensure_ascii=False, indent=2)

with open(os.path.join(OUT_DIR, "question-branch-mapping.json"), "w", encoding="utf-8") as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)

print(f"Done. MCQ mapped: {mcq_count}, total questions: {seq_counter}")
