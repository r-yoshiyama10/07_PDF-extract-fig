---
title: 論文PDF図表抽出ツール
emoji: 📄
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
---

# 論文PDF図表抽出ツール

AI技術を使って、PDFから図表を自動抽出するWebアプリケーションです。

## 機能

- PDF内の図（Figure）を自動検出・抽出
- PDF内の表（Table）を自動検出・抽出
- 表データのCSVエクスポート
- 抽出結果のZIPダウンロード

## 制限事項

- 最大ファイルサイズ: 100MB
- 最大ページ数: 100ページ
- パスワード保護されたPDFは非対応
- スキャンPDF（画像PDF）は非対応

## 技術スタック

- Streamlit
- Docling (IBM)
- PyMuPDF
- PyTorch (CPU)
