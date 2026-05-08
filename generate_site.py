import html
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "news.json"
DOCS_DIR = BASE_DIR / "docs"
INDEX_PATH = DOCS_DIR / "index.html"
JST = ZoneInfo("Asia/Tokyo")


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


def render_news_card(news):
    title = escape_text(news.get("title") or "タイトルなし")
    url = escape_text(news.get("url") or "#")
    summary = format_multiline(news.get("summary"))
    importance = normalize_importance(news.get("importance"))
    category = escape_text(news.get("category") or "未分類")
    reason = format_multiline(news.get("reason"))
    published_at = escape_text(news.get("published_at") or "不明")
    created_at = escape_text(news.get("created_at") or "不明")

    return f"""
    <article class="news-card">
      <div class="news-card__meta">
        <span class="category">{category}</span>
        <span class="importance">重要度 {importance}/5</span>
      </div>
      <h2 class="news-title">{title}</h2>
      <dl class="news-details">
        <div>
          <dt>公開日時</dt>
          <dd>{published_at}</dd>
        </div>
        <div>
          <dt>要約</dt>
          <dd>{summary}</dd>
        </div>
        <div>
          <dt>選定理由</dt>
          <dd>{reason}</dd>
        </div>
      </dl>
      <div class="news-card__footer">
        <a class="article-link" href="{url}" target="_blank" rel="noopener noreferrer">記事を読む</a>
        <span>保存日時: {created_at}</span>
      </div>
    </article>
"""


def build_html(news_list):
    generated_at = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
    sorted_news = sort_news(news_list)

    if sorted_news:
        cards_html = "\n".join(render_news_card(news) for news in sorted_news)
    else:
        cards_html = """
    <article class="news-card news-card--empty">
      <h2 class="news-title">ニュースはまだありません</h2>
      <p>先に <code>python agent.py</code> を実行すると、AIが選定したニュースがここに表示されます。</p>
    </article>
"""

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI ITニュース</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header class="site-header">
    <div>
      <p class="eyebrow">ITmedia RSS + OpenAI</p>
      <h1>AI ITニュース</h1>
      <p class="subtitle">AIが選定・要約したITニュース一覧</p>
    </div>
    <p class="generated-at">最終生成: {escape_text(generated_at)}</p>
  </header>

  <main class="news-list">
{cards_html}
  </main>
</body>
</html>
"""


def generate_site():
    news_list = load_news()
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    with INDEX_PATH.open("w", encoding="utf-8") as f:
        f.write(build_html(news_list))

    print(f"{INDEX_PATH} を生成しました。ニュース件数: {len(news_list)}件")


if __name__ == "__main__":
    generate_site()
