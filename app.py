import streamlit as st
import tempfile
from pathlib import Path
import time
import logging
from typing import Tuple, Optional, Generator
from contextlib import contextmanager
import fitz  # PyMuPDF
from docling_core.types.doc import PictureItem, TableItem
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

# ロギング設定
logging.basicConfig(level=logging.WARNING)


# =============================================================================
# 定数定義
# =============================================================================
MAX_FILE_SIZE_MB = 100
MAX_PAGES = 100
PROCESSING_TIMEOUT_SECONDS = 600


# =============================================================================
# 一時ファイル管理
# =============================================================================
@contextmanager
def temporary_pdf_file(content: bytes) -> Generator[str, None, None]:
    """
    一時PDFファイルを安全に管理するコンテキストマネージャ。

    Args:
        content: PDFファイルのバイナリコンテンツ

    Yields:
        str: 一時ファイルのパス

    Note:
        コンテキスト終了時に自動的にファイルを削除する。
        削除に失敗しても例外は発生しない。
    """
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        yield tmp_path
    finally:
        if tmp_path is not None:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass  # クリーンアップ失敗は無視


# =============================================================================
# セッション状態管理
# =============================================================================
def init_session_state() -> None:
    """セッション状態を初期化する。"""
    if "processing_result" not in st.session_state:
        st.session_state.processing_result = None
    if "last_processed_file" not in st.session_state:
        st.session_state.last_processed_file = None


def save_processing_result(
    filename: str,
    figures: list,
    tables: list,
    table_csvs: list,
    elapsed: float
) -> None:
    """処理結果をセッション状態に保存する。"""
    st.session_state.processing_result = {
        "figures": figures,
        "tables": tables,
        "table_csvs": table_csvs,
        "elapsed": elapsed
    }
    st.session_state.last_processed_file = filename


def clear_processing_result() -> None:
    """処理結果をクリアする。"""
    st.session_state.processing_result = None
    st.session_state.last_processed_file = None


