const fallbackSubjectMap = {
  "瀹忚缁忔祹": "AP Macro",
  "寰缁忔祹": "AP Micro",
  "寰Н鍒咮C": "AP Calculus BC",
  "缁熻瀛?": "AP Statistics",
  "蹇冪悊": "AP Psychology",
  "鐗╃悊C鍔涘": "AP Physics C: Mechanics",
  "鐗╃悊C鐢电": "AP Physics C: E&M",
  "CSA": "AP CSA"
};

const state = {
  catalog: null,
  mockData: window.MOKAO_MOCK_DATA || {}
};

document.addEventListener("DOMContentLoaded", () => {
  init().catch((error) => {
    console.error(error);
    renderFailure(error);
  });
});

async function init() {
  const page = document.body.dataset.page;
  hydrateAvatarEntry();

  if (!page || page === "home") {
    return;
  }

  state.catalog = await loadCatalog();

  if (page === "mock") {
    renderMockPage(document.getElementById("mock-root"));
    return;
  }

  if (page === "training") {
    renderTrainingPage(document.getElementById("training-root"));
    return;
  }

  if (page === "dashboard-home") {
    renderDashboardHome(document.getElementById("dashboard-root"));
    return;
  }

  if (page === "dashboard-subject") {
    renderDashboardSubject(document.getElementById("dashboard-subject-root"));
    return;
  }

  if (page === "dashboard-unit") {
    renderDashboardUnit(document.getElementById("dashboard-unit-root"));
    return;
  }

  if (page === "profile") {
    renderProfilePage(document.getElementById("profile-root"));
  }
}

function hydrateAvatarEntry() {
  const user = state.mockData.user || window.MOKAO_MOCK_DATA?.user || {};
  document.querySelectorAll(".avatar-entry").forEach((entry) => {
    const avatar = entry.querySelector(".avatar");
    const strong = entry.querySelector("strong");
    const sub = entry.querySelector(".avatar-meta span");
    if (avatar && user.avatarText) {
      avatar.textContent = user.avatarText;
    }
    if (strong && user.name) {
      strong.textContent = user.name;
    }
    if (sub) {
      sub.textContent = "Profile";
    }
  });
}

async function loadCatalog() {
  try {
    const response = await fetch("/mock-data/exam-catalog.json");
    if (!response.ok) {
      return { items: [] };
    }
    return await response.json();
  } catch (error) {
    console.warn("Failed to load catalog", error);
    return { items: [] };
  }
}

function renderMockPage(root) {
  const items = state.catalog?.items || [];
  if (!items.length) {
    root.innerHTML = '<div class="empty-state">当前没有可展示的本地试卷。</div>';
    return;
  }

  renderSubjectExamBrowser(root, items, "mock");
}

