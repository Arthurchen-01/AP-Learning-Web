const catalogRoot = document.getElementById("catalog-root");
const catalogMeta = document.getElementById("catalog-meta");
const searchInput = document.getElementById("search-input");
const yearTags = document.getElementById("year-tags");
const typeTags = document.getElementById("type-tags");

const state = {
  catalog: null,
  search: "",
  year: "all",
  paperType: "all"
};

init().catch((error) => {
  console.error(error);
  catalogRoot.innerHTML = `<div class="empty-card">题库索引加载失败：${escapeHtml(String(error.message || error))}</div>`;
});

async function init() {
  const response = await fetch("/mock-data/exam-catalog.json");
  if (!response.ok) {
    throw new Error("Missing local exam catalog");
  }

  state.catalog = await response.json();
  buildFilterTags();
  bindEvents();
  render();
}

function bindEvents() {
  searchInput.addEventListener("input", () => {
    state.search = searchInput.value.trim().toLowerCase();
    render();
  });
}

function buildFilterTags() {
  renderTagGroup(yearTags, [{ value: "all", label: "全部年份" }, ...state.catalog.years.map((year) => ({ value: year, label: year }))], "year");
  renderTagGroup(typeTags, [{ value: "all", label: "全部卷型" }, ...state.catalog.paperTypes.map((paperType) => ({ value: paperType, label: paperType }))], "paperType");
}

function renderTagGroup(root, tags, key) {
  root.innerHTML = tags
    .map((tag) => `<button class="tag ${state[key] === tag.value ? "is-active" : ""}" type="button" data-filter-key="${key}" data-filter-value="${escapeHtml(tag.value)}">${escapeHtml(tag.label)}</button>`)
    .join("");

  root.addEventListener("click", (event) => {
    const target = event.target.closest("[data-filter-key]");
    if (!target) {
      return;
    }
    state[key] = target.dataset.filterValue;
    buildFilterTags();
    render();
  });
}

function render() {
  const filtered = state.catalog.items.filter((item) => {
    const haystack = `${item.title} ${item.subject} ${item.year} ${item.paperType}`.toLowerCase();
    if (state.search && !haystack.includes(state.search)) {
      return false;
    }
    if (state.year !== "all" && item.year !== state.year) {
      return false;
    }
    if (state.paperType !== "all" && item.paperType !== state.paperType) {
      return false;
    }
    return true;
  });

  catalogMeta.textContent = `共 ${filtered.length} 套试卷，按科目分组展示。`;

  if (filtered.length === 0) {
    catalogRoot.innerHTML = `<div class="empty-card">没有匹配结果，试试更换搜索词或筛选条件。</div>`;
    return;
  }

  const grouped = groupBySubject(filtered);
  catalogRoot.innerHTML = Object.entries(grouped)
    .map(([subject, exams]) => {
      return `
        <section class="subject-block">
          <div class="subject-head">
            <div>
              <h2>${escapeHtml(subject)}</h2>
              <p>${exams.length} 套本地试卷</p>
            </div>
          </div>
          <div class="subject-grid">
            ${exams.map(renderCard).join("")}
          </div>
        </section>
      `;
    })
    .join("");
}

function groupBySubject(items) {
  return items.reduce((groups, item) => {
    if (!groups[item.subject]) {
      groups[item.subject] = [];
    }
    groups[item.subject].push(item);
    return groups;
  }, {});
}

function renderCard(item) {
  const progress = getProgressState(item.examId);
  const actionLabel = progress.inProgress ? "继续做题" : "进入准备页";
  const statusBadges = [
    progress.hasProgress ? `<span class="status-pill">本地有进度</span>` : "",
    progress.inProgress ? `<span class="status-pill">继续做题</span>` : "",
  ].filter(Boolean).join("");

  return `
    <article class="exam-card">
      <div class="card-top">
        <div class="card-title">
          <span class="meta-chip">${escapeHtml(item.year)}</span>
          <h3>${escapeHtml(item.title)}</h3>
          <p>${escapeHtml(item.subject)} · ${escapeHtml(item.paperType)}</p>
        </div>
        ${statusBadges}
      </div>
      <div class="card-meta">
        <span class="meta-chip">题量 ${item.questionCount}</span>
        <span class="meta-chip">Sections ${item.sectionCount}</span>
        <span class="meta-chip">${escapeHtml(item.paperType)}</span>
      </div>
      <div class="card-actions">
        <a class="card-button" href="/ap/start/?examId=${encodeURIComponent(item.examId)}">${actionLabel}</a>
      </div>
    </article>
  `;
}

function getProgressState(examId) {
  const storageKey = `mokaoai-local-mock:${examId}`;
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw) {
      return { hasProgress: false, inProgress: false };
    }

    const state = JSON.parse(raw);
    const answers = (state.sectionStates || []).flatMap((section) => section.answers || []);
    const hasAnswers = answers.some((answer) => {
      if (Array.isArray(answer)) {
        return answer.length > 0;
      }
      return String(answer || "").trim().length > 0;
    });
    const hasProgress = Boolean(state.startedAt || hasAnswers || state.results);
    const inProgress = hasProgress && !state.results;
    return { hasProgress, inProgress };
  } catch (error) {
    console.warn("Failed to parse local progress", examId, error);
    return { hasProgress: false, inProgress: false };
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
