# MyPet01

## Overview
MyPet01 is a family blog built with Django 5.1+ for publishing photo and video content about pets. The project aims for gradual development, scalability, maximum security, and 100% test coverage. It includes features for content management, user authentication with role-based access, and advanced security measures. The business vision is to provide a robust and secure platform for sharing family-oriented pet content, with potential for market expansion into a niche social media or content sharing platform.

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

### Django Apps and Models
The project is structured around several Django applications: `blog` for content, search, and file serving; `core` for base models, middleware, security, and utilities; and `users` for authentication, roles, and moderator management. Key models include `Content`, `ContentType`, `Category`, `TagGroup`, and `Tag`, all inheriting from a `BaseModel` for `created_at` and `updated_at` fields. A strong emphasis is placed on Object-Oriented Programming (OOP) with extensive use of inheritance from abstract classes.

### UI/UX and Feature Specifications
The application provides a public interface for viewing content and searching, and a moderator interface for CRUD operations on content, tags, and file management. User roles include Guest, User (authenticated), Moderator, and Admin (superuser), with permissions scaled accordingly. The search functionality utilizes PostgreSQL's `SearchVector` and `SearchRank`, with fallbacks for keyboard layout conversion and Trigram similarity, and is rate-limited.

### Security and Middleware
Security is a multi-layered approach involving Django application-level measures and proxy-level hardening.
- **Django App Security**: Includes rate limiting for login, uploads, and API calls; honeypot for bot detection; input sanitization using `bleach`; security logging; path traversal protection; strict Content Security Policy (CSP); HTTPS/HSTS enforcement; and protected media serving for authenticated users.
- **Middleware Stack**: A carefully ordered middleware stack handles GZip compression, security headers (CSP, HSTS, X-Frame-Options), session management, CSRF protection, authentication, and custom `BrowserCacheMiddleware`, `HoneypotMiddleware`, and `SecurityLoggingMiddleware`.

### Caching
A robust caching architecture is implemented using server-side caching for content IDs and filter contexts, with configurable cache backends (locmem, db, redis, memcached). Cache invalidation is managed via Django signals for relevant model changes. Browser caching is also configurable.

### File Processing
The system handles video and image thumbnail generation using ffmpeg and Pillow, respectively. Video thumbnails are extracted from the first frame, and both video and image thumbnails are resized and optimized. MD5 hashing is used for unique filenames, and unique thumbnail naming ensures no conflicts.

### Configuration System
Project settings are managed using `pydantic-settings` to read environment variables from a `.env` file, ensuring flexible and secure configuration for various environments (DEBUG, SECRET_KEY, DATABASE_URL, etc.).

### Docker Architecture
The project utilizes Docker and Docker Compose for both local development and production deployments.
- **Local Development**: `docker-compose.yml` sets up a Django dev server, PostgreSQL, and Redis.
- **Production Deployment**: `docker-compose.prod.yml` orchestrates HAProxy (for load balancing and security), Nginx (for SSL termination and static/media serving), Gunicorn (for the Django app), PostgreSQL, Redis, Certbot (for SSL certificate management), and SoftEther VPN. A multi-stage Dockerfile optimizes image size by separating Tailwind CSS build from the Python application.

## External Dependencies

- **Frameworks**: Django 5.1+, Django REST Framework
- **Database**: PostgreSQL 15 (`psycopg2-binary`, `dj-database-url`)
- **Configuration**: `pydantic-settings`
- **Security**: `django-csp`, `django-ratelimit`, `bleach`
- **Image/Video Processing**: Pillow, ffmpeg (system dependency)
- **Containerization**: Docker, Docker Compose
- **Dependency Management**: Poetry
- **Linting**: `ruff`, `mypy` (`django-stubs`, `drf-stubs`)
- **Testing**: pytest, pytest-django, pytest-cov, pytest-playwright, locust
- **Frontend**: Tailwind CSS v4 (CLI build)
- **Web Server**: Gunicorn, Nginx
- **Load Balancer/Proxy**: HAProxy 2.9
- **VPN**: SoftEther VPN
- **SSL Certificate Management**: Let's Encrypt (Certbot)
- **CI/CD**: GitHub Actions