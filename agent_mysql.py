import os
import json
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import feedparser
import mysql.connector
from dotenv import load_dotenv
from openai import OpenAI


RSS_URL = "https://rss.itmedia.co.jp/rss/2.0/news_bursts.xml"

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def get_connection():
    return mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST", "localhost"),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        database=os.environ.get("MYSQL_DATABASE", "news_ai")
    )


def fetch_news():
    feed = feedparser.parse(RSS_URL)

    jst = ZoneInfo("Asia/Tokyo")
    today = datetime.now(jst).date()
    yesterday = today - timedelta(days=1)

    news_items = []

    for entry in feed.entries:
        title = getattr(entry, "title", "")
        url = getattr(entry, "link", "")

        if not title or not url:
            continue

        published_at = None
        published_date = None

        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published_utc = datetime(*entry.published_parsed[:6], tzinfo=ZoneInfo("UTC"))
            published_at = published_utc.astimezone(jst)
            published_date = published_at.date()

        if published_date == yesterday:
            news_items.append({
                "title": title,
                "url": url,
                "published_at": published_at.strftime("%Y-%m-%d %H:%M:%S") if published_at else None
            })

    # 保険：昨日の記事がRSS内に残っていない場合は最新10件を候補にする
    if not news_items:
        print("昨日公開の記事が見つからないため、RSS最新10件を候補にします。")

        for entry in feed.entries[:10]:
            title = getattr(entry, "title", "")
            url = getattr(entry, "link", "")

            if not title or not url:
                continue

            published_at = None

            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_utc = datetime(*entry.published_parsed[:6], tzinfo=ZoneInfo("UTC"))
                published_at = published_utc.astimezone(jst)

            news_items.append({
                "title": title,
                "url": url,
                "published_at": published_at.strftime("%Y-%m-%d %H:%M:%S") if published_at else None
            })

    return news_items


def extract_json(text):
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```json", "", text)
        text = re.sub(r"^```", "", text)
        text = re.sub(r"```$", "", text)
        text = text.strip()

    return json.loads(text)


def select_and_summarize_news(news_items):
    news_text = ""

    for i, item in enumerate(news_items, start=1):
        news_text += f"""
{i}.
タイトル: {item["title"]}
URL: {item["url"]}
公開日時: {item.get("published_at")}
"""

    prompt = f"""
あなたはITニュース編集者です。

以下のITニュース一覧から、知っておく価値が高いニュースを最大5件選んでください。

選定基準:
- AI、セキュリティ、クラウド、半導体、OS、スマホ、ビジネス、法規制、プライバシーに関するニュースを重視
- 技術トレンド、企業戦略、社会、仕事、生活への影響が大きいものを優先
- 単なる小ネタ、広告色の強い記事、ランキング、キャンペーン、限定的な製品紹介は優先度を下げる
- 似たニュースがある場合は代表的な1件だけ選ぶ

重要度は1〜5で評価してください。
評価は厳しめに行ってください。

重要度5:
- 業界全体、社会、規制、大企業の戦略に大きな影響がある
- 多くの企業・開発者・ユーザーの行動に影響する可能性が高い
- 主要AIモデルの大幅アップデート、大規模サイバー攻撃、法規制、巨大企業の戦略転換など

重要度4:
- 広い範囲の企業・ユーザー・開発者に影響しそう
- 今後の技術トレンドやビジネスの流れを理解する上で重要
- ただし社会全体を揺らすほどではない

重要度3:
- ITニュースとして標準的に重要
- 特定分野では知っておく価値がある
- 新サービス、新機能、企業提携、製品アップデートなど

重要度2:
- 話題性はあるが影響範囲が狭い
- 特定企業・特定製品・一部ユーザー向け
- 周辺機器、限定的な製品情報、キャンペーンなど

重要度1:
- 小ネタ、PR寄り、ランキング、個別事例、軽い話題
- 技術・社会・ビジネスへの影響が小さい

追加ルール:
- 重要度5は本当に大きな影響がある場合だけ使う
- 迷ったら高く評価せず低めにつける
- 最大5件まで選ぶが、重要なニュースが少ない場合は3件以下でもよい

ニュース一覧:
{news_text}

各ニュースについて以下を出力:
- title
- url
- summary: 3行以内の日本語要約
- importance: 1〜5
- category: AI, セキュリティ, クラウド, 半導体, ガジェット, ビジネス, 法規制, その他 のどれか
- reason: 選定理由を短く

必ずJSON配列だけで返してください。
説明文やコードブロックは不要です。
"""

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt
    )

    return extract_json(response.output_text)


def save_news(title, url, summary, importance, category, reason, published_at):
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    INSERT IGNORE INTO news
    (title, url, summary, importance, category, reason, published_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(sql, (title, url, summary, importance, category, reason, published_at))
    conn.commit()

    cursor.close()
    conn.close()


def run_agent():
    news_items = fetch_news()

    if not news_items:
        print("候補ニュースがありませんでした。")
        return

    selected_news = select_and_summarize_news(news_items)

    published_map = {
        item["url"]: item.get("published_at")
        for item in news_items
    }

    for item in selected_news:
        save_news(
            item["title"],
            item["url"],
            item["summary"],
            item["importance"],
            item["category"],
            item["reason"],
            published_map.get(item["url"])
        )

        print(f"保存完了: {item['title']} / 重要度{item['importance']} / {item['category']}")


if __name__ == "__main__":
    run_agent()
