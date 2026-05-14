# お気に入り登録機能 設計書

## 1. 目的

星マークをクリックしてページやアイテムをお気に入り登録し、専用のお気に入りページで登録済みのものをまとめて確認できるようにする。

今回はユーザーの要望に合わせて Cookie にお気に入り情報を保存する。ただし、お気に入り情報はログインユーザーに紐づく重要データではなく、同じブラウザ内で使う軽量な個人設定として扱う。

## 2. 前提

- 現在の作業フォルダには既存アプリのファイルがないため、特定のフレームワークに依存しない設計とする。
- お気に入り対象は「ページ」または「一覧に表示されるアイテム」を想定する。
- お気に入りは端末・ブラウザ単位で保存される。
- Cookie を削除した場合、ブラウザを変えた場合、シークレットモードを閉じた場合などは、お気に入り情報が消えることがある。
- ログインユーザー間でお気に入りを同期する機能は今回の対象外とする。

## 3. Cookie の基本説明

Cookie は、Web サイトがブラウザに保存できる小さなデータである。通常は `name=value` の形式で保存され、同じサイトへアクセスするときにブラウザからサーバーへ自動送信される。

代表的な使い道は次の通り。

- ログイン状態やセッション情報の管理
- 表示言語、テーマなどのユーザー設定
- 買い物かごや簡単な状態保存
- アクセス解析や広告計測

ただし、Cookie は一般的なデータ保存場所としては制限が多い。1つの Cookie に保存できる量は小さく、Cookie は対象サイトへのリクエストごとに送られる。そのため、たくさんのデータを入れる用途には向かない。

今回のお気に入り機能では、Cookie にはお気に入り対象の ID だけを保存する。タイトル、説明文、画像URLなどの表示用データは Cookie に入れず、既存のデータソースから取得する。

参考:

