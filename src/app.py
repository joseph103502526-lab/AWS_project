from flask import Flask, jsonify, render_template

app = Flask(__name__)


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=19191, debug=True)
