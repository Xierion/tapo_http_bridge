FROM python:3.12-slim
LABEL org.opencontainers.image.source=https://github.com/Xierion/tapo_http_bridge
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5111
CMD ["gunicorn", "-b", "0.0.0.0:5111", "-w", "1", "app:app"]
