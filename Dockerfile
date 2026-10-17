# syntax=docker/dockerfile:1

FROM python:3.13-slim-bookworm AS builder

RUN apt-get update \
&& apt-get install -y --no-install-recommends git \
&& rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


FROM python:3.13-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/Xierion/tapo_http_bridge"
LABEL org.opencontainers.image.description="HTTP bridge for a Tapo P100 smart plug"

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
PYTHONUNBUFFERED=1

RUN useradd --system --no-create-home --uid 10001 tapo

WORKDIR /app
COPY app.py .

USER tapo

EXPOSE 5111

CMD ["gunicorn", "--workers", "1", "--timeout", "15", "--graceful-timeout", "5", "--bind", "0.0.0.0:5111", "--no-control-socket", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
