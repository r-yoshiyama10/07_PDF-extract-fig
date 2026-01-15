"""
論文PDF図表抽出Webアプリ - UIモックアップ
==========================================
実装前の見た目確認用。処理ロジックは含まない。

実行方法:
    streamlit run mockup.py
"""

import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io


# =============================================================================
# ダミーデータ生成
# =============================================================================

def create_dummy_figure(index: int, width: int = 400, height: int = 300) -> Image.Image:
    """ダミーの図画像を生成"""
    img = Image.new('RGB', (width, height), color='#E8E8E8')
    draw = ImageDraw.Draw(img)

    # 枠線
    draw.rectangle([0, 0, width-1, height-1], outline='#CCCCCC', width=2)

    # テキスト
    text = f"Figure {index:03d}"
    bbox = draw.textbbox((0, 0), text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    draw.text((x, y), text, fill='#666666')

    return img


def create_dummy_table(index: int) -> pd.DataFrame:
    """ダミーの表データを生成"""
    data = {
        'Category': [f'Item {i}' for i in range(1, 6)],
        'Value A': [10.5, 20.3, 15.7, 25.1, 18.9],
        'Value B': [100, 200, 150, 250, 180],
        'Status': ['Active', 'Pending', 'Active', 'Complete', 'Active']
    }
    return pd.DataFrame(data)


# =============================================================================
# サイドバー
# =============================================================================

def render_sidebar():
    """サイドバーを描画"""
    with st.sidebar:
        st.title("論文PDF図表抽出")

        st.divider()

        # 設定セクション
        st.subheader("設定")

        resolution = st.radio(
            "出力解像度",
            options=["低品質（高速）", "標準（推奨）", "高品質（低速）"],
            index=1,
            help="解像度が高いほど処理時間が長くなります"
        )

        st.divider()

        # 使い方セクション
        with st.expander("使い方", expanded=False):
            st.markdown("""
            1. PDFファイルをアップロード
            2. 「処理を開始」をクリック
            3. 抽出された図表を確認
            4. ダウンロード
            """)

        # 制限事項
        with st.expander("制限事項", expanded=False):
            st.markdown("""
            - 最大ファイルサイズ: 100MB
            - 最大ページ数: 100ページ
            - 対応形式: テキスト埋め込みPDF
            """)

        st.divider()

        # モックアップ用：状態切り替え
        st.subheader("モック状態切り替え")
        mock_state = st.selectbox(
            "表示状態",
            options=["初期状態", "アップロード後", "処理中", "処理完了"],
            index=0
        )

        return resolution, mock_state


# =============================================================================
# メインエリア
# =============================================================================

def render_upload_area():
    """アップロードエリアを描画"""
    uploaded_file = st.file_uploader(
        "PDFファイルをアップロード",
        type=['pdf'],
        help="100MB以下、100ページ以下のPDFファイル"
    )
    return uploaded_file


def render_file_info(filename: str = "sample_paper.pdf", pages: int = 20):
    """ファイル情報を表示"""
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"ファイル名: {filename}")
    with col2:
        st.info(f"ページ数: {pages}ページ")


def render_processing():
    """処理中の表示"""
    st.warning("処理中...")
    progress = st.progress(0.6)
    st.caption("処理中: 12 / 20 ページ")
    st.caption("推定残り時間: 約16秒")


def render_results(num_figures: int = 5, num_tables: int = 3):
    """結果表示エリアを描画"""
    st.success(f"処理が完了しました（図: {num_figures}個、表: {num_tables}個）")

    # 一括ダウンロードボタン
    st.download_button(
        label="すべてダウンロード（ZIP）",
        data=b"dummy_zip_data",
        file_name="sample_paper_extracted_20260115_120000.zip",
        mime="application/zip",
        use_container_width=True
    )

    st.divider()

    # 図セクション
    st.subheader(f"図（{num_figures}個）")

    # 3列グリッドで表示
    cols = st.columns(3)
    for i in range(num_figures):
        with cols[i % 3]:
            img = create_dummy_figure(i + 1)
            st.image(img, caption=f"figure_{i+1:03d}.png", use_container_width=True)

            # 個別ダウンロードボタン
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            st.download_button(
                label="ダウンロード",
                data=buf.getvalue(),
                file_name=f"sample_paper_figure_{i+1:03d}.png",
                mime="image/png",
                key=f"fig_download_{i}"
            )

    st.divider()

    # 表セクション
    st.subheader(f"表（{num_tables}個）")

    for i in range(num_tables):
        with st.expander(f"table_{i+1:03d}", expanded=(i == 0)):
            df = create_dummy_table(i + 1)

            # 表のプレビュー
            st.dataframe(df, use_container_width=True)

            # ダウンロードボタン（CSV/PNG）
            col1, col2 = st.columns(2)
            with col1:
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="CSV ダウンロード",
                    data=csv_data,
                    file_name=f"sample_paper_table_{i+1:03d}.csv",
                    mime="text/csv",
                    key=f"table_csv_{i}"
                )
            with col2:
                st.download_button(
                    label="PNG ダウンロード",
                    data=b"dummy_png_data",
                    file_name=f"sample_paper_table_{i+1:03d}.png",
                    mime="image/png",
                    key=f"table_png_{i}"
                )


# =============================================================================
# メイン
# =============================================================================

def main():
    # ページ設定
    st.set_page_config(
        page_title="論文PDF図表抽出",
        page_icon="📄",
        layout="wide"
    )

    # 追加のカスタムCSS（config.tomlで主要な非表示設定済み）
    st.markdown("""
    <style>
    /* フッターを非表示 */
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

    # サイドバー
    resolution, mock_state = render_sidebar()

    # メインエリア
    st.title("論文PDF図表抽出ツール")
    st.caption("PDFから図表を自動抽出するWebアプリケーション")

    st.divider()

    # 状態に応じた表示
    if mock_state == "初期状態":
        render_upload_area()
        st.info("PDFファイルをアップロードしてください")

    elif mock_state == "アップロード後":
        render_upload_area()
        render_file_info()

        if st.button("処理を開始", type="primary", use_container_width=True):
            st.info("（モックアップのため処理は実行されません）")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("リセット", use_container_width=True):
                st.info("（モックアップのため処理は実行されません）")

    elif mock_state == "処理中":
        render_upload_area()
        render_file_info()
        render_processing()

    elif mock_state == "処理完了":
        render_upload_area()
        render_file_info()
        render_results()


if __name__ == "__main__":
    main()
