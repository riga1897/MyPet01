# MyPet01

## Overview
MyPet01 — семейный блог на Django 5.1+ для публикации фото/видео контента о домашних животных. Проект ориентирован на постепенное развитие, масштабируемость, максимальную безопасность и 100% покрытие тестами.

**Веб-домены**: `www.mine-craft.su`, `site.mine-craft.su`, `mine-craft.su`
**VPN SNI**: `vpn.mine-craft.su` (preprod), `mainsrv01.mine-craft.su` (prod)
**Preprod VPS**: 217.147.15.220 | **Prod VPS**: 91.204.75.25

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

## Project Structure
```
MyPet01/
├── mypet_project/              # Django project settings
│   ├── settings.py             # Main Django settings (reads from config.py)
│   ├── config.py               # pydantic-settings (Settings class, reads .env)
│   ├── urls.py                 # Root URL conf (blog, users, admin, sitemap, protected_media)
│   └── wsgi.py                 # WSGI entry point
│
├── blog/                       # Main content app
│   ├── models.py               # Category, TagGroup, Tag, ContentType, Content, ContentQuerySet
│   ├── views/                  # Views package (split by responsibility)
│   │   ├── __init__.py         # Re-exports all views for backward compatibility
│   │   ├── public.py           # HomeView (cached), SearchView (FTS + fuzzy + layout conversion)
│   │   ├── moderator.py        # CRUD: ContentCreateView, ContentUpdateView, ContentDeleteView,
│   │   │                       #   ContentListView, TagCreateView, TagUpdateView, TagDeleteView,
│   │   │                       #   TagGroupCreateView, TagGroupUpdateView, TagGroupDeleteView,
│   │   │                       #   TagListView, TagReorderView
│   │   ├── api.py              # AJAX: AvailableFilesView, AvailableThumbnailsView,
│   │   │                       #   CheckCategoryCodeView, CheckContentTypeCodeView,
│   │   │                       #   CheckContentTypeFolderView, CheckUniqueFieldView
│   │   │                       #   (BaseAvailableView — abstract base class)
│   │   ├── files.py            # FileListView, FileUploadView, FileDeleteView, ProtectedMediaView
│   │   └── mixins.py           # FileHandlingMixin, ModeratorContextMixin,
│   │                           #   ModeratorFilterContextMixin, get_filter_context(),
│   │                           #   get_available_thumbnails(), validate_existing_file(),
│   │                           #   validate_existing_thumbnail(), validate_media_path()
│   ├── services.py             # Video/image processing: generate_thumbnail_from_video(),
│   │                           #   generate_thumbnail_from_image(), generate_hashed_filename(),
│   │                           #   generate_unique_thumbnail_name()
│   ├── cache.py                # Server-side caching: get/set_cached_content_ids(),
│   │                           #   get/set_cached_filter_context(), invalidate_*()
│   ├── signals.py              # Cache invalidation via Django signals (post_save, post_delete, m2m_changed)
│   ├── sitemaps.py             # ContentSitemap, StaticViewSitemap
│   ├── urls.py                 # Blog URL patterns (app_name='blog')
│   ├── admin.py                # Django admin configuration
│   ├── apps.py                 # AppConfig with signal import
│   ├── forms.py                # Content/tag forms
│   ├── fixtures/
│   │   ├── initial_structure.json  # Base categories/content types
│   │   ├── demo_content.json       # Demo content data
│   │   └── demo_media/            # Demo media files
│   ├── management/commands/
│   │   ├── setup_demo_content.py       # Load demo content
│   │   ├── setup_initial_structure.py  # Load initial structure
│   │   └── create_superuser_if_not_exists.py
│   ├── templates/blog/
│   │   ├── index.html                          # Home page
│   │   ├── search_results.html                 # Search results
│   │   ├── content_list.html                   # Moderator content list
│   │   ├── content_form.html                   # Create/edit content
│   │   ├── content_confirm_delete.html         # Delete confirmation
│   │   ├── tag_list.html                       # Tag management
│   │   ├── tag_form.html / taggroup_form.html  # Tag/group forms
│   │   ├── tag_confirm_delete.html / taggroup_confirm_delete.html
│   │   ├── file_list.html                      # File manager
│   │   └── partials/                           # Template partials
│   │       ├── _header.html                    # Navigation + burger menu
│   │       ├── _hero.html                      # Hero section
│   │       ├── _footer.html                    # Footer
│   │       ├── _about.html                     # About section
│   │       ├── _video_card.html                # Content card component
│   │       ├── _category_filter_dropdown.html  # Category filter UI
│   │       ├── _category_filter_js.html        # Filter JS logic
│   │       ├── _category_select_dropdown.html  # Category select in forms
│   │       ├── _content_type_select_dropdown.html
│   │       └── _tag_filter_dropdowns.html      # Tag filter dropdowns
│   └── tests/                  # Blog app tests (100% coverage)
│
├── core/                       # Shared utilities and base models
│   ├── models.py               # BaseModel (abstract: created_at, updated_at)
│   ├── middleware.py            # BrowserCacheMiddleware (Cache-Control headers)
│   ├── security.py             # HoneypotMiddleware, SecurityLoggingMiddleware,
│   │                           #   rate_limit_login/upload/api decorators,
│   │                           #   sanitize_html(), sanitize_text(), get_client_ip(),
│   │                           #   log_security_event(), honeypot_check()
│   ├── mixins.py               # ModeratorRequiredMixin, AdminRequiredMixin
│   ├── context_processors.py   # user_permissions() -> is_moderator in all templates
│   ├── utils/
│   │   ├── path.py             # safe_media_path() — path traversal protection
│   │   └── text.py             # convert_layout() (QWERTY<->ЙЦУКЕН), transliterate(),
│   │                           #   is_latin(), is_cyrillic()
│   └── tests/
│
├── users/                      # Authentication and role management
│   ├── models.py               # is_moderator(), can_manage_moderators(),
│   │                           #   get_or_create_moderators_group()
│   │                           #   MODERATORS_GROUP_NAME = 'Модераторы'
│   ├── views.py                # RateLimitedLoginView, ModeratorListView,
│   │                           #   add_moderator(), remove_moderator()
│   ├── urls.py                 # (app_name='users') login, logout, moderator mgmt
│   ├── templates/users/
│   │   ├── login.html
│   │   └── moderator_list.html
│   └── tests/
│
├── templates/
│   └── base.html               # Base template (theme toggle, FOUC prevention, CSP-aware)
│
├── static/css/
│   └── tailwind-input.css      # Tailwind v4 input (built via CLI in Docker)
│
├── tests/                      # E2E, integration, load tests
│   ├── e2e/                    # Playwright E2E tests
│   ├── integration/
│   └── load/                   # Locust load tests
│
├── docs/                       # Project documentation (Russian)
│   ├── CI_CD.md                # CI/CD pipeline (GitHub Actions)
│   ├── DEPLOY_CHECKLIST.md     # VPS deployment checklist
│   ├── DEPLOYMENT_STRATEGY.md  # Dev->Staging->PreProd->Prod strategy (Gitflow)
│   ├── DEPUSER_SETUP.md        # depuser setup for automated deployment
│   ├── DOCKER_SETUP.md         # Docker local development guide
│   ├── GITHUB_SECRETS.md       # GitHub Secrets configuration
│   ├── HAPROXY_SECURITY.md     # HAProxy security hardening documentation
│   ├── QUICK_START_TESTING.md  # Testing quick start guide
│   ├── S3_MIGRATION_PLAN.md    # S3 storage migration plan
│   └── STAGING_TESTING.md      # Staging testing guide
│
├── scripts/
│   ├── setup_vps.sh            # VPS initial setup (users, firewall, sysctl, ICMP block)
│   ├── update-geoip.sh         # Download RIPE NCC data -> haproxy/geoip/ru_networks.lst
│   ├── cron-geoip-update.sh    # Weekly cron wrapper for GeoIP update
│   ├── init-letsencrypt.sh     # Let's Encrypt initial certificate setup
│   ├── generate-preprod-env.sh # Generate preprod .env file
│   └── generate-production-env.sh  # Generate production .env file
│
├── haproxy/
│   ├── haproxy.cfg             # HAProxy config (SNI routing, GeoIP, rate limiting, scanner blocking)
│   ├── geoip/                  # GeoIP data (ru_networks.lst, generated by scripts)
│   └── blacklist/
│       └── blocked_ips.lst     # Manually curated IP blacklist (scanners, crawlers)
│
├── nginx/
│   ├── nginx.conf              # Nginx config (SSL, gzip, static/media serving, proxy)
│   ├── docker-entrypoint.sh    # Self-signed cert bootstrap -> Let's Encrypt
│   └── ssl-dhparams.pem        # DH parameters for SSL
│
├── Dockerfile                  # Multi-stage: node (Tailwind build) -> python (app)
├── docker-compose.yml          # Local dev: web(5000), db(postgres), redis
├── docker-compose.prod.yml     # Production: haproxy, nginx, web, db, redis, certbot, softether
├── docker-entrypoint.sh        # App entrypoint: migrate, collectstatic, gzip, fixtures, gunicorn
├── pyproject.toml              # Poetry config, ruff, mypy, pytest settings
├── manage.py
└── .env.example                # Environment variable template
```

