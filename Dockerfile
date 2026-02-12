# Stage 1: Build Tailwind CSS
FROM node:20-slim AS tailwind-builder
WORKDIR /build
COPY package.json package-lock.json* /build/
RUN npm ci --no-audit
COPY static/css/tailwind-input.css /build/static/css/tailwind-input.css
COPY templates/ /build/templates/
COPY blog/templates/ /build/blog/templates/
COPY users/templates/ /build/users/templates/
RUN npx @tailwindcss/cli -i static/css/tailwind-input.css -o static/css/tailwind.css --minify

# Stage 2: Python application
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

# Copy built Tailwind CSS from builder stage
COPY --from=tailwind-builder /build/static/css/tailwind.css /app/static/css/tailwind.css

# Create logs directory for security logging
RUN mkdir -p /app/logs

# Copy and set entrypoint
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "mypet_project.wsgi:application"]
