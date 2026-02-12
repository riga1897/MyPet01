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
- **Full-Text Search**: PostgreSQL Full-Text Search implementation with SearchVector for title and description fields. SearchView with pagination at `/search/`. Search form integrated in header (desktop + mobile).
- **Content Management**: Features a robust content model (`Content`) supporting various content types (`ContentType`), multiple categories (ManyToMany), and a dynamic tag system (`TagGroup`, `Tag`). Content types dictate upload folders, and both tags and categories support multi-select with "Select All" functionality in forms.
- **User Management**: Includes a `users` app with authentication, role-based access control (Guests, Moderators, Admins), and a moderator management interface.
- **Security**: Configurable security settings for development (HTTP) and production (HTTPS with HSTS, secure cookies, XSS protection, content sniffing prevention, clickjacking prevention).
  - **Rate Limiting**: Login form limited to 5 attempts/minute per IP via django-ratelimit.
  - **Honeypot Protection**: Hidden field in login form to detect bots (middleware blocks filled honeypot).
  - **Input Sanitization**: Description fields sanitized via bleach library (strips dangerous HTML/JS).
  - **Security Logging**: All suspicious requests and auth events logged to `logs/security.log` and console.
  - **CSP (Content Security Policy)**: Strict policy limiting script/style sources.
- **Caching**: Implements both server-side caching (local memory, DB, Redis, or Memcached) and browser caching with configurable `Cache-Control` headers. Server-side cache invalidation is automated via Django signals on content changes.
- **File Management**: Handles image and video uploads, with thumbnails automatically compressed and unique MD5 hash names. Supports selecting existing files and path traversal protection. Media files are served via Django's `FileResponse` through `ProtectedMediaView` (requires authentication via `@login_required`).
- **Configuration**: Environment variables are managed via `pydantic-settings` for typed configuration, with support for `.env` files and fallbacks.

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
- **Database**: PostgreSQL (via `psycopg2-binary`, `dj-database-url`)
- **Configuration**: `pydantic-settings`
- **Containerization**: Docker, Docker Compose
- **Dependency Management**: Poetry
- **Static Analysis/Linting**: `mypy`, `ruff`
- **Image Processing**: Pillow (for thumbnail compression)
- **Testing**: pytest, pytest-django, pytest-cov, locust

## Roadmap

### Функционал блога
- [ ] **Комментарии** — гости/пользователи оставляют комментарии к контенту
- [ ] **Лайки/избранное** — пользователи сохраняют понравившийся контент
- [ ] **Счётчик просмотров** — статистика популярности контента
- [ ] **Галереи/альбомы** — группировка фото в альбомы
- [ ] **RSS-лента** — подписка на обновления блога
- [ ] **Расписание публикаций** — отложенный постинг (scheduled posts)
- [ ] **Уведомления** — email при новом контенте в избранной категории
- [ ] **Шаринг в соцсети** — кнопки поделиться

### Инфраструктура
- [ ] **Тестирование на VPS** — задеплоить и проверить всё в боевых условиях
- [ ] **Мониторинг** — добавить Prometheus + Grafana для отслеживания состояния сервисов
- [ ] **Бэкапы** — скрипт автобэкапа PostgreSQL и медиафайлов
- [x] **CI/CD** — автодеплой при пуше в репозиторий (GitHub Actions)

## CI/CD Pipeline

Проект использует **единый** GitHub Actions workflow для автоматизации:

**Workflow:** `.github/workflows/ci-cd.yml` — обслуживает оба окружения (preprod + production).

**Логика ветвления:**
- `release/*` → Препрод: Test → Lint → Build → Deploy (preprod VPS)
- `main` → Прод: Build → Deploy (prod VPS) — тесты не нужны, т.к. прошли на препроде

**Jobs:**
1. **Test** — pytest + PostgreSQL + Redis (coverage 100%) — только `release/*`
2. **Lint** — ruff, mypy — только `release/*`
3. **Build** — Docker → GitHub Container Registry — оба окружения
4. **Deploy** — единый job с определением окружения по ветке (VPS infra, SSL, миграции)

**Определение окружения:**
- Ветка `release/*` → секреты `PREPROD_*`, тег `preprod-latest`, демо-данные, draft PR
- Ветка `main` → секреты `SSH_*`, тег `latest`, `STAGING=0`

**GitHub Variables:**
- `LOAD_DEMO_DATA` — загрузка демо-данных (только препрод)
- `CERTBOT_STAGING` — тестовый SSL (только препрод, в проде захардкожен `STAGING=0`)
- `CREATE_PR_ON_PREDEPLOY` — создание draft PR

**SSL Bootstrap:**
- Nginx стартует с временным self-signed сертификатом (симлинки из `/etc/nginx/ssl-temp/`)
- CI/CD автоматически проверяет наличие реального сертификата и запускает `init-letsencrypt.sh` при необходимости
- Проверка: `[ ! -L fullchain.pem ] && grep -qv 'O=Temporary'` (не симлинк + не временный)

**docker-entrypoint.sh:**
- Миграции → collectstatic → initial_structure → setup_demo_content (если `LOAD_DEMO_DATA=true`) → createsuperuser → Gunicorn

**Gitflow:**
```
feature/* → develop → release/* → main
                          ↓           ↓
                     preprod VPS   prod VPS
```

**Документация:**
- [docs/CI_CD.md](docs/CI_CD.md)
- [docs/GITHUB_SECRETS.md](docs/GITHUB_SECRETS.md)
- [docs/DEPLOY_CHECKLIST.md](docs/DEPLOY_CHECKLIST.md)