# =============================================================================
# PDF検証機能
# =============================================================================
def validate_pdf(file_content: bytes, file_size_bytes: int) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    PDFファイルを検証する。

    Args:
        file_content: PDFファイルのバイナリコンテンツ
        file_size_bytes: ファイルサイズ（バイト）

    Returns:
        Tuple[bool, Optional[str], Optional[int]]:
            - 検証成功: (True, None, ページ数)
            - 検証失敗: (False, エラーメッセージ, None)
    """
    # ファイルサイズチェック
    file_size_mb = file_size_bytes / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        return (
            False,
            f"ファイルサイズが大きすぎます（最大{MAX_FILE_SIZE_MB}MB）。現在: {file_size_mb:.1f}MB",
            None
        )

    # PDFを開いて検証
    try:
        doc = fitz.open(stream=file_content, filetype="pdf")
    except Exception:
        return (False, "PDFファイルが破損している可能性があります", None)

    try:
        # パスワード保護チェック
        if doc.needs_pass:
            doc.close()
            return (False, "パスワードで保護されたPDFは処理できません", None)

        # ページ数取得・チェック
        page_count = doc.page_count

        # 空PDFチェック
        if page_count == 0:
            doc.close()
            return (False, "PDFにページが含まれていません", None)

        # ページ数上限チェック
        if page_count > MAX_PAGES:
            doc.close()
            return (
                False,
                f"ページ数が多すぎます（最大{MAX_PAGES}ページ）。現在: {page_count}ページ",
                None
            )

        doc.close()
        return (True, None, page_count)

    except Exception:
        doc.close()
        return (False, "PDFファイルの読み取り中にエラーが発生しました", None)


# =============================================================================
# モデルキャッシュ（メモリ最適化）
# =============================================================================
@st.cache_resource
def load_document_converter(resolution: float) -> DocumentConverter:
    """
    DocumentConverterをキャッシュして再利用する。
    解像度ごとにキャッシュされるため、同じ解像度での連続処理が高速化される。
    """
    pipeline_options = PdfPipelineOptions()

    # 画像生成設定
    pipeline_options.images_scale = resolution
    pipeline_options.generate_page_images = True
    pipeline_options.generate_picture_images = True

    # OCR無効化（スキャンPDF対象外のため）
    pipeline_options.do_ocr = False

    # 不要な機能を無効化（メモリ・処理時間削減）
    pipeline_options.do_table_structure = True  # 表の構造解析は有効
    pipeline_options.do_code_enrichment = False
    pipeline_options.do_formula_enrichment = False

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

# ページ設定
st.set_page_config(
    page_title="📄 論文PDF図表抽出ツール",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# セッション状態の初期化
init_session_state()

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

        # PDF検証
        status_text.write("🔍 PDFを検証中...")
        progress_bar.progress(5)

        file_content = uploaded_file.getbuffer()
        is_valid, error_message, page_count = validate_pdf(
            bytes(file_content), uploaded_file.size
        )

        if not is_valid:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ {error_message}")
            st.stop()

        st.info(f"📄 {page_count}ページのPDFを処理します")

        try:
            # コンテキストマネージャで一時ファイルを安全に管理
            with temporary_pdf_file(bytes(file_content)) as tmp_path:
                status_text.write("🔄 PDF を解析中...（AIモデルを初期化）")
                progress_bar.progress(10)

                # DocumentConverter取得（キャッシュ済み）
                doc_converter = load_document_converter(resolution)

                status_text.write("🔄 PDFを処理中...")
                progress_bar.progress(30)

                # PDF 変換
                start_time = time.time()
                conv_res = doc_converter.convert(tmp_path)
                elapsed = time.time() - start_time

                # タイムアウトチェック
                if elapsed > PROCESSING_TIMEOUT_SECONDS:
                    raise TimeoutError(f"処理時間が{PROCESSING_TIMEOUT_SECONDS}秒を超えました")

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
                                # 重複列名を自動リネーム
                                if df.columns.duplicated().any():
                                    new_cols = []
                                    col_count = {}
                                    for col in df.columns:
                                        if col in col_count:
                                            col_count[col] += 1
                                            new_cols.append(f"{col}_{col_count[col]}")
                                        else:
                                            col_count[col] = 0
                                            new_cols.append(col)
                                    df.columns = new_cols
                                table_csvs.append(df)
                            except:
                                pass
                        except Exception:
                            pass

                    # 図抽出
                    if isinstance(element, PictureItem):
                        try:
                            element_image = element.get_image(conv_res.document)
                            if element_image is not None:
                                figures.append(element_image)
                        except Exception:
                            pass

                progress_bar.progress(80)

                # 処理結果をセッション状態に保存
                save_processing_result(
                    uploaded_file.name, figures, tables, table_csvs, elapsed
                )

                # 結果表示
                status_text.write("✅ 処理完了！")
                progress_bar.progress(100)
                time.sleep(0.5)
                progress_bar.empty()
                status_text.empty()

        except MemoryError:
            progress_bar.empty()
            status_text.empty()
            st.error("❌ メモリ不足エラーが発生しました")
            st.info("💡 より小さいPDFを試すか、解像度を下げてください。")

        except TimeoutError as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ {str(e)}")
            st.info("💡 ページ数の少ないPDFを試すか、解像度を下げてください。")

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ エラーが発生しました：{str(e)}")
            st.info("💡 別の PDF を試してみてください。複雑な PDF の場合、処理に時間がかかることがあります。")

    # 結果ダッシュボード（run_buttonの外で表示 - ダウンロード後も維持される）
    if (st.session_state.processing_result is not None and
        st.session_state.last_processed_file == uploaded_file.name):
        result = st.session_state.processing_result
        figures = result["figures"]
        tables = result["tables"]
        table_csvs = result["table_csvs"]
        elapsed = result["elapsed"]

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
                st.image(fig, caption=f"図 {idx}", use_container_width=True)

        if len(tables) > 0:
            st.subheader("📊 抽出された表")
            for idx, table in enumerate(tables, 1):
                col1, col2 = st.columns(2)
                with col1:
                    st.image(table, caption=f"表 {idx}", use_container_width=True)
                with col2:
                    if idx <= len(table_csvs):
                        try:
                            st.dataframe(table_csvs[idx-1], use_container_width=True)
                        except Exception as e:
                            st.warning(f"表 {idx} のデータ表示でエラー: {str(e)}")

        if len(figures) == 0 and len(tables) == 0:
            st.warning("⚠️ この PDF に抽出可能な図表が見つかりませんでした")

        # ダウンロード準備
        st.markdown("---")
        st.subheader("⬇️ ステップ3：結果をダウンロード")

        import io
        import zipfile

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
            file_name=f"{Path(st.session_state.last_processed_file).stem}_extracted.zip",
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
                        file_name=f"{Path(st.session_state.last_processed_file).stem}_Figure_{idx}.png",
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
                        file_name=f"{Path(st.session_state.last_processed_file).stem}_Table_{idx}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

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
