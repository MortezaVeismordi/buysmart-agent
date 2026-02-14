FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    # Playwright dependencies
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libasound2 libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy backend code
COPY backend /app/backend

# Install Python packages
WORKDIR /app/backend
RUN pip install --upgrade pip && \
    pip install -r requirements/base.txt

# Install Playwright system dependencies (as root)
RUN playwright install-deps

# Create non-root user
RUN useradd -m appuser && \
    chown -R appuser:appuser /app

USER appuser

# Install Playwright browsers (as appuser)
RUN playwright install chromium

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]