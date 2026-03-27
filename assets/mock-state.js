window.MOKAO_MOCK_DATA = {
  masteryStates: {
    crown: {
      label: "皇冠",
      short: "C",
      tone: "tone-crown",
      fill: "fill-full"
    },
    full: {
      label: "满格",
      short: "F",
      tone: "tone-strong",
      fill: "fill-full"
    },
    two_thirds: {
      label: "三分之二",
      short: "2/3",
      tone: "tone-warm",
      fill: "fill-two-thirds"
    },
    one_third: {
      label: "三分之一",
      short: "1/3",
      tone: "tone-muted",
      fill: "fill-one-third"
    }
  },
  user: {
    id: "user-demo-01",
    name: "Olivia Chen",
    avatarText: "OC",
    bio: "目标是在 2026 AP 季把 Calculus BC、Statistics、Microeconomics 三门稳定冲到 5 分。",
    goal: "每周至少完成 3 次训练，1 次 FRQ 深度复盘，考试前两个月把薄弱单元全部补到两格以上。",
    examSubjects: ["calculus-bc", "statistics", "microeconomics"],
    settings: [
      "每日提醒：19:30",
      "目标院校方向：Economics / Data",
      "偏好训练：先知识点后 FRQ",
      "AI 生成题：开启"
    ]
  },
  training: {
    subjects: [
      {
        id: "calculus-bc",
        label: "AP Calculus BC",
        summary: "把知识点、MCQ 和 FRQ 三条路径分开训练。",
        recommendation: "先补 related rates，再回到 series FRQ。",
        paths: [
          {
            id: "knowledge",
            title: "知识点训练",
            description: "按单点知识刷题，适合补基础和查缺补漏。",
            emphasis: "教辅题 / AI 拆点题 / 练习册",
            stat: "18 组题组"
          },
          {
            id: "mcq",
            title: "MCQ 训练",
            description: "练选择题方法、节奏和判断速度。",
            emphasis: "真题 MCQ / 难度分层 / 限时",
            stat: "42 道可刷"
          },
          {
            id: "frq",
            title: "FRQ 训练",
            description: "练推理、结构和论证表达。",
            emphasis: "rubric / 高分结构 / AI 摘要",
            stat: "9 道 FRQ"
          }
        ],
        items: {
          knowledge: [
            {
              title: "Related Rates 基础组",
              source: "Workbook",
              difficulty: "基础",
              unit: "Unit 4",
              tags: ["related rates", "implicit differentiation"],
              progress: "已完成 8 / 10",
              reason: "你最近在变量关系式建立上重复出错。"
            },
            {
              title: "Series Convergence Drill",
              source: "AI Generated",
              difficulty: "进阶",
              unit: "Unit 10",
              tags: ["series", "ratio test"],
              progress: "已完成 3 / 8",
              reason: "针对最近 FRQ 的判别链条不稳定问题。"
            }
          ],
          mcq: [
            {
              title: "2019 BC MCQ Sprint",
              source: "Past Exam",
              difficulty: "中等",
              unit: "Mixed",
              tags: ["time pressure", "calculator"],
              progress: "限时 35 分钟",
              reason: "适合练考试节奏。"
            },
            {
              title: "Derivative Strategy Pack",
              source: "Past Exam",
              difficulty: "基础",
              unit: "Unit 3",
              tags: ["derivative", "graph reading"],
              progress: "已做 12 / 20",
              reason: "用于稳定基础正确率。"
            }
          ],
          frq: [
            {
              title: "FRQ 6: Series Justification",
              source: "Past Exam",
              difficulty: "高",
              unit: "Unit 10",
              tags: ["justification", "error bound"],
              progress: "已评分 4 / 9",
              reason: "推荐作为本周重点 FRQ。"
            }
          ]
        }
      },
      {
        id: "statistics",
        label: "AP Statistics",
        summary: "按知识点、MCQ、FRQ 三条路径拆开统计训练。",
        recommendation: "Sampling distributions 和 inference wording 是当前重点。",
        paths: [
          {
            id: "knowledge",
            title: "知识点训练",
            description: "围绕单个统计概念重复刷题。",
            emphasis: "教辅题 / 小练习 / AI 题组",
            stat: "16 组题组"
          },
          {
            id: "mcq",
            title: "MCQ 训练",
            description: "练统计题型判断、条件识别和节奏。",
            emphasis: "真题 MCQ / 条件识别 / 时间控制",
            stat: "29 道可刷"
          },
          {
            id: "frq",
            title: "FRQ 训练",
            description: "练统计语言、条件说明和结论写法。",
            emphasis: "官方 rubric / 回答结构 / AI 建议",
            stat: "8 道 FRQ"
          }
        ],
        items: {
          knowledge: [
            {
              title: "Sampling Distribution Warmup",
              source: "5 Steps to a 5",
              difficulty: "中等",
              unit: "Unit 5",
              tags: ["sampling", "mean", "spread"],
              progress: "已完成 4 / 9",
              reason: "针对最近混淆的抽样分布概念。"
            }
          ],
          mcq: [
            {
              title: "Inference MCQ Speed Set",
              source: "Past Exam",
              difficulty: "高",
              unit: "Unit 7",
              tags: ["inference", "conditions"],
              progress: "未开始",
              reason: "训练文字判断和套路。"
            }
          ],
          frq: [
            {
              title: "Investigative Task Review",
              source: "Official-style Mock",
              difficulty: "高",
              unit: "Mixed",
              tags: ["investigative task", "design"],
              progress: "等待作答",
              reason: "强化综合表达。"
            }
          ]
        }
      },
      {
        id: "microeconomics",
        label: "AP Microeconomics",
        summary: "针对概念理解、图像判断和结构化 FRQ 作答拆分训练。",
        recommendation: "Elasticity 和 market failure 是当前最值得优先补的板块。",
        paths: [
          {
            id: "knowledge",
            title: "知识点训练",
            description: "围绕图像、概念、定义做查缺补漏。",
            emphasis: "教材题 / 图像题 / AI 拆点题",
            stat: "13 组题组"
          },
          {
            id: "mcq",
            title: "MCQ 训练",
            description: "强化图像读取、推理和节奏。",
            emphasis: "真题 MCQ / 图像判断 / 限时",
            stat: "31 道可刷"
          },
          {
            id: "frq",
            title: "FRQ 训练",
            description: "练因果链条和经济学表达。",
            emphasis: "官方得分点 / 作答模板 / AI 摘要",
            stat: "7 道 FRQ"
          }
        ],
        items: {
          knowledge: [
            {
              title: "Elasticity Core Drill",
              source: "Workbook",
              difficulty: "基础",
              unit: "Unit 2",
              tags: ["elasticity", "graphs"],
              progress: "已完成 5 / 8",
              reason: "最近错题集中在弹性与总收益变化。"
            }
          ],
          mcq: [
            {
              title: "Market Structures Timed Set",
              source: "Past Exam",
              difficulty: "中等",
              unit: "Unit 4",
              tags: ["market structure", "marginal analysis"],
              progress: "限时 22 分钟",
              reason: "训练题感和图像判断。"
            }
          ],
          frq: [
            {
              title: "Externalities FRQ",
              source: "Official-style Mock",
              difficulty: "高",
              unit: "Unit 6",
              tags: ["market failure", "policy"],
              progress: "已评分 3 / 6",
              reason: "建议强化因果链条完整性。"
            }
          ]
        }
      }
    ]
  },
  dashboard: {
    subjects: [
      {
        id: "calculus-bc",
        label: "AP Calculus BC",
        shortLabel: "Calculus BC",
        layout: "wide",
        examDate: "2026-05-12",
        examTime: "08:00",
        overallMastery: 74,
        masteryState: "two_thirds",
        fiveRate: 58,
        knowledgeCoverage: 71,
        mcqPrediction: "29-34 / 45",
        frqPrediction: "5-6 / 9",
        overviewMetrics: [
          { label: "5 分概率", value: "58%" },
          { label: "整体掌握", value: "74%" },
          { label: "MCQ 预测", value: "29-34 / 45" },
          { label: "FRQ 预测", value: "5-6 / 9" }
        ],
        units: [
          {
            id: "unit-3",
            title: "Unit 3 · Differentiation",
            weight: "20%-24%",
            masteryState: "two_thirds",
            masteryText: "链条基本建立，但 related rates 还不稳。",
            skills: [
              { id: "derivative-rules", title: "Differentiation rules", masteryState: "full", action: "继续刷中等难度 MCQ" },
              { id: "implicit", title: "Implicit differentiation", masteryState: "two_thirds", action: "补图像和代换步骤" },
              { id: "related-rates", title: "Related rates", masteryState: "one_third", action: "优先做知识点训练" }
            ]
          },
          {
            id: "unit-10",
            title: "Unit 10 · Infinite Series",
            weight: "17%-20%",
            masteryState: "one_third",
            masteryText: "判别法和误差界是当前主风险点。",
            skills: [
              { id: "convergence-tests", title: "Convergence tests", masteryState: "one_third", action: "补 test selection 训练" },
              { id: "taylor-series", title: "Taylor series", masteryState: "two_thirds", action: "保持每周一次练习" },
              { id: "error-bound", title: "Error bound", masteryState: "one_third", action: "配合 FRQ 模板训练" }
            ]
          },
          {
            id: "unit-8",
            title: "Unit 8 · Applications of Integration",
            weight: "10%-15%",
            masteryState: "full",
            masteryText: "整体较稳，但极坐标面积仍需复盘。",
            skills: [
              { id: "polar-area", title: "Polar area", masteryState: "two_thirds", action: "错题复盘一次" },
              { id: "volume", title: "Volume", masteryState: "full", action: "维持即可" }
            ]
          }
        ]
      },
      {
        id: "statistics",
        label: "AP Statistics",
        shortLabel: "Statistics",
        layout: "tall",
        examDate: "2026-05-07",
        examTime: "12:00",
        overallMastery: 81,
        masteryState: "full",
        fiveRate: 73,
        knowledgeCoverage: 78,
        mcqPrediction: "33-37 / 40",
        frqPrediction: "4-5 / 6",
        overviewMetrics: [
          { label: "5 分概率", value: "73%" },
          { label: "整体掌握", value: "81%" },
          { label: "MCQ 预测", value: "33-37 / 40" },
          { label: "FRQ 预测", value: "4-5 / 6" }
        ],
        units: [
          {
            id: "unit-5",
            title: "Unit 5 · Sampling Distributions",
            weight: "12%-15%",
            masteryState: "two_thirds",
            masteryText: "概念判断还需要重复巩固。",
            skills: [
              { id: "sampling-mean", title: "Sampling mean", masteryState: "two_thirds", action: "补定义辨析题" },
              { id: "sampling-spread", title: "Spread and shape", masteryState: "one_third", action: "回到基础组训练" }
            ]
          },
          {
            id: "unit-7",
            title: "Unit 7 · Inference",
            weight: "20%-30%",
            masteryState: "two_thirds",
            masteryText: "条件判断和结论表述仍是扣分点。",
            skills: [
              { id: "conditions", title: "Checking conditions", masteryState: "two_thirds", action: "继续做 MCQ speed set" },
              { id: "wording", title: "Interpretation wording", masteryState: "one_third", action: "背模板并做 FRQ 改写" },
              { id: "ci", title: "Confidence intervals", masteryState: "full", action: "维持" }
            ]
          }
        ]
      },
      {
        id: "microeconomics",
        label: "AP Microeconomics",
        shortLabel: "Microeconomics",
        layout: "wide",
        examDate: "2026-05-06",
        examTime: "08:00",
        overallMastery: 67,
        masteryState: "two_thirds",
        fiveRate: 46,
        knowledgeCoverage: 64,
        mcqPrediction: "42-48 / 60",
        frqPrediction: "3-4 / 6",
        overviewMetrics: [
          { label: "5 分概率", value: "46%" },
          { label: "整体掌握", value: "67%" },
          { label: "MCQ 预测", value: "42-48 / 60" },
          { label: "FRQ 预测", value: "3-4 / 6" }
        ],
        units: [
          {
            id: "unit-2",
            title: "Unit 2 · Supply and Demand",
            weight: "20%-25%",
            masteryState: "full",
            masteryText: "基础图像较稳，可以维持。",
            skills: [
              { id: "elasticity", title: "Elasticity", masteryState: "two_thirds", action: "继续做图像变体题" },
              { id: "consumer-surplus", title: "Consumer / producer surplus", masteryState: "full", action: "维持" }
            ]
          },
          {
            id: "unit-6",
            title: "Unit 6 · Market Failure",
            weight: "10%-15%",
            masteryState: "one_third",
            masteryText: "政策因果链条仍不完整。",
            skills: [
              { id: "externalities", title: "Externalities", masteryState: "one_third", action: "优先做 FRQ 结构训练" },
              { id: "public-goods", title: "Public goods", masteryState: "two_thirds", action: "补知识点训练" }
            ]
          }
        ]
      }
    ]
  }
};
