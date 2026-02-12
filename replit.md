# MyPet01

## Overview
MyPet01 is a family blog built with Django 5.1+ for publishing photo and video content about pets. The project aims for gradual development, scalability, maximum security, and 100% test coverage. It focuses on providing a secure and performant platform for sharing pet-related media, with a vision for future growth and community features.

## User Preferences
- **Coding Workflow (TDD + QA)**:
  1. Write tests first.
  2. Implement code.
  3. Verify with tests (`poetry run pytest`).
  4. ОБЯЗАТЕЛЬНО проверить линтеры (`poetry run ruff check .` и `poetry run mypy .`).
- **Test Coverage**: 100% code coverage is mandatory. All new code must be fully tested before merging.
- **Linters**: Проверка линтерами обязательна перед завершением любой задачи. Код не считается готовым без прохождения Ruff и Mypy.
- **Database Choice**: PostgreSQL is the preferred database for its robust Django support and features.
- **Tools**: Use `mypy` for static analysis and `ruff` for linting (line-length=119).
- **Design Principles**:
  - Strict adherence to **OOP** (Object-Oriented Programming).
  - Maximum use of **inheritance from abstract classes** to minimize code duplication and ensure consistent behavior across models.
- **Language**: Документация проекта и комментарии к пользовательским интерфейсам на русском языке. Код и имена переменных на английском.

## System Architecture

### Core Project Design
The application is built on Django, utilizing a modular structure with dedicated apps for content (`blog`), shared utilities (`core`), and user management (`users`). A strong emphasis is placed on Object-Oriented Programming (OOP) principles, particularly through model inheritance from a `BaseModel` to ensure consistency in `created_at` and `updated_at` fields across all main entities.

### UI/UX and Frontend
The frontend uses templates based on the "Гармония Души" Figma design, featuring components like video/photo cards, modal windows, and dynamic filtering for categories and tags. Tailwind CSS v4 is used for styling, built via CLI. A dark/light theme toggle is implemented and persisted using `localStorage`, with FOUC prevention via inline CSS.

### Key Features
- **Content Management**: CRUD operations for `Content`, `Category`, `TagGroup`, and `Tag` models.
- **Role-Based Access**: Guests, Authenticated Users, Moderators (CRUD for content and files), and Admins (moderator management, Django admin).
- **Full-Text Search**: Implemented with PostgreSQL `SearchVector` and `SearchRank`, including keyboard layout conversion (QWERTY<->ЙЦУКЕН) and Trigram similarity for robust search capabilities.
- **File Management**: Secure upload, deletion, and serving of media files, with thumbnail generation for videos (ffmpeg) and images (Pillow). Files are served only to authenticated users via `ProtectedMediaView`.
- **Caching**: Server-side caching for content lists and filter contexts, with invalidation triggered by Django signals. Browser caching is also configurable.

### Security
Multiple layers of security are integrated:
- **Django Application**:
    - Rate limiting (`django-ratelimit`) for login, uploads, API, and search.
    - Honeypot middleware for bot detection.
    - Input sanitization (`bleach`) for HTML and text fields.
    - Security logging for suspicious requests.
    - Path traversal protection for media paths.
    - Content Security Policy (CSP), X-Frame-Options (`DENY` by default), HTTPS/HSTS enforcement.
- **HAProxy (Production)**:
    - GeoIP filtering (Russian IPs only, with VPN/ACME bypass).
    - Extensive rate limiting for connections and requests across different services.
    - Blocking of known scanner paths and automatic banning for HTTP errors.
    - Manual IP blacklist.
    - ICMP blocking at the VPS level.
- **Nginx**:
    - SSL/TLS termination with strong ciphers and headers (HSTS, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection).
    - Gzip compression and efficient static/media file serving.

### Configuration
`pydantic-settings` is used for managing environment-based configurations, reading from `.env` files. Key settings include database connections, security parameters, and caching configurations.

### Docker Architecture
- **Local Development**: `docker-compose.yml` sets up `web` (Django dev server), `db` (PostgreSQL), and `redis`.
- **Production**: `docker-compose.prod.yml` orchestrates `haproxy`, `nginx`, `web` (Gunicorn), `db`, `redis`, `certbot`, and `softether` (VPN server).
- **Multi-stage Dockerfile**: Builds Tailwind CSS in a Node.js stage, then builds the Python application.
- **Entrypoint Script**: Automates database migrations, static file collection, fixture loading, and superuser creation before starting Gunicorn.

## External Dependencies

- **Frameworks**: Django 5.1+, Django REST Framework
- **Database**: PostgreSQL 15 (`psycopg2-binary`, `dj-database-url`)
- **Configuration**: `pydantic-settings`
- **Security**: `django-csp`, `django-ratelimit`, `bleach`
- **Image/Video Processing**: Pillow, ffmpeg (system dependency)
- **Containerization**: Docker, Docker Compose
- **Dependency Management**: Poetry
- **Linting**: `ruff`, `mypy` (with `django-stubs`, `drf-stubs`)
- **Testing**: `pytest`, `pytest-django`, `pytest-cov`, `pytest-playwright`, `locust`
- **Frontend**: Tailwind CSS v4 (CLI build)
- **Web Server**: Gunicorn, Nginx
- **Load Balancer**: HAProxy 2.9
- **VPN**: SoftEther VPN
- **SSL**: Let's Encrypt (Certbot)
- **CI/CD**: GitHub Actions