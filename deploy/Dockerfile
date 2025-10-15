# Production Dockerfile for Aldudu Academy
# Uses gunicorn to serve the Flask app

FROM python:3.11-slim

# system deps for psycopg2 and other packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage layer caching
COPY requirements.txt /app/
RUN python -m pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . /app

# Create non-root user
RUN useradd -m -d /home/appuser appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
EXPOSE ${PORT}

# Use gunicorn as the production WSGI server
CMD ["gunicorn", "app:create_app()", "-b", "0.0.0.0:8000", "-w", "3", "--log-level=info"]
