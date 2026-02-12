# MyPet01

## Overview
MyPet01 is a family-oriented blog built with Django 5.1+ for publishing photo and video content about pets. The project is designed for gradual development, scalability, maximum security, and 100% test coverage. It includes robust content management, user authentication, and advanced security features. The project aims to serve domains like `www.mine-craft.su` and `mine-craft.su`, with dedicated pre-production and production VPS environments.

## User Preferences
- **Coding Workflow (TDD + QA)**:
  1. Write tests first.
  2. Implement code.
  3. Verify with tests (`poetry run pytest`).
  4. **ОБЯЗАТЕЛЬНО** проверить линтеры (`poetry run ruff check .` и `poetry run mypy .`).
- **Test Coverage**: 100% code coverage is mandatory. All new code must be fully tested before merging.
- **Linters**: Проверка линтерами обязательна перед завершением любой задачи. Код не считается готовым без прохождения Ruff и Mypy.
- **Database Choice**: PostgreSQL is the preferred database for its robust Django support and features.
- **Tools**: Use `mypy` for static analysis and `ruff` for linting (line-length=119).
- **Design Principles**:
  - Strict adherence to **OOP** (Object-Oriented Programming).
  - Maximum use of **inheritance from abstract classes** to minimize code duplication and ensure consistent behavior across models.
- **Language**: Документация проекта и комментарии к пользовательским интерфейсам на русском языке. Код и имена переменных на английском.

## System Architecture

### Django Apps and Core Structure
The project is organized into `blog` (content management), `core` (shared utilities, security), and `users` (authentication, roles). Key architectural decisions include:
- **Models Hierarchy**: An OOP-based hierarchy starting with `BaseModel`, extending to `Category`, `TagGroup`, `Tag`, `ContentType`, and `Content`.
- **URL Structure**: Clearly defined public, moderator, and admin access patterns for content, tags, files, and user management.
- **Role-Based Access**: Granular permissions for Guest, Authenticated User, Moderator, and Admin roles.
- **Configuration**: `pydantic-settings` handles environment variables for critical settings like `DEBUG`, `SECRET_KEY`, `DATABASE_URL`, and security parameters.

### UI/UX and Frontend
- **Templating**: Django's template engine is used with a `base.html` for consistent layout, including theme toggling and CSP awareness.
- **Styling**: Tailwind CSS v4 is used for styling, built via a multi-stage Docker process.
- **Design Approach**: Focus on clear navigation and content presentation for the family blog theme.

### Technical Implementations
- **Full-Text Search**: Implemented with PostgreSQL's `SearchVector` and `SearchRank`, enhanced with keyboard layout conversion and Trigram similarity for robust search capabilities. Rate-limited to prevent abuse.
- **Caching**: Server-side caching for content IDs and filter contexts using configurable backends (locmem, db, redis, memcached). Invalidation is managed via Django signals. Browser caching is also implemented.
- **File Processing**: `ffmpeg` for video thumbnail generation and `Pillow` for image processing and resizing. Files are named using MD5 hashing for uniqueness.
- **Middleware Stack**: A carefully ordered middleware stack handles GZip compression, security (HTTPS, HSTS, CSP, CSRF, X-Frame-Options), session management, authentication, and custom browser caching, honeypot, and security logging.

### Security Layers
- **Django Application Security**: Includes rate limiting for various actions (login, uploads, API, search), honeypot for bot detection, input sanitization using `bleach`, path traversal protection, strict CSP, and `X-Frame-Options: DENY`. HTTPS and HSTS are enforced.
- **HAProxy Security (Production)**: Features GeoIP filtering (Russian IPs only, with VPN/ACME bypasses), extensive rate limiting for SSL, HTTP, and Minecraft traffic, scanner path blocking, BADREQ auto-banning, and a manual IP blacklist. ICMP blocking is also configured at the VPS level.
- **Nginx Security**: Manages SSL/TLS termination, robust headers (HSTS, X-Frame-Options, etc.), gzip compression, and efficient static/media file serving.

### Docker Architecture
- **Local Development**: `docker-compose.yml` sets up `web` (Django dev server), `db` (PostgreSQL), and `redis`.
- **Production**: `docker-compose.prod.yml` orchestrates `haproxy`, `nginx`, `web` (Gunicorn), `db`, `redis`, `certbot`, and `softether` for a complete production environment.
- **Multi-stage Dockerfile**: Optimizes image size by building Tailwind CSS in a `node` stage and then copying it into a `python` stage for the application.

## External Dependencies

- **Frameworks**: Django 5.1+, Django REST Framework
- **Database**: PostgreSQL 15 (`psycopg2-binary`, `dj-database-url`)
- **Configuration**: `pydantic-settings`
- **Security**: `django-csp`, `django-ratelimit`, `bleach`
- **Image/Video Processing**: Pillow, ffmpeg (system dependency)
- **Containerization**: Docker, Docker Compose
- **Dependency Management**: Poetry
- **Linting**: `ruff`, `mypy` (with `django-stubs`, `drf-stubs`)
- **Testing**: pytest, pytest-django, pytest-cov, pytest-playwright, locust
- **Frontend**: Tailwind CSS v4 (CLI build)
- **Web Servers**: Gunicorn, Nginx
- **Load Balancer**: HAProxy 2.9
- **VPN**: SoftEther VPN
- **SSL Certificates**: Let's Encrypt (Certbot)
- **CI/CD**: GitHub Actions