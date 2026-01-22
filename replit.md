# MyPet01

## Overview
MyPet01 is a personal pet website designed to be a family blog. It is built as a Django project with a minimalist backend, focusing on gradual development and scalability. The project aims to provide a platform for sharing content (videos, photos) related to pets, with features such as user authentication, role-based access for content management, and a focus on a pleasant user experience with responsive design and theme options.

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
The project is built on Python 3.12 with Django and Django REST Framework. It uses a clean architectural approach with a focus on Object-Oriented Programming and inheritance from abstract base models for consistency (`BaseModel` with `created_at`, `updated_at`).

**UI/UX Decisions:**
- Frontend templates are based on the "Гармония Души" Figma design, featuring a yoga and essential oils blog aesthetic.
- The design includes a mobile-responsive "burger menu", category filters, search functionality, and a dark/light theme toggle with `localStorage` persistence.
- Key UI components include video/photo cards, modal windows for content viewing, and dynamic tag filters.
- **Design Theme (CSS Variables)**:
  - Primary: `#7AA9BA` (голубой)
  - Secondary: `#A8B89C` (зелёный)
  - Background: `#F9FAFA`
  - Muted: `#E8EDE7`

**Technical Implementations:**
- **Content Management**: Features a robust content model (`Content`) supporting various content types (`ContentType`), categories, and a dynamic tag system (`TagGroup`, `Tag`). Content types dictate upload folders, and tags can be grouped and filtered.
- **User Management**: Includes a `users` app with authentication, role-based access control (Guests, Moderators, Admins), and a moderator management interface.
- **Security**: Configurable security settings for development (HTTP) and production (HTTPS with HSTS, secure cookies, XSS protection, content sniffing prevention, clickjacking prevention).
- **Caching**: Implements both server-side caching (local memory, DB, Redis, or Memcached) and browser caching with configurable `Cache-Control` headers. Server-side cache invalidation is automated via Django signals on content changes.
- **File Management**: Handles image and video uploads, with thumbnails automatically compressed and unique MD5 hash names. Supports selecting existing files and path traversal protection.
- **Configuration**: Environment variables are managed via `pydantic-settings` for typed configuration, with support for `.env` files and fallbacks.

**System Design Choices:**
- **Containerization**: Designed to be container-compatible, running within Docker and Docker Compose environments.
- **Database**: Utilizes PostgreSQL as the primary database.
- **Code Quality**: Emphasizes TDD, 100% test coverage, and strict linting with `ruff` and static analysis with `mypy`.

## External Dependencies
- **Frameworks**: Django, Django REST Framework
- **Database**: PostgreSQL (via `psycopg2-binary`, `dj-database-url`)
- **Configuration**: `pydantic-settings`
- **Containerization**: Docker, Docker Compose
- **Dependency Management**: Poetry
- **Static Analysis/Linting**: `mypy`, `ruff`
- **Image Processing**: Pillow (for thumbnail compression)