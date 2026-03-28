import json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

exam = {
    "examId": "microeconomics-2024NASet1",
    "title": "AP \u5fae\u89c2\u7ecf\u6d4e 2024\u5e74\u771f\u9898\u5317\u7f8e\u5377Set1",
    "subjectName": "\u5fae\u89c2\u7ecf\u6d4e",
    "yearLabel": "2024",
    "description": "Practice mode only.",
    "answerKeyAvailable": False,
    "scoring": {
        "answerKeyAvailable": False,
        "apBands": [],
        "note": "Scoring unavailable until answer keys are imported."
    },
    "sections": [
        {
            "id": "section-frq",
            "title": "Section II - Free Response",
            "partTitle": "Part FRQ - Free Response Questions",
            "limitMinutes": 60,
            "directions": (
                'You are advised to spend the first 10 minutes reading all of the questions and planning your answers. '
                'You will then have 50 minutes to answer all three of the following questions. You may begin writing your '
                'responses before the reading period is over. It is suggested that you spend approximately half your time '
                'on the first question and divide the remaining time equally between the next two questions. Include correctly '
                'labeled diagrams, if useful or required, in explaining your answers. A correctly labeled diagram must have '
                'all axes and curves clearly labeled and must show directional changes. If the question prompts you to '
                '\u201cCalculate,\u201d you must show how you arrived at your final answer. Use a pen with black or dark blue ink.'
            ),
            "questions": [
                {
                    "id": "1",
                    "type": "frq",
                    "prompt": (
                        "Soja Farm is a typical profit-maximizing firm that produces and sells soybeans in a constant-cost, "
                        "perfectly competitive market that is in long-run equilibrium. The market equilibrium price of soybeans "
                        "is $14 per bushel."
                    ),
                    "parts": [
                        {
                            "id": "1a", "label": "(a)",
                            "prompt": "Draw correctly labeled side-by-side graphs for the soybean market and for Soja Farm, and show each of the following.",
                            "subparts": [
                                {"id": "1a-i", "label": "(i)", "prompt": "The market equilibrium price and quantity, labeled $14 and QM, respectively"},
                                {"id": "1a-ii", "label": "(ii)", "prompt": "Soja Farm\u2019s profit-maximizing price and quantity, labeled PF and QF, respectively"},
                                {"id": "1a-iii", "label": "(iii)", "prompt": "Soja Farm\u2019s average total cost curve consistent with a long-run equilibrium, labeled ATC"},
                            ]
                        },
                        {
                            "id": "1b", "label": "(b)",
                            "prompt": "If Soja Farm is the only firm in the market that chooses to increase its price of soybeans to $15 per bushel, will Soja Farm\u2019s total revenue increase by $1, remain the same, or decrease to $0? Explain.",
                        },
                        {
                            "id": "1c", "label": "(c)",
                            "prompt": "Soybeans are used as an input in the production of tofu. Tofu now becomes a more popular food option among consumers. On your graphs in part (a), show the short-run effect of the increased popularity of tofu on each of the following.",
                            "subparts": [
                                {"id": "1c-i", "label": "(i)", "prompt": "The new market equilibrium price and quantity of soybeans, labeled P2 and Q2, respectively"},
                                {"id": "1c-ii", "label": "(ii)", "prompt": "Soja Farm\u2019s new profit-maximizing quantity, labeled Q*"},
                            ]
                        },
                        {
                            "id": "1d", "label": "(d)",
                            "prompt": "Given the increase in popularity of tofu in part (c), what will happen to the number of firms in the soybean market in the long run? Explain.",
                        },
                        {
                            "id": "1e", "label": "(e)",
                            "prompt": "Suppose a 25% increase in the market price of quinoa causes a 5% decrease in the quantity demanded of quinoa and a 10% increase in the quantity demanded for tofu.",
                            "subparts": [
                                {"id": "1e-i", "label": "(i)", "prompt": "Is the demand for quinoa elastic, inelastic, or unit elastic? Explain using numbers."},
                                {"id": "1e-ii", "label": "(ii)", "prompt": "Calculate the cross-price elasticity of demand between quinoa and tofu. Show your work."},
                            ]
                        },
                    ],
                    "answer": None,
                    "explanation": "Answer key not available yet for this imported exam.",
                },
                {
                    "id": "2",
                    "type": "frq",
                    "prompt": "Good X is produced and sold in a perfectly competitive market. The provided graph shows the market for Good X.",
                    "parts": [
                        {"id": "2a", "label": "(a)", "prompt": "Identify the market equilibrium price and quantity."},
                        {"id": "2b", "label": "(b)", "prompt": "Calculate the deadweight loss at the market equilibrium. Show your work."},
                        {
                            "id": "2c", "label": "(c)",
                            "prompt": "Suppose the government wants to eliminate the deadweight loss in the market for Good X.",
                            "subparts": [
                                {"id": "2c-i", "label": "(i)", "prompt": "Which of the following will achieve the government\u2019s objective: a per-unit tax on consumers or a per-unit subsidy to consumers? Explain."},
                                {"id": "2c-ii", "label": "(ii)", "prompt": "What is the dollar value of the per-unit tax or per-unit subsidy identified in part (c)(i)?"},
                            ]
                        },
                        {"id": "2d", "label": "(d)", "prompt": "Suppose instead the government imposes a price ceiling of $10. Will the price ceiling achieve the socially optimal quantity of Good X? Explain."},
                    ],
                    "answer": None,
                    "explanation": "Answer key not available yet for this imported exam.",
                },
                {
                    "id": "3",
                    "type": "frq",
                    "prompt": (
                        "Nice Ride and Field Cruiser are the only two producers of vehicles. Nice Ride is deciding whether to "
                        "improve Safety or Comfort. Field Cruiser is deciding whether to improve Reliability or Power. The payoff "
                        "matrix shows the payoffs for each combination of strategies. The first entry in each cell shows Nice Ride\u2019s "
                        "profit, and the second entry shows Field Cruiser\u2019s profit. Each firm independently and simultaneously chooses "
                        "its strategy. Assume the two firms know all the information in the matrix and do not cooperate."
                    ),
                    "parts": [
                        {"id": "3a", "label": "(a)", "prompt": "What is Field Cruiser\u2019s most profitable strategy if Nice Ride chooses to improve Safety?"},
                        {"id": "3b", "label": "(b)", "prompt": "Does Nice Ride have a dominant strategy? Explain using numbers from the payoff matrix."},
                        {"id": "3c", "label": "(c)", "prompt": "Is Nice Ride choosing to improve Safety and Field Cruiser choosing to improve Power a Nash equilibrium? Explain using numbers from the payoff matrix."},
                        {"id": "3d", "label": "(d)", "prompt": "Suppose Nice Ride and Field Cruiser decide to merge to maximize combined profits and choose to keep producing both Nice Ride and Field Cruiser vehicles. Assuming the values in the payoff matrix do not change, what would be the new firm\u2019s total profit?"},
                        {"id": "3e", "label": "(e)", "prompt": "Suppose instead that a change in fuel prices reduces the profitability of choosing to improve Power by $10 million for Field Cruiser. Identify each firm\u2019s profit at the Nash equilibrium."},
                    ],
                    "answer": None,
                    "explanation": "Answer key not available yet for this imported exam.",
                },
            ],
        }
    ],
}

out = r'C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json\microeconomics\2024NASet1.json'
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, 'w', encoding='utf-8') as f:
    json.dump(exam, f, ensure_ascii=False, indent=2)

# Validate
with open(out, 'r', encoding='utf-8') as f:
    data = json.load(f)

sec = data["sections"][0]
print("OK - wrote", out)
print("Questions:", len(sec["questions"]))
for q in sec["questions"]:
    p = len(q["parts"])
    sp = sum(len(x.get("subparts", [])) for x in q["parts"])
    print("  Q%s: %d parts, %d subparts" % (q["id"], p, sp))
