const embeddedData = document.getElementById("news-data");
const allNews = embeddedData ? JSON.parse(embeddedData.textContent) : [];

const form = document.getElementById("search-form");
const keywordInput = document.getElementById("keyword");
const categoryInput = document.getElementById("category");
const importanceInput = document.getElementById("importance");
const dateFromInput = document.getElementById("date-from");
const dateToInput = document.getElementById("date-to");
const summary = document.getElementById("search-summary");
const results = document.getElementById("search-results");

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatMultiline(value) {
  return escapeHtml(value).replace(/\n/g, "<br>");
}

function normalizeImportance(value) {
  const importance = Number.parseInt(value, 10);
  if (Number.isNaN(importance)) {
    return 0;
  }
  return Math.max(0, Math.min(5, importance));
}

function categoryClass(value) {
  const classes = {
    AI: "ai",
    セキュリティ: "security",
    クラウド: "cloud",
    半導体: "semiconductor",
    ガジェット: "gadget",
    ビジネス: "business",
    法規制: "law",
    その他: "other",
  };

  return classes[String(value || "").trim()] || "other";
}

function dateOnly(value) {
  return String(value || "").slice(0, 10);
}

function getFilters() {
  return {
    keyword: keywordInput.value.trim().toLowerCase(),
    category: categoryInput.value,
    importance: normalizeImportance(importanceInput.value),
    dateFrom: dateFromInput.value,
    dateTo: dateToInput.value,
  };
}

function matches(news, filters) {
  const targetText = [
    news.title,
    news.summary,
    news.reason,
    news.category,
  ].join(" ").toLowerCase();
  const publishedDate = dateOnly(news.published_at);

  if (filters.keyword && !targetText.includes(filters.keyword)) {
    return false;
  }

  if (filters.category && news.category !== filters.category) {
    return false;
  }

  if (filters.importance && normalizeImportance(news.importance) < filters.importance) {
    return false;
  }

  if ((filters.dateFrom || filters.dateTo) && !publishedDate) {
    return false;
  }

  if (filters.dateFrom && publishedDate && publishedDate < filters.dateFrom) {
    return false;
  }

  if (filters.dateTo && publishedDate && publishedDate > filters.dateTo) {
    return false;
  }

  return true;
}

function renderCard(news) {
  const title = escapeHtml(news.title || "タイトルなし");
  const url = escapeHtml(news.url || "#");
  const summaryText = formatMultiline(news.summary || "");
  const reason = formatMultiline(news.reason || "");
  const rawCategory = news.category || "未分類";
  const category = escapeHtml(rawCategory);
  const categoryClassName = escapeHtml(categoryClass(rawCategory));
  const importance = normalizeImportance(news.importance);
  const publishedAt = escapeHtml(news.published_at || "不明");
  const createdAt = escapeHtml(news.created_at || "不明");
  const favoriteButton = window.TechCompassFavorites
    ? window.TechCompassFavorites.renderFavoriteButton(news)
    : "";

  return `
    <article class="news-card">
      <div class="news-card__head">
        <div class="news-card__meta">
          <span class="category category--${categoryClassName}">${category}</span>
          <time class="published-at">${publishedAt}</time>
          <span class="importance">重要度 ${importance}/5</span>
        </div>
${favoriteButton}
      </div>
      <h2 class="news-title">${title}</h2>
      <div class="summary">
        <span class="label">要約</span>
        <p>${summaryText}</p>
      </div>
      <details class="reason">
        <summary>選定理由を見る</summary>
        <p>${reason}</p>
      </details>
      <div class="news-card__footer">
        <a class="article-link" href="${url}" target="_blank" rel="noopener noreferrer">記事を読む</a>
        <span>保存日時: ${createdAt}</span>
      </div>
    </article>
  `;
}

function updateUrl(filters) {
  const params = new URLSearchParams();

  if (filters.keyword) params.set("q", filters.keyword);
  if (filters.category) params.set("category", filters.category);
  if (filters.importance) params.set("importance", String(filters.importance));
  if (filters.dateFrom) params.set("from", filters.dateFrom);
  if (filters.dateTo) params.set("to", filters.dateTo);

  const nextUrl = `${window.location.pathname}${params.toString() ? `?${params}` : ""}`;
  window.history.replaceState(null, "", nextUrl);
}

function render() {
  const filters = getFilters();
  const filteredNews = allNews.filter((news) => matches(news, filters));

  summary.textContent = `${filteredNews.length}件のニュースが見つかりました。`;
  results.innerHTML = filteredNews.length
    ? filteredNews.map(renderCard).join("")
    : '<article class="news-card news-card--empty"><h2 class="news-title">条件に合うニュースはありません。</h2></article>';

  window.TechCompassFavorites?.initFavoriteButtons(results);
  updateUrl(filters);
}

function restoreFromUrl() {
  const params = new URLSearchParams(window.location.search);
  keywordInput.value = params.get("q") || "";
  categoryInput.value = params.get("category") || "";
  importanceInput.value = params.get("importance") || "0";
  dateFromInput.value = params.get("from") || "";
  dateToInput.value = params.get("to") || "";
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  render();
});

form.addEventListener("reset", () => {
  window.setTimeout(render, 0);
});

restoreFromUrl();
render();
