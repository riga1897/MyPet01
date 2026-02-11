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

**Performance Optimizations:**
- **Tailwind CSS**: Local build via Tailwind v4 CLI (`@tailwindcss/cli`) instead of CDN. Input: `static/css/tailwind-input.css` with `@source` directives for template scanning. Output: `static/css/tailwind.css` (~28KB minified vs ~300KB+ CDN). Docker multi-stage build compiles CSS in `node:20-slim` builder stage.
  - **Пайплайн сборки CSS:**
    1. **Docker multi-stage build** (в `Dockerfile`) — при сборке образа первым этапом запускается `node:20-slim`, который компилирует Tailwind CSS. Готовый `tailwind.css` копируется в финальный Python-образ. Node.js нужен только на этапе сборки, в рабочем контейнере его нет.
    2. **CI/CD pipeline** — при пуше кода GitHub Actions собирает Docker-образ, и Tailwind компилируется автоматически внутри `docker build`.
    3. **docker-entrypoint.sh** — при старте контейнера `collectstatic` собирает все статические файлы (включая скомпилированный `tailwind.css`), а затем `gzip -9 -k` сжимает их для nginx.
    4. **Итого цепочка**: `git push → CI/CD → docker build (Tailwind компилируется) → deploy → collectstatic → gzip → nginx отдаёт`
    5. **Локальная разработка**: Команда `npm run build:css` нужна **только** для локальной разработки в Replit, чтобы увидеть изменения в стилях без пересборки Docker-образа.
    6. **Пересборка в проде**: Пересобрать Docker-образ и задеплоить заново (`docker compose -f docker-compose.prod.yml build web && docker compose -f docker-compose.prod.yml up -d web`). Внутри работающего контейнера Node.js нет — изменения идут только через пересборку образа.
- **Gzip Pre-compression**: `docker-entrypoint.sh` runs `gzip -9 -k` on all CSS/JS/SVG/HTML/JSON/XML/TXT files in staticfiles after `collectstatic`. Nginx `gzip_static on` serves pre-compressed files directly.
- **Media Caching**: Nginx `/media/` location with `expires 7d` and `Cache-Control: public`.
- **Browser Caching**: `BrowserCacheMiddleware` with `BROWSER_CACHE_ENABLED` env var (default: False). When enabled, static/media requests get `Cache-Control: public, max-age=86400`.
- **FOUC Prevention**: Inline CSS in `base.html` hides `#mobile-menu` and `#menu-close-icon` with `display: none` before Tailwind loads.
- **Query-level Caching**: `blog/cache.py` caches content IDs and filter context (5min TTL) with signal-based invalidation on content changes.

**System Design Choices:**

- **Containerization**: Designed to be container-compatible, running within Docker and Docker Compose environments. Multi-stage build: Node.js (Tailwind) → Python (app).
- **Database**: Utilizes PostgreSQL as the primary database.
- **Code Quality**: Emphasizes TDD, 100% test coverage, and strict linting with `ruff` and static analysis with `mypy`.
- **SSL/TLS Bootstrap**: Nginx uses a custom entrypoint (`nginx/docker-entrypoint.sh`) that creates a self-signed certificate on first deploy if none exists, allowing Nginx to start immediately. CI/CD then runs `init-letsencrypt.sh --auto` to replace it with a real Let's Encrypt certificate. Precomputed DH params are bundled as `nginx/ssl-dhparams.pem`.
- **VPS Deployment**: Two separate VPS (preprod + production). `setup_vps.sh` creates depuser + SSH key only. CI/CD handles all infrastructure (Docker, UFW, fail2ban) on first deploy.

## Testing

### Unit Tests
```bash
# Запуск всех тестов с покрытием
poetry run pytest

# Запуск конкретного модуля
poetry run pytest blog/tests/test_views.py -v
```

### E2E Tests (16 тестов)
```bash
# Запуск E2E тестов
poetry run pytest tests/e2e/ -v

# Покрытые сценарии:
# - TestHomepageFlow: загрузка главной страницы, hero-секция
# - TestAuthenticationFlow: логин/логаут, защита страниц
# - TestNavigationFlow: admin, sitemap, статические файлы
# - TestSearchFlow: поиск с параметрами, XSS-защита
```

### Load Testing (Locust)
```bash
# Запуск с веб-интерфейсом (http://localhost:8089)
poetry run locust -f tests/load/locustfile.py

# Headless режим (100 пользователей, 10/сек)
poetry run locust -f tests/load/locustfile.py --headless -u 100 -r 10 -t 1m --host http://localhost:5000

# Типы пользователей:
# - GuestUser: просмотр главной, поиск, sitemap
# - AuthenticatedUser: авторизованные пользователи
# - APIUser: тестирование API endpoints
# - MixedUser: реалистичное смешанное поведение
```

### Linters
```bash
# Ruff (linting)
poetry run ruff check .
poetry run ruff check . --fix  # автоисправление

# Mypy (static analysis)
poetry run mypy .
```

## External Dependencies
- **Frameworks**: Django, Django REST Framework
- **Database**: PostgreSQL (`psycopg2-binary`, `dj-database-url`)
- **Configuration**: `pydantic-settings`
- **Containerization**: Docker, Docker Compose
- **Dependency Management**: Poetry
- **Static Analysis/Linting**: `mypy`, `ruff`
- **Image Processing**: Pillow
- **Testing**: pytest, pytest-django, pytest-cov, locust