## System Architecture

### Django Apps
| App | Purpose | Key Classes |
|-----|---------|-------------|
| `blog` | Content management, search, file serving | Content, ContentType, Category, TagGroup, Tag |
| `core` | Base models, middleware, security, utilities | BaseModel, BrowserCacheMiddleware, HoneypotMiddleware |
| `users` | Auth, roles, moderator management | RateLimitedLoginView, ModeratorListView |

### Models Hierarchy (OOP)
```
BaseModel (abstract: created_at, updated_at)
├── Category (name, code)
├── TagGroup (name, M2M->Category)
├── Tag (name, FK->TagGroup, order)
├── ContentType (name, code, upload_folder; is_video, is_photo)
└── Content (title, description, FK->ContentType, video_file, thumbnail,
             M2M->Category, M2M->Tag)
    └── ContentQuerySet.with_relations() — optimized prefetch
```

### URL Structure
| Pattern | View | Access |
|---------|------|--------|
| `/` | HomeView | Public |
| `/search/?q=` | SearchView | Public (rate limited 30/min) |
| `/content/` | ContentListView | Moderator |
| `/content/create/` | ContentCreateView | Moderator |
| `/content/<pk>/edit/` | ContentUpdateView | Moderator |
| `/content/<pk>/delete/` | ContentDeleteView | Moderator |
| `/tags/` | TagListView | Moderator |
| `/tags/group/create/` | TagGroupCreateView | Moderator |
| `/tags/group/<pk>/edit/` | TagGroupUpdateView | Moderator |
| `/tags/group/<pk>/delete/` | TagGroupDeleteView | Moderator |
| `/tags/create/` | TagCreateView | Moderator |
| `/tags/<pk>/edit/` | TagUpdateView | Moderator |
| `/tags/<pk>/delete/` | TagDeleteView | Moderator |
| `/tags/reorder/` | TagReorderView | Moderator |
| `/files/` | FileListView | Moderator |
| `/api/files/upload/` | FileUploadView | Moderator (rate limited 20/min) |
| `/api/files/delete/` | FileDeleteView | Moderator |
| `/api/available-files/` | AvailableFilesView | Moderator |
| `/api/available-thumbnails/` | AvailableThumbnailsView | Moderator |
| `/api/check-contenttype-code/` | CheckContentTypeCodeView | Moderator |
| `/api/check-contenttype-folder/` | CheckContentTypeFolderView | Moderator |
| `/api/check-category-code/` | CheckCategoryCodeView | Moderator |
| `/media/<path>` | ProtectedMediaView | Authenticated |
| `/users/login/` | RateLimitedLoginView | Public (rate limited 5/min) |
| `/users/logout/` | LogoutView | Authenticated |
| `/users/moderators/` | ModeratorListView | Admin |
| `/users/moderators/add/<id>/` | add_moderator | Admin (POST) |
| `/users/moderators/remove/<id>/` | remove_moderator | Admin (POST) |
| `/admin/` | Django Admin | Superuser |
| `/sitemap.xml` | Sitemap | Public |

