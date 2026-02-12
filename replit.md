# MyPet01

## Overview
MyPet01 is a family blog built with Django 5.1+ for publishing photo and video content about pets. The project aims for gradual development, scalability, maximum security, and 100% test coverage. Key capabilities include rich content publishing, advanced search, robust moderation tools, and secure media handling. The business vision is to create a secure, high-performance platform for family content sharing with future potential for community features and personalized experiences.

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

### UI/UX Decisions
The front-end uses Tailwind CSS v4 for styling, built via a multi-stage Docker process. The base template (`base.html`) includes features like theme toggling, FOUC prevention, and is CSP-aware. Content is presented through customizable video/content cards. Navigation includes a burger menu, and filtering mechanisms utilize dropdowns for categories and tags.

### Technical Implementations
- **Django Apps**: `blog` (content, search, files), `core` (base models, middleware, security, utilities), `users` (authentication, roles, moderator management).
- **Models**: A strict OOP hierarchy extends from `BaseModel` to `Category`, `TagGroup`, `Tag`, `ContentType`, and `Content`. `ContentQuerySet` provides optimized data retrieval.
- **URL Structure**: Comprehensive URL patterns for public access, authenticated user features, and moderator/admin CRUD operations for content, tags, and files.
- **Role-Based Access**: Granular permissions for Guest, Authenticated User, Moderator, and Admin roles.
- **Full-Text Search**: Implemented via PostgreSQL `SearchVector` and `SearchRank`, with fallbacks for keyboard layout conversion (QWERTY<->ЙЦУКЕН) and Trigram similarity, plus rate limiting.
- **Caching**: Server-side caching for content IDs and filter contexts using configurable backends (locmem, db, redis, memcached). Invalidation is handled by Django signals. Browser caching is also configurable.
- **File Processing**: `ffmpeg` for video thumbnail generation, `Pillow` for image resizing and thumbnailing. Files are hashed for unique naming and securely stored.
- **Configuration**: Uses `pydantic-settings` to manage environment variables from `.env` files, providing robust and validated settings.
- **Middleware**: A carefully ordered middleware stack handles GZip compression, security (HTTPS, HSTS, CSP, CSRF, X-Frame-Options), session management, authentication, browser caching, honeypot detection, and security logging.

### System Design Choices
- **Security**: Multi-layered security includes Django application-level rate limiting, honeypot, input sanitization (`bleach`), path traversal protection, CSP, X-Frame-Options (default DENY), and HTTPS/HSTS enforcement. Production deployments leverage HAProxy for GeoIP filtering, advanced rate limiting, scanner path blocking, and manual IP blacklisting. Nginx provides additional SSL/TLS hardening and static/media serving.
- **Docker Architecture**:
    - **Local Development**: `docker-compose.yml` sets up `web` (Django dev server), `db` (PostgreSQL), and `redis`.
    - **Production**: `docker-compose.prod.yml` orchestrates `haproxy` (network_mode: host), `nginx`, `web` (Gunicorn), `db`, `redis`, `certbot`, and `softether` (VPN server).
    - **Multi-stage Dockerfile**: Optimizes image size by building Tailwind CSS in a `node` stage and then copying it to a `python` stage for the application.
- **Deployment Strategy**: Automated deployments using GitHub Actions with a Dev -> Staging -> PreProd -> Prod pipeline following Gitflow principles. Initial VPS setup is automated via shell scripts.

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