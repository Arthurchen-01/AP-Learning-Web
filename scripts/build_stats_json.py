#!/usr/bin/env python3
"""Build AP Statistics 2024 NA JSON from extracted OCR text + image verification."""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')

OUT_DIR = r"C:\Users\25472\projects\methods\mokaoai.com\database\01_raw\json\statistics"
os.makedirs(OUT_DIR, exist_ok=True)

exam = {
    "code": 200,
    "msg": "success",
    "enMsg": "success",
    "data": {
        "id": "statistics-2024NA",
        "examName": "AP 统计学 2024年真题北美卷",
        "nickName": None,
        "studentName": None,
        "answerId": None,
        "subjectId": 20,
        "subjectName": "统计学",
        "subjectType": 1,
        "totalQuestion": 6,
        "limitTime": 5400,
        "type": 0,
        "useTime": 0,
        "submitTime": None,
        "currentQuestionIndex": 0,
        "questionList": [
            {
                "type": 2,
                "questionId": 2024001,
                "sort": 1,
                "specialSort": "1",
                "specialSortIndex": None,
                "questionTitle": "Online Fitness Classes - Proportion Inference",
                "questionType": 0,
                "isRight": None,
                "subjectiveQuestionList": [
                    {
                        "type": 2,
                        "questionId": 2024001,
                        "sort": 1,
                        "specialSort": "1",
                        "specialSortIndex": None,
                        "questionTitle": None,
                        "questionType": 0,
                        "isRight": None,
                        "choiceQuestionContent": None,
                        "subjectiveQuestionContent": (
                            "1. A large exercise center has several thousand members from age 18 to 55 years and several thousand members age 56 and older. "
                            "The manager of the center is considering offering online fitness classes. The manager is investigating whether members' opinions "
                            "of taking online fitness classes differ by age. The manager selected a random sample of 170 exercise center members ages 18 to 55 years "
                            "and a second random sample of 230 exercise center members ages 56 years and older. Each sampled member was asked whether they would "
                            "be interested in taking online fitness classes.\n\n"
                            "The manager found that 51 of the 170 sampled members ages 18 to 55 years and that 79 of the 230 sampled members ages 56 years and older "
                            "said they would be interested in taking online fitness classes. At a significance level of α = 0.05, do the data provide convincing "
                            "statistical evidence of a difference in the proportion of all exercise center members ages 18 to 55 years who would be interested "
                            "in taking online fitness classes and the proportion of all exercise center members ages 56 years and older who would be interested "
                            "in taking online fitness classes? Complete the appropriate inference procedure to justify your response."
                        ),
                        "answerContent": None
                    }
                ],
                "choiceQuestionContent": None
            },
            {
                "type": 2,
                "questionId": 2024002,
                "sort": 2,
                "specialSort": "2",
                "specialSortIndex": None,
                "questionTitle": "Bottle Sales - Segmented Bar Graphs and Mosaic Plot",
                "questionType": 0,
                "isRight": None,
                "subjectiveQuestionList": [
                    {
                        "type": 2,
                        "questionId": 2024002,
                        "sort": 1,
                        "specialSort": "2",
                        "specialSortIndex": None,
                        "questionTitle": None,
                        "questionType": 0,
                        "isRight": None,
                        "choiceQuestionContent": None,
                        "subjectiveQuestionContent": (
                            "2. A local elementary school decided to sell bottles printed with the school district's logo as a fund-raiser. The students in the "
                            "elementary school were asked to sell bottles in three different sizes (small, medium, and large). The relative frequencies of the number "
                            "of bottles sold for each size by the elementary school were 0.5 for small bottles, 0.3 for medium bottles, and 0.2 for large bottles.\n\n"
                            "A local middle school also decided to sell bottles as a fund-raiser, using the same three sizes (small, medium, and large). The middle "
                            "school students sold three times the number of bottles that the elementary school students sold. For the middle school students, the "
                            "proportion of bottles sold was equal for all three sizes.\n\n"
                            "(a) Complete the segmented bar graphs representing the relative frequencies of the number of bottles sold for each size by students at each school:\n\n"
                            "[Segmented bar graph for Elementary School: Small bottles (relative frequency = 0.5), Medium bottles (relative frequency = 0.3), Large bottles (relative frequency = 0.2)]\n"
                            "[Segmented bar graph for Middle School: Small bottles (relative frequency = 1/3), Medium bottles (relative frequency = 1/3), Large bottles (relative frequency = 1/3)]\n\n"
                            "(b) An administrator at the elementary school concluded that the elementary school students sold more small bottles than the middle school "
                            "students did. Is the elementary school administrator's conclusion correct? Explain your response.\n\n"
                            "Two high schools are also selling the bottles and are competing to see which one sold more large bottles.\n\n"
                            "(c) A mosaic plot for the distribution of the number of bottles sold by each of the high schools is shown here.\n\n"
                            "[Mosaic plot: Distribution of the Number of Bottles Sold by High School. Shows relative frequency distributions for High School A and High School B with three categories: Small bottles, Medium bottles, Large bottles.]\n\n"
                            "(i) Which of the two high schools sold a greater proportion of large bottles? Justify your answer.\n\n"
                            "(ii) Which of the two high schools sold a greater number of large bottles? Justify your answer."
                        ),
                        "answerContent": None
                    }
                ],
                "choiceQuestionContent": None
            },
            {
                "type": 2,
                "questionId": 2024003,
                "sort": 3,
                "specialSort": "3",
                "specialSortIndex": None,
                "questionTitle": "Car Mileage - Observational Study vs Experiment",
                "questionType": 0,
                "isRight": None,
                "subjectiveQuestionList": [
                    {
                        "type": 2,
                        "questionId": 2024003,
                        "sort": 1,
                        "specialSort": "3",
                        "specialSortIndex": None,
                        "questionTitle": None,
                        "questionType": 0,
                        "isRight": None,
                        "choiceQuestionContent": None,
                        "subjectiveQuestionContent": (
                            "3. A car maker produces four different models of cars: A, B, C, and D. A group of researchers is investigating which model of car has "
                            "the longest distance traveled per gallon of gas (mileage). Higher mileage is considered better than lower mileage. The researchers will "
                            "conduct a study in which they contact several owners of each model of car and ask them to estimate their mileage.\n\n"
                            "(a) Is this an observational study or an experiment? Justify your answer in context.\n\n"
                            "Model D has an autopilot feature, in which the car controls its own motion with human supervision. James owns a Model D car and will "
                            "investigate whether using the autopilot feature results in higher mileage than not using the autopilot. James will drive his car on "
                            "70 different days to and from work, using the same route at the same time each day. James will record the mileage each day.\n\n"
                            "(b) James will use a completely randomized design to conduct his investigation. Describe an appropriate method James could use to randomly "
                            "assign the two treatments, driving using the autopilot feature and driving without using the autopilot feature, to 35 days each.\n\n"
                            "After the investigation was completed, James verified that the conditions for inference were met and conducted a hypothesis test. He "
                            "discovered the mean mileage when using the autopilot feature was significantly higher than the mean mileage when not using the autopilot feature.\n\n"
                            "James is a member of a Model D club with thousands of members who all drive Model D cars. He will give a presentation at a Model D club "
                            "members' meeting later this year and would like to state that the results of his hypothesis test apply to all Model D cars in his club.\n\n"
                            "(c) Another member of the club who is a statistician tells James his findings do not apply to all Model D cars in the club. What change "
                            "would James need to make to his original study to be able to generalize to all Model D cars in the club?"
                        ),
                        "answerContent": None
                    }
                ],
                "choiceQuestionContent": None
            },
            {
                "type": 2,
                "questionId": 2024004,
                "sort": 4,
                "specialSort": "4",
                "specialSortIndex": None,
                "questionTitle": "Geode Game - Geometric Distribution",
                "questionType": 0,
                "isRight": None,
                "subjectiveQuestionList": [
                    {
                        "type": 2,
                        "questionId": 2024004,
                        "sort": 1,
                        "specialSort": "4",
                        "specialSortIndex": None,
                        "questionTitle": None,
                        "questionType": 0,
                        "isRight": None,
                        "choiceQuestionContent": None,
                        "subjectiveQuestionContent": (
                            "4. In an online game, players move through a virtual world collecting geodes, a type of hollow rock. When broken open, these geodes "
                            "contain crystals of different colors that are useful in the game. A red crystal is the most useful crystal in the game. The color of the "
                            "crystal in each geode is independent and the probability that a geode contains a red crystal is 0.08.\n\n"
                            "(a) Sarah, a player, will collect and open geodes until a red crystal is found.\n\n"
                            "(i) Calculate the mean of the distribution of the number of geodes Sarah will open until a red crystal is found. Show your work.\n\n"
                            "(ii) Calculate the standard deviation of the distribution of the number of geodes Sarah will open until a red crystal is found. Show your work.\n\n"
                            "(b) Another player, Conrad, decides to play the game and will stop opening geodes after finding a red crystal or when 4 geodes have been "
                            "opened, whichever comes first. Let Y = the number of geodes Conrad will open. The table shows the partially completed probability distribution "
                            "for the random variable Y:\n\n"
                            "| Number of geodes Conrad will open, y | 1     | 2      | 3 | 4 |\n"
                            "| Probability, P(Y = y)                | 0.08  | 0.0736 | ? | ? |\n\n"
                            "(i) Calculate P(Y = 3). Show your work.\n\n"
                            "(ii) Calculate P(Y = 4). Show your work.\n\n"
                            "(c) Consider the table and your results from part (b).\n\n"
                            "(i) Calculate the mean of the distribution of the number of geodes Conrad will open. Show your work.\n\n"
                            "(ii) Interpret the mean of the distribution of the number of geodes Conrad will open, which was calculated in part (c)(i)."
                        ),
                        "answerContent": None
                    }
                ],
                "choiceQuestionContent": None
            },
            {
                "type": 2,
                "questionId": 2024005,
                "sort": 5,
                "specialSort": "5",
                "specialSortIndex": None,
                "questionTitle": "Baseball Cards - Chi-Square Test of Association",
                "questionType": 0,
                "isRight": None,
                "subjectiveQuestionList": [
                    {
                        "type": 2,
                        "questionId": 2024005,
                        "sort": 1,
                        "specialSort": "5",
                        "specialSortIndex": None,
                        "questionTitle": None,
                        "questionType": 0,
                        "isRight": None,
                        "choiceQuestionContent": None,
                        "subjectiveQuestionContent": (
                            "5. Baseball cards are trading cards that feature data on a player's performance in baseball games. Michelle is at a national baseball "
                            "card collector's convention with approximately 20,000 attendees. She notices that some collectors have both regular cards, which are "
                            "easily obtained, and rare cards, which are harder to obtain. Michelle believes that there is a relationship between the number of months "
                            "a collector has been collecting baseball cards and whether the majority of the cards (cards appearing more often) in their collection are "
                            "regular or rare. She obtains information from a random sample of 500 baseball card collectors at the convention and records how many full "
                            "months they have been collecting baseball cards and whether the majority of the cards in their card collection are regular or rare. Her "
                            "results are displayed in a two-way table:\n\n"
                            "Majority Type of Baseball Cards and Months of Collecting Baseball Cards\n\n"
                            "|                                        | Fewer Than 6 Months | 6-10 Months | 11-15 Months | 16-20 Months | 21 or More Months | Total |\n"
                            "| Has a Majority of Regular Baseball Cards | 80 | 84 | 71 | 76 | 112 | 423 |\n"
                            "| Has a Majority of Rare Baseball Cards    | 11 | 16 |  9 |  6 |  35 |  77 |\n"
                            "| Total                                    | 91 | 100 | 80 | 82 | 147 | 500 |\n\n"
                            "(a) If one collector from the sample is selected at random, what is the probability that the collector has been collecting baseball cards "
                            "for 11 or more months and has a majority of regular baseball cards? Show your work.\n\n"
                            "(b) Given that a randomly selected collector from the sample has been collecting baseball cards for fewer than 6 months, what is the "
                            "probability the collector has a majority of regular baseball cards? Show your work.\n\n"
                            "(c) Michelle believes there is a relationship between the number of months spent collecting baseball cards and which type of card is the "
                            "majority in the collection (regular or rare).\n\n"
                            "(i) Name the hypothesis test Michelle should use to investigate her belief. Do not perform the hypothesis test.\n\n"
                            "(ii) State the appropriate null and alternative hypotheses for the hypothesis test you identified in (c)(i). Do not perform the hypothesis test.\n\n"
                            "(d) After completing the hypothesis test described in part (c), Michelle obtains a p-value of 0.0075. Assuming the conditions for inference "
                            "are met, what conclusion should Michelle make about her belief? Justify your response."
                        ),
                        "answerContent": None
                    }
                ],
                "choiceQuestionContent": None
            },
            {
                "type": 2,
                "questionId": 2024006,
                "sort": 6,
                "specialSort": "6",
                "specialSortIndex": None,
                "questionTitle": "Whistle Prices - t-Interval and Pearson's Skewness",
                "questionType": 0,
                "isRight": None,
                "subjectiveQuestionList": [
                    {
                        "type": 2,
                        "questionId": 2024006,
                        "sort": 1,
                        "specialSort": "6",
                        "specialSortIndex": None,
                        "questionTitle": None,
                        "questionType": 0,
                        "isRight": None,
                        "choiceQuestionContent": None,
                        "subjectiveQuestionContent": (
                            "6. A company sells a certain type of whistle. The price of the whistle varies from store to store. Julio, a statistician at the company, "
                            "wants to estimate the mean price, in dollars ($), of this type of whistle at all stores that sell the whistle.\n\n"
                            "(a) (i) Identify the appropriate inference procedure for Julio to use.\n\n"
                            "(ii) Describe the parameter for the inference procedure you identified in part (a)(i) in context.\n\n"
                            "Julio called the managers of 20 randomly selected stores that sell the whistle and recorded the price of the whistle at each store. "
                            "Following is a dotplot of Julio's data.\n\n"
                            "[Dotplot: Price of the Whistle at 20 Stores. Horizontal axis labeled 'Whistle Price ($)' ranging from 4.2 to 6.6. Dots are concentrated around 4.4-5.6 with one dot near 6.6.]\n\n"
                            "The summary statistics for Julio's data are shown in the following table:\n\n"
                            "Summary Statistics for Julio's Data\n"
                            "| Sample Size | Mean | Standard Deviation | Minimum | Q1   | Median | Q3    | Maximum |\n"
                            "| 20          | 5.12 | 0.743              | 4.25    | 4.51 | 4.885  | 5.475 | 6.58    |\n\n"
                            "(b) Julio wants to examine some characteristics of the distribution of the sample of whistle prices.\n\n"
                            "(i) Describe the shape of the distribution of the sample of whistle prices. Justify your response using appropriate values from the summary statistics table.\n\n"
                            "(ii) Using the 1.5 × IQR rule, determine whether there are any outliers in the sample of whistle prices. Justify your response.\n\n"
                            "(c) It can often be difficult to determine whether the distribution of sample data is skewed by looking at a graph of the data and the summary "
                            "statistics, particularly when the sample size is small. Thus, statisticians sometimes measure how skewed a data set is. One such measure is "
                            "Pearson's coefficient of skewness, which is calculated using the following formula:\n\n"
                            "Pearson's Coefficient of Skewness = 3(x̄ − m) / S\n\n"
                            "In the formula, x̄ is the sample mean, m is the sample median, and S is the sample standard deviation.\n\n"
                            "(i) Calculate Pearson's coefficient of skewness for Julio's sample of 20 whistle prices. Show your work.\n\n"
                            "(ii) The following graph shows conclusions that can be made about the shape of the distribution of sample data based on Pearson's coefficient "
                            "of skewness and sample size.\n\n"
                            "[Graph: Conclusion from Pearson's Coefficient of Skewness. Vertical axis: Sample Size (0-100). Horizontal axis: Pearson's Coefficient of Skewness (-1.20 to 1.20). "
                            "Three regions: 'The distribution of sample data is considered strongly skewed' (left), 'The distribution of sample data is considered approximately symmetric' (center), "
                            "'The distribution of sample data is considered strongly skewed' (right).]\n\n"
                            "Indicate the value of the Pearson's coefficient of skewness you calculated in part (c)(i) for the appropriate sample size by marking it with "
                            "an \"X\" on the preceding graph.\n\n"
                            "(d) Consider your work in part (c):\n\n"
                            "(i) What should you conclude about the shape of the distribution of the sample of whistle prices? Justify your response.\n\n"
                            "Julio's inference procedure in part (a)(i) needs one of the following requirements to be satisfied to verify the normality condition:\n"
                            "- The sample size is greater than or equal to 30.\n"
                            "- If the sample size is less than 30, the distribution of the sample data is not strongly skewed and does not have outliers.\n\n"
                            "(ii) Using your response to (d)(i) and the preceding requirements, is the normality condition satisfied for Julio's data? Explain your response."
                        ),
                        "answerContent": None
                    }
                ],
                "choiceQuestionContent": None
            }
        ]
    }
}

out_path = os.path.join(OUT_DIR, "2024NA.json")
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(exam, f, ensure_ascii=False, indent=2)

# Validate
with open(out_path, 'r', encoding='utf-8') as f:
    validated = json.load(f)

print(f"✅ Saved to {out_path}")
print(f"   Total questions: {len(validated['data']['questionList'])}")
print(f"   File size: {os.path.getsize(out_path):,} bytes")
print(f"   Exam ID: {validated['data']['id']}")
print(f"   Subject: {validated['data']['subjectName']}")
print(f"   Title: {validated['data']['examName']}")
for q in validated['data']['questionList']:
    content_len = len(q['subjectiveQuestionList'][0]['subjectiveQuestionContent'])
    print(f"   Q{q['sort']}: {q['questionTitle']} ({content_len} chars)")
