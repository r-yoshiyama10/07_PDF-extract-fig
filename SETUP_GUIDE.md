# HuggingFace Spaces セットアップガイド

このガイドでは、PDF図表抽出アプリを自分専用のHuggingFace Spaceとしてデプロイする方法を説明します。

---

## はじめに

### このガイドの目的

HuggingFace Spacesを使えば、このアプリを自分専用の環境で動かすことができます。

**メリット**:
- 自分専用のリソースで安定動作
- URLを共有して仲間と使える
- 無料で利用可能

### 必要なもの

- HuggingFaceアカウント（無料）
- 本リポジトリのファイル一式

---

## 必要なファイル一覧

デプロイに必要なファイルは以下の5つです。

```
pdf-figure-extractor/
├── app.py                  # メインアプリケーション
├── requirements.txt        # Python依存関係
├── Dockerfile              # Dockerビルド設定
├── README.md               # Spaces設定（フロントマター必須）
└── .streamlit/
    └── config.toml         # Streamlit設定
```

### 各ファイルの役割

| ファイル | 説明 |
|----------|------|
| `app.py` | Streamlitアプリ本体。PDF処理・図表抽出のロジック |
| `requirements.txt` | Python依存ライブラリ（Docling, PyMuPDF等） |
| `Dockerfile` | Dockerイメージのビルド手順 |
| `README.md` | Spacesの設定情報（フロントマター）とアプリ説明 |
| `.streamlit/config.toml` | Streamlitの動作設定 |

---

## セットアップ手順

### Step 1: HuggingFaceアカウント作成

