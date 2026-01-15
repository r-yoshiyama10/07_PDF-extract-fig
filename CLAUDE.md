# CLAUDE.md - PDF図表抽出Webアプリ

## プロジェクト概要（WHAT）

論文PDFから図表を自動抽出するStreamlit Webアプリケーション。

**技術スタック**: Python 3.11 / Streamlit / Docling / PyMuPDF / PyTorch(CPU) / Docker
**デプロイ先**: HuggingFace Spaces（16GB RAM、Docker対応）

## 目的（WHY）

研究者・学生がPDF論文から図表を効率的に抽出できるツールを提供する。

## 開発ワークフロー（HOW）

### よく使うコマンド

```bash
# ローカル実行
streamlit run extract_figures_streamlit.py

# Docker ビルド & 実行
docker build -t pdf-extract .
docker run -p 7860:7860 pdf-extract

# 依存関係インストール
pip install -r requirements.txt
```

### 開発フロー

1. **探索** → コードベースを理解
2. **計画** → 変更内容を明確化
3. **実装** → コード変更
4. **テスト** → 動作確認

---

## 必須ルール（MUST）

### Windowsパス変換
```
C:\Users\user1\Pictures\test.jpg → /mnt/c/Users/user1/Pictures/test.jpg
```

### Context7 自動利用

コード生成、セットアップ手順、ライブラリ/APIドキュメントが必要な場合は**自動的にContext7 MCPツール**を使用する。

1. `mcp__context7__resolve-library-id` でライブラリIDを解決
2. `mcp__context7__query-docs` でドキュメントを取得

---

## ドキュメント参照

詳細情報は以下を参照：

| ファイル | 内容 |
|---------|------|
| `要件定義（3版）.md` | 機能要件・非機能要件 |
| `アーキテクチャ（2版）.md` | システム構成・処理フロー |
| `技術スタック（2版）.md` | 依存ライブラリ・バージョン |
| `実装計画書.md` | 実装タスク・優先度 |
| `引き継ぎプロンプト.md` | 現在の作業状況 |
