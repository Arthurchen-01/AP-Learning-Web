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

export function storageKey(examId) {
  return `mokaoai-local-mock:${examId}`;
}

export function initialAnswer(question) {
  return question.type === "multi" ? [] : "";
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
      answers: section.questions.map((question) => initialAnswer(question)),
      flagged: section.questions.map(() => false)
    })),
    results: null
  };
}

export function loadState(examId) {
  try {
    const raw = localStorage.getItem(storageKey(examId));
    return raw ? JSON.parse(raw) : null;
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
  state.breakState = state.breakState || {};
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

  exam.sections.forEach((section, index) => {
    const existing = state.sectionStates[index];
    if (!existing) {
      state.sectionStates[index] = {
        status: "locked",
        timeRemainingSec: section.limitMinutes * 60,
        answers: section.questions.map((question) => initialAnswer(question)),
        flagged: section.questions.map(() => false)
      };
      return;
    }

    existing.status = typeof existing.status === "string" ? existing.status : "locked";
    existing.timeRemainingSec = typeof existing.timeRemainingSec === "number" ? existing.timeRemainingSec : section.limitMinutes * 60;
    existing.answers = Array.isArray(existing.answers) ? existing.answers : section.questions.map((question) => initialAnswer(question));
    existing.flagged = Array.isArray(existing.flagged) ? existing.flagged : section.questions.map(() => false);

    if (existing.answers.length < section.questions.length) {
      existing.answers = existing.answers.concat(
        section.questions.slice(existing.answers.length).map((question) => initialAnswer(question))
      );
    }
    if (existing.flagged.length < section.questions.length) {
      existing.flagged = existing.flagged.concat(
        section.questions.slice(existing.flagged.length).map(() => false)
      );
    }
  });
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

  return {
    sectionLabel,
    partLabel,
    subjectLine,
    calculatorRule,
    questionCount: section.questions.length,
    timeLabel: section.limitMinutes >= 60
      ? `${section.limitMinutes / 60} hour${section.limitMinutes === 60 ? "" : "s"}`
      : `${section.limitMinutes} minutes`
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
