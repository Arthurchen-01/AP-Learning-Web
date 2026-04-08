/**
 * AP Learning v2 - Exam Engine
 * 考试核心逻辑：计时、答题、状态管理
 */

// 加载 KaTeX
export function loadKatex() {
  return new Promise((resolve) => {
    if (window.katex) return resolve();
    const css = document.createElement('link');
    css.rel = 'stylesheet';
    css.href = 'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css';
    document.head.appendChild(css);
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js';
    script.onload = () => resolve();
    script.onerror = () => resolve();
    document.head.appendChild(script);
  });
}

// 渲染数学公式
export function renderMath(element) {
  if (!window.katex) return;
  element.querySelectorAll('.math-inline').forEach(el => {
    try {
      window.katex.render(el.textContent, el, { throwOnError: false, displayMode: false });
    } catch (e) {}
  });
}

// 存储 key
function storageKey(examId) {
  return `ap-learning-exam:${examId}`;
}

// 创建初始状态
export function createFreshState(exam) {
  return {
    stage: 'question', // question | review | results
    sectionIndex: 0,
    questionIndex: 0,
    startedAt: null,
    timekeepingModeOn: true,
    ui: {
      navigatorOpen: false,
      flagged: []
    },
    sections: exam.sections.map(section => ({
      section_id: section.section_id,
      status: 'locked',
      timeRemainingSec: (section.time_limit_minutes || 60) * 60,
      answers: new Array(section.question_count).fill(null),
      flagged: new Array(section.question_count).fill(false),
      excluded: new Array(section.question_count).fill(false),
      frqImages: null
    })),
    results: null
  };
}

// 加载状态
export function loadState(examId) {
  try {
    const raw = localStorage.getItem(storageKey(examId));
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
}

// 保存状态
export function saveState(examId, state) {
  localStorage.setItem(storageKey(examId), JSON.stringify(state));
}

// 清除状态
export function clearState(examId) {
  localStorage.removeItem(storageKey(examId));
}

// 格式化时间
export function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// 计算成绩
export function calculateResults(exam, state) {
  const results = {
    sections: [],
    totalCorrect: 0,
    totalQuestions: 0,
    accuracy: 0
  };

  exam.sections.forEach((section, sIdx) => {
    const secState = state.sections[sIdx];
    let correct = 0;
    let answered = 0;

    section.questions.forEach((q, qIdx) => {
      const answer = secState.answers[qIdx];
      if (answer !== null && answer !== undefined && answer !== '') {
        answered++;
        if (answer === q.correct_answer) {
          correct++;
        }
      }
    });

    results.sections.push({
      section_id: section.section_id,
      correct,
      answered,
      total: section.question_count
    });

    results.totalCorrect += correct;
    results.totalQuestions += section.question_count;
  });

  results.accuracy = results.totalQuestions > 0
    ? Math.round((results.totalCorrect / results.totalQuestions) * 100)
    : 0;

  return results;
}

// 答题验证
export function checkAnswer(exam, sectionIndex, questionIndex, userAnswer) {
  const section = exam.sections[sectionIndex];
  if (!section || !section.questions[questionIndex]) return false;
  return userAnswer === section.questions[questionIndex].correct_answer;
}

// 计时器管理
export class ExamTimer {
  constructor(onTick, onExpire) {
    this.onTick = onTick;
    this.onExpire = onExpire;
    this.interval = null;
    this.remaining = 0;
  }

  start(seconds) {
    this.remaining = seconds;
    this.stop();
    this.interval = setInterval(() => {
      this.remaining--;
      this.onTick(this.remaining);
      if (this.remaining <= 0) {
        this.stop();
        this.onExpire();
      }
    }, 1000);
  }

  stop() {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }
  }

  pause() { this.stop(); }
  resume() { this.start(this.remaining); }
}
