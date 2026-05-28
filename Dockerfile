# ── Stage: Base Image ──────────────────────────────────────────────
# 使用輕量官方映像，python:3.14-slim 基於 Debian，體積小且穩定
FROM python:3.14-slim


# ── Working Directory ───────────────────────────────────────────────
# 設定容器內工作目錄，後續所有指令皆在此路徑下執行
WORKDIR /app

# ── Install Dependencies ────────────────────────────────────────────
# 先複製 requirements.txt（利用 Docker layer cache，只有此檔變動時才重跑 pip）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy Application Source ─────────────────────────────────────────
# 將 src/ 資料夾內容複製至容器 /app 目錄下
COPY src/ .

# ── Expose Port ─────────────────────────────────────────────────────
# 宣告應用程式監聽的連接埠（與 app.py 中 port=19191 一致）
EXPOSE 19191

# ── Start Command ───────────────────────────────────────────────────
# 使用 python 直接執行 app.py（host=0.0.0.0 已在程式碼中設定）
CMD ["python", "app.py"]
