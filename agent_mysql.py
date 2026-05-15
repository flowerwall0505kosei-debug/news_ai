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

以下のITニュース一覧を、まず重要度0〜5で絶対評価してください。
そのうえで、重要度1以上の記事だけから、知っておく価値が高いニュースを最大5件選んでください。
重要度0の記事は、候補が5件未満でも絶対に選ばないでください。

選定基準:
- AI、セキュリティ、クラウド、半導体、OS、スマホ、ビジネス、法規制、プライバシーに関するニュースを重視
- 技術トレンド、企業戦略、社会、仕事、生活への影響が大きいものを優先
- 単なる小ネタ、広告色の強い記事、ランキング、キャンペーン、限定的な製品紹介は優先度を下げる
- 似たニュースがある場合は代表的な1件だけ選ぶ

重要度は0〜5で評価してください。
評価は厳しめに行ってください。

重要度0:
- 掲載対象外
- 読者との関係が薄い、既報の焼き直し、噂段階、広告・ランキング・軽い話題
- 変化が小さく、知っても理解や判断にほぼ影響しない
- 枠が余っても選ばない

重要度1:
- 掲載候補ではあるが低重要
- 読者に一定の関係があり、事実として新しい情報がある
- 影響は特定企業、特定製品、一部ユーザー、小規模な更新に限られる
- 知らなくても、多くの読者の判断はほぼ変わらない

重要度2:
- 掲載価値が明確にある
- 読者に関係する新情報があり、一定数の人の理解や判断に役立つ
- 単なる小ネタではなく、今後を追う意味がある
- ただし影響範囲または変化量は限定的

重要度3:
- 多くの読者が押さえる価値がある
- 主要企業、主要製品、主要技術、政策のいずれかに関する動き
- 製品選択、事業判断、業界理解、今後の見通しのいずれかに明確な影響がある

重要度4:
- 多くの読者に関係し、主要企業、市場、技術動向、政策に関わる
- 読者の判断や行動を実際に変えうる
- 今後の競争環境、業界の流れ、主要プラットフォームの使われ方に強く影響する

重要度5:
- 重要度4の条件を満たしたうえで、安全性、セキュリティ、法規制、社会的混乱のいずれかで重大なリスクがある
- 影響が広範囲かつ急速に及ぶ、または取り返しのつきにくい損失につながる
- 大規模サイバー攻撃、重大な規制変更、広範囲の障害、社会的混乱を伴う事故など

追加ルール:
- 重要度5は本当に大きな影響がある場合だけ使う
- 0と1の境界は「載せる理由があるか」
- 1と2の境界は「掲載価値が明確か」
- 2と3の境界は「一部の読者に有用か、多くの読者が押さえるべきか」
- 3と4の境界は「知っておくべきか、判断や行動を変えうるか」
- 単なる新製品発表、新機能追加、キャンペーン、個別企業ニュースは原則2以下。広い波及がある場合だけ3以上
- 迷ったら高く評価せず低めにつける
- 最大5件まで選ぶが、重要なニュースが少ない場合は3件以下でもよい

ニュース一覧:
{news_text}

各ニュースについて以下を出力:
- title
- url
- summary: 3行以内の日本語要約
- importance: 1〜5。重要度0の記事は返さない
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


def normalize_importance(value):
    try:
        importance = int(value)
    except (TypeError, ValueError):
        return 0

    return min(5, max(0, importance))


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
        importance = normalize_importance(item.get("importance"))
        if importance == 0:
            print(f"除外: {item.get('title', 'タイトルなし')} / 重要度0")
            continue

        save_news(
            item["title"],
            item["url"],
            item["summary"],
            importance,
            item["category"],
            item["reason"],
            published_map.get(item["url"])
        )

        print(f"保存完了: {item['title']} / 重要度{importance} / {item['category']}")


if __name__ == "__main__":
    run_agent()