### Role-Based Access
| Role | Permissions |
|------|------------|
| **Guest** (anonymous) | View public content, search, theme toggle |
| **User** (authenticated) | + Access protected media files |
| **Moderator** (group 'Модераторы') | + CRUD content, tags, tag groups, file management |
| **Admin** (superuser) | + Manage moderators, Django admin access |

### Full-Text Search (SearchView)
1. **Primary**: PostgreSQL `SearchVector` (title weight='A', description weight='B') + `SearchRank`
2. **Fallback 1**: Keyboard layout conversion (QWERTY<->ЙЦУКЕН via `core/utils/text.py`)
3. **Fallback 2**: Trigram similarity (`TrigramSimilarity`, threshold=0.3)
4. Rate limited: 30 requests/min per IP

### Caching Architecture
- **Server-side** (`blog/cache.py`):
  - `CONTENT_LIST_CACHE_KEY` — cached content IDs for home page (TTL=300s)
  - `FILTER_CONTEXT_CACHE_KEY` — cached tag groups, categories, content types (TTL=300s)
- **Invalidation** (`blog/signals.py`): Django signals on Content, Tag, TagGroup, Category (post_save, post_delete, m2m_changed)
- **Cache backends** (configurable via `CACHE_BACKEND` env): `locmem` (default), `db`, `redis`, `memcached`
- **Browser caching** (`BrowserCacheMiddleware`): Configurable via `BROWSER_CACHE_ENABLED` / `BROWSER_CACHE_MAX_AGE`

