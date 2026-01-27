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
- **Caching**: Implements both server-side caching (local memory, DB, Redis, or Memcached) and browser caching with configurable `Cache-Control` headers. Server-side cache invalidation is automated via Django signals on content changes.
- **File Management**: Handles image and video uploads, with thumbnails automatically compressed and unique MD5 hash names. Supports selecting existing files and path traversal protection.
- **Configuration**: Environment variables are managed via `pydantic-settings` for typed configuration, with support for `.env` files and fallbacks.

**System Design Choices:**
- **Containerization**: Designed to be container-compatible, running within Docker and Docker Compose environments.
- **Database**: Utilizes PostgreSQL as the primary database.
- **Code Quality**: Emphasizes TDD, 100% test coverage, and strict linting with `ruff` and static analysis with `mypy`.

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

Проект использует GitHub Actions для автоматизации:

**Workflow:** `.github/workflows/ci-cd.yml`

**Jobs:**
1. **Test** — pytest + PostgreSQL + Redis (coverage 80%+)
2. **Lint** — ruff, mypy
3. **Build** — Docker → GitHub Container Registry
4. **Deploy Pre-Prod** — release/* → preprod VPS
5. **Deploy Production** — main → prod VPS

**Gitflow:**
```
feature/* → develop → release/* → main
                          ↓           ↓
                     preprod VPS   prod VPS
```

**Документация:**
- [docs/CI_CD.md](docs/CI_CD.md)
- [docs/GITHUB_SECRETS.md](docs/GITHUB_SECRETS.md)