function renderTrainingPage(root) {
  const trainingSubjects = state.mockData.training?.subjects || [];
  if (!trainingSubjects.length) {
    root.innerHTML = '<div class="empty-state">专项训练 mock 数据暂未准备好。</div>';
    return;
  }

  const subject = pickTrainingSubject(trainingSubjects);
  const path = pickTrainingPath(subject);
  const items = subject.items[path.id] || [];
  const selectedItem = pickTrainingItem(items);

  root.innerHTML = `
    <section class="overview-card">
      <div class="overview-head">
        <div>
          <span class="eyebrow">Training Logic</span>
          <h2>${escapeHtml(subject.label)}</h2>
          <p>${escapeHtml(subject.summary)}</p>
        </div>
        <span class="summary-badge">${escapeHtml(path.stat)}</span>
      </div>
      <p class="overview-note">${escapeHtml(subject.recommendation)}</p>
    </section>
    <div class="subject-tabs" role="tablist" aria-label="专项训练学科切换">
      ${trainingSubjects.map((item) => `
        <button
          class="subject-tab${item.id === subject.id ? " is-active" : ""}"
          type="button"
          data-subject="${escapeHtml(item.id)}"
        >
          ${escapeHtml(item.label)}
        </button>
      `).join("")}
    </div>
    <section class="path-grid">
      ${subject.paths.map((item) => `
        <button class="path-card${item.id === path.id ? " is-active" : ""}" type="button" data-path="${escapeHtml(item.id)}">
          <span class="path-title">${escapeHtml(item.title)}</span>
          <span class="path-copy">${escapeHtml(item.description)}</span>
          <span class="path-meta">${escapeHtml(item.emphasis)}</span>
          <span class="summary-badge">${escapeHtml(item.stat)}</span>
        </button>
      `).join("")}
    </section>
    <section class="page-section-grid">
      <article class="page-section-card">
        <div class="section-card-head">
          <div>
            <span class="eyebrow">Current Path</span>
            <h3>${escapeHtml(path.title)}</h3>
          </div>
          <span class="summary-badge">${escapeHtml(path.stat)}</span>
        </div>
        <article class="launch-card">
          <span class="eyebrow">Mock Launch</span>
          <h3>${escapeHtml(selectedItem.title)}</h3>
          <p>${escapeHtml(selectedItem.unit)} · ${escapeHtml(selectedItem.source)} · ${escapeHtml(selectedItem.difficulty)}</p>
          <div class="card-meta">
            ${(selectedItem.tags || []).map((tag) => `<span class="chip">${escapeHtml(tag)}</span>`).join("")}
          </div>
          <p>${escapeHtml(selectedItem.reason)}</p>
          <div class="training-footer">
            <span class="progress-copy">${escapeHtml(selectedItem.progress)}</span>
            <button class="card-link training-launch-button" type="button">开始</button>
          </div>
        </article>
        <div class="training-list">
          ${items.map((item) => renderTrainingItem(item)).join("")}
        </div>
      </article>
      <aside class="page-section-card">
        <div class="section-card-head">
          <div>
            <span class="eyebrow">Recommended</span>
            <h3>训练建议</h3>
          </div>
        </div>
        <div class="insight-list">
          <article class="insight-item">
            <strong>当前推荐路径</strong>
            <p>${escapeHtml(path.description)}</p>
          </article>
          <article class="insight-item">
            <strong>推荐原因</strong>
            <p>${escapeHtml(subject.recommendation)}</p>
          </article>
          <article class="insight-item">
            <strong>路径定位</strong>
            <p>${escapeHtml(path.emphasis)}</p>
          </article>
        </div>
      </aside>
    </section>
  `;

  root.querySelectorAll(".subject-tab").forEach((button) => {
    button.addEventListener("click", () => {
      const url = new URL(window.location.href);
      url.searchParams.set("subject", button.dataset.subject || "");
      url.searchParams.delete("path");
      url.searchParams.delete("item");
      history.replaceState({}, "", `${url.pathname}${url.search}`);
      renderTrainingPage(root);
    });
  });

  root.querySelectorAll(".path-card").forEach((button) => {
    button.addEventListener("click", () => {
      const url = new URL(window.location.href);
      url.searchParams.set("subject", subject.id);
      url.searchParams.set("path", button.dataset.path || "");
      url.searchParams.delete("item");
      history.replaceState({}, "", `${url.pathname}${url.search}`);
      renderTrainingPage(root);
    });
  });

  root.querySelectorAll(".training-start").forEach((button) => {
    button.addEventListener("click", () => {
      const url = new URL(window.location.href);
      url.searchParams.set("subject", subject.id);
      url.searchParams.set("path", path.id);
      url.searchParams.set("item", button.dataset.item || "");
      history.replaceState({}, "", `${url.pathname}${url.search}`);
      renderTrainingPage(root);
    });
  });

  const launchButton = root.querySelector(".training-launch-button");
  if (launchButton) {
    launchButton.addEventListener("click", () => {
      const url = new URL(window.location.href);
      url.searchParams.set("subject", subject.id);
      url.searchParams.set("path", path.id);
      url.searchParams.set("item", slugify(selectedItem.title));
      history.replaceState({}, "", `${url.pathname}${url.search}`);
      renderTrainingPage(root);
    });
  }
}

function renderDashboardHome(root) {
  const user = state.mockData.user || {};
  const subjects = getUserDashboardSubjects();

  if (!subjects.length) {
    root.innerHTML = '<div class="empty-state">当前用户还没有配置报考科目。</div>';
    return;
  }

  root.innerHTML = `
    <section class="overview-card">
      <div class="overview-head">
        <div>
          <span class="eyebrow">Learning Center</span>
          <h2>${escapeHtml(user.name || "AP Learner")}</h2>
          <p>${escapeHtml(user.goal || "先用 mock 数据把个人学习记录中心跑起来。")}</p>
        </div>
        <span class="summary-badge">${subjects.length} 门报考科目</span>
      </div>
      <div class="card-meta">
        ${(user.examSubjects || []).map((subjectId) => {
          const subject = getDashboardSubjectById(subjectId);
          return subject ? `<span class="chip">${escapeHtml(subject.label)}</span>` : "";
        }).join("")}
      </div>
    </section>
    <section class="dashboard-cards dashboard-cards-${subjects.length > 3 ? "dense" : "open"}">
      ${subjects.map((subject, index) => renderDashboardHomeCard(subject, index)).join("")}
    </section>
  `;
}

function renderDashboardSubject(root) {
  const subject = getCurrentDashboardSubject();
  if (!subject) {
    root.innerHTML = '<div class="empty-state">没有找到该学科的 Dashboard 数据。</div>';
    return;
  }

  root.innerHTML = `
    <section class="overview-card">
      <div class="overview-head">
        <div>
          <span class="eyebrow">Subject Overview</span>
          <h2>${escapeHtml(subject.label)}</h2>
          <p>${escapeHtml(subject.examDate)} · ${escapeHtml(subject.examTime)} · 预测与掌握度总览</p>
        </div>
        ${renderMasteryPill(subject.masteryState)}
      </div>
      <div class="summary-grid summary-grid-four">
        ${subject.overviewMetrics.map((metric) => `
          <article class="summary-card compact">
            <span class="eyebrow">${escapeHtml(metric.label)}</span>
            <h3>${escapeHtml(metric.value)}</h3>
          </article>
        `).join("")}
      </div>
    </section>
    <section class="page-section-card">
      <div class="section-card-head">
        <div>
          <span class="eyebrow">Unit Map</span>
          <h3>单元掌握地图</h3>
        </div>
      </div>
      <div class="unit-map-grid">
        ${subject.units.map((unit) => renderUnitOverviewCard(subject, unit)).join("")}
      </div>
    </section>
  `;
}

function renderDashboardUnit(root) {
  const subject = getCurrentDashboardSubject();
  const unit = getCurrentUnit(subject);
  if (!subject || !unit) {
    root.innerHTML = '<div class="empty-state">没有找到该单元的掌握数据。</div>';
    return;
  }

  root.innerHTML = `
    <section class="overview-card">
      <div class="overview-head">
        <div>
          <span class="eyebrow">Unit Detail</span>
          <h2>${escapeHtml(unit.title)}</h2>
          <p>${escapeHtml(subject.label)} · 考试权重 ${escapeHtml(unit.weight)}</p>
        </div>
        ${renderMasteryPill(unit.masteryState)}
      </div>
      <p class="overview-note">${escapeHtml(unit.masteryText)}</p>
      <div class="card-footer is-start">
        <a class="card-link" href="/dashboard/subject/?subject=${encodeURIComponent(subject.id)}">返回学科 Dashboard</a>
      </div>
    </section>
    <section class="page-section-card">
      <div class="section-card-head">
        <div>
          <span class="eyebrow">Skill Map</span>
          <h3>知识点层级掌握情况</h3>
        </div>
      </div>
      <div class="skill-map-grid">
        ${unit.skills.map((skill) => renderSkillMapCard(skill)).join("")}
      </div>
    </section>
  `;
}

