FROM python:3.11-slim

WORKDIR /app

# システム依存パッケージのインストール
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルのコピー
COPY app.py .
COPY .streamlit .streamlit

# ポート公開
EXPOSE 7860

# ヘルスチェック
HEALTHCHECK CMD curl --fail http://localhost:7860/_stcore/health

# アプリケーション起動
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
