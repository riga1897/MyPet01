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
- [x] Frontend templates created based on Figma design "Гармония Души"
- [x] Video model extended with category, thumbnail, duration fields

## Frontend Structure
- **Base template**: `templates/base.html` (Tailwind CSS CDN + custom CSS variables)
- **Blog templates**: `blog/templates/blog/`
  - `index.html` — главная страница
  - `partials/_header.html` — шапка с навигацией
  - `partials/_hero.html` — приветственный блок
  - `partials/_video_card.html` — карточка видео
  - `partials/_about.html` — секция "О блоге"
  - `partials/_footer.html` — подвал

## Design Theme (CSS Variables)
- Primary: `#7AA9BA` (голубой)
- Secondary: `#A8B89C` (зелёный)
- Background: `#F9FAFA`
- Muted: `#E8EDE7`

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

## Security Configuration

### Development (current)
All security features are disabled to allow HTTP development:
```env
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
SECURE_HSTS_SECONDS=0
```

### Production (when HTTPS is ready)
Enable these settings in `.env` when you have SSL certificate:
```env
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
X_FRAME_OPTIONS=DENY
```

### Security Headers (always enabled)
- `SECURE_BROWSER_XSS_FILTER=True` — XSS protection
- `SECURE_CONTENT_TYPE_NOSNIFF=True` — prevent MIME-type sniffing
- `X_FRAME_OPTIONS=DENY` — prevent clickjacking

### SSL Certificate Options
1. **Replit Deployment**: HTTPS is automatic
2. **Ubuntu + Docker**: Use Let's Encrypt with Caddy (recommended) or Nginx + Certbot

## Recent Changes
- 2026-01-21: Added production security settings (SSL redirect, HSTS, secure cookies) with env toggles.
- 2026-01-21: Implemented frontend based on Figma design "Гармония Души" — yoga & essential oils blog.
- 2026-01-21: Extended Video model with title, category (yoga/oils), thumbnail, duration fields.
- 2026-01-21: Created HomeView with ListView for displaying videos on the main page.
- 2026-01-21: Migrated from django-environ to pydantic-settings for fully typed configuration.
- 2026-01-21: Integrated PostgreSQL, created `blog` app, configured Admin, and documented the TDD workflow in `replit.md`.