function renderProfilePage(root) {
  const user = state.mockData.user || {};
  const subjects = getUserDashboardSubjects();

  root.innerHTML = `
    <section class="profile-shell">
      <aside class="profile-card">
        <div class="profile-avatar">${escapeHtml(user.avatarText || "AP")}</div>
        <h2>${escapeHtml(user.name || "AP Learner")}</h2>
        <p>${escapeHtml(user.bio || "")}</p>
      </aside>
      <section class="profile-content">
        <article class="page-section-card">
          <div class="section-card-head">
            <div>
              <span class="eyebrow">Goal</span>
              <h3>个人目标</h3>
            </div>
          </div>
          <p>${escapeHtml(user.goal || "")}</p>
        </article>
        <article class="page-section-card">
          <div class="section-card-head">
            <div>
              <span class="eyebrow">AP Subjects</span>
              <h3>报考科目</h3>
            </div>
          </div>
          <div class="card-meta">
            ${subjects.map((subject) => `<span class="chip">${escapeHtml(subject.label)}</span>`).join("")}
          </div>
        </article>
        <article class="page-section-card">
          <div class="section-card-head">
            <div>
              <span class="eyebrow">Settings</span>
              <h3>个人设置</h3>
            </div>
          </div>
          <div class="insight-list">
            ${(user.settings || []).map((item) => `<article class="insight-item"><p>${escapeHtml(item)}</p></article>`).join("")}
          </div>
        </article>
      </section>
    </section>
  `;
}

function renderSubjectExamBrowser(root, items, mode) {
  const grouped = groupBySubject(items);
  const subjects = Object.keys(grouped);
  const selectedSubject = getQueryValue("subject") || subjects[0];
  const safeSubject = grouped[selectedSubject] ? selectedSubject : subjects[0];
  const exams = [...grouped[safeSubject]].sort(compareExamItems);

  root.innerHTML = `
    <div class="subject-tabs" role="tablist" aria-label="套题模考学科切换">
      ${subjects.map((subject) => `
        <button class="subject-tab${subject === safeSubject ? " is-active" : ""}" type="button" data-subject="${escapeHtml(subject)}">
          ${escapeHtml(subject)}
        </button>
      `).join("")}
    </div>
    <section class="subject-shell">
      <div class="subject-grid">
        ${exams.map((item) => renderExamCard(item)).join("")}
      </div>
    </section>
  `;

  root.querySelectorAll(".subject-tab").forEach((button) => {
    button.addEventListener("click", () => {
      const url = new URL(window.location.href);
      url.searchParams.set("subject", button.dataset.subject || "");
      history.replaceState({}, "", `${url.pathname}${url.search}`);
      renderSubjectExamBrowser(root, items, mode);
    });
  });
}

function renderDashboardHomeCard(subject, index) {
  const stateMeta = getMasteryStateMeta(subject.masteryState);
  const layoutClass = subject.layout === "wide" && index === 0 ? "is-wide" : "";
  return `
    <a class="dashboard-home-card ${layoutClass}" href="/dashboard/subject/?subject=${encodeURIComponent(subject.id)}">
      <div class="dashboard-home-top">
        <div>
          <span class="eyebrow">Exam</span>
          <h3>${escapeHtml(subject.label)}</h3>
          <p>${escapeHtml(subject.examDate)} · ${escapeHtml(subject.examTime)}</p>
        </div>
        <span class="mastery-chip ${escapeHtml(stateMeta.tone)}">${escapeHtml(stateMeta.label)}</span>
      </div>
      <div class="dashboard-home-metrics">
        <div class="metric-block">
          <span>5 分概率</span>
          <strong>${escapeHtml(String(subject.fiveRate))}%</strong>
        </div>
        <div class="metric-block">
          <span>整体掌握</span>
          <strong>${escapeHtml(String(subject.overallMastery))}%</strong>
        </div>
        <div class="metric-block">
          <span>MCQ 预测</span>
          <strong>${escapeHtml(subject.mcqPrediction)}</strong>
        </div>
        <div class="metric-block">
          <span>FRQ 预测</span>
          <strong>${escapeHtml(subject.frqPrediction)}</strong>
        </div>
      </div>
      <div class="mastery-progress">
        <span>知识点掌握</span>
        <div class="progress-track">
          <span class="progress-fill ${escapeHtml(stateMeta.fill)}"></span>
        </div>
        <strong>${escapeHtml(String(subject.knowledgeCoverage))}%</strong>
      </div>
    </a>
  `;
}

