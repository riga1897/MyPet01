# MyPet01

## Overview
MyPet01 is a personal pet website designed for family use, focusing on sharing content related to pets. It is a Django-based project with a minimalist backend, built for gradual development and easy maintenance. The project aims to provide a robust platform for content sharing, user management, and administrative control, with a strong emphasis on clean architecture and test-driven development.

## User Preferences
- **Coding Workflow (TDD + QA)**:
  1. Write tests first.
  2. Implement code.
  3. Verify with tests (`poetry run pytest`).
  4. **ОБЯЗАТЕЛЬНО** проверить линтеры (`poetry run ruff check .` и `poetry run mypy .`).
- **Test Coverage**: 100% code coverage is mandatory. All new code must be fully tested before merging.
- **Linters**: Проверка линтерами обязательна перед завершением любой задачи. Код не считается готовым без прохождения Ruff и Mypy.
- **Database Choice**: PostgreSQL is the preferred database for its robust Django support and features.
- **Tools**: Use `mypy` for static analysis and `ruff` for linting.
- **Design Principles**:
  - Strict adherence to **OOP** (Object-Oriented Programming).
  - Maximum use of **inheritance from abstract classes** to minimize code duplication and ensure consistent behavior across models.

## System Architecture
The project is built on Python 3.12 and Django, using Django REST Framework for API capabilities. It adopts a container-compatible design using Docker and Docker Compose for development and deployment. Configuration is managed via `pydantic-settings` for typed environment variables.

### Core Features
- **Content Management**: Supports video and photo content, categorized and tagged dynamically. Includes a robust content model (`Content`) with fields for title, description, type, categories, thumbnail, and media files.
- **User Authentication & Authorization**: Features a `users` app with authentication and role-based permissions, including a "moderator" group with dedicated management interfaces.
- **Dynamic Tagging System**: Implements `TagGroup` and `Tag` models for flexible content organization, including a moderator interface for managing tags and groups, and filters on the homepage.
- **UI/UX**: Frontend templates are based on a Figma design named "Гармония Души" (Harmony of Soul), featuring a mobile-responsive menu, dark/light theme toggle, category filters, and search functionality.
  - **Color Scheme**: Primary: `#7AA9BA` (blue), Secondary: `#A8B89C` (green), Background: `#F9FAFA`, Muted: `#E8EDE7`.
- **SEO & Performance**: Includes SEO optimization (meta tags, Open Graph, favicon), server-side caching (locmem, db, redis, memcached backends), browser cache control, and GZip compression.
- **Data Models**:
    - `BaseModel`: Abstract base for common fields (`created_at`, `updated_at`).
    - `Category`: Defines content categories.
    - `TagGroup`: Organizes tags, can be linked to specific categories.
    - `Tag`: Individual tags, linked to `TagGroup`, with ordering capability.
    - `Content`: Main content model supporting videos and photos, linked to `Category` and `Tag`.
- **Security**: Development settings disable some security features for ease of development, while production settings enforce `SECURE_SSL_REDIRECT`, `HSTS`, and other secure cookie flags. XSS protection and MIME-type sniffing prevention are always enabled.
- **Containerization**: Dockerfiles for production (with Gunicorn) and development (DEBUG=1), along with Docker Compose configurations for both environments. A `docker-entrypoint.sh` script handles migrations, static file collection, and Gunicorn startup.

## External Dependencies
- **Database**: PostgreSQL
- **Dependency Management**: Poetry
- **Static Analysis**: Mypy
- **Linting**: Ruff
- **Container Orchestration**: Docker & Docker Compose
- **Configuration Management**: Pydantic-settings
- **Image Processing**: Pillow (for thumbnail compression)
- **Web Server (Production)**: Gunicorn
- **Reverse Proxy (Production)**: Nginx (configured for static/media serving and gzip)
- **CI/CD**: GitHub Actions