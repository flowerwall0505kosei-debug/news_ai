# Tech Compass 505 設計書

このディレクトリには、現行ソースコードを正として整理した設計情報を置きます。

## 設計書一覧

- [システム設計書](system-design.md)
  - システム全体像、処理フロー、主要モジュール、画面仕様を記載します。
- [データ設計書](data-design.md)
  - `data/news.json` のJSON構造、カテゴリ、重要度、保持期間、旧MySQL構成を記載します。
- [運用設計書](operation-design.md)
  - ローカル実行、GitHub Actions、GitHub Pages公開、環境変数、障害時の確認ポイントを記載します。
- [お気に入り登録機能設計書](favorites-cookie-design.md)
  - Cookieを使ったお気に入り登録、星ボタン、お気に入りページ、テスト観点を記載します。

## 前提

- 現行の主経路は、`agent.py` でニュースを取得・選定・保存し、`generate_site.py` で `docs/` 配下の静的サイトを生成する方式です。
- GitHub Pages では Flask や MySQL は動かさず、`docs/` 配下の静的ファイルを公開します。
- `app.py` と `agent_mysql.py` は、MySQLを使う旧方式またはローカル確認用の補助実装として扱います。