function renderUnitOverviewCard(subject, unit) {
  const meta = getMasteryStateMeta(unit.masteryState);
  return `
    <a class="unit-overview-card" href="/dashboard/unit/?subject=${encodeURIComponent(subject.id)}&unit=${encodeURIComponent(unit.id)}">
      <div class="section-card-head">
        <div>
          <h4>${escapeHtml(unit.title)}</h4>
          <p>考试权重 ${escapeHtml(unit.weight)}</p>
        </div>
        <span class="mastery-chip ${escapeHtml(meta.tone)}">${escapeHtml(meta.label)}</span>
      </div>
      <p>${escapeHtml(unit.masteryText)}</p>
      <div class="progress-track">
        <span class="progress-fill ${escapeHtml(meta.fill)}"></span>
      </div>
      <div class="card-meta">
        <span class="chip">${unit.skills.length} 个知识点</span>
      </div>
    </a>
  `;
}

function renderSkillMapCard(skill) {
  const meta = getMasteryStateMeta(skill.masteryState);
  return `
    <article class="skill-map-card ${escapeHtml(meta.tone)}">
      <div class="skill-map-top">
        <span class="skill-block ${escapeHtml(meta.fill)}"></span>
        <span class="skill-level-text">${escapeHtml(meta.label)}</span>
      </div>
      <strong>${escapeHtml(skill.title)}</strong>
      <p>${escapeHtml(skill.action)}</p>
    </article>
  `;
}

function renderTrainingItem(item) {
  return `
    <article class="training-item">
      <div>
        <h3>${escapeHtml(item.title)}</h3>
        <p>${escapeHtml(item.unit)} · ${escapeHtml(item.source)} · ${escapeHtml(item.difficulty)}</p>
      </div>
      <div class="card-meta">
        ${(item.tags || []).map((tag) => `<span class="chip">${escapeHtml(tag)}</span>`).join("")}
      </div>
      <p>${escapeHtml(item.reason)}</p>
      <div class="training-footer">
        <span class="progress-copy">${escapeHtml(item.progress)}</span>
        <button class="card-link training-start" type="button" data-item="${escapeHtml(slugify(item.title))}">开始</button>
      </div>
    </article>
  `;
}

function renderExamCard(item) {
  const progress = getProgressState(item.examId);
  const subject = getSubjectLabel(item);
  const title = cleanTitle(item.title, subject);
  const year = normalizeYear(item.year, item.title);
  const paperType = normalizePaperType(item.paperType, item.title);

  return `
    <article class="exam-card">
      <div>
        <h3>${escapeHtml(title)}</h3>
        <p>${escapeHtml(year)} · ${escapeHtml(subject)} · ${escapeHtml(paperType)}</p>
      </div>
      <div class="card-meta">
        <span class="chip">题量 ${Number(item.questionCount) || 0}</span>
        <span class="chip">Sections ${Number(item.sectionCount) || 0}</span>
        ${progress.hasProgress ? '<span class="chip">本地有进度</span>' : ""}
      </div>
      <div class="card-footer">
        <a class="card-link" href="/ap/start/?examId=${encodeURIComponent(item.examId)}">开始</a>
      </div>
    </article>
  `;
}

function pickTrainingSubject(subjects) {
  const subjectId = getQueryValue("subject");
  return subjects.find((item) => item.id === subjectId) || subjects[0];
}

function pickTrainingPath(subject) {
  const pathId = getQueryValue("path");
  return subject.paths.find((item) => item.id === pathId) || subject.paths[0];
}

function pickTrainingItem(items) {
  const itemId = getQueryValue("item");
  return items.find((item) => slugify(item.title) === itemId) || items[0];
}

function getUserDashboardSubjects() {
  const user = state.mockData.user || {};
  return (user.examSubjects || [])
    .map((subjectId) => getDashboardSubjectById(subjectId))
    .filter(Boolean);
}

function getDashboardSubjectById(subjectId) {
  return (state.mockData.dashboard?.subjects || []).find((item) => item.id === subjectId) || null;
}

