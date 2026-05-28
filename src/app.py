from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

app = Flask(__name__)
app.secret_key = "aws-s3-storage-secret"

# ─────────────────────────────────────────────
# 全域設定：S3 儲存桶名稱與 AWS 區域（台北機房）
# ─────────────────────────────────────────────
BUCKET_NAME = "ckc101-05"
AWS_REGION = "ap-northeast-3"

# ⚠️ 資安原則：不硬編碼任何金鑰。
# boto3 會自動讀取本機 Windows 系統的環境變數、
# ~/.aws/credentials 或 IAM Role 憑證。
def get_s3_client():
    """建立並回傳 S3 Client（憑證由系統環境自動提供）。"""
    return boto3.client("s3", region_name=AWS_REGION)


# ─────────────────────────────────────────────
# 路由定義
# ─────────────────────────────────────────────

@app.route("/")
def index():
    """首頁路由，渲染前端 HTML 頁面。"""
    return render_template("index.html")


@app.route("/health")
def health():
    """健康檢查路由，供 Load Balancer / Container 使用。"""
    return jsonify({"status": "healthy"}), 200


@app.route("/feature1")
def feature1():
    """Feature 1：早上看股票提醒。"""
    return jsonify({"status": "ok", "message": "早上要看股票"})


@app.route("/feature2")
def feature2():
    """Feature 2：找下午上班的公司提醒。"""
    return jsonify({"status": "ok", "message": "要找下午上班的公司"})


# ─────────────────────────────────────────────
# Feature 3：AWS S3 雲端檔案管理
# ─────────────────────────────────────────────

@app.route("/storage", methods=["GET"])
def storage():
    """
    Feature 3：AWS S3 雲端檔案管理頁面。
    列出 Bucket 內所有物件，並提供上傳與下載功能。
    """
    s3 = get_s3_client()
    files = []
    error_msg = None

    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME)
        objects = response.get("Contents", [])

        for obj in objects:
            key = obj["Key"]
            size_kb = round(obj["Size"] / 1024, 2)
            last_modified = obj["LastModified"].strftime("%Y-%m-%d %H:%M")

            # 生成有效期 1 小時的預簽名下載網址
            download_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": BUCKET_NAME, "Key": key},
                ExpiresIn=3600,
            )

            files.append({
                "name": key,
                "size_kb": size_kb,
                "last_modified": last_modified,
                "download_url": download_url,
            })

    except NoCredentialsError:
        error_msg = "❌ 找不到 AWS 憑證，請確認環境變數或 ~/.aws/credentials 設定正確。"
    except ClientError as e:
        error_msg = f"❌ AWS 錯誤：{e.response['Error']['Message']}"

    return render_template(
        "storage.html",
        files=files,
        bucket_name=BUCKET_NAME,
        error_msg=error_msg,
    )


@app.route("/storage/upload", methods=["POST"])
def storage_upload():
    """接收檔案上傳表單，使用 upload_fileobj 推送到 S3。"""
    if "file" not in request.files:
        flash("❌ 未選取任何檔案", "error")
        return redirect(url_for("storage"))

    file = request.files["file"]
    if file.filename == "":
        flash("❌ 檔案名稱為空，請重新選取", "error")
        return redirect(url_for("storage"))

    s3 = get_s3_client()
    try:
        s3.upload_fileobj(
            file,
            BUCKET_NAME,
            file.filename,
            ExtraArgs={"ContentType": file.content_type or "application/octet-stream"},
        )
        flash(f"✅ 檔案「{file.filename}」已成功上傳至 S3！", "success")
    except NoCredentialsError:
        flash("❌ 找不到 AWS 憑證，請確認環境變數設定。", "error")
    except ClientError as e:
        flash(f"❌ 上傳失敗：{e.response['Error']['Message']}", "error")

    return redirect(url_for("storage"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=19191, debug=True)
