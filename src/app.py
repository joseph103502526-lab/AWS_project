import math
import os
import time
from multiprocessing import Process

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    boto3 = None
    ClientError = None
    NoCredentialsError = None


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "aws-devops-lab-secret")

BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "ckc101-05")
AWS_REGION = os.environ.get("AWS_REGION", "ap-northeast-3")
DEFAULT_STRESS_SECONDS = int(os.environ.get("STRESS_SECONDS", "45"))
MAX_STRESS_SECONDS = int(os.environ.get("MAX_STRESS_SECONDS", "90"))
STRESS_WORKER_MULTIPLIER = int(os.environ.get("STRESS_WORKER_MULTIPLIER", "2"))
MAX_STRESS_WORKERS = int(os.environ.get("MAX_STRESS_WORKERS", "0"))


def get_s3_client():
    if boto3 is None:
        raise RuntimeError("boto3 is not installed. Run pip install -r requirements.txt.")
    return boto3.client("s3", region_name=AWS_REGION)


def _cpu_burn_worker(duration_seconds):
    deadline = time.perf_counter() + duration_seconds
    value = 1.000001

    while time.perf_counter() < deadline:
        for i in range(1, 80_000):
            value = math.sin(value + i) * math.sqrt(i) + math.cos(value)
            if value == 0:
                value = 1.000001


def run_cpu_stress(duration_seconds):
    cpu_count = os.cpu_count() or 1
    requested_workers = max(1, cpu_count * max(1, STRESS_WORKER_MULTIPLIER))
    workers = requested_workers
    if MAX_STRESS_WORKERS > 0:
        workers = min(requested_workers, MAX_STRESS_WORKERS)

    processes = [
        Process(target=_cpu_burn_worker, args=(duration_seconds,))
        for _ in range(workers)
    ]

    started_at = time.perf_counter()
    for process in processes:
        process.start()

    for process in processes:
        remaining = max(0.1, duration_seconds + 2 - (time.perf_counter() - started_at))
        process.join(timeout=remaining)

    for process in processes:
        if process.is_alive():
            process.terminate()
            process.join(timeout=1)

    return workers, round(time.perf_counter() - started_at, 2)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200


@app.route("/feature1")
def feature1():
    return jsonify({"status": "ok", "message": "Feature 1 completed"})


@app.route("/feature2")
def feature2():
    return jsonify({"status": "ok", "message": "Feature 2 completed"})


@app.route("/feature4")
def feature4():
    requested_duration = request.args.get("duration", DEFAULT_STRESS_SECONDS, type=int)
    duration_seconds = max(1, min(requested_duration, MAX_STRESS_SECONDS))
    workers, elapsed_seconds = run_cpu_stress(duration_seconds)

    return jsonify(
        {
            "status": "success",
            "message": "CPU stress test completed",
            "target_cpu": ">=90%",
            "duration_seconds": duration_seconds,
            "elapsed_seconds": elapsed_seconds,
            "workers": workers,
        }
    )


@app.route("/storage", methods=["GET"])
def storage():
    s3 = get_s3_client()
    files = []
    error_msg = None

    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME)
        objects = response.get("Contents", [])

        for obj in objects:
            key = obj["Key"]
            files.append(
                {
                    "name": key,
                    "size_kb": round(obj["Size"] / 1024, 2),
                    "last_modified": obj["LastModified"].strftime("%Y-%m-%d %H:%M"),
                    "download_url": s3.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": BUCKET_NAME, "Key": key},
                        ExpiresIn=3600,
                    ),
                }
            )
    except Exception as error:
        if NoCredentialsError is not None and isinstance(error, NoCredentialsError):
            error_msg = "AWS credentials were not found. Configure credentials or attach an IAM role."
        elif ClientError is not None and isinstance(error, ClientError):
            error_msg = f"AWS error: {error.response['Error']['Message']}"
        else:
            error_msg = str(error)

    return render_template(
        "storage.html",
        files=files,
        bucket_name=BUCKET_NAME,
        error_msg=error_msg,
    )


@app.route("/storage/upload", methods=["POST"])
def storage_upload():
    if "file" not in request.files:
        flash("No file was selected.", "error")
        return redirect(url_for("storage"))

    file = request.files["file"]
    if file.filename == "":
        flash("No file was selected.", "error")
        return redirect(url_for("storage"))

    s3 = get_s3_client()
    try:
        s3.upload_fileobj(
            file,
            BUCKET_NAME,
            file.filename,
            ExtraArgs={"ContentType": file.content_type or "application/octet-stream"},
        )
        flash(f"{file.filename} uploaded to S3.", "success")
    except Exception as error:
        if NoCredentialsError is not None and isinstance(error, NoCredentialsError):
            flash("AWS credentials were not found.", "error")
        elif ClientError is not None and isinstance(error, ClientError):
            flash(f"Upload failed: {error.response['Error']['Message']}", "error")
        else:
            flash(f"Upload failed: {error}", "error")

    return redirect(url_for("storage"))


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=19191,
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