function getCurrentDashboardSubject() {
  const userSubjects = getUserDashboardSubjects();
  const subjectId = getQueryValue("subject");
  return userSubjects.find((item) => item.id === subjectId) || userSubjects[0] || null;
}

function getCurrentUnit(subject) {
  if (!subject) {
    return null;
  }
  const unitId = getQueryValue("unit");
  return subject.units.find((item) => item.id === unitId) || subject.units[0] || null;
}

function getMasteryStateMeta(stateKey) {
  return state.mockData.masteryStates?.[stateKey] || state.mockData.masteryStates?.one_third || {
    label: stateKey,
    tone: "tone-muted",
    fill: "fill-one-third"
  };
}

function renderMasteryPill(stateKey) {
  const meta = getMasteryStateMeta(stateKey);
  return `<span class="mastery-chip ${escapeHtml(meta.tone)}">${escapeHtml(meta.label)}</span>`;
}

function getQueryValue(key) {
  return new URLSearchParams(window.location.search).get(key);
}

function groupBySubject(items) {
  return items.reduce((groups, item) => {
    const key = getSubjectLabel(item);
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(item);
    return groups;
  }, {});
}

function getSubjectLabel(item) {
  const raw = [item.subject, item.category, item.discipline, item.course, item.examType]
    .find((value) => String(value || "").trim());
  return normalizeSubject(raw);
}

function normalizeSubject(subject) {
  const value = String(subject || "").trim();
  if (fallbackSubjectMap[value]) {
    return fallbackSubjectMap[value];
  }
  if (!value || value.includes("\uFFFD") || value.includes("?")) {
    return "AP Subject";
  }
  return value;
}

function normalizePaperType(paperType, title) {
  const value = String(paperType || "").trim();
  const titleValue = String(title || "").trim();

  if (titleValue.includes("国际卷")) return "国际卷";
  if (titleValue.includes("样题")) return "样题";
  if (titleValue.includes("真题拼题")) return "练习卷";
  if (!value || value.includes("\uFFFD") || value.includes("?")) return "练习卷";
  return value;
}

function normalizeYear(year, title) {
  const value = String(year || "").trim();
  if (/^\d{4}$/.test(value)) return value;
  const matched = String(title || "").match(/(20\d{2})/);
  return matched ? matched[1] : "未标年份";
}

function cleanTitle(title, subject) {
  const value = String(title || "").trim();
  if (!value || value.includes("\uFFFD") || value.includes("?")) {
    return `${subject} 试卷`;
  }
  return value.replaceAll("__", " ").trim();
}

function getProgressState(examId) {
  const storageKey = `mokaoai-local-mock:${examId}`;
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw) return { hasProgress: false, inProgress: false, updatedAt: 0 };
    const parsed = JSON.parse(raw);
    const answers = (parsed.sectionStates || []).flatMap((section) => section.answers || []);
    const hasAnswers = answers.some((answer) => Array.isArray(answer) ? answer.length > 0 : String(answer || "").trim().length > 0);
    const hasProgress = Boolean(parsed.startedAt || hasAnswers || parsed.results);
    const inProgress = hasProgress && !parsed.results;
    const updatedAt = Date.parse(parsed.updatedAt || parsed.startedAt || "") || 0;
    return { hasProgress, inProgress, updatedAt };
  } catch (error) {
    console.warn("Failed to parse local progress", examId, error);
    return { hasProgress: false, inProgress: false, updatedAt: 0 };
  }
}

function compareExamItems(a, b) {
  const yearDiff = Number(normalizeYear(b.year, b.title)) - Number(normalizeYear(a.year, a.title));
  if (!Number.isNaN(yearDiff) && yearDiff !== 0) return yearDiff;
  return cleanTitle(a.title, getSubjectLabel(a)).localeCompare(cleanTitle(b.title, getSubjectLabel(b)));
}

function renderFailure(error) {
  const root = document.querySelector("[data-page-root]");
  if (root) {
    root.innerHTML = `<div class="empty-state">加载失败：${escapeHtml(String(error.message || error))}</div>`;
  }
}

function slugify(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