### File Processing (`blog/services.py`)
- **Video thumbnails**: ffmpeg extracts first frame -> Pillow resize (800x600) -> JPEG quality=85
  - Max video size: 500 MB, ffmpeg timeout: 60s
- **Image thumbnails**: Pillow resize + RGBA->RGB conversion -> JPEG
- **MD5 hashing**: `generate_hashed_filename()` creates unique filenames from content hash
- **Thumbnail naming**: `generate_unique_thumbnail_name()` uses timestamp MD5

### Security Layers

#### Django Application Security (`core/security.py`)
- **Rate limiting** (django-ratelimit): Login (5/min), uploads (20/min), API (60/min), search (30/min)
- **Honeypot** (HoneypotMiddleware): Hidden field `website_url` in all POST forms
- **Input sanitization**: `bleach` — `sanitize_html()` (allows safe HTML tags), `sanitize_text()` (strips all HTML)
- **Security logging** (SecurityLoggingMiddleware): Detects `../`, `<script`, `javascript:`, etc. -> `logs/security.log`
- **Path traversal protection**: `safe_media_path()` in `core/utils/path.py`
- **CSP** (django-csp): Strict policy — self-only + Google Fonts + inline styles/scripts
- **X-Frame-Options**: `DENY` by default in `config.py` (override via `.env: X_FRAME_OPTIONS=ALLOWALL`)
  - **CRITICAL**: Дефолт MUST быть 'DENY'. НЕ менять в коде! Для Replit iframe: `.env` -> `X_FRAME_OPTIONS=ALLOWALL`
- **HTTPS/HSTS**: Automatic via `USE_HTTPS=True` (SSL redirect, HSTS 31536000s / 1 year, secure cookies)
- **Protected media**: `ProtectedMediaView` serves files via `FileResponse` only to authenticated users

