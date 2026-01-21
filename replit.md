# MyPet01

## Overview
A personal pet website for the family. This is a Django project using a minimalist backend stack for gradual development.

## Tech Stack
- **Python**: 3.12
- **Framework**: Django
- **API**: Django REST Framework
- **Database**: PostgreSQL (psycopg2-binary, dj-database-url)
- **Configuration**: pydantic-settings (typed environment variables)
- **Containerization**: Docker & Docker Compose (minimal setup)
- **Dependency Management**: Poetry 2.0+

## Project Architecture
- **Base Models**: All models must inherit from an abstract `BaseModel` that provides common fields like `created_at` and `updated_at`.
- **Containerization**: The project is designed to be container-compatible. In Replit, it runs as a single "container" with integrated services.

## User Preferences
- **Coding Workflow (TDD + QA)**:
  1. Write tests first.
  2. Implement code.
  3. Verify with tests.
  4. Run linters (Ruff, Mypy).
- **Test Coverage**: 100% code coverage is mandatory. All new code must be fully tested before merging.
- **Database Choice**: PostgreSQL is the preferred database for its robust Django support and features.
- **Tools**: Use `mypy` for static analysis and `ruff` for linting.
- **Design Principles**:
  - Strict adherence to **OOP** (Object-Oriented Programming).
  - Maximum use of **inheritance from abstract classes** to minimize code duplication and ensure consistent behavior across models.

## Current Setup Progress
- [x] Environment configured with Python 3.12
- [x] Dependencies minimized in `pyproject.toml`
- [x] Docker configuration files simplified
- [x] Basic Django structure initialized
- [x] PostgreSQL database integrated
- [x] Created `blog` app with Post, Video, and Comment models
- [x] Configured Django Admin for blog management

## How to Run (Replit)
Click the "Run" button to start the Django development server.

## Future Deployment (Ubuntu 24.04)
1. Install Docker and Docker Compose on Ubuntu.
2. Clone the repository.
3. Run `docker-compose up --build`.

## Configuration
Environment variables are managed via `pydantic-settings` in `mypet_project/config.py`:
- Reads from `.env` file automatically
- Fully typed with no `# type: ignore` comments
- Comma-separated values (ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS) handled via properties
- DATABASE_URL fallback: auto-constructs from POSTGRES_* variables if not set

## Recent Changes
- 2026-01-21: Migrated from django-environ to pydantic-settings for fully typed configuration.
- 2026-01-21: Integrated PostgreSQL, created `blog` app, configured Admin, and documented the TDD workflow in `replit.md`.
