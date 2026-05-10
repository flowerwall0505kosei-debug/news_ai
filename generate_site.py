import html
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


SITE_NAME = "Tech Compass 505"
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "news.json"
DOCS_DIR = BASE_DIR / "docs"
PUBLIC_JSON_PATH = DOCS_DIR / "news.json"
JST = ZoneInfo("Asia/Tokyo")
CATEGORIES = ["AI", "セキュリティ", "クラウド", "半導体", "ガジェット", "ビジネス", "法規制", "その他"]
CATEGORY_CLASS_MAP = {
    "AI": "ai",
    "セキュリティ": "security",
    "クラウド": "cloud",
    "半導体": "semiconductor",
    "ガジェット": "gadget",
    "ビジネス": "business",
    "法規制": "law",
    "その他": "other",
}


def load_news():
    if not DATA_PATH.exists():
        return []

    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"{DATA_PATH} はJSON配列にしてください。")

    return data


def parse_datetime(value):
    if not value:
        return datetime.min

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            continue

    return datetime.min


def normalize_importance(value):
    try:
        importance = int(value)
    except (TypeError, ValueError):
        return 0

    return max(0, min(5, importance))


def sort_news(news_list):
    return sorted(
        news_list,
        key=lambda item: (
            parse_datetime(item.get("published_at")),
            normalize_importance(item.get("importance")),
            parse_datetime(item.get("created_at")),
        ),
        reverse=True,
    )


def escape_text(value):
    return html.escape(str(value or ""), quote=True)


def format_multiline(value):
    escaped = escape_text(value)
    return escaped.replace("\n", "<br>")


def category_class(value):
    return CATEGORY_CLASS_MAP.get(str(value or "").strip(), "other")


def is_yesterday(news, today):
    published = parse_datetime(news.get("published_at"))
    return published.date() == today - timedelta(days=1)


def is_important(news):
    return normalize_importance(news.get("importance")) >= 4


def is_ai_news(news):
    return str(news.get("category", "")).strip() == "AI"


def render_news_card(news):
    title = escape_text(news.get("title") or "タイトルなし")
    url = escape_text(news.get("url") or "#")
    summary = format_multiline(news.get("summary"))
    importance = normalize_importance(news.get("importance"))
    raw_category = news.get("category") or "未分類"
    category = escape_text(raw_category)
    category_class_name = escape_text(category_class(raw_category))
    reason = format_multiline(news.get("reason"))
    published_at = escape_text(news.get("published_at") or "不明")
    created_at = escape_text(news.get("created_at") or "不明")

    return f"""
    <article class="news-card">
      <div class="news-card__meta">
        <span class="category category--{category_class_name}">{category}</span>
        <time class="published-at">{published_at}</time>
        <span class="importance">重要度 {importance}/5</span>
      </div>
      <h2 class="news-title">{title}</h2>
      <div class="summary">
        <span class="label">要約</span>
        <p>{summary}</p>
      </div>
      <details class="reason">
        <summary>選定理由を見る</summary>
        <p>{reason}</p>
      </details>
      <div class="news-card__footer">
        <a class="article-link" href="{url}" target="_blank" rel="noopener noreferrer">記事を読む</a>
        <span>保存日時: {created_at}</span>
      </div>
    </article>
"""


def render_empty_card(message):
    return f"""
    <article class="news-card news-card--empty">
      <h2 class="news-title">{escape_text(message)}</h2>
    </article>
"""


def render_cards(news_list, empty_message):
    if not news_list:
        return render_empty_card(empty_message)

    return "\n".join(render_news_card(news) for news in news_list)


def render_section(title, subtitle, news_list, empty_message):
    return f"""
    <section class="page-section">
      <div class="section-heading">
        <h2>{escape_text(title)}</h2>
        <p>{escape_text(subtitle)}</p>
      </div>
      <div class="news-list">
{render_cards(news_list, empty_message)}
      </div>
    </section>
"""


def nav_link(prefix, href, label, active, page_id):
    active_attr = ' aria-current="page"' if active == page_id else ""
    return f'<a href="{prefix}{href}"{active_attr}>{label}</a>'


def render_header(prefix, active, generated_at):
    return f"""
  <header class="site-header">
    <div class="header-inner">
      <div class="brand-block">
        <p class="eyebrow">ITmedia RSS + OpenAI</p>
        <a class="site-title" href="{prefix}index.html">{SITE_NAME}</a>
        <p class="subtitle">重要なITニュースを、毎朝コンパクトに。</p>
      </div>
      <form class="site-search" action="{prefix}search/index.html" method="get">
        <label class="visually-hidden" for="site-search-{active}">検索</label>
        <input id="site-search-{active}" name="q" type="search" placeholder="ニュースを検索">
        <button type="submit">検索</button>
      </form>
    </div>
    <nav class="site-nav" aria-label="主要ページ">
      {nav_link(prefix, "index.html", "トップ", active, "home")}
      {nav_link(prefix, "news/index.html", "ニュース一覧", active, "news")}
      {nav_link(prefix, "ai/index.html", "AIニュース", active, "ai")}
      {nav_link(prefix, "search/index.html", "検索", active, "search")}
    </nav>
    <p class="generated-at">最終生成: {escape_text(generated_at)}</p>
  </header>
"""