- [MDN: Using HTTP cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies)
- [MDN: Document.cookie](https://developer.mozilla.org/en-US/docs/Web/API/Document/cookie)
- [MDN: Secure cookie configuration](https://developer.mozilla.org/en-US/docs/Web/Security/Practical_implementation_guides/Cookies)

## 4. Cookie を使うときの用語

| 項目 | 説明 | 今回の方針 |
| --- | --- | --- |
| Cookie 名 | 保存する値の名前 | `favorite_items_v1` |
| Cookie 値 | 実際に保存する文字列 | お気に入り ID の JSON 配列を URL エンコードしたもの |
| `Max-Age` | Cookie の有効期間を秒数で指定 | 400日。サイトを開いた時に既存Cookieの期限を延長する |
| `Path` | Cookie が有効なパス | `/` |
| `SameSite` | 別サイト経由のリクエスト時に Cookie を送るか制御 | `Lax` |
| `Secure` | HTTPS 通信時だけ Cookie を送る | 本番環境が HTTPS の場合に付与 |
| `HttpOnly` | JavaScript から Cookie を読めなくする | 今回は使わない |

`HttpOnly` を使うと JavaScript から Cookie を読めなくなるため、フロントエンドで星マークの状態を切り替える今回の用途には合わない。認証情報やセッションIDを保存する Cookie では `HttpOnly` が重要だが、お気に入り ID をクライアント側で扱う今回の設計では使用しない。

## 5. 保存データ設計

### Cookie 名

```text
favorite_items_v1
```

末尾に `v1` を付ける。将来、保存形式を変更したい場合に `favorite_items_v2` へ移行しやすくするため。

### Cookie 値

JSON 配列を `encodeURIComponent` でエンコードして保存する。

保存前のデータ例:

```json
["article-001", "article-015", "product-092"]
```

Cookie に保存するイメージ:

```text
favorite_items_v1=%5B%22article-001%22%2C%22article-015%22%2C%22product-092%22%5D; Max-Age=34560000; Path=/; SameSite=Lax
```

### 保存する情報

保存する:

- お気に入り対象の安定した ID

保存しない:

- ユーザー名
- メールアドレス
- 認証トークン
- 個人情報
- タイトル、説明文、画像URLなどの表示用データ
- 大量のページ情報

### ID の決め方

優先順位は次の通り。

1. データベースやAPIに存在する安定ID
2. 記事や商品などの slug
3. URL パス

Tech Compass 505 の現行 `news.json` には専用IDがないため、初期実装では記事URLをお気に入りIDとして使用する。URLが存在しない場合のみ、タイトルと公開日時を組み合わせた代替IDを使う。

URL を ID として使う場合は、不要なクエリ文字列やハッシュを除外して正規化する。

例:

```text
/articles/001?utm_source=x#section
```

正規化後:

```text
/articles/001
```

### 登録上限

Cookie の容量制限を避けるため、初期上限は 50 件とする。

50件を超えて登録しようとした場合は、次のどちらかを選ぶ。

- 推奨: 登録できないことを通知する
- 代替: 一番古いお気に入りを削除して新しいものを追加する

初期実装では「登録できないことを通知する」を採用する。

## 6. 画面設計

### お気に入りボタン

各ページまたは各アイテムに星マークのボタンを表示する。

未登録:

```text
☆ お気に入りに追加
```

登録済み:

```text
★ お気に入り済み
```

実際のUIでは、画面幅やデザインに応じてアイコンだけにしてもよい。その場合もアクセシビリティのために `aria-label` を設定する。

推奨仕様:

- 未登録時はアウトラインの星
- 登録済み時は塗りつぶしの星
- ホバー時に押せることが分かるスタイルにする
- キーボード操作に対応する
- `aria-pressed` で選択状態を表す
- クリック後は即時に表示を切り替える

### お気に入りページ

URL 例:

```text
/favorites
```

表示内容:

- お気に入り登録済みアイテムの一覧
- アイテム名
- サムネイルがあれば画像
- 概要文があれば概要
- 詳細ページへのリンク
- お気に入り解除ボタン

空の場合:

```text
お気に入りはまだありません。
```

存在しない ID が Cookie に残っていた場合:

- 表示対象から除外する
- 必要に応じて Cookie から削除する

## 7. 処理フロー

### 初期表示

1. ページ読み込み時に Cookie `favorite_items_v1` を読む。
2. Cookie が存在しない場合は空配列として扱う。
3. JSON として復元できない場合は空配列として扱う。
4. 現在のページまたはアイテム ID が配列に含まれるか判定する。
5. 星マークの表示状態を決定する。

### お気に入り追加

1. 現在の Cookie を読む。
2. 対象 ID が含まれていないことを確認する。
3. 上限件数未満なら ID を追加する。
4. JSON 文字列化して URL エンコードする。
5. Cookie に保存する。
6. UI を登録済み状態に更新する。

### お気に入り解除

1. 現在の Cookie を読む。
2. 対象 ID を配列から削除する。
3. Cookie に保存する。
4. UI を未登録状態に更新する。

### お気に入りページ表示

1. Cookie からお気に入り ID 一覧を読む。
2. 既存のページ・アイテムデータから該当 ID のデータを取得する。
3. Cookie に保存されている順番で表示する。
4. データが見つからない ID は無視する。

## 8. ユーティリティ設計

Cookie の読み書きは画面側に直接書かず、専用のユーティリティにまとめる。

想定関数:

```ts
const FAVORITES_COOKIE_NAME = "favorite_items_v1";
const FAVORITES_MAX_COUNT = 50;

function getFavoriteIds(): string[];
function setFavoriteIds(ids: string[]): void;
function isFavorite(id: string): boolean;
function addFavorite(id: string): { ok: boolean; reason?: "limit" };
function removeFavorite(id: string): void;
function toggleFavorite(id: string): { favorited: boolean; reason?: "limit" };
function clearFavorites(): void;
```

実装時の注意:

- `document.cookie` は Cookie 全体の文字列を返すため、名前ごとに分解して取得する。
- Cookie の属性は `document.cookie` で読み取れない。
- Cookie を削除するときは、同じ Cookie 名と `Path=/` を指定して `Max-Age=0` にする。
- 不正な値が入っていても画面が壊れないように、JSON パースは例外処理する。
- 同じ ID が重複しないように保存する。
- ID は文字列として扱い、空文字は登録しない。

## 9. Cookie 保存処理のサンプル

実装時のイメージ:

```ts
function writeFavoritesCookie(ids: string[]) {
  const value = encodeURIComponent(JSON.stringify(ids));
  const maxAge = 60 * 60 * 24 * 400;
  const secure = location.protocol === "https:" ? "; Secure" : "";

  document.cookie = [
    `favorite_items_v1=${value}`,
    `Max-Age=${maxAge}`,
    "Path=/",
    "SameSite=Lax",
  ].join("; ") + secure;
}
```

読み取り処理のイメージ:

```ts
function readFavoritesCookie(): string[] {
  const cookies = document.cookie.split("; ");
  const target = cookies.find((cookie) =>
    cookie.startsWith("favorite_items_v1=")
  );

  if (!target) return [];

  const rawValue = target.split("=").slice(1).join("=");

  try {
    const parsed = JSON.parse(decodeURIComponent(rawValue));
    return Array.isArray(parsed)
      ? parsed.filter((id): id is string => typeof id === "string" && id.length > 0)
      : [];
  } catch {
    return [];
  }
}
```

## 10. コンポーネント設計

### FavoriteButton

責務:

- 対象 ID を受け取る
- 現在のお気に入り状態を表示する
- クリックで追加・解除する
- 登録上限に達した場合は通知する

Props 例:

```ts
type FavoriteButtonProps = {
  id: string;
  label?: string;
};
```

### FavoritesPage

責務:

- Cookie からお気に入り ID を取得する
- ID に該当するアイテム情報を取得する
- 一覧表示する
- 各アイテムからお気に入り解除できるようにする
- 空状態を表示する

## 11. エラーハンドリング

| ケース | 対応 |
| --- | --- |
| Cookie が存在しない | 空のお気に入りとして扱う |
| Cookie が壊れている | 空配列として扱い、次回保存時に正常化する |
| 上限件数を超える | 追加せず、メッセージを表示する |
| Cookie が無効なブラウザ | 一時的な画面状態だけ更新し、再読み込みで消える可能性を伝える |
| 対象 ID が存在しない | 表示しない。可能なら Cookie から削除する |

## 12. セキュリティ・プライバシー方針

- Cookie には個人情報や認証情報を保存しない。
- JavaScript から読み書きできる Cookie は、XSS があると読み取られる可能性がある。
- Cookie 値は信頼せず、必ずバリデーションする。
- 本番環境が HTTPS の場合は `Secure` を付ける。
- `SameSite=Lax` を指定する。
- Cookie を利用していることをプライバシーポリシーや必要な表示に記載する。
- ユーザーが自分で Cookie を削除できる前提で設計する。

## 13. Cookie と localStorage の比較

| 項目 | Cookie | localStorage |
| --- | --- | --- |
| 保存容量 | 小さい | Cookie より大きい |
| サーバーへ自動送信 | される | されない |
| JavaScript から操作 | 可能。ただし `HttpOnly` は不可 | 可能 |
| 今回の用途との相性 | 小規模なら可 | 純粋なフロント保存ならより向いている |
| SSR でサーバー側から状態を見たい場合 | 向いている | 向いていない |

今回 Cookie を使う理由:

- ユーザーの希望に沿うため
- 小規模なお気に入り ID 保存なら実装可能なため
- 将来的にサーバー側で Cookie を読んで初期表示に反映しやすいため

ただし、完全にフロントエンドだけで完結するお気に入り機能なら、通常は `localStorage` の方が扱いやすい。今回の設計では Cookie 操作をユーティリティに閉じ込めることで、将来 `localStorage` や DB 保存へ変更しやすくする。

## 14. テスト観点

### 単体テスト

- Cookie がない場合に空配列を返す
- 正常な Cookie を配列に復元できる
- 壊れた Cookie で例外が出ない
- お気に入り追加ができる
- 同じ ID を重複追加しない
- お気に入り解除ができる
- 上限件数を超えた場合に追加しない
- 空文字や不正な ID を保存しない

### 画面テスト

- 星マークをクリックすると登録済み表示になる
- もう一度クリックすると未登録表示になる
- ページを再読み込みしても状態が残る
- お気に入りページに登録済みアイテムが表示される
- お気に入りページから解除できる
- お気に入りがない場合に空状態が表示される

### 手動確認

- ブラウザの開発者ツールで Cookie が保存されていることを確認する
- Cookie を削除するとお気に入りが空になることを確認する
- 50件を超える登録時の表示を確認する
- HTTPS 環境で `Secure` が付与されることを確認する

## 15. 実装ステップ

1. お気に入り対象に使う ID 仕様を決める。
2. Cookie 操作用ユーティリティを作成する。
3. `FavoriteButton` を作成する。
4. 詳細ページや一覧カードに星マークを配置する。
5. `/favorites` ページを作成する。
6. お気に入り一覧のデータ取得処理を接続する。
7. 空状態、上限到達、Cookie 破損時の挙動を整える。
8. 単体テストと画面テストを追加する。
9. 開発者ツールで Cookie の保存内容を確認する。

## 16. 受け入れ条件

- ユーザーは星マークからお気に入り登録・解除ができる。
- 登録状態はページ再読み込み後も維持される。
- お気に入りページで登録済みアイテムを一覧確認できる。
- お気に入りページから登録解除できる。
- Cookie に個人情報や表示用の大きなデータを保存していない。
- Cookie が壊れていても画面がクラッシュしない。
- Cookie の保存件数上限が守られている。
- 本番 HTTPS 環境では `Secure` が付与される。

## 17. 将来拡張

- ログインユーザーのお気に入りを DB に保存する。
- Cookie のお気に入りをログイン時にアカウントへ移行する。
- お気に入り追加日時を保存して並び替えできるようにする。
- お気に入りカテゴリやメモを追加する。
- Cookie から `localStorage` へ保存先を変更する。
- サーバー側レンダリング時に Cookie を読んで初期表示へ反映する。
