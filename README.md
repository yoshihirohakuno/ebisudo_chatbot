# えびす堂 FAQチャットBot

株式会社えびす堂の公開サイト [https://www.ebisudo.co.jp/](https://www.ebisudo.co.jp/) を巡回し、保存したページ情報をもとに回答する、初心者向けのシンプルな Web チャットBotです。

Gemini API を使って回答を生成しますが、回答の根拠は保存済みのサイトデータだけに限定しています。サイトに書かれていないことは断定せず、不明な場合は `サイト内では確認できませんでした。` と返す構成です。

## 特徴

- 指定サイト配下の公開HTMLページを巡回
- `header` `footer` `nav` `script` `style` などを除去して本文だけを保存
- 保存形式は `タイトル / URL / 本文`
- 保存済みデータから関連ページを探して Gemini に渡す
- 日本語で回答
- ブラウザで使えるチャットUI付き
- 外部サイトに埋め込める `embed.js` 付き
- Render などへそのままデプロイしやすい構成

## ディレクトリ構成

```text
ebisudo_chatbot/
├── app.py                  # Flask起動ファイル
├── requirements.txt        # Python依存関係
├── render.yaml             # Render用設定
├── .env.example            # 環境変数の見本
├── data/
│   └── .gitkeep
├── scripts/
│   └── crawl_site.py       # サイト巡回スクリプト
└── webapp/
    ├── __init__.py
    ├── config.py
    ├── routes.py
    ├── services/
    │   ├── chat_service.py
    │   └── search_service.py
    ├── static/
    │   ├── css/style.css
    │   └── js/chat.js
    └── templates/
        ├── embed.js
        ├── index.html
        └── widget.html
```

## 1. 準備

### 必要なもの

- Python 3.10 以上
- Gemini API キー

### APIキーの設定

このプロジェクトでは API キーをコードに直接書かず、環境変数で管理します。

1. `.env.example` をコピーして `.env` を作ります
2. `GEMINI_API_KEY` に自分のキーを入れます

例:

```env
GEMINI_API_KEY=あなたのGemini APIキー
GEMINI_MODEL=gemini-2.5-flash
DATA_FILE=data/site_pages.json
BASE_URL=https://www.ebisudo.co.jp/
```

今回の手元環境では API キーが別ファイルにあるとのことなので、その内容を `.env` の `GEMINI_API_KEY=` に貼り付けてください。

## 2. インストール

プロジェクトのルートで実行します。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. サイトを巡回してデータ保存

最初に、えびす堂サイトをクロールして保存データを作成します。

```bash
python3 scripts/crawl_site.py
```

成功すると、`data/site_pages.json` が作られます。

このプロジェクトでは、最初のデプロイを簡単にするために `data/site_pages.json` をそのままリポジトリに含めて運用できます。まずはローカルでクロールして動作確認し、その保存結果を Render に載せる形がおすすめです。

### オプション例

最大ページ数を減らしたい場合:

```bash
python3 scripts/crawl_site.py --max-pages 30
```

保存先を変えたい場合:

```bash
python3 scripts/crawl_site.py --output data/custom_pages.json
```

## 4. アプリ起動

```bash
python3 app.py
```

ブラウザで以下を開きます。

```text
http://127.0.0.1:5000/
```

## 5. 使い方

1. 画面の入力欄に質問を書きます
2. 保存済みデータから関連するページ本文を探します
3. その内容だけを Gemini に渡して回答を作ります
4. 回答と参考ページURLを表示します

## 回答の考え方

このBotは「サイトに書いてある範囲でだけ答える」ことを重視しています。

- サイト内に根拠がある場合は、その内容を短く日本語で回答
- 根拠が弱い場合は推測しない
- 確認できない場合は `サイト内では確認できませんでした。` と返す

## 埋め込み方法

このBotは外部サイトに埋め込みできます。

外部サイトの HTML に、次のような script タグを追加してください。

```html
<script
  src="https://あなたのデプロイ先URL/embed.js"
  data-chatbot-url="https://あなたのデプロイ先URL"
></script>
```

ページ右下にチャットボタンが表示され、クリックするとウィジェットが開きます。

## デプロイ手順

ここでは Render を例にします。

### 1. GitHub に push

```bash
git add .
git commit -m "Add ebisudo FAQ chatbot"
git push origin main
```

### 2. Render で新規 Web Service を作成

- GitHub リポジトリを選択
- `render.yaml` を使うか、手動で設定

手動設定する場合:

- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`

### 3. Render の環境変数を設定

- `GEMINI_API_KEY`
- `GEMINI_MODEL` 例: `gemini-2.5-flash`
- `DATA_FILE` 例: `data/site_pages.json`

### 4. クロール済みデータについて

この構成では、`data/site_pages.json` をアプリが参照します。

初心者向けのおすすめ運用は、ローカルでクロールして `data/site_pages.json` を作成し、そのまま GitHub に push して Render に載せる方法です。

将来的には、必要に応じて次のような運用に拡張できます。

- 定期的にクロールして保存データを更新する
- デプロイ後に別ジョブでクロールして差し替える

## よくあるつまずき

### `まだサイトデータがありません` と表示される

先に以下を実行してください。

```bash
python3 scripts/crawl_site.py
```

### `GEMINI_API_KEY が設定されていません` と表示される

`.env` の設定を確認してください。

### 埋め込みで表示されない

- デプロイ先URLが正しいか確認
- `embed.js` の URL と `data-chatbot-url` が一致しているか確認
- まずは `/widget` に直接アクセスして表示されるか確認

## 今後の改善候補

- 定期クロール
- 検索精度の改善
- 管理画面から再クロール
- 回答ログ保存
- FAQのよくある質問を先に表示

## ライセンス

必要に応じて追加してください。