def build_page(title, description, body_html, active, prefix="", extra_body=""):
    generated_at = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape_text(title)} | {SITE_NAME}</title>
  <meta name="description" content="{escape_text(description)}">
  <link rel="stylesheet" href="{prefix}style.css">
</head>
<body>
{render_header(prefix, active, generated_at)}
  <main>
{body_html}
  </main>
{extra_body}
</body>
</html>
"""


def build_home_page(news_list):
    today = datetime.now(JST).date()
    sorted_news = sort_news(news_list)
    yesterday_news = [news for news in sorted_news if is_yesterday(news, today)][:5]
    important_news = [news for news in sorted_news if is_important(news)][:5]

    body = f"""
{render_section("昨日のニュース", "前日に公開されたニュースから選定しています。", yesterday_news, "昨日のニュースはまだありません。")}
{render_section("直近の重要ニュース", "重要度4以上のニュースを新しい順に表示します。", important_news, "重要ニュースはまだありません。")}
"""

    return build_page(SITE_NAME, "AIが選定したITニュースのトップページです。", body, "home")


def build_news_page(news_list):
    sorted_news = sort_news(news_list)
    body = render_section("ニュース一覧", "保存中の全ニュースを新しい順に表示します。", sorted_news, "ニュースはまだありません。")
    return build_page("ニュース一覧", "保存中の全ITニュース一覧です。", body, "news", "../")


def build_ai_page(news_list):
    ai_news = [news for news in sort_news(news_list) if is_ai_news(news)]
    body = render_section("AIニュース", "カテゴリがAIのニュースだけを表示します。", ai_news, "AIニュースはまだありません。")
    return build_page("AIニュース", "AI関連ニュースだけを集めたページです。", body, "ai", "../")


def build_search_page(news_list):
    embedded_json = json.dumps(sort_news(news_list), ensure_ascii=False).replace("<", "\\u003c")
    options = "\n".join(f'          <option value="{escape_text(category)}">{escape_text(category)}</option>' for category in CATEGORIES)
    body = f"""
    <section class="page-section">
      <div class="section-heading">
        <h1>ニュース検索</h1>
        <p>キーワード、日付、重要度、カテゴリで絞り込めます。</p>
      </div>
      <form id="search-form" class="filter-panel">
        <label>
          <span>キーワード</span>
          <input id="keyword" type="search" placeholder="タイトル・要約・理由を検索">
        </label>
        <label>
          <span>カテゴリ</span>
          <select id="category">
            <option value="">すべて</option>
{options}
          </select>
        </label>
        <label>
          <span>重要度</span>
          <select id="importance">
            <option value="0">すべて</option>
            <option value="5">5以上</option>
            <option value="4">4以上</option>
            <option value="3">3以上</option>
            <option value="2">2以上</option>
            <option value="1">1以上</option>
          </select>
        </label>
        <label>
          <span>開始日</span>
          <input id="date-from" type="date">
        </label>
        <label>
          <span>終了日</span>
          <input id="date-to" type="date">
        </label>
        <div class="filter-actions">
          <button type="submit">検索</button>
          <button type="reset">リセット</button>
        </div>
      </form>
      <p id="search-summary" class="search-summary"></p>
      <div id="search-results" class="news-list"></div>
    </section>
"""
    extra_body = f"""
  <script id="news-data" type="application/json">{embedded_json}</script>
  <script src="../search.js"></script>
"""
    return build_page("ニュース検索", "ITニュースをキーワードやカテゴリで検索できます。", body, "search", "../", extra_body)


def write_page(path, html_text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(html_text)


def publish_json(news_list):
    PUBLIC_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PUBLIC_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(sort_news(news_list), f, ensure_ascii=False, indent=2)
        f.write("\n")


def generate_site():
    news_list = load_news()
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    write_page(DOCS_DIR / "index.html", build_home_page(news_list))
    write_page(DOCS_DIR / "news" / "index.html", build_news_page(news_list))
    write_page(DOCS_DIR / "ai" / "index.html", build_ai_page(news_list))
    write_page(DOCS_DIR / "search" / "index.html", build_search_page(news_list))
    publish_json(news_list)

    print(f"{DOCS_DIR} に静的サイトを生成しました。ニュース件数: {len(news_list)}件")


if __name__ == "__main__":
    generate_site()
