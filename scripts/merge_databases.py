#!/usr/bin/env python3
"""
Merge exam data from both local and web repos into database_merged/.
Each file is labeled with its source (local/web) and organized by subject.
"""
import json
import os
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
LOCAL_MOCK = ROOT / "mock-data"
WEB_MOCK = ROOT / "AP-Learning-Web-01" / "mock-data"
OUT = ROOT / "database_merged"

# Subject folder mapping
SUBJECT_SUFFIXES = {
    "_CALC": "calculus_bc",
    "_MECH": "physics_c_mechanics",
    "_EM": "physics_c_em",
    "_CSA": "csa",
}

SUBJECT_FOLDERS = {
    "calculus_bc": "calculus_bc",
    "physics_c_mechanics": "physics_c_mechanics",
    "physics_c_em": "physics_c_em",
    "computer_science_a": "csa",
    "macroeconomics": "macroeconomics",
    "microeconomics": "microeconomics",
    "statistics": "statistics",
    "psychology": "psychology",
}

def detect_subject_from_filename(fname):
    """Detect subject from filename suffix."""
    for suffix, subject in SUBJECT_SUFFIXES.items():
        if suffix in fname:
            return subject
    # Flat calc files (no suffix, in our local mock-data)
    if fname.startswith("ap-exam-20") and "_CALC" not in fname and "_MECH" not in fname and "_EM" not in fname and "_CSA" not in fname:
        return "calculus_bc"
    return None

def get_exam_id_from_data(fpath):
    """Try to get the real exam title from the JSON data."""
    try:
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)
        title = data.get("title", "")
        exam_id = data.get("examId", "")
        subject = data.get("subjectName", "")
        year = data.get("yearLabel", "")
        return title or exam_id, subject, year
    except:
        return "", "", ""

def merge():
    # Track what we've seen to detect conflicts
    seen = {}  # (subject, base_name) -> source

    # 1. Process LOCAL files
    print("=== Processing LOCAL files ===")
    for fpath in sorted(LOCAL_MOCK.glob("ap-exam-*.json")):
        fname = fpath.name
        if fname == "exam-catalog.json":
            continue
        subject = detect_subject_from_filename(fname)
        if not subject:
            # Try to detect from data
            title, subj_name, _ = get_exam_id_from_data(fpath)
            if "calculus" in subj_name.lower() or "微积分" in subj_name:
                subject = "calculus_bc"
            elif "mechanic" in subj_name.lower() or "力学" in subj_name:
                subject = "physics_c_mechanics"
            elif "电磁" in subj_name or "em" in subj_name.lower():
                subject = "physics_c_em"
            elif "csa" in subj_name.lower() or "计算机" in subj_name:
                subject = "csa"
            else:
                subject = "unknown"

        base = fname.replace("ap-exam-", "")
        key = (subject, base)

        if key in seen:
            # Conflict: both have this file
            out_name = f"local__{base}"
        else:
            out_name = f"local__{base}"
            seen[key] = "local"

        dest = OUT / subject / out_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fpath, dest)
        print(f"  {subject}/{out_name}")

    # 2. Process WEB files
    print("\n=== Processing WEB files ===")
    for web_subject, local_subject in SUBJECT_FOLDERS.items():
        web_dir = WEB_MOCK / web_subject
        if not web_dir.exists():
            continue
        for fpath in sorted(web_dir.glob("ap-exam-*.json")):
            base = fpath.name.replace("ap-exam-", "")
            key = (local_subject, base)

            if key in seen:
                out_name = f"web__{base}"
            else:
                out_name = f"web__{base}"
                seen[key] = "web"

            dest = OUT / local_subject / out_name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fpath, dest)
            print(f"  {local_subject}/{out_name}")

    # 3. Summary
    print("\n=== Summary ===")
    for subject_dir in sorted(OUT.iterdir()):
        if subject_dir.is_dir():
            files = list(subject_dir.glob("*.json"))
            local_count = sum(1 for f in files if f.name.startswith("local__"))
            web_count = sum(1 for f in files if f.name.startswith("web__"))
            print(f"  {subject_dir.name}: {len(files)} files (local={local_count}, web={web_count})")

if __name__ == "__main__":
    merge()
