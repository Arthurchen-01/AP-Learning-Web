export const PREPARING_DELAY_MS = 1400;
export const BREAK_DURATION_SEC = 600;

export const START_OPTIONS = [
  {
    key: "timekeepingModeOn",
    label: "计时模式",
    description: "开启后会显示剩余时间，自动结束模块",
    enabledLabel: "✓ 开启",
    disabledLabel: "✗ 开关",
    defaultValue: true
  },
  {
    key: "talkModeOn",
    label: "语音模式",
    description: "后台将接收语音输入的答案",
    enabledLabel: "✓ 开启",
    disabledLabel: "✗ 关闭",
    defaultValue: false
  }
];

export const ENTRANCE_PANELS = [
  {
    title: "计时",
    body: "计时器在你进入第一部分时开始。在考试过程中可以随时隐藏或显示计时器。"
  },
  {
    title: "成绩",
    body: "这个导入的试卷目前在练习模式下运行。答案已保存，但官方评分尚未导入。"
  },
  {
    title: "辅助技术",
    body: "高亮、笔记、行阅读器、快捷键和其他支持功能在整个测试界面中都可用。"
  }
];

export const TOOL_MENU_ITEMS = [
  "Help",
  "Keyboard Shortcuts",
  "Assistive Technology",
  "Line Reader",
  "On-Schedule Break"
];

const NORMALIZED_EXAM_SOURCES = {
  "1902622411800285184": "calc-bc-2018-intl",
  "calc-bc-2018-intl": "calc-bc-2018-intl",
  "1902622411338911744": "calc-bc-2017-intl",
  "calc-bc-2017-intl": "calc-bc-2017-intl",
  "2015Intl": "calc-bc-2015-intl",
  "calc-bc-2015-intl": "calc-bc-2015-intl",
  "2016Intl": "calc-bc-2016-intl",
  "calc-bc-2016-intl": "calc-bc-2016-intl",
  "1902622413180211200": "statistics-2017-intl",
  "statistics-2017-intl": "statistics-2017-intl",
  "1902622413633196032": "statistics-2018-intl",
  "statistics-2018-intl": "statistics-2018-intl",
  "1902622414081986560": "statistics-2019-intl",
  "statistics-2019-intl": "statistics-2019-intl",
  "1902622414539165696": "statistics-2021-intl",
  "statistics-2021-intl": "statistics-2021-intl",
  "1902622410416164864": "microeconomics-2017-intl",
  "microeconomics-2017-intl": "microeconomics-2017-intl",
  "1902622410881732608": "microeconomics-2018-intl",
  "microeconomics-2018-intl": "microeconomics-2018-intl",
  "1902622418683138048": "microeconomics-2019-intl",
  "microeconomics-2019-intl": "microeconomics-2019-intl",
  "1902622419140317184": "microeconomics-2021-intl",
  "microeconomics-2021-intl": "microeconomics-2021-intl"
};

export async function loadExamShellData(examId) {
  const normalizedExamId = NORMALIZED_EXAM_SOURCES[String(examId || "")];
  if (!normalizedExamId) {
    return fetchMockExamData(examId);
  }

  try {
    return await fetchNormalizedExamData(normalizedExamId, examId);
  } catch (error) {
    console.warn("Failed to load normalized exam data, falling back to mock data", examId, error);
    return fetchMockExamData(examId);
  }
}

async function fetchMockExamData(examId) {
  const response = await fetch(window.sitePath(`/mock-data/ap-exam-${examId}.json`));
  if (!response.ok) {
    throw new Error(`Missing local exam data for ${examId}`);
  }
  return response.json();
}

async function fetchNormalizedExamData(normalizedExamId, requestedExamId) {
  const [packetResponse, questionsResponse] = await Promise.all([
    fetch(window.sitePath(`/v2/data/${normalizedExamId}/exam_packet.json`)),
    fetch(window.sitePath(`/v2/data/${normalizedExamId}/questions.json`))
  ]);

  if (!packetResponse.ok || !questionsResponse.ok) {
    throw new Error(`Missing normalized exam data for ${normalizedExamId}`);
  }

  const [packet, questions] = await Promise.all([
    packetResponse.json(),
    questionsResponse.json()
  ]);

  return buildExamShellData(packet, questions, requestedExamId);
}

function buildExamShellData(packet, questions, requestedExamId) {
  const safeQuestions = Array.isArray(questions) ? questions : [];
  const sections = Array.isArray(packet.sections) ? packet.sections : [];
  const subjectName = packet.subject_display || packet.subject || "AP Practice Test";
  const yearLabel = packet.year ? `${packet.year}年国际卷` : "";

  return {
    examId: String(requestedExamId || packet.exam_id || ""),
    title: packet.exam_title || packet.exam_id || "AP Practice Test",
    subjectName,
    yearLabel,
    description: packet.exam_title || "",
    answerKeyAvailable: false,
    scoring: {
      answerKeyAvailable: false,
      apBands: [],
      note: "Scoring unavailable until answer keys are imported."
    },
    sections: sections.map((section, index) => ({
      id: section.section_id || `section-${index + 1}`,
      title: `Section ${index + 1}`,
      partTitle: section.part_label || section.section_type || `Part ${index + 1}`,
      limitMinutes: Number(section.time_limit_minutes || 0),
      directions: section.calculator_allowed
        ? "Calculator is allowed for this part of the exam."
        : "No calculator is allowed for this part of the exam.",
      questions: safeQuestions
        .filter((question) => question.section_id === section.section_id)
        .sort((left, right) => Number(left.sequence_in_exam || 0) - Number(right.sequence_in_exam || 0))
        .map(mapNormalizedQuestion)
    }))
  };
}

