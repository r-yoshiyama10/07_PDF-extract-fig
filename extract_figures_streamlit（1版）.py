import streamlit as st
import tempfile
from pathlib import Path
import time
import logging
from docling_core.types.doc import PictureItem, TableItem
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

# ロギング設定
logging.basicConfig(level=logging.WARNING)

# ページ設定
st.set_page_config(
    page_title="📄 論文PDF図表抽出ツール",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# タイトル
st.title("📄 論文PDF図表抽出ツール")
st.markdown("**AI技術を使って、PDFから図表を自動抽出します**")

# サイドバー設定
with st.sidebar:
    st.header("⚙️ 設定")
    
    # 解像度設定
    resolution = st.radio(
        "📐 出力解像度を選択：",
        options=[0.5, 1.0, 1.5, 2.0, 3.0],
        format_func=lambda x: f"{x} ✕ ({int(x*72)} DPI)",
        index=3  # デフォルト 2.0
    )
    
    st.info(f"**現在の設定：{int(resolution*72)} DPI**")
    
    st.markdown("---")
    st.markdown("### 📖 使い方")
    st.markdown("""
    1. PDFファイルをアップロード
    2. 「処理開始」ボタンをクリック
    3. 抽出された図表をダウンロード
    
    処理時間は PDF のページ数と複雑度によって異なります。
    """)

# メインコンテンツ
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📤 ステップ1：PDFをアップロード")
    uploaded_file = st.file_uploader(
        "PDFファイルを選択してください",
        type="pdf",
        help="論文や資料のPDFファイルを選択してください"
    )

with col2:
    st.subheader("📊 処理情報")
    if uploaded_file is None:
        st.info("📌 PDFをアップロードするのを待機中...")
    else:
        st.success(f"✅ ファイル選択済み\n**{uploaded_file.name}**")
        st.metric("ファイルサイズ", f"{uploaded_file.size / 1024:.1f} KB")

# 処理実行
if uploaded_file is not None:
    st.markdown("---")
    st.subheader("⚡ ステップ2：処理実行")
    
    col1, col2 = st.columns(2)
    with col1:
        run_button = st.button(
            "🚀 処理開始",
            type="primary",
            use_container_width=True
        )
    
    with col2:
        st.write("")  # スペーサー
    
    if run_button:
        # プログレス表示
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                tmp_path = tmp_file.name
            
            status_text.write("🔄 PDF を解析中...（AIモデルを初期化）")
            progress_bar.progress(10)
            
            # Docling 設定
            pipeline_options = PdfPipelineOptions()
            pipeline_options.images_scale = resolution
            pipeline_options.generate_page_images = True
            pipeline_options.generate_picture_images = True
            
            status_text.write("🔄 PDFを処理中...")
            progress_bar.progress(30)
            
            # DocumentConverter 初期化
            doc_converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
            
            # PDF 変換
            start_time = time.time()
            conv_res = doc_converter.convert(tmp_path)
            elapsed = time.time() - start_time
            
            progress_bar.progress(50)
            status_text.write(f"📊 図表を抽出中... ({elapsed:.1f}秒経過)")
            
            # 図表抽出
            figures = []
            tables = []
            table_csvs = []
            
            for element, _level in conv_res.document.iterate_items():
                # テーブル抽出
                if isinstance(element, TableItem):
                    try:
                        element_image = element.get_image(conv_res.document)
                        if element_image is not None:
                            tables.append(element_image)
                        
                        # CSV エクスポート
                        try:
                            df = element.export_to_dataframe()
                            table_csvs.append(df)
                        except:
                            pass
                    except Exception as e:
                        pass
                
                # 図抽出
                if isinstance(element, PictureItem):
                    try:
                        element_image = element.get_image(conv_res.document)
                        if element_image is not None:
                            figures.append(element_image)
                    except Exception as e:
                        pass
            
            progress_bar.progress(80)
            
            # 結果表示
            status_text.write("✅ 処理完了！")
            progress_bar.progress(100)
            time.sleep(0.5)
            progress_bar.empty()
            status_text.empty()
            
            # 結果ダッシュボード
            st.markdown("---")
            st.subheader("📈 抽出結果")
            
            result_col1, result_col2, result_col3 = st.columns(3)
            with result_col1:
                st.metric("抽出された図", len(figures), delta=None)
            with result_col2:
                st.metric("抽出された表", len(tables), delta=None)
            with result_col3:
                st.metric("処理時間", f"{elapsed:.1f}秒", delta=None)
            
            # 図表表示
            if len(figures) > 0:
                st.subheader("🖼️ 抽出された図")
                for idx, fig in enumerate(figures, 1):
                    st.image(fig, caption=f"図 {idx}", use_column_width=True)
            
            if len(tables) > 0:
                st.subheader("📊 抽出された表")
                for idx, table in enumerate(tables, 1):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.image(table, caption=f"表 {idx}", use_column_width=True)
                    with col2:
                        if idx <= len(table_csvs):
                            st.dataframe(table_csvs[idx-1], use_container_width=True)
            
            if len(figures) == 0 and len(tables) == 0:
                st.warning("⚠️ この PDF に抽出可能な図表が見つかりませんでした")
            
            # ダウンロード準備
            st.markdown("---")
            st.subheader("⬇️ ステップ3：結果をダウンロード")
            
            import io
            import zipfile
            from PIL import Image
            
            # ZIP ファイル作成
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for idx, fig in enumerate(figures, 1):
                    buf = io.BytesIO()
                    fig.save(buf, format='PNG')
                    zip_file.writestr(f"Figure_{idx}.png", buf.getvalue())
                
                for idx, table in enumerate(tables, 1):
                    buf = io.BytesIO()
                    table.save(buf, format='PNG')
                    zip_file.writestr(f"Table_{idx}.png", buf.getvalue())
                
                for idx, df in enumerate(table_csvs, 1):
                    csv_data = df.to_csv(index=False, encoding='utf-8-sig')
                    zip_file.writestr(f"Table_{idx}.csv", csv_data)
            
            zip_buffer.seek(0)
            
            st.download_button(
                label="📥 全て ZIP でダウンロード",
                data=zip_buffer.getvalue(),
                file_name=f"{Path(uploaded_file.name).stem}_extracted.zip",
                mime="application/zip",
                use_container_width=True,
                type="primary"
            )
            
            # 個別ダウンロード
            if len(figures) > 0:
                st.markdown("### 📥 図のダウンロード")
                download_cols = st.columns(min(3, len(figures)))
                for idx, fig in enumerate(figures, 1):
                    buf = io.BytesIO()
                    fig.save(buf, format='PNG')
                    buf.seek(0)
                    with download_cols[(idx-1) % 3]:
                        st.download_button(
                            label=f"図 {idx}",
                            data=buf.getvalue(),
                            file_name=f"{Path(uploaded_file.name).stem}_Figure_{idx}.png",
                            mime="image/png",
                            use_container_width=True
                        )
            
            if len(table_csvs) > 0:
                st.markdown("### 📥 表（CSV）のダウンロード")
                download_cols = st.columns(min(3, len(table_csvs)))
                for idx, df in enumerate(table_csvs, 1):
                    csv_data = df.to_csv(index=False, encoding='utf-8-sig')
                    with download_cols[(idx-1) % 3]:
                        st.download_button(
                            label=f"表 {idx}",
                            data=csv_data,
                            file_name=f"{Path(uploaded_file.name).stem}_Table_{idx}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
            
            # クリーンアップ
            Path(tmp_path).unlink()
        
        except Exception as e:
            st.error(f"❌ エラーが発生しました：{str(e)}")
            st.info("💡 別の PDF を試してみてください。複雑な PDF の場合、処理に時間がかかることがあります。")

# フッター
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**🔧 技術スタック**")
    st.markdown("- Streamlit")
    st.markdown("- Docling AI")
with col2:
    st.markdown("**💬 サポート**")
    st.markdown("- [GitHub Issues](https://github.com)")
    st.markdown("- [ドキュメント](https://docs)")
with col3:
    st.markdown("**📄 バージョン**")
    st.markdown("- v1.0.0")
    st.markdown("- 最終更新：2026/01/12")
