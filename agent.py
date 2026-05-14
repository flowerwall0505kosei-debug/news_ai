import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import feedparser
from dotenv import load_dotenv
from openai import OpenAI


RSS_URL = "https://rss.itmedia.co.jp/rss/2.0/news_bursts.xml"
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
NEWS_JSON_PATH = DATA_DIR / "news.json"
JST = ZoneInfo("Asia/Tokyo")

CATEGORIES = {
    "AI",
    "セキュリティ",
    "クラウド",
    "半導体",
    "ガジェット",
    "ビジネス",
    "法規制",
    "その他",
}

RETENTION_DAYS = {
    1: 7,
    2: 7,
    3: 30,
    4: 183,
    5: None,
}


def now_jst_string():
    return datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")


def parse_entry_datetime(entry):
    parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if not parsed:
        return None

    published_utc = datetime(*parsed[:6], tzinfo=ZoneInfo("UTC"))
    return published_utc.astimezone(JST)


def fetch_news():
    feed = feedparser.parse(RSS_URL)

    today = datetime.now(JST).date()
    yesterday = today - timedelta(days=1)
    news_items = []

    for entry in feed.entries:
        title = getattr(entry, "title", "").strip()
        url = getattr(entry, "link", "").strip()
        published_at = parse_entry_datetime(entry)

        if not title or not url:
            continue

        if published_at and published_at.date() == yesterday:
            news_items.append(
                {
                    "title": title,
                    "url": url,
                    "published_at": published_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

    if news_items:
        return news_items

    print("昨日公開の記事がRSS内に見つからないため、RSS最新10件を候補にします。")

    for entry in feed.entries[:10]:
        title = getattr(entry, "title", "").strip()
        url = getattr(entry, "link", "").strip()
        published_at = parse_entry_datetime(entry)

        if not title or not url:
            continue

        news_items.append(
            {
                "title": title,
                "url": url,
                "published_at": published_at.strftime("%Y-%m-%d %H:%M:%S") if published_at else "",
            }
        )

    return news_items


def extract_json(text):
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    data = json.loads(text)

    if not isinstance(data, list):
        raise ValueError("OpenAI APIの返答がJSON配列ではありません。")

    return data


def select_and_summarize_news(news_items):
    load_dotenv(BASE_DIR / ".env")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(".env または環境変数に OPENAI_API_KEY を設定してください。")

    client = OpenAI(api_key=api_key)
    model = os.environ.get("OPENAI_MODEL", "gpt-5-mini")
    news_json = json.dumps(news_items, ensure_ascii=False, indent=2)

    prompt = f"""
あなたはITニュース編集者です。

以下のITmedia RSS候補記事から、知っておく価値が高いニュースを最大5件選んでください。
重要なニュースが少ない場合は、5件未満でも構いません。

選定基準:
- AI、セキュリティ、クラウド、半導体、OS、スマートフォン、ビジネス、法規制、プライバシーに関するニュースを重視する
- 技術トレンド、企業戦略、社会、仕事、生活への影響が大きいものを優先する
- 単なる小ネタ、広告色の強い記事、ランキング、キャンペーン、限定的な製品紹介は優先度を下げる
- 似たニュースが複数ある場合は、代表的な1件だけを選ぶ

重要度は1から5の整数で評価してください。
評価は厳しめにしてください。
重要度は保存期間にも使うため、迷った場合は高くしすぎず低めに評価してください。
追加ルール:
- 重要度4は社会、業界、開発者の広範囲に影響がある場合だけにしてください。
- 新製品発表、キャンペーン、個別企業ニュースは原則3以下にしてください。
- 個人、芸能、炎上系の話題はIT社会への影響が明確でなければ2以下にしてください。
- セキュリティ事故は被害規模、影響を受ける利用者数、企業規模、再発防止への示唆で判定してください。
- AIニュースは「AI」という言葉があるだけでは高評価にせず、技術、規制、社会、業務、開発者への影響で判定してください。

重要度5:
- 業界全体、社会、法規制、大企業の戦略に大きな影響がある
- 多くの企業、開発者、ユーザーの行動に影響する可能性が高い
- 主要AIモデルの大型アップデート、大規模サイバー攻撃、法規制、巨大企業の戦略転換など
- 例外的に重要なニュースだけに使う

重要度4:
- 広い範囲の企業、ユーザー、開発者に影響しそう
- 今後の技術トレンドやビジネスの流れを理解する上で重要
- ニュース全体の中でも明確に重要なものだけに使う

重要度3:
- ITニュースとして標準的に重要
- 特定分野では知っておく価値がある

重要度2:
- 話題性はあるが影響範囲が狭い
- 特定企業、特定製品、一部ユーザー向け

重要度1:
- 小ネタ、PR寄り、ランキング、個別事例など
- 技術、社会、ビジネスへの影響が小さい

カテゴリは必ず次のどれかにしてください:
AI, セキュリティ, クラウド, 半導体, ガジェット, ビジネス, 法規制, その他

候補記事:
{news_json}

次のキーを持つJSON配列だけを返してください。説明文やコードブロックは不要です。
- title
- url
- summary: 3行以内の日本語要約
- importance: 1から5の整数
- category
- reason: 選定理由を短く
- published_at
"""

    response = client.responses.create(
        model=model,
        input=prompt,
    )

    return extract_json(response.output_text)


def load_existing_news():
    if not NEWS_JSON_PATH.exists():
        return []

    with NEWS_JSON_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"{NEWS_JSON_PATH} はJSON配列にしてください。")

    return data


def normalize_importance(value):
    try:
        importance = int(value)
    except (TypeError, ValueError):
        return 3

    return min(5, max(1, importance))


def normalize_news_item(item, published_map):
    url = str(item.get("url", "")).strip()
    title = str(item.get("title", "")).strip()

    if not title or not url:
        return None

    category = str(item.get("category", "その他")).strip()
    if category not in CATEGORIES:
        category = "その他"

    return {
        "title": title,
        "url": url,
        "summary": str(item.get("summary", "")).strip(),
        "importance": normalize_importance(item.get("importance")),
        "category": category,
        "reason": str(item.get("reason", "")).strip(),
        "published_at": str(item.get("published_at") or published_map.get(url) or "").strip(),
        "created_at": now_jst_string(),
    }


def parse_datetime_for_sort(value):
    if not value:
        return datetime.min

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            continue

    return datetime.min


def sort_news(news_list):
    return sorted(
        news_list,
        key=lambda item: (
            parse_datetime_for_sort(item.get("published_at")),
            normalize_importance(item.get("importance")),
            parse_datetime_for_sort(item.get("created_at")),
        ),
        reverse=True,
    )


def retention_reference_datetime(item):
    published_at = parse_datetime_for_sort(item.get("published_at"))
    if published_at != datetime.min:
        return published_at

    return parse_datetime_for_sort(item.get("created_at"))


def apply_retention(news_list):
    today = datetime.now(JST).date()
    kept_news = []
    removed_count = 0

    for item in news_list:
        importance = normalize_importance(item.get("importance"))
        retention_days = RETENTION_DAYS.get(importance, 7)

        if retention_days is None:
            kept_news.append(item)
            continue

        reference_date = retention_reference_datetime(item).date()
        if reference_date == datetime.min.date():
            kept_news.append(item)
            continue

        if reference_date >= today - timedelta(days=retention_days):
            kept_news.append(item)
        else:
            removed_count += 1

    if removed_count:
        print(f"保存期間を過ぎたニュースを{removed_count}件整理しました。")

    return kept_news


def save_news_json(selected_news, candidate_news):
    existing_news = load_existing_news()
    published_map = {item["url"]: item.get("published_at", "") for item in candidate_news}
    news_by_url = {
        str(item.get("url", "")).strip(): item
        for item in existing_news
        if str(item.get("url", "")).strip()
    }

    saved_count = 0
    updated_count = 0

    for item in selected_news:
        normalized = normalize_news_item(item, published_map)
        if not normalized:
            continue

        url = normalized["url"]

        if url in news_by_url:
            original_created_at = news_by_url[url].get("created_at")
            news_by_url[url].update(normalized)
            if original_created_at:
                news_by_url[url]["created_at"] = original_created_at
            updated_count += 1
            print(f"更新: {normalized['title']} / 重要度{normalized['importance']} / {normalized['category']}")
        else:
            news_by_url[url] = normalized
            saved_count += 1
            print(f"保存: {normalized['title']} / 重要度{normalized['importance']} / {normalized['category']}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    sorted_news = sort_news(apply_retention(list(news_by_url.values())))
    with NEWS_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(sorted_news, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"{NEWS_JSON_PATH} を更新しました。新規{saved_count}件、更新{updated_count}件。")


def run_agent():
    news_items = fetch_news()

    if not news_items:
        print("候補ニュースがありませんでした。")
        return

    print(f"候補ニュース: {len(news_items)}件")

    selected_news = select_and_summarize_news(news_items)

    if not selected_news:
        print("OpenAI APIがニュースを選定しませんでした。")
        return

    save_news_json(selected_news, news_items)


if __name__ == "__main__":
    run_agent()
