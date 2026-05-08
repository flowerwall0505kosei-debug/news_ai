import os

from flask import Flask
import mysql.connector
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


def get_connection():
    return mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST", "localhost"),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        database=os.environ.get("MYSQL_DATABASE", "news_ai")
    )


@app.route("/")
def index():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM news
        ORDER BY published_at DESC, importance DESC, created_at DESC
    """)

    news_list = cursor.fetchall()

    cursor.close()
    conn.close()

    html = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>AI ITニュース</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f5f5f5;
                margin: 0;
                padding: 24px;
                color: #222;
            }

            h1 {
                margin-bottom: 8px;
            }

            .subtitle {
                color: #666;
                margin-bottom: 24px;
            }

            .news-card {
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 16px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.05);
            }

            .news-title {
                margin-top: 0;
                margin-bottom: 12px;
                font-size: 20px;
            }

            .meta {
                font-size: 14px;
                color: #555;
                margin-bottom: 8px;
            }

            .label {
                font-weight: bold;
            }

            .summary,
            .reason {
                line-height: 1.6;
                margin-top: 8px;
            }

            .importance {
                font-weight: bold;
            }

            a {
                color: #0066cc;
                text-decoration: none;
            }

            a:hover {
                text-decoration: underline;
            }

            .footer {
                font-size: 12px;
                color: #888;
                margin-top: 12px;
            }
        </style>
    </head>
    <body>
        <h1>AI ITニュース</h1>
        <p class="subtitle">AIが選定・要約したITニュース一覧</p>
    """

    if not news_list:
        html += """
        <div class="news-card">
            <p>まだニュースが保存されていません。</p>
        </div>
        """

    for news in news_list:
        title = news.get("title") or "タイトルなし"
        url = news.get("url") or "#"
        summary = news.get("summary") or ""
        importance = news.get("importance") or "未設定"
        category = news.get("category") or "未分類"
        reason = news.get("reason") or ""
        published_at = news.get("published_at") or "不明"
        created_at = news.get("created_at") or "不明"

        html += f"""
        <div class="news-card">
            <h2 class="news-title">{title}</h2>

            <div class="meta">
                <span class="label">カテゴリ:</span> {category}
            </div>

            <div class="meta">
                <span class="label">重要度:</span>
                <span class="importance">{importance}</span>
            </div>

            <div class="meta">
                <span class="label">公開日時:</span> {published_at}
            </div>

            <div class="summary">
                <span class="label">要約:</span><br>
                {summary}
            </div>

            <div class="reason">
                <span class="label">選定理由:</span><br>
                {reason}
            </div>

            <p>
                <a href="{url}" target="_blank">記事を開く</a>
            </p>

            <div class="footer">
                保存日時: {created_at}
            </div>
        </div>
        """

    html += """
    </body>
    </html>
    """

    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
