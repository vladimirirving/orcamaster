FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    fonts-liberation \
    libglib2.0-0 libpango-1.0-0 libpangoft2-1.0-0 \
    libharfbuzz0b libfontconfig1 libfreetype6 \
    libcairo2 libcairo-gobject2 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

COPY . .
