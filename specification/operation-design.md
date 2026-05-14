# 運用設計書

## 1. 運用概要

Tech Compass 505 の主な運用は、次の2段階です。

1. `agent.py` でニュースを取得し、AIで選定・要約して `data/news.json` を更新する。
2. `generate_site.py` で `docs/` 配下の静的サイトを生成する。

GitHub Pagesでは `docs/` 配下を公開します。

## 2. ローカル実行

### 2.1 依存ライブラリのインストール

```bash
pip install -r requirements.txt
```

### 2.2 環境変数

`.env.example` を参考に `.env` を作成します。

必須:

```env
OPENAI_API_KEY=your_api_key_here
```

任意:

```env
OPENAI_MODEL=gpt-5-mini
```

MySQL版を使う場合のみ:

```env
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=news_ai
```

### 2.3 ニュース更新

```bash
python agent.py
```

出力:

- `data/news.json`

### 2.4 静的サイト生成

```bash
python generate_site.py
```

出力:

- `docs/index.html`
- `docs/news/index.html`
- `docs/ai/index.html`
- `docs/search/index.html`
- `docs/news.json`

### 2.5 ブラウザ確認

`docs/index.html` をブラウザで開きます。

検索ページはJavaScriptを使用するため、必要に応じて簡易HTTPサーバーで確認します。

```bash
python -m http.server 8000 -d docs
```

## 3. Windowsバッチ実行

`run_agent.bat` は次の処理を連続実行します。

1. 実行ログの開始時刻を `agent_log.txt` に追記する。
2. `python` または `py` を検出する。
3. `agent.py` を実行する。
4. `generate_site.py` を実行する。
5. それぞれの終了コードを `agent_log.txt` に記録する。

用途:

- Windowsローカルでの手動更新
- タスクスケジューラからの実行

## 4. GitHub Actions

ワークフロー:

- `.github/workflows/update-news.yml`

実行タイミング:

- 毎日 00:23〜05:23 JST の毎時
- 手動実行 `workflow_dispatch`

GitHub Actionsの定期実行は遅延またはドロップされる可能性があるため、朝6時頃までの反映を狙って複数回スケジュールします。同じ日にすでにスケジュール更新済みの場合、後続の定期実行はスキップします。手動実行はスキップ対象外です。

主な処理:

1. リポジトリをチェックアウトする。
2. `main` の最新状態へfast-forwardする。
3. スケジュール実行時は、当日分がすでに更新済みか確認する。
4. Python 3.12 をセットアップする。
5. `requirements.txt` をインストールする。
6. `python agent.py` を実行する。
7. `python generate_site.py` を実行する。
8. `data/news.json` と `docs/` に変更があればコミットして `main` にpushする。

必要なGitHub Secret:

- `OPENAI_API_KEY`

ワークフロー内の既定モデル:

- `OPENAI_MODEL=gpt-5-mini`

## 5. GitHub Pages公開

GitHub Pagesの公開元は次の設定を想定します。

- Source: `Deploy from a branch`
- Branch: `main`
- Folder: `/docs`

公開されるファイル:

- `docs/index.html`
- `docs/news/index.html`
- `docs/ai/index.html`
- `docs/search/index.html`
- `docs/news.json`
- `docs/search.js`
- `docs/style.css`

## 6. 障害時の確認ポイント

### 6.1 `OPENAI_API_KEY` 未設定

症状:

- `agent.py` が `.env または環境変数に OPENAI_API_KEY を設定してください。` を出して終了する。

確認:

- ローカルでは `.env`
- GitHub ActionsではRepository Secrets

### 6.2 RSSに昨日の記事がない

症状:

- `昨日公開の記事がRSS内に見つからないため、RSS最新10件を候補にします。` と表示される。

挙動:

- エラーではありません。
- RSS最新10件を候補として処理します。

### 6.3 OpenAI APIの返答がJSONではない

症状:

- JSONパースエラーまたは `OpenAI APIの返答がJSON配列ではありません。`

確認:

- `OPENAI_MODEL`
- プロンプト変更有無
- API障害有無

### 6.4 `data/news.json` がJSON配列ではない

症状:

- `data/news.json はJSON配列にしてください。`

対応:

- `data/news.json` の形式をJSON配列へ戻す。
- 破損している場合は直近のGit履歴から復旧する。

### 6.5 検索ページが動かない

確認:

- `docs/search/index.html` に `news-data` スクリプトが埋め込まれているか。
- `docs/search.js` が読み込めているか。
- ブラウザのコンソールにJavaScriptエラーがないか。

## 7. 運用上の注意

- `.env` はGit管理に含めない。
- APIキーはREADME、HTML、JavaScript、JSONに書かない。
- `docs/` は生成物ですが、GitHub Pages公開対象のためリポジトリに含める。
- `data/news.json` はニュース蓄積データであり、更新対象として扱う。
- MySQL版を使わない通常運用では、MySQLサーバーは不要です。