1. [HuggingFace](https://huggingface.co/) にアクセス
2. 右上の「Sign Up」をクリック
3. メールアドレス、ユーザー名、パスワードを入力
4. メール認証を完了

※ 既にアカウントがある場合はログインしてください。

---

### Step 2: 新しいSpaceを作成

1. HuggingFaceにログイン後、右上のプロフィールアイコンをクリック
2. 「New Space」を選択
3. 以下の設定を入力:

| 項目 | 設定値 |
|------|--------|
| **Space name** | 任意の名前（例: `pdf-figure-extractor`） |
| **License** | MIT（推奨） |
| **SDK** | **Docker** を選択 |
| **Space hardware** | CPU basic（無料） |
| **Visibility** | Public または Private |

4. 「Create Space」をクリック

---

### Step 3: ファイルをアップロード

Spaceが作成されると、ファイルをアップロードする画面が表示されます。

#### 方法A: Web UIでアップロード（簡単）

1. 「Files」タブを選択
2. 「+ Add file」→「Upload files」をクリック
3. 以下のファイルをドラッグ＆ドロップ:
   - `app.py`
   - `requirements.txt`
   - `Dockerfile`
   - `README.md`
4. 「Commit changes」をクリック

5. `.streamlit/config.toml` をアップロード:
   - 「+ Add file」→「Create a new file」をクリック
   - ファイル名に `.streamlit/config.toml` と入力
   - 以下の内容をコピー＆ペースト:

```toml
[client]
toolbarMode = "viewer"

[server]
headless = true
port = 7860
address = "0.0.0.0"
enableCORS = false
enableXsrfProtection = false
maxUploadSize = 100

[browser]
gatherUsageStats = false

[theme]
base = "light"
```

6. 「Commit new file」をクリック

#### 方法B: Git でアップロード（上級者向け）

```bash
# リポジトリをクローン
git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME

# ファイルをコピー
cp app.py requirements.txt Dockerfile README.md YOUR_SPACE_NAME/
mkdir -p YOUR_SPACE_NAME/.streamlit
cp .streamlit/config.toml YOUR_SPACE_NAME/.streamlit/

# コミット＆プッシュ
cd YOUR_SPACE_NAME
git add .
git commit -m "Initial commit"
git push
```

※ `YOUR_USERNAME` と `YOUR_SPACE_NAME` は自分の情報に置き換えてください。

---

### Step 4: ビルドと動作確認

1. ファイルをアップロードすると、自動的にビルドが開始されます
2. 「App」タブでビルドログを確認できます
3. ステータスが「Running」になれば完了

**初回ビルドの注意点**:
- 初回は依存ライブラリとAIモデルのダウンロードで時間がかかります
- 「Building」状態が続いても、気長にお待ちください

---

## カスタマイズ方法

### Space名を変更する

Space作成時に設定した名前を後から変更することはできません。
新しい名前で別のSpaceを作成してください。

### README.mdのフロントマター

README.mdの先頭にあるフロントマター（`---`で囲まれた部分）でSpaceの設定を変更できます。

```yaml
---
title: 論文PDF図表抽出ツール    # アプリのタイトル
emoji: 📄                        # 表示される絵文字
colorFrom: blue                  # グラデーション開始色
colorTo: green                   # グラデーション終了色
sdk: docker                      # 使用するSDK（変更不要）
pinned: false                    # プロフィールにピン留め
license: mit                     # ライセンス
---
```

**変更可能な項目**:
- `title`: アプリ名を自由に変更
- `emoji`: 好きな絵文字に変更
- `colorFrom` / `colorTo`: テーマカラーを変更
- `pinned`: `true`にするとプロフィールページで目立つ位置に表示

### テーマを変更する

`.streamlit/config.toml` の `[theme]` セクションを編集:

```toml
[theme]
base = "dark"  # "light" または "dark"
```

---

## トラブルシューティング

### ビルドエラーが発生した場合

**症状**: ステータスが「Build Error」になる

**確認ポイント**:
1. Dockerfileの内容が正しいか確認
2. requirements.txtのパッケージ名・バージョンが正しいか確認
3. 「Logs」タブでエラー詳細を確認

**よくある原因**:
- ファイル名のタイプミス（大文字/小文字を区別）
- `.streamlit/config.toml` のパスが間違っている

### アプリが起動しない場合

**症状**: ステータスが「Runtime Error」になる

**確認ポイント**:
1. app.pyの構文エラーがないか確認
2. 必要なライブラリがrequirements.txtに含まれているか確認

### 403エラーが発生する場合

**症状**: ファイルアップロード時に403エラー

**解決策**:
`.streamlit/config.toml` に以下の設定があることを確認:
```toml
enableXsrfProtection = false
```

### メモリ不足エラー

**症状**: 大きなPDFを処理するとクラッシュ

**解決策**:
- 無料プランでは16GB RAMの制限があります
- 大きなPDF（50ページ以上）の処理は避けてください
- 有料プランへのアップグレードを検討

---

## 制限事項・注意点

### 無料プランのリソース制限

| リソース | 制限 |
|----------|------|
| CPU | 2 vCPU |
| RAM | 16 GB |
| ストレージ | 50 GB |
| 同時実行 | 制限あり |

### 初回起動時間

初回起動時、以下のダウンロードが発生するため時間がかかります:
- Pythonライブラリ（約2GB）
- Docling AIモデル（約500MB）

2回目以降はキャッシュが効くため高速に起動します。

### 同時使用時の注意

- Spaceのリソースは使用者全員で共有されます
- 複数人が同時にPDFを処理すると、パフォーマンスが低下する可能性があります
- 個人使用または少人数での利用を推奨

### スリープ機能

- 無料プランでは、一定時間アクセスがないとSpaceがスリープ状態になります
- 再度アクセスすると自動的に起動しますが、起動に時間がかかります

---

## 参考リンク

- [HuggingFace Spaces ドキュメント](https://huggingface.co/docs/hub/spaces)
- [Streamlit ドキュメント](https://docs.streamlit.io/)
- [Docling ドキュメント](https://ds4sd.github.io/docling/)

---

## サポート

問題が発生した場合は、以下を確認してください:
1. このガイドのトラブルシューティングセクション
2. HuggingFace Spacesの公式ドキュメント
3. 元リポジトリのIssues

---

最終更新: 2026-01-17
