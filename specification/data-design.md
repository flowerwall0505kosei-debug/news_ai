# データ設計書

## 1. データ保存方式

現行の主保存先は `data/news.json` です。

`agent.py` がニュースを保存し、`generate_site.py` がこのJSONを読み込んで静的サイトを生成します。

## 2. `data/news.json`

形式はJSON配列です。各要素が1件のニュースを表します。

### 2.1 スキーマ

| 項目 | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| `title` | string | 必須 | ニュースタイトル |
| `url` | string | 必須 | 記事URL。重複判定のキーとして使う |
| `summary` | string | 任意 | OpenAI APIが生成した3行以内の日本語要約 |
| `importance` | number | 任意 | 1から5の重要度 |
| `category` | string | 任意 | ニュースカテゴリ |
| `reason` | string | 任意 | 選定理由 |
| `published_at` | string | 任意 | 記事公開日時。形式は `YYYY-MM-DD HH:MM:SS` |
| `created_at` | string | 任意 | 保存日時。形式は `YYYY-MM-DD HH:MM:SS` |

### 2.2 例

```json
{
  "title": "OpenAI、企業向けAI導入支援を本格展開",
  "url": "https://www.itmedia.co.jp/news/articles/example.html",
  "summary": "OpenAIが企業向けAI導入支援を本格化した。",
  "importance": 4,
  "category": "AI",
  "reason": "企業のAI導入や市場競争に影響するため。",
  "published_at": "2026-05-12 06:31:00",
  "created_at": "2026-05-13 17:15:09"
}
```

## 3. カテゴリ

`agent.py` と `generate_site.py` で扱うカテゴリは次の8種類です。

- `AI`
- `セキュリティ`
- `クラウド`
- `半導体`
- `ガジェット`
- `ビジネス`
- `法規制`
- `その他`

OpenAI APIの返答に未知のカテゴリが含まれる場合、`agent.py` は `その他` に正規化します。

## 4. 重要度

重要度は1から5の整数です。

| 重要度 | 意味 |
| --- | --- |
| 5 | 業界全体、社会、法規制、大企業の戦略に大きな影響がある例外的に重要なニュース |
| 4 | 広い範囲の企業、ユーザー、開発者に影響する重要ニュース |
| 3 | ITニュースとして標準的に重要なニュース |
| 2 | 話題性はあるが影響範囲が狭いニュース |
| 1 | 小ネタ、PR寄り、個別事例など影響が小さいニュース |

`agent.py` は重要度を1から5に丸めます。

`generate_site.py` と `docs/search.js` は表示・検索用に0から5の範囲へ丸めます。値が不正な場合、表示側では0扱いになります。

## 5. 並び順

ニュースの標準並び順は次のキーの降順です。

1. `published_at`
2. `importance`
3. `created_at`

日付文字列は次の形式を解釈します。

- `YYYY-MM-DD HH:MM:SS`
- `YYYY-MM-DD`

解釈できない日付は最小値として扱います。

## 6. 重複判定

`agent.py` は `url` を重複判定キーにします。

- 既存URLがある場合はニュース内容を更新する。
- 既存URLがない場合は新規追加する。

## 7. 保持期間

`agent.py` は重要度に応じて古いニュースを整理します。

| 重要度 | 保持期間 |
| --- | --- |
| 1 | 7日 |
| 2 | 7日 |
| 3 | 30日 |
| 4 | 183日 |
| 5 | 無期限 |

保持期間の基準日は、`published_at` があれば `published_at`、なければ `created_at` です。

基準日が解釈できないニュースは削除対象にしません。

## 8. 公開用JSON `docs/news.json`

`generate_site.py` は `data/news.json` を並び替えたうえで `docs/news.json` にも出力します。

用途:

- 検索ページでのクライアントサイド検索
- 公開サイト上で利用できるニュースデータ

## 9. 旧MySQLテーブル

`app.py` と `agent_mysql.py` はMySQLの `news` テーブルを前提にしています。

`test.sql` から読み取れる現行カラムは次の通りです。

| カラム | 型 | 説明 |
| --- | --- | --- |
| `id` | INT AUTO_INCREMENT PRIMARY KEY | 内部ID |
| `title` | VARCHAR(255) | タイトル |
| `url` | VARCHAR(500) UNIQUE | 記事URL |
| `summary` | TEXT | 要約 |
| `importance` | INT | 重要度 |
| `created_at` | DATETIME DEFAULT CURRENT_TIMESTAMP | 保存日時 |
| `category` | VARCHAR(50) | カテゴリ |
| `reason` | TEXT | 選定理由 |
| `published_at` | DATETIME | 公開日時 |

GitHub Pages公開ではMySQLを使用しません。