#### HAProxy Security Hardening (production)
- **GeoIP filtering**: Russian IP-only for web (ft_ssl, ft_http) and Minecraft (ft_minecraft, ft_minecraft_rcon)
  - VPN SNI bypass: `vpn.mine-craft.su`, `mainsrv01.mine-craft.su` — unrestricted geo
  - ACME challenges: always unrestricted
  - Data source: RIPE NCC delegated stats (no MaxMind needed)
  - Script: `scripts/update-geoip.sh` -> `haproxy/geoip/ru_networks.lst`
- **Rate limiting** (stick-tables):
  - SSL: 30 conn/10s, 20 concurrent max
  - HTTP: 50 req/10s
  - Minecraft: 10 conn/10s
  - RCON: 5 conn/10s
- **Scanner path blocking**: 27 ACL paths (`/wp-admin`, `/.env`, `/.git`, `/phpmyadmin`, etc.) -> 403 + gpc0 ban
- **BADREQ auto-ban**: >5 HTTP errors/10s -> gpc0 increment -> 403 for 30min (stick-table expire)
- **Manual IP blacklist**: `haproxy/blacklist/blocked_ips.lst` — checked FIRST in all 4 frontends (ft_ssl, ft_http, ft_minecraft, ft_minecraft_rcon), ACME exempt in ft_http
  - Reload: `docker compose -f docker-compose.prod.yml kill -s HUP haproxy`
- **ICMP blocking**: `net.ipv4.icmp_echo_ignore_all = 1` (configured by `scripts/setup_vps.sh`)
- **Stats**: `127.0.0.1:8404/stats` (local access only)

#### Nginx Security (`nginx/nginx.conf`)
- SSL/TLS: TLSv1.2/1.3, ECDHE ciphers, OCSP stapling, session cache
- Headers: HSTS (63072000s), X-Frame-Options DENY, X-Content-Type-Options nosniff, X-XSS-Protection
- Gzip: level 6, `gzip_static on` for pre-compressed files
- Static: `/static/` -> 30d cache, immutable
- Media: `/media/` -> 7d cache, public
- Note: Nginx HSTS (63072000s) differs from Django HSTS (31536000s) — Nginx value takes precedence in production as it adds the header at the reverse proxy level

### Configuration System (`mypet_project/config.py`)
- **Engine**: `pydantic-settings` `BaseSettings` class reading `.env`
- **Key settings**:
  - `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS` (comma-separated)
  - `DATABASE_URL` or individual `POSTGRES_*` vars
  - `CSRF_TRUSTED_ORIGINS` (comma-separated, default: `*.replit.dev,*.repl.co,*.pike.replit.dev`)
  - `USE_HTTPS` -> auto-enables SSL_REDIRECT, HSTS (31536000s), secure cookies
  - `X_FRAME_OPTIONS` (default: DENY)
  - `CACHE_BACKEND` (locmem/db/redis/memcached), `CACHE_LOCATION`, `CACHE_TIMEOUT`
  - `BROWSER_CACHE_ENABLED`, `BROWSER_CACHE_MAX_AGE`

### Middleware Stack (order matters)
1. `GZipMiddleware` — compress responses
2. `SecurityMiddleware` — HTTPS redirect, HSTS
3. `CSPMiddleware` — Content Security Policy headers
4. `SessionMiddleware` — session handling
5. `CommonMiddleware` — URL normalization
6. `CsrfViewMiddleware` — CSRF protection
7. `AuthenticationMiddleware` — user authentication
8. `MessageMiddleware` — flash messages
9. `XFrameOptionsMiddleware` — clickjacking protection
10. `BrowserCacheMiddleware` — Cache-Control headers
11. `HoneypotMiddleware` — bot detection
12. `SecurityLoggingMiddleware` — suspicious request logging

### Docker Architecture

#### Local Development (`docker-compose.yml`)
- `web`: Django dev server on port 5000, mounts source code
- `db`: PostgreSQL 15 Alpine
- `redis`: Redis 7 Alpine

