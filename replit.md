# MyPet01

## Overview
MyPet01 is a personal pet website designed as a family blog. It is a Django project focused on sharing pet-related content (videos, photos) with features such as user authentication, role-based access, responsive design, and theme options. The project emphasizes gradual development and scalability, providing a pleasant user experience.

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
The project is built on Python 3.12 with Django and Django REST Framework, following a clean architectural approach with strong emphasis on Object-Oriented Programming and inheritance from abstract base models (e.g., `BaseModel` with `created_at`, `updated_at`).

**UI/UX Decisions:**
- Frontend templates are based on the "Гармония Души" Figma design, reflecting a yoga and essential oils blog aesthetic.
- Key UI features include a mobile-responsive "burger menu," category filters, search functionality, and a dark/light theme toggle with `localStorage` persistence.
- Components include video/photo cards, modal windows for content viewing, and dynamic tag filters.
- **Design Theme (CSS Variables)**:
  - Primary: `#7AA9BA` (голубой)
  - Secondary: `#A8B89C` (зелёный)
  - Background: `#F9FAFA`
  - Muted: `#E8EDE7`

**Technical Implementations:**
- **Full-Text Search**: PostgreSQL Full-Text Search with `SearchVector` for title and description fields, accessible via `/search/` with pagination.
- **Content Management**: A `Content` model supports various `ContentType`s, multiple categories, and a dynamic tag system (`TagGroup`, `Tag`). Content types dictate upload folders, and forms support multi-select.
- **User Management**: `users` app provides authentication, role-based access control (Guests, Moderators, Admins), and a moderator management interface.
- **Security**: Configurable settings for development and production, including rate limiting (django-ratelimit), honeypot protection, input sanitization via `bleach`, security logging, and a strict Content Security Policy (CSP).
- **Caching**: Implements server-side caching (local memory, DB, Redis, or Memcached) and browser caching. Server-side cache invalidation uses Django signals.
- **File Management**: Handles image and video uploads with automatic thumbnail compression and unique MD5 hash names. Media files are served authenticated via Django's `FileResponse` through `ProtectedMediaView`.
- **Configuration**: Environment variables are managed via `pydantic-settings` with `.env` file support.

**Performance Optimizations:**
- **Tailwind CSS**: Local build via Tailwind v4 CLI integrated into a Docker multi-stage build process for efficient production deployment.
- **Gzip Pre-compression**: `docker-entrypoint.sh` pre-compresses static files using `gzip -9 -k`, served by Nginx with `gzip_static on`.
- **Media Caching**: Nginx serves `/media/` with `expires 7d` and `Cache-Control: public`.
- **Browser Caching**: `BrowserCacheMiddleware` provides configurable `Cache-Control` headers for static/media requests.
- **FOUC Prevention**: Inline CSS in `base.html` prevents Flash of Unstyled Content.
- **Query-level Caching**: `blog/cache.py` caches content IDs and filter context with signal-based invalidation.

**System Design Choices:**
- **Containerization**: Designed for Docker and Docker Compose environments, utilizing a multi-stage build.
- **Database**: PostgreSQL is the primary database.
- **Code Quality**: Emphasizes TDD, 100% test coverage, `ruff` linting, and `mypy` static analysis.
- **SSL/TLS Bootstrap**: Nginx uses a custom entrypoint to generate self-signed certificates on first deploy, replaced by Let's Encrypt via CI/CD.
- **Deployment**: Supports deployment to pre-production and production VPS environments, with CI/CD handling infrastructure setup.

## External Dependencies
- **Frameworks**: Django, Django REST Framework
- **Database**: PostgreSQL (`psycopg2-binary`, `dj-database-url`)
- **Configuration**: `pydantic-settings`
- **Containerization**: Docker, Docker Compose
- **Dependency Management**: Poetry
- **Static Analysis/Linting**: `mypy`, `ruff`
- **Image Processing**: Pillow
- **Testing**: pytest, pytest-django, pytest-cov, locust