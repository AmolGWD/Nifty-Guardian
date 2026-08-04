FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# `app/` includes its own `app/market_data/sample_data/` - the one
# canonical copy of the runtime's default replay dataset (moved here
# from `scripts/sample_data/`, not duplicated - see that directory's
# own README.md) - specifically so it ships with this image (see
# app/api/dashboard/dashboard_service.py and
# app/api/signals/signals_service.py's own path-resolution comments).
# `scripts/` itself is intentionally never copied here - it's outside
# this Dockerfile's build context in a typical Railway
# "root directory: backend" setup, and the app must not depend on
# anything there at runtime.
COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