function mapNormalizedQuestion(question) {
  return {
    id: question.question_id,
    type: mapNormalizedQuestionType(question),
    prompt: normalizeExamText(question.question_html || ""),
    options: Array.isArray(question.options)
      ? question.options.map((option) => ({
          key: option.key,
          content: normalizeExamText(option.html || option.text || "")
        }))
      : [],
    answer: "",
    correctAnswer: question.correct_answer || "",
    explanation: question.correct_answer ? `Correct answer: ${question.correct_answer}` : "Answer key not available yet for this imported exam."
  };
}

function mapNormalizedQuestionType(question) {
  if (question.question_type === "multiple_select") {
    return "multi";
  }
  if (question.question_type === "free_response" || question.question_type === "frq") {
    return "frq";
  }
  if (Array.isArray(question.options) && question.options.length) {
    return "single";
  }
  return "frq";
}

function normalizedStorageExamId(examId) {
  return NORMALIZED_EXAM_SOURCES[String(examId || "")] || String(examId || "");
}

export function storageKey(examId) {
  return `mokaoai-local-mock:${normalizedStorageExamId(examId)}`;
}

export function initialAnswer(question) {
  return question.type === "multi" ? [] : "";
}

function questionIdList(section) {
  return section.questions.map((question, index) => String(question.id || `question-${index + 1}`));
}

function realignSectionState(section, existing) {
  const nextQuestionIds = questionIdList(section);
  const previousQuestionIds = Array.isArray(existing.questionIds) ? existing.questionIds.map((id) => String(id)) : [];
  const previousAnswers = Array.isArray(existing.answers) ? existing.answers : [];
  const previousFlags = Array.isArray(existing.flagged) ? existing.flagged : [];
  const hasStableQuestionIds = previousQuestionIds.length === previousAnswers.length && previousQuestionIds.length > 0;
  const answerById = new Map();
  const flagById = new Map();

  if (hasStableQuestionIds) {
    previousQuestionIds.forEach((questionId, index) => {
      answerById.set(questionId, previousAnswers[index]);
      flagById.set(questionId, previousFlags[index]);
    });
  }

  existing.questionIds = nextQuestionIds;
  existing.answers = nextQuestionIds.map((questionId, index) => {
    if (hasStableQuestionIds) {
      return answerById.has(questionId) ? answerById.get(questionId) : initialAnswer(section.questions[index]);
    }
    return index < previousAnswers.length ? previousAnswers[index] : initialAnswer(section.questions[index]);
  });
  existing.flagged = nextQuestionIds.map((questionId, index) => {
    if (hasStableQuestionIds) {
      return flagById.has(questionId) ? Boolean(flagById.get(questionId)) : false;
    }
    return Boolean(previousFlags[index]);
  });
}

export function createFreshState(examData) {
  return {
    stage: "question",
    sectionIndex: 0,
    questionIndex: 0,
    startedAt: null,
    lastSavedAt: Date.now(),
    startConfig: {
      timekeepingModeOn: true,
      talkModeOn: false
    },
    breakState: {},
    ui: {
      navigatorOpen: false,
      directionsOpen: false,
      moreOpen: false,
      helpOpen: false,
      shortcutsOpen: false,
      notesOpen: false,
      scratchOpen: false,
      lineReaderOn: false,
      hideTimer: false,
      assistiveOpen: false,
      onScheduleBreak: false
    },
    sectionStates: examData.sections.map((section) => ({
      status: "locked",
      timeRemainingSec: section.limitMinutes * 60,
      questionIds: questionIdList(section),
      answers: section.questions.map((question) => initialAnswer(question)),
      flagged: section.questions.map(() => false)
    })),
    results: null
  };
}

export function loadState(examId) {
  try {
    const canonicalKey = storageKey(examId);
    const legacyKey = `mokaoai-local-mock:${examId}`;
    const raw = localStorage.getItem(canonicalKey) || localStorage.getItem(legacyKey);
    if (!raw) {
      return null;
    }
    if (!localStorage.getItem(canonicalKey) && legacyKey !== canonicalKey) {
      localStorage.setItem(canonicalKey, raw);
    }
    return JSON.parse(raw);
  } catch (error) {
    console.warn("Failed to restore exam state", examId, error);
    return null;
  }
}

