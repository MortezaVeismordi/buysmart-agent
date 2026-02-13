# Stage 1: Base image
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m appuser

# Stage 2: Dependencies
FROM base AS builder

RUN pip install --upgrade pip

COPY backend/requirements/ /app/requirements/
RUN pip install -r /app/requirements/base.txt \
    && pip install -r /app/requirements/dev.txt

COPY backend/ /app/

RUN chown -R appuser:appuser /app

# Stage 3: Final image
FROM base

COPY --from=builder /app /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

USER appuser

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]