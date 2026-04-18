"""
Merge FRQ sub-parts from frq-*.json into main exam data.
Match by question number and subject.
"""
import json, os, sys, re

sys.stdout.reconfigure(encoding="utf-8")

MOCK_DIR = "mock-data"

# Load all FRQ part data
frq_data = {}
for f in os.listdir(MOCK_DIR):
    if f.startswith("frq-") and f.endswith(".json"):
        exam_id = f.replace("frq-", "").replace(".json", "")
        with open(f"{MOCK_DIR}/{f}", encoding="utf-8") as fh:
            frq_data[exam_id] = json.load(fh)

print(f"Loaded {len(frq_data)} FRQ files")

# For each main exam file, try to match FRQ sub-parts
merged_count = 0
for fname in sorted(os.listdir(MOCK_DIR)):
    if not fname.startswith("ap-exam-") or not fname.endswith(".json"):
        continue
    if "exam-catalog" in fname:
        continue

    exam_id = fname.replace("ap-exam-", "").replace(".json", "")

    # Check if we have FRQ data for this exam
    if exam_id not in frq_data:
        continue

    frq = frq_data[exam_id]

    try:
        with open(f"{MOCK_DIR}/{fname}", encoding="utf-8") as fh:
            main = json.load(fh)
    except:
        continue

    # Find FRQ questions in main exam
    changes = 0
    frq_index = 0  # Track position of FRQ questions
    for section in main.get("sections", []):
        for q in section.get("questions", []):
            if q.get("type") != "frq":
                continue

            # Match by position (FRQ questions appear in order)
            frq_questions = frq.get("questions", [])
            if frq_index < len(frq_questions):
                frq_q = frq_questions[frq_index]
                # Merge sub-parts
                if frq_q.get("parts"):
                    q["_frqParts"] = frq_q.get("parts", [])
                    q["_frqImages"] = frq_q.get("images", [])
                    # Update prompt with full stem if better
                    stem = frq_q.get("stem", "")
                    if stem and len(stem) > 10:
                        existing = q.get("prompt", "")
                        if len(stem) > len(existing):
                            q["prompt"] = stem
                    changes += 1
                    merged_count += 1
                frq_index += 1

    if changes > 0:
        with open(f"{MOCK_DIR}/{fname}", "w", encoding="utf-8") as fh:
            json.dump(main, fh, ensure_ascii=False, indent=2)
        print(f"  {fname}: {changes} FRQ sub-parts merged")

print(f"\nTotal merged: {merged_count}")
