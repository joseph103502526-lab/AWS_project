# Feature 4 CPU Stress Deployment Guide

本專案提供 Flask `/feature4` CPU 壓力測試路由、深色模式前端儀表板、Dockerfile，以及 AWS CloudWatch + SNS Email 警報設定流程。

## 本機測試

```powershell
.\venv\Scripts\python.exe -m pytest -q
.\venv\Scripts\python.exe src\app.py
```

瀏覽器開啟：

```text
http://localhost:19191/
```

點擊「壓力測試 (Stress)」會呼叫 `/feature4?duration=60`，伺服器端預設執行約 45 秒 CPU 密集計算。測試短時間呼叫可使用：

```text
http://localhost:19191/feature4?duration=1
```

## Docker Build / Tag / Push

請將 `YOUR_DOCKERHUB_USERNAME` 換成你的 Docker Hub 帳號。

```powershell
docker login
docker build -t aws-flask-feature4:latest .
docker tag aws-flask-feature4:latest YOUR_DOCKERHUB_USERNAME/aws-flask-feature4:feature4-cpu-stress
docker tag aws-flask-feature4:latest YOUR_DOCKERHUB_USERNAME/aws-flask-feature4:latest
docker push YOUR_DOCKERHUB_USERNAME/aws-flask-feature4:feature4-cpu-stress
docker push YOUR_DOCKERHUB_USERNAME/aws-flask-feature4:latest
```

本機用 Docker 驗證：

```powershell
docker run --rm -p 19191:19191 YOUR_DOCKERHUB_USERNAME/aws-flask-feature4:feature4-cpu-stress
```

## AWS 部署範例

若使用 EC2，登入 EC2 後執行：

```bash
sudo yum update -y
sudo yum install -y docker
sudo systemctl enable --now docker
sudo docker pull YOUR_DOCKERHUB_USERNAME/aws-flask-feature4:feature4-cpu-stress
sudo docker run -d --name aws-flask-feature4 --restart unless-stopped -p 80:19191 YOUR_DOCKERHUB_USERNAME/aws-flask-feature4:feature4-cpu-stress
```

EC2 Security Group 需允許 HTTP `80` inbound，之後開啟：

```text
http://EC2_PUBLIC_IP/
```

## SNS Email 通知設定

1. 進入 AWS Console，確認右上角 Region 是你的 EC2 所在區域。
2. 搜尋並進入 `Simple Notification Service`。
3. 左側選 `Topics`，點 `Create topic`。
4. Type 選 `Standard`。
5. Name 輸入 `cpu-stress-email-topic`，建立 Topic。
6. 進入該 Topic，點 `Create subscription`。
7. Protocol 選 `Email`。
8. Endpoint 輸入你的 Email，建立 subscription。
9. 到信箱收 AWS 確認信，點 `Confirm subscription`。

## CloudWatch Alarm 設定

以 EC2 CPU 為例：

1. 進入 AWS Console，搜尋 `CloudWatch`。
2. 左側選 `Alarms` > `All alarms`。
3. 點 `Create alarm`。
4. 點 `Select metric`。
5. 選 `EC2` > `Per-Instance Metrics`。
6. 搜尋並勾選你的 EC2 InstanceId 的 `CPUUtilization`。
7. Metric 設定：
   - Statistic: `Average`
   - Period: `1 minute`
8. Conditions 設定：
   - Threshold type: `Static`
   - Whenever CPUUtilization is: `Greater/Equal`
   - than: `70`
9. Additional configuration：
   - Datapoints to alarm: `1 out of 1`
   - Missing data treatment: `Treat missing data as missing`
10. Notification 設定：
    - Alarm state trigger: `In alarm`
    - Select an SNS topic: 選 `cpu-stress-email-topic`
11. Alarm name 輸入 `feature4-cpu-greater-equal-70-1min`。
12. Review 後點 `Create alarm`。

設定完成後，打開網站點「壓力測試 (Stress)」。CloudWatch 需要等待下一個 1 分鐘 metric period 才會評估，通常 1-3 分鐘內會看到 Alarm 轉為 `In alarm` 並收到 Email。

## 注意事項

- EC2 `CPUUtilization` 監控的是整台 EC2 的 CPU。如果 EC2 上只跑這個容器，最容易觀察。
- 若 EC2 有多核心，單次測試可能不一定讓整台機器平均 CPU 超過 70%。可改用較小 instance，例如 `t2.micro` 或 `t3.micro`，或設定環境變數增加 worker。預設會使用 `vCPU 數量 x 2` 個 worker；若還不夠，可加大 `STRESS_WORKER_MULTIPLIER`：

```bash
sudo docker run -d --name aws-flask-feature4 --restart unless-stopped -p 80:19191 -e STRESS_WORKER_MULTIPLIER=4 YOUR_DOCKERHUB_USERNAME/aws-flask-feature4:feature4-cpu-stress
```

- 若部署在 ECS 並想監控容器層級 CPU，請啟用 ECS Container Insights，CloudWatch metric 選 `ECS/ContainerInsights` 中對應 Service 或 Task 的 CPU 指標。
