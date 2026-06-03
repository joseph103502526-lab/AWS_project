FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .

EXPOSE 19191

CMD ["gunicorn", "--bind", "0.0.0.0:19191", "--workers", "2", "--threads", "1", "--timeout", "60", "app:app"]
