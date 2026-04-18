import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "data" / "contracts" / "ap-calculus-bc-trunk-contract.json"
QUESTIONS_PATH = ROOT / "data" / "calc-bc-2018-intl" / "questions.json"
MAPPING_PATH = ROOT / "data" / "calc-bc-2018-intl" / "question-branch-mapping.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main() -> int:
    contract = load_json(CONTRACT_PATH)
    questions = load_json(QUESTIONS_PATH)
    mapping = load_json(MAPPING_PATH)

    question_ids = {item["question_id"] for item in questions}
    trunks = {item["id"]: set(item["branchIds"]) for item in contract["trunks"]}
    branches = {
        item["id"]: {"trunkId": item["trunkId"], "skillNodeIds": set(item["skillNodeIds"])}
        for item in contract["branches"]
    }
    skills = {item["id"]: item["branchId"] for item in contract["skillNodes"]}

    errors = []
    branch_counts = Counter()

    for item in mapping["mappings"]:
        question_id = item["questionId"]
        trunk_id = item["trunkId"]
        branch_id = item["branchId"]
        primary_skill_id = item["primarySkillId"]

        if question_id not in question_ids:
            errors.append(f"unknown questionId: {question_id}")

        if trunk_id not in trunks:
            errors.append(f"unknown trunkId: {trunk_id} ({question_id})")
            continue

        if branch_id not in branches:
            errors.append(f"unknown branchId: {branch_id} ({question_id})")
            continue

        if branches[branch_id]["trunkId"] != trunk_id:
            errors.append(f"branch/trunk mismatch: {question_id}")

        if branch_id not in item["branchIds"]:
            errors.append(f"primary branch missing from branchIds: {question_id}")

        for branch_ref in item["branchIds"]:
            if branch_ref not in branches:
                errors.append(f"unknown branchIds ref: {branch_ref} ({question_id})")
            elif branches[branch_ref]["trunkId"] != trunk_id:
                errors.append(f"branchIds trunk mismatch: {branch_ref} ({question_id})")

        if primary_skill_id not in skills:
            errors.append(f"unknown primarySkillId: {primary_skill_id} ({question_id})")
        elif skills[primary_skill_id] != branch_id:
            errors.append(f"primary skill/branch mismatch: {question_id}")

        for skill_id in item["skillIds"]:
            if skill_id not in skills:
                errors.append(f"unknown skillId: {skill_id} ({question_id})")
            elif skills[skill_id] not in item["branchIds"]:
                errors.append(f"skill branch mismatch: {skill_id} ({question_id})")

        branch_counts[branch_id] += 1

    sample_branches = {branch_id: count for branch_id, count in branch_counts.items() if 3 <= count <= 5}

    if not any(count > 1 for count in branch_counts.values()):
        errors.append("no shared branchId across mapped questions")

    if not sample_branches:
        errors.append("no branch with 3-5 mapped questions")

    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("VALIDATION PASSED")
    print(f"mapped questions: {len(mapping['mappings'])}")
    print("branch counts:")
    for branch_id, count in sorted(branch_counts.items()):
        print(f"- {branch_id}: {count}")
    print("3-5 question sample branches:")
    for branch_id, count in sorted(sample_branches.items()):
        print(f"- {branch_id}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
