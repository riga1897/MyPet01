# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry

# Copy project files
COPY pyproject.toml poetry.lock* /app/

# Install dependencies (--no-root: don't install project as package)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the application
COPY . /app/

# Collect static files for nginx
RUN python manage.py collectstatic --noinput

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "mypet_project.wsgi:application"]