#### Production (`docker-compose.prod.yml`)
- `haproxy`: SNI routing (ports 443, 80, 25565, 25575), network_mode: host
- `nginx`: SSL termination (8443), static/media serving, ACME challenges
- `web`: Gunicorn (8000), 4 workers, 2 threads
- `db`: PostgreSQL 15 Alpine
- `redis`: Redis 7 Alpine (AOF persistence)
- `certbot`: Auto-renewal every 12h
- `softether`: VPN server (ports 992, 5555, 500, 4500, 1701, 1194)

#### Multi-stage Dockerfile
1. **Stage 1** (node:20-slim): Build Tailwind CSS v4 via `@tailwindcss/cli` -> `static/css/tailwind.css`
2. **Stage 2** (python:3.12-slim): Install Poetry deps, copy app + built CSS, setup entrypoint

#### Entrypoint (`docker-entrypoint.sh`)
1. `migrate --noinput`
2. `collectstatic --noinput`
3. Pre-compress static files (`gzip -9 -k`)
4. Load fixtures (`initial_structure.json`)
5. Optionally load demo content (`LOAD_DEMO_DATA=true`)
6. Create superuser if not exists
7. Start Gunicorn

## Operational Notes

### First Deploy Checklist
1. Run `bash scripts/update-geoip.sh` (generates GeoIP data for HAProxy)
2. Run `bash scripts/setup_vps.sh` (VPS hardening: firewall, sysctl, ICMP block)
3. Configure `.env` via `scripts/generate-production-env.sh`
4. `docker compose -f docker-compose.prod.yml up -d`
5. Run `scripts/init-letsencrypt.sh` (obtain Let's Encrypt certs)

### Weekly Maintenance
- GeoIP auto-update: cron `0 3 * * 0 /path/to/scripts/cron-geoip-update.sh`
- Certbot auto-renewal: built into docker-compose (every 12h)

### SoftEther VPN
- Config: `softether_data:/mnt/vpn_server.config`
- Logs: `softether_logs:/usr/local/bin/server_log`
- Backup: `docker cp <container>:/mnt/vpn_server.config ./backup`

### HAProxy Blacklist Management
- File: `haproxy/blacklist/blocked_ips.lst` (one IP per line, `#` comments)
- Apply: `docker compose -f docker-compose.prod.yml kill -s HUP haproxy`

### Minecraft Backend
- Primary: `newnout01:25565` (via VPN, health check every 5s)
- Backup: `mainserv01.netcraze.pro:25565` (external, failover)
- RCON: same scheme on port 25575

## External Dependencies
| Category | Packages |
|----------|----------|
| Frameworks | Django 5.1+, Django REST Framework |
| Database | PostgreSQL 15 (`psycopg2-binary`, `dj-database-url`) |
| Configuration | `pydantic-settings` |
| Security | `django-csp`, `django-ratelimit`, `bleach` |
| Image/Video | Pillow, ffmpeg (system) |
| Containerization | Docker, Docker Compose |
| Dependencies | Poetry |
| Linting | `ruff` (line-length=119), `mypy` (strict, django-stubs, drf-stubs) |
| Testing | pytest, pytest-django, pytest-cov, pytest-playwright, locust |
| Frontend | Tailwind CSS v4 (CLI build) |
| Web Server | Gunicorn, Nginx |
| Load Balancer | HAProxy 2.9 |
| VPN | SoftEther VPN |
| SSL | Let's Encrypt (Certbot) |
| CI/CD | GitHub Actions |

## Recent Changes
- **2026-02-12**: HAProxy security hardening — GeoIP filtering, rate limiting, scanner path blocking, BADREQ auto-ban, manual IP blacklist, ICMP blocking. Created `docs/HAPROXY_SECURITY.md`.
- **2026-02-12**: Fixed `x_frame_options` default to 'DENY' in `config.py` with protective comment.
- **2026-02-12**: Created `haproxy/blacklist/blocked_ips.lst` (20 IPs), integrated in all 4 frontends.
- **2026-02-12**: Full replit.md expansion with comprehensive project documentation.
