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
- **Views Architecture**: `blog/views/` is a package split into modules: `public.py` (HomeView, SearchView), `moderator.py` (CRUD views), `api.py` (AJAX endpoints with `BaseAvailableView` base class), `files.py` (file management, ProtectedMediaView), `mixins.py` (shared mixins and helpers). Re-exported via `__init__.py` for backward compatibility.
- **Path Security**: Centralized `safe_media_path()` in `core/utils/path.py` validates all media paths against traversal attacks (replaces 6+ inline duplications).
- **User Management**: `users` app provides authentication, role-based access control (Guests, Moderators, Admins), and a moderator management interface.
- **Security**: `X_FRAME_OPTIONS='DENY'` by default (overridable via `.env`). Rate limiting (django-ratelimit), honeypot protection, input sanitization via `bleach`, security logging, and a strict Content Security Policy (CSP).
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

## HAProxy Security Hardening (2026-02-12)
- **GeoIP Filtering**: Russian IP-only access for website (ft_ssl, ft_http) and Minecraft (ft_minecraft, ft_minecraft_rcon). VPN allows traffic from any country — two SNI: `vpn.mine-craft.su` (preprod) and `mainsrv01.mine-craft.su` (prod). ACME challenges also unrestricted.
- **Data Source**: RIPE NCC delegated stats (no MaxMind API key needed). Script: `scripts/update-geoip.sh` generates `haproxy/geoip/ru_networks.lst`.
- **Rate Limiting**: stick-table based — 30 conn/10s and 20 concurrent for SSL; 50 req/10s for HTTP; 10 conn/10s for Minecraft; 5 conn/10s for RCON.
- **Scanner Path Blocking**: ACL list blocks common scanner paths (/SDK/webLanguage, /hudson, /wp-admin, /.env, /.git, etc.) with 403 + auto-ban via gpc0.
- **BADREQ Auto-ban**: IPs with high HTTP error rate (>5 errors/10s, which includes 400 from malformed requests) get gpc0 incremented and are banned (403) for 30 minutes. Scanner path hits also trigger gpc0 ban.
- **Auto-update**: `scripts/cron-geoip-update.sh` — run weekly via cron: `0 3 * * 0 /path/to/scripts/cron-geoip-update.sh`
- **ICMP Blocking**: `net.ipv4.icmp_echo_ignore_all = 1` in `/etc/sysctl.conf` — server does not respond to ping. Configured by `scripts/setup_vps.sh`.
- **Docker**: GeoIP data mounted as `./haproxy/geoip:/usr/local/etc/haproxy/geoip:ro` in haproxy container.
- **SoftEther VPN Volumes**: `softether_data:/mnt` (config `vpn_server.config`), `softether_logs:/usr/local/bin/server_log` (logs). Config backup: `docker cp <container>:/mnt/vpn_server.config ./backup`.
- **First deploy**: Run `bash scripts/update-geoip.sh` before starting HAProxy to generate the GeoIP data.

## External Dependencies
- **Frameworks**: Django, Django REST Framework
- **Database**: PostgreSQL (`psycopg2-binary`, `dj-database-url`)
- **Configuration**: `pydantic-settings`
- **Containerization**: Docker, Docker Compose
- **Dependency Management**: Poetry
- **Static Analysis/Linting**: `mypy`, `ruff`
- **Image Processing**: Pillow
- **Testing**: pytest, pytest-django, pytest-cov, locust