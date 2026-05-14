(() => {
  const COOKIE_NAME = "favorite_items_v1";
  const MAX_FAVORITES = 50;
  const LONG_TERM_SECONDS = 60 * 60 * 24 * 400;

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

  function normalizeId(id) {
    return String(id || "").trim();
  }

  function getNewsId(news) {
    const url = normalizeId(news && news.url);
    if (url) {
      return url;
    }

    const title = normalizeId(news && news.title);
    const publishedAt = normalizeId(news && news.published_at);
    return `${title}|${publishedAt}`.replace(/^\||\|$/g, "");
  }

  function getCookieValue(name) {
    const cookies = document.cookie ? document.cookie.split("; ") : [];

    for (const cookie of cookies) {
      const separatorIndex = cookie.indexOf("=");
      const cookieName = separatorIndex >= 0 ? cookie.slice(0, separatorIndex) : cookie;

      if (cookieName === name) {
        return separatorIndex >= 0 ? cookie.slice(separatorIndex + 1) : "";
      }
    }

    return "";
  }

  function cleanFavoriteIds(ids) {
    const cleanIds = [];

    for (const id of ids) {
      const normalizedId = normalizeId(id);
      if (normalizedId && !cleanIds.includes(normalizedId)) {
        cleanIds.push(normalizedId);
      }
    }

    return cleanIds.slice(0, MAX_FAVORITES);
  }

  function getFavoriteIds() {
    const value = getCookieValue(COOKIE_NAME);
    if (!value) {
      return [];
    }

    try {
      const parsed = JSON.parse(decodeURIComponent(value));
      return Array.isArray(parsed) ? cleanFavoriteIds(parsed) : [];
    } catch {
      return [];
    }
  }

  function setFavoriteIds(ids) {
    const cleanIds = cleanFavoriteIds(ids);
    const value = encodeURIComponent(JSON.stringify(cleanIds));
    const secure = window.location.protocol === "https:" ? "; Secure" : "";

    document.cookie = [
      `${COOKIE_NAME}=${value}`,
      `Max-Age=${LONG_TERM_SECONDS}`,
      "Path=/",
      "SameSite=Lax",
    ].join("; ") + secure;
  }

  function refreshFavoriteCookie() {
    const ids = getFavoriteIds();
    if (ids.length > 0) {
      setFavoriteIds(ids);
    }
  }

  function isFavorite(id) {
    return getFavoriteIds().includes(normalizeId(id));
  }

  function addFavorite(id) {
    const normalizedId = normalizeId(id);
    if (!normalizedId) {
      return { ok: false, reason: "invalid" };
    }

    const ids = getFavoriteIds();
    if (ids.includes(normalizedId)) {
      return { ok: true };
    }

    if (ids.length >= MAX_FAVORITES) {
      return { ok: false, reason: "limit" };
    }

    setFavoriteIds([normalizedId, ...ids]);
    return { ok: true };
  }

  function removeFavorite(id) {
    const normalizedId = normalizeId(id);
    setFavoriteIds(getFavoriteIds().filter((favoriteId) => favoriteId !== normalizedId));
  }

  function toggleFavorite(id) {
    const normalizedId = normalizeId(id);

    if (isFavorite(normalizedId)) {
      removeFavorite(normalizedId);
      return { favorited: false };
    }

    const result = addFavorite(normalizedId);
    return {
      favorited: result.ok,
      reason: result.reason,
    };
  }

  function showMessage(message) {
    let toast = document.getElementById("favorite-toast");

    if (!toast) {
      toast = document.createElement("div");
      toast.id = "favorite-toast";
      toast.className = "favorite-toast";
      toast.setAttribute("role", "status");
      toast.setAttribute("aria-live", "polite");
      document.body.appendChild(toast);
    }

    window.clearTimeout(showMessage.timerId);
    toast.textContent = message;
    toast.classList.add("favorite-toast--visible");

    showMessage.timerId = window.setTimeout(() => {
      toast.classList.remove("favorite-toast--visible");
    }, 2400);
  }

  function renderFavoriteButton(news) {
    const id = escapeHtml(getNewsId(news));
    const title = escapeHtml(news && news.title ? news.title : "ニュース");

    return `
        <button class="favorite-button" type="button" data-favorite-button data-favorite-id="${id}" data-favorite-title="${title}" aria-pressed="false" aria-label="お気に入りに追加: ${title}" title="お気に入りに追加">
          <span class="favorite-button__icon" aria-hidden="true">☆</span>
          <span class="favorite-button__text visually-hidden">お気に入り</span>
        </button>
    `;
  }

  function setButtonState(button, favorited) {
    const title = button.dataset.favoriteTitle || "ニュース";
    const icon = button.querySelector(".favorite-button__icon");
    const text = button.querySelector(".favorite-button__text");

    button.setAttribute("aria-pressed", favorited ? "true" : "false");
    button.setAttribute(
      "aria-label",
      `${favorited ? "お気に入りから削除" : "お気に入りに追加"}: ${title}`
    );
    button.title = favorited ? "お気に入りから削除" : "お気に入りに追加";

    if (icon) {
      icon.textContent = favorited ? "★" : "☆";
    }

    if (text) {
      text.textContent = favorited ? "お気に入り済み" : "お気に入り";
    }
  }

  function syncFavoriteButtons(root = document) {
    root.querySelectorAll("[data-favorite-button]").forEach((button) => {
      setButtonState(button, isFavorite(button.dataset.favoriteId));
    });
  }

  function initFavoriteButtons(root = document) {
    root.querySelectorAll("[data-favorite-button]").forEach((button) => {
      if (button.dataset.favoriteReady === "true") {
        return;
      }

      button.dataset.favoriteReady = "true";
      button.addEventListener("click", (event) => {
        event.preventDefault();

        const result = toggleFavorite(button.dataset.favoriteId);
        if (result.reason === "limit") {
          showMessage(`お気に入りは${MAX_FAVORITES}件まで登録できます。`);
          return;
        }

        syncFavoriteButtons(document);

        if (document.getElementById("favorites-results")) {
          renderFavoritesPage();
        }
      });
    });

    syncFavoriteButtons(root);
  }

  function readEmbeddedNews() {
    const embeddedData = document.getElementById("news-data");
    if (!embeddedData) {
      return [];
    }

    try {
      const parsed = JSON.parse(embeddedData.textContent);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  function renderNewsCard(news) {
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

    return `
    <article class="news-card">
      <div class="news-card__head">
        <div class="news-card__meta">
          <span class="category category--${categoryClassName}">${category}</span>
          <time class="published-at">${publishedAt}</time>
          <span class="importance">重要度 ${importance}/5</span>
        </div>
${renderFavoriteButton(news)}
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

  function renderFavoritesPage() {
    const results = document.getElementById("favorites-results");
    if (!results) {
      return;
    }

    const summary = document.getElementById("favorites-summary");
    const newsById = new Map();

    for (const news of readEmbeddedNews()) {
      const id = getNewsId(news);
      if (id) {
        newsById.set(id, news);
      }
    }

    const storedIds = getFavoriteIds();
    const availableIds = storedIds.filter((id) => newsById.has(id));

    if (availableIds.length !== storedIds.length) {
      setFavoriteIds(availableIds);
    }

    const favoriteNews = availableIds.map((id) => newsById.get(id));

    if (summary) {
      summary.textContent = `${favoriteNews.length}件のお気に入りがあります。`;
    }

    results.innerHTML = favoriteNews.length
      ? favoriteNews.map(renderNewsCard).join("")
      : '<article class="news-card news-card--empty"><h2 class="news-title">お気に入りはまだありません。</h2></article>';

    initFavoriteButtons(results);
  }

  window.TechCompassFavorites = {
    addFavorite,
    getFavoriteIds,
    initFavoriteButtons,
    isFavorite,
    removeFavorite,
    renderFavoriteButton,
    renderFavoritesPage,
    renderNewsCard,
    setFavoriteIds,
    syncFavoriteButtons,
    toggleFavorite,
  };

  document.addEventListener("DOMContentLoaded", () => {
    refreshFavoriteCookie();
    initFavoriteButtons();
    renderFavoritesPage();
  });
})();