export function persistState(examId, state) {
  state.lastSavedAt = Date.now();
  localStorage.setItem(storageKey(examId), JSON.stringify(state));
}

export function ensureStateShape(exam, state) {
  state.startConfig = {
    timekeepingModeOn: true,
    talkModeOn: false,
    ...(state.startConfig || {})
  };
  state.breakState = typeof state.breakState === "object" && state.breakState !== null ? state.breakState : {};
  Object.values(state.breakState).forEach((entry) => {
    if (!entry || typeof entry !== "object") {
      return;
    }
    if (entry.startedAt != null) {
      entry.startedAt = String(entry.startedAt);
    }
    if (entry.recordedAt != null) {
      entry.recordedAt = String(entry.recordedAt);
    }
    if (entry.skipped != null) {
      entry.skipped = Boolean(entry.skipped);
    }
  });
  state.ui = {
    navigatorOpen: false,
    directionsOpen: false,
    moreOpen: false,
    helpOpen: false,
    shortcutsOpen: false,
    notesOpen: false,
    scratchOpen: false,
    lineReaderOn: false,
    hideTimer: false,
    assistiveOpen: false,
    onScheduleBreak: false,
    ...(state.ui || {})
  };
  state.sectionStates = Array.isArray(state.sectionStates) ? state.sectionStates : [];

  const previousActiveState = state.sectionStates[state.sectionIndex];
  const previousQuestionId = Array.isArray(previousActiveState?.questionIds)
    ? previousActiveState.questionIds[state.questionIndex]
    : null;

  exam.sections.forEach((section, index) => {
    const existing = state.sectionStates[index];
    if (!existing) {
      state.sectionStates[index] = {
        status: "locked",
        timeRemainingSec: section.limitMinutes * 60,
        questionIds: questionIdList(section),
        answers: section.questions.map((question) => initialAnswer(question)),
        flagged: section.questions.map(() => false),
        scratchpad: ""
      };
      return;
    }

    existing.status = typeof existing.status === "string" ? existing.status : "locked";
    existing.timeRemainingSec = typeof existing.timeRemainingSec === "number" ? existing.timeRemainingSec : section.limitMinutes * 60;
    existing.scratchpad = typeof existing.scratchpad === "string" ? existing.scratchpad : "";
    realignSectionState(section, existing);
  });

  if (!state.sectionStates[state.sectionIndex]) {
    state.sectionIndex = 0;
  }

  const activeSection = exam.sections[state.sectionIndex];
  const activeState = state.sectionStates[state.sectionIndex];
  if (!activeSection || !activeState) {
    state.questionIndex = 0;
    return;
  }

  const activeQuestionIds = questionIdList(activeSection);
  const remappedIndex = previousQuestionId ? activeQuestionIds.indexOf(String(previousQuestionId)) : -1;
  if (remappedIndex >= 0) {
    state.questionIndex = remappedIndex;
    return;
  }

  const lastIndex = activeSection.questions.length - 1;
  state.questionIndex = Math.max(0, Math.min(lastIndex, Number(state.questionIndex) || 0));
}

export function deriveSectionMeta(section, exam) {
  const sectionLabel = section.title || "Section";
  const partLabel = section.partTitle || "Part";
  const directions = String(section.directions || "");
  const calculatorAllowed = /calculator is allowed/i.test(directions);
  const calculatorRule = calculatorAllowed
    ? "Calculator is allowed for this part of the exam."
    : "No calculator is allowed for this part of the exam.";
  const subjectLine = String(exam.subjectName || exam.title || "AP Practice Test");
  const limitMinutes = Number(section.limitMinutes ?? section.time_limit_minutes ?? 0);
  const hours = Math.floor(limitMinutes / 60);
  const minutes = limitMinutes % 60;
  const timeLabel = hours > 0
    ? `${hours} hour${hours === 1 ? "" : "s"}${minutes > 0 ? ` ${minutes} minute${minutes === 1 ? "" : "s"}` : ""}`
    : `${limitMinutes} minute${limitMinutes === 1 ? "" : "s"}`;

  return {
    sectionLabel,
    partLabel,
    subjectLine,
    calculatorRule,
    questionCount: section.questions.length,
    timeLabel
  };
}

export function normalizeExamText(value) {
  return String(value || "")
    .replaceAll("路", "·")
    .replaceAll("鈥?", "'")
    .replaceAll("鈭?", "-")
    .replaceAll("鈪?", "II")
    .replaceAll("鈱?", "")
    .replaceAll("蟺", "π")
    .replaceAll("宦", "")
    .replace(/\s+@[\w]+@/g, "")
    .replace(/MathType@MTEF@[^ ]+/g, "")
    .replace(/\s{2,}/g, " ")
    .trim();
}

export function formatClock(totalSeconds) {
  const safe = Math.max(0, Math.round(totalSeconds));
  const hours = Math.floor(safe / 3600);
  const minutes = Math.floor((safe % 3600) / 60);
  const seconds = safe % 60;
  if (hours > 0) {
    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  }
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}
