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
  3. Verify with tests (`poetry run pytest`).
  4. **ОБЯЗАТЕЛЬНО** проверить линтеры (`poetry run ruff check .` и `poetry run mypy .`).
- **Test Coverage**: 100% code coverage is mandatory. All new code must be fully tested before merging.
- **Linters**: Проверка линтерами обязательна перед завершением любой задачи. Код не считается готовым без прохождения Ruff и Mypy.
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
- [x] Created `blog` app with Content model (video/photo support)
- [x] Configured Django Admin for blog management
- [x] Frontend templates created based on Figma design "Гармония Души"
- [x] Content model with content_type (video/photo), category, thumbnail, duration fields
- [x] Created `users` app with authentication and role-based permissions
- [x] Implemented moderator group with management interface
- [x] Added content editing on site (CRUD for moderators only)
- [x] Mobile responsive menu (burger menu)
- [x] Category filters (Все/Йога/Масла)
- [x] Search by title and description
- [x] Dark/Light theme toggle with localStorage persistence
- [x] SEO optimization (meta tags, Open Graph)
- [x] Favicon for the website
- [x] Caching system (server-side + browser cache control)
- [x] Dynamic tag system (TagGroup → Tag → Content ManyToMany)
- [x] Tag management interface for moderators (CRUD for groups and tags)
- [x] Tag filters on home page (dropdown per group)
- [x] Tag columns in content list table (dynamic per group)
- [x] Category model (separate table instead of TextChoices)
- [x] Tag groups can be linked to specific categories or apply to all

## Data Models
```
BaseModel (abstract)
  └── created_at, updated_at

Category (inherits BaseModel)
  ├── name: CharField (unique)
  ├── slug: SlugField (auto-generated)
  └── code: CharField (unique, e.g. 'yoga', 'oils')

TagGroup (inherits BaseModel)
  ├── name: CharField (unique)
  ├── slug: SlugField (auto-generated)
  └── categories: ManyToMany → Category (empty = applies to all)

Tag (inherits BaseModel)
  ├── name: CharField
  ├── slug: SlugField (auto-generated)
  └── group: ForeignKey → TagGroup

Content (inherits BaseModel)
  ├── title: CharField
  ├── description: TextField
  ├── content_type: video | photo
  ├── category: ForeignKey → Category (nullable)
  ├── thumbnail: ImageField
  ├── video_file: FileField
  ├── duration: CharField (MM:SS)
  └── tags: ManyToMany → Tag
```

## Frontend Structure
- **Base template**: `templates/base.html` (Tailwind CSS CDN + custom CSS variables)
- **Blog templates**: `blog/templates/blog/`
  - `index.html` — главная страница
  - `partials/_header.html` — шапка с навигацией
  - `partials/_hero.html` — приветственный блок
  - `partials/_video_card.html` — карточка видео
  - `partials/_about.html` — секция "О блоге"
  - `partials/_footer.html` — подвал
  - `content_list.html` — список контента для модераторов
  - `content_form.html` — форма создания/редактирования контента
  - `content_confirm_delete.html` — подтверждение удаления
- **Users templates**: `users/templates/users/`
  - `login.html` — страница входа
  - `moderator_list.html` — управление модераторами

## Role-Based Access
| Действие | Гости | Модераторы | Админы |
|----------|-------|------------|--------|
| Просмотр контента | ✅ | ✅ | ✅ |
| Редактирование контента | ❌ | ✅ | ✅ |
| Управление модераторами | ❌ | ✅ | ✅ |

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

## Caching Configuration

### Server-side Cache (Django)
Configured via environment variables:
```env
CACHE_BACKEND=locmem    # Options: locmem, db, redis, memcached
CACHE_LOCATION=mypet-cache
CACHE_TIMEOUT=300       # 5 minutes default
```

Backend options:
- `locmem` — Local memory (development, single process)
- `db` — PostgreSQL table (production, multi-worker safe)
- `redis` — Redis server (high performance)
- `memcached` — Memcached server

For `db` backend, create cache table:
```bash
python manage.py createcachetable cache_table
```

### Browser Cache (HTTP headers)
```env
BROWSER_CACHE_ENABLED=False  # True for production
BROWSER_CACHE_MAX_AGE=86400  # 1 day for static files
```

When enabled, adds `Cache-Control` headers:
- Static/media files: `public, max-age=<BROWSER_CACHE_MAX_AGE>`
- Dynamic pages: `no-cache, no-store, must-revalidate`

### Cache Invalidation
Content cache is automatically invalidated via Django signals when:
- Content is created
- Content is updated
- Content is deleted

## Future Improvements (Backlog)
- [ ] Счётчик просмотров контента
- [ ] Подписка на email-рассылку
- [ ] Пагинация (когда контента станет много)
- [ ] Комментарии к видео/фото

## Recent Changes
- 2026-01-22: Added GZipMiddleware for HTTP compression, nginx production config with gzip/static/media serving, Docker setup with gunicorn (4 workers), collectstatic in build.
- 2026-01-22: Added thumbnail auto-compression on upload (Pillow: max 800x600, JPEG quality 85%), lazy loading for images, browser cache enabled.
- 2026-01-22: Group filter on tag management page now uses dropdown menu with checkboxes (consistent with tag filters). Added "Выбрать все" checkbox, swapped buttons order (+Тег first), equal button widths.
- 2026-01-22: Added drag-and-drop tag ordering on tag management page. Tags can be reordered horizontally, saved via AJAX.
- 2026-01-22: Added `order` field to Tag model for custom sorting. Tags now sorted by order within groups.
- 2026-01-22: Simplified TagGroup model - removed applies_to_all field, empty categories now means "applies to all".
- 2026-01-22: Created blog/utils.py with reusable filtering functions (filter_content, filter_tag_groups, get_visible_tag_groups).
- 2026-01-22: Added "Select All" checkbox to TagGroup form with JavaScript synchronization.
- 2026-01-22: Added category filtering and search to content_list and tag_list pages.
- 2026-01-22: Added Category model (replaces TextChoices), tag groups can be linked to specific categories or apply to all.
- 2026-01-22: Added dynamic tag system with TagGroup and Tag models, moderator management interface, home page filters, and content list columns.
- 2026-01-22: Added caching system (locmem/db/redis/memcached backends), browser cache middleware, and favicon.
- 2026-01-22: Made "About blog" section tiles clickable for category filtering.
- 2026-01-21: Added mobile menu, category filters, search, dark theme, and SEO meta tags.
- 2026-01-21: Added modal windows for viewing video/photo content.
- 2026-01-21: Added users app with login/logout, moderator group management, and role-based content editing.
- 2026-01-21: Created content CRUD interface on site (accessible only to moderators and admins).
- 2026-01-21: Restructured tests into app-specific directories with 100% coverage (76 tests).
- 2026-01-21: Refactored Video → Content model with content_type (video/photo), removed Post and Comment models.
- 2026-01-21: Added production security settings (SSL redirect, HSTS, secure cookies) with env toggles.
- 2026-01-21: Implemented frontend based on Figma design "Гармония Души" — yoga & essential oils blog.
- 2026-01-21: Migrated from django-environ to pydantic-settings for fully typed configuration.
- 2026-01-21: Integrated PostgreSQL, created `blog` app, configured Admin, and documented the TDD workflow in `replit.md`.
