/**
 * AP Learning v2 - Data Service
 * 统一数据服务：加载考试数据、题目JSON、用户进度
 */

// 考试包存储路径 - 相对于当前文件的位置
const DATA_BASE = '../data/';

// 加载考试索引
export async function loadExamIndex() {
  try {
    const res = await fetch(DATA_BASE + 'exams/index.json');
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    console.warn('Failed to load exam index:', e);
  }
  return getDefaultExams();
}

// 默认考试列表
function getDefaultExams() {
  return [
    {
      exam_id: 'calc-bc-2018-intl',
      exam_title: 'AP Calculus BC 2018 国际卷',
      subject: 'calculus_bc',
      subject_display: '微积分BC',
      year: 2018,
      form: 'international',
      total_questions: 45,
      sections: [
        { section_id: 'mcq-1', part_label: 'Part A', calculator_allowed: false, question_count: 30 },
        { section_id: 'mcq-2', part_label: 'Part B', calculator_allowed: true, question_count: 15 }
      ]
    }
  ];
}

// 加载单个考试包
export async function loadExam(examId) {
  try {
    const res = await fetch(`${DATA_BASE}${examId}/exam_packet.json`);
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    console.warn('Failed to load exam:', e);
  }
  return null;
}

// 加载考试的所有题目
export async function loadExamQuestions(examId) {
  try {
    const res = await fetch(`${DATA_BASE}${examId}/questions.json`);
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    console.warn('Failed to load questions:', e);
  }
  return null;
}

// 加载单个题目
export async function loadQuestion(examId, questionId) {
  try {
    const res = await fetch(`${DATA_BASE}${examId}/questions/${questionId}.json`);
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    console.warn('Failed to load question:', e);
  }
  return null;
}

// 加载做题记录
export function loadSession(examId) {
  try {
    const raw = localStorage.getItem(`ap-learning-session:${examId}`);
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
}

// 保存做题记录
export function saveSession(examId, session) {
  localStorage.setItem(`ap-learning-session:${examId}`, JSON.stringify(session));
}

// 清除做题记录
export function clearSession(examId) {
  localStorage.removeItem(`ap-learning-session:${examId}`);
}

// 加载用户进度
export function loadProgress() {
  try {
    const raw = localStorage.getItem('ap-learning-progress');
    return raw ? JSON.parse(raw) : {
      exams: 0,
      questions: 0,
      correct: 0,
      accuracy: 0,
      subjects: {}
    };
  } catch (e) {
    return { exams: 0, questions: 0, correct: 0, accuracy: 0, subjects: {} };
  }
}

// 保存用户进度
export function saveProgress(progress) {
  localStorage.setItem('ap-learning-progress', JSON.stringify(progress));
}

// 更新进度
export function updateProgress(examId, subject, score, totalQuestions, correctCount) {
  const progress = loadProgress();

  progress.exams = (progress.exams || 0) + 1;
  progress.questions = (progress.questions || 0) + totalQuestions;
  progress.correct = (progress.correct || 0) + correctCount;
  progress.accuracy = Math.round((progress.correct / progress.questions) * 100);

  if (!progress.subjects) progress.subjects = {};
  if (!progress.subjects[subject]) {
    progress.subjects[subject] = { exams: 0, questions: 0, correct: 0 };
  }
  progress.subjects[subject].exams++;
  progress.subjects[subject].questions += totalQuestions;
  progress.subjects[subject].correct += correctCount;

  saveProgress(progress);
}

// 获取本地存储的答案
export function getStoredAnswer(examId, sectionId, questionIndex) {
  const session = loadSession(examId);
  if (session && session.sections) {
    const section = session.sections.find(s => s.section_id === sectionId);
    if (section && section.answers) {
      return section.answers[questionIndex];
    }
  }
  return null;
}
