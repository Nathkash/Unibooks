FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies needed for some Python packages (psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

# Use the existing start script (migrations, collectstatic, gunicorn)
CMD ["bash", "start.sh"]
