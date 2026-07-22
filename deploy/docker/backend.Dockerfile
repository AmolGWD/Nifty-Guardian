# Multi-stage build for the FastAPI backend. Build context is the
# REPOSITORY ROOT (see deploy/docker-compose*.yml) - every COPY path
# below is `backend/...`, since this Dockerfile also needs to be able
# to reach sibling directories in later stages if that's ever needed.
#
# Stages:
#   builder    - installs Python dependencies only, nothing else
#   dev        - builder + dev dependencies + source, hot-reload command
#   production - builder + source only, non-root user, healthcheck
#
# `docker build --target dev` / `--target production` selects which
# one to build; docker-compose.dev.yml / docker-compose.prod.yml pick
# the target for you.

FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY backend/requirements.txt ./
RUN pip install --user --no-cache-dir -r requirements.txt


FROM python:3.12-slim AS dev

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH

COPY --from=builder /root/.local /root/.local
COPY backend/requirements-dev.txt ./
RUN pip install --user --no-cache-dir -r requirements-dev.txt

COPY backend/app ./app
COPY backend/tests ./tests

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


FROM python:3.12-slim AS production

RUN groupadd --system appuser && useradd --system --gid appuser --no-create-home appuser

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/appuser/.local/bin:$PATH

COPY --from=builder /root/.local /home/appuser/.local
COPY backend/app ./app

RUN chown -R appuser:appuser /app /home/appuser/.local

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health/live', timeout=3).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
