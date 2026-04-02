# MyPet01

Веб-приложение для публикации и просмотра фото- и видеоконтента.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-5.1+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Coverage](https://img.shields.io/badge/Coverage-100%25-brightgreen)
![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue)
![Code style](https://img.shields.io/badge/code%20style-ruff-000000)

---

## Возможности

- Управление контентом с типизацией, категориями и системой тегов (TagGroup / Tag)
- Полнотекстовый поиск на базе PostgreSQL SearchVector с конвертацией раскладки (QWERTY↔ЙЦУКЕН) и нечётким поиском (Trigram)
- Защищённая отдача медиафайлов через ProtectedMediaView (только для авторизованных пользователей)
- Адаптивный дизайн с переключением светлой/тёмной темы (localStorage)
- Мобильное меню (бургер)
- Автоматическое сжатие миниатюр (Pillow, MD5-хеш в именах файлов)
- Серверное кеширование с инвалидацией по сигналам Django
- Ролевая модель доступа: Гость, Модератор, Администратор
- Загрузка демо-данных через фикстуры и management-команду
- Sitemap для поисковых систем

---

## Технологический стек

| Категория | Технологии |
|---|---|
| Язык | Python 3.12 |
| Фреймворк | Django 5.1+, Django REST Framework |
| База данных | PostgreSQL 15 |
| Кеширование | Redis 7 |
| Менеджер зависимостей | Poetry |
| Контейнеризация | Docker, Docker Compose |
| Веб-сервер | Gunicorn + Nginx |
| Балансировщик | HAProxy (SNI-маршрутизация) |
| SSL | Let's Encrypt (Certbot) |
| VPN | SoftEther VPN |
| CI/CD | GitHub Actions |
| Линтеры | ruff (line-length=119), mypy (strict, django-stubs, drf-stubs) |
| Тестирование | pytest, pytest-django, pytest-cov, pytest-playwright, locust |
| Обработка изображений | Pillow |
| Безопасность | django-csp, django-ratelimit, bleach, honeypot |
| Конфигурация | pydantic-settings, dj-database-url |

---

## Структура проекта

```
MyPet01/
├── mypet_project/          # Настройки Django-проекта
│   ├── settings.py
│   ├── config.py           # pydantic-settings конфигурация
│   ├── urls.py
│   └── wsgi.py
├── blog/                   # Основное приложение (контент)
│   ├── models.py           # Content, ContentType, Category, TagGroup, Tag
│   ├── views/              # Пакет views (public, moderator, api, files, mixins)
│   ├── services.py
│   ├── cache.py            # Серверное кеширование
│   ├── signals.py          # Инвалидация кеша
│   ├── sitemaps.py
│   ├── fixtures/           # Демо-данные и начальная структура
│   ├── management/commands/ # setup_demo_content, setup_initial_structure
│   ├── templates/blog/
│   └── tests/
├── core/                   # Общие утилиты и базовые модели
│   ├── models.py           # BaseModel (created_at, updated_at)
│   ├── middleware.py
│   ├── security.py
│   ├── mixins.py
│   ├── context_processors.py
│   └── tests/
├── users/                  # Аутентификация и управление ролями
│   ├── models.py
│   ├── views.py
│   ├── signals.py
│   └── tests/
├── templates/              # Базовые шаблоны
│   └── base.html
├── static/css/             # Стили
├── tests/                  # E2E, интеграционные и нагрузочные тесты
│   ├── e2e/
│   ├── integration/
│   └── load/
├── docs/                   # Документация проекта
│   ├── DEPLOYMENT_GUIDE.md # Деплой на VPS (CI/CD, Docker, ручной)
│   ├── DEPLOYMENT_STRATEGY.md # Стратегия и CI/CD pipeline
│   ├── VPS_AND_SECRETS.md  # Настройка VPS и GitHub Secrets
│   ├── LOCAL_DEVELOPMENT.md # Локальная разработка с Docker
│   ├── TESTING.md          # Тестирование
│   └── planning/           # Планы развития
├── deploy/                 # Скрипты деплоя
├── scripts/                # Автоматизация настройки VPS
├── haproxy/                # Конфигурации HAProxy (prod, preprod)
├── nginx/                  # Конфигурации Nginx (prod, preprod)
├── Dockerfile
├── docker-compose.yml      # Локальная разработка (Docker Desktop)
├── docker-compose.prod.yml # Продакшен (VPS)
├── pyproject.toml
└── manage.py
```

---

## Быстрый старт

### Локальная разработка (Poetry)

```bash
git clone https://github.com/riga1897/MyPet01.git
cd MyPet01

poetry install

cp .env.example .env
# Отредактируйте .env — укажите параметры подключения к PostgreSQL

poetry run python manage.py migrate
poetry run python manage.py loaddata blog/fixtures/initial_structure.json
poetry run python manage.py setup_demo_content  # опционально
poetry run python manage.py createsuperuser

poetry run python manage.py runserver 0.0.0.0:5000
```

### Разработка в Docker

```bash
git clone https://github.com/riga1897/MyPet01.git
cd MyPet01

cp .env.example .env

docker-compose up --build
```

Приложение будет доступно по адресу `http://localhost:5000`.

Docker Compose поднимает три сервиса: веб-приложение (Django), PostgreSQL 15 и Redis 7.

---

## Конфигурация

Все параметры задаются через переменные окружения или файл `.env`. Типизированная конфигурация реализована на базе `pydantic-settings`.

| Переменная | Описание | Пример | Обязательная |
|---|---|---|---|
| `DATABASE_URL` | URL подключения к PostgreSQL | `postgresql://user:pass@localhost:5432/mypet` | Да* |
| `POSTGRES_USER` | Имя пользователя PostgreSQL | `postgres` | Да* |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL | `postgres` | Да* |
| `POSTGRES_HOST` | Хост PostgreSQL | `localhost` | Нет |
| `POSTGRES_PORT` | Порт PostgreSQL | `5432` | Нет |
| `POSTGRES_DB` | Имя базы данных | `mypet` | Да* |
| `SECRET_KEY` | Секретный ключ Django | `django-insecure-...` | Да |
| `DEBUG` | Режим отладки | `True` | Нет |
| `ALLOWED_HOSTS` | Разрешённые хосты (через запятую) | `*` | Нет |
| `CSRF_TRUSTED_ORIGINS` | Доверенные источники CSRF | `https://*.example.com` | Нет |
| `USE_HTTPS` | Включение HTTPS-настроек | `True` | Нет |
| `CACHE_BACKEND` | Бэкенд кеширования | `locmem`, `redis`, `db` | Нет |
| `CACHE_LOCATION` | Адрес кеш-сервера | `redis://redis:6379/0` | Нет |
| `CACHE_TIMEOUT` | Время жизни кеша (секунды) | `300` | Нет |
| `BROWSER_CACHE_ENABLED` | Кеширование в браузере | `False` | Нет |
| `BROWSER_CACHE_MAX_AGE` | max-age для Cache-Control | `86400` | Нет |
| `X_FRAME_OPTIONS` | Защита от clickjacking | `DENY` | Нет |
| `LOAD_DEMO_DATA` | Загрузка демо-данных при старте | `true` | Нет |
| `LANGUAGE_CODE` | Язык интерфейса | `ru` | Нет |
| `TIME_ZONE` | Часовой пояс | `UTC` | Нет |

*Обязательна либо `DATABASE_URL`, либо набор `POSTGRES_USER` + `POSTGRES_PASSWORD` + `POSTGRES_DB`.

---

## Тестирование

Покрытие тестами 100% является обязательным требованием проекта.

### Запуск всех тестов

```bash
poetry run pytest
```

### Запуск тестов конкретного модуля

```bash
poetry run pytest blog/tests/test_views.py -v
```

### E2E-тесты (Playwright)

```bash
poetry run pytest tests/e2e/ -v
```

### Нагрузочное тестирование (Locust)

```bash
# Веб-интерфейс (http://localhost:8089)
poetry run locust -f tests/load/locustfile.py

# Headless-режим
poetry run locust -f tests/load/locustfile.py --headless -u 100 -r 10 -t 1m --host http://localhost:5000
```

### Линтеры

```bash
# Ruff
poetry run ruff check .
poetry run ruff check . --fix

# Mypy
poetry run mypy .
```

---

## Деплой

Проект разворачивается на VPS с использованием Docker Compose. Архитектура продакшена:

```
HAProxy (SNI-маршрутизация, порт 443)
├── Веб-домен  -> Nginx -> Gunicorn (Django)
└── VPN-домен  -> SoftEther VPN
```

**Среды:**

| Среда | Ветка | VPS | Домены |
|---|---|---|---|
| Pre-production | `release/*` | 217.147.15.220 | site.mine-craft.su, vpn.mine-craft.su |
| Production | `main` | 91.204.75.25 | www.mine-craft.su, mainsrv01.mine-craft.su |

**Gitflow:**

```
feature/* -> develop -> release/* -> main
                           |           |
                      preprod VPS   prod VPS
```

Подробная документация: [docs/DEPLOYMENT_STRATEGY.md](docs/DEPLOYMENT_STRATEGY.md)

---

## Документация

| Документ | Описание |
|---|---|
| [docs/DEPLOYMENT_STRATEGY.md](docs/DEPLOYMENT_STRATEGY.md) | Стратегия деплоя |
| [docs/CI_CD.md](docs/CI_CD.md) | CI/CD пайплайн |
| [docs/GITHUB_SECRETS.md](docs/GITHUB_SECRETS.md) | GitHub Secrets и Variables |
| [docs/DEPLOY.md](docs/DEPLOY.md) | Деплой на VPS (Docker / ручная установка) |
| [docs/DEPLOY_CHECKLIST.md](docs/DEPLOY_CHECKLIST.md) | Чек-лист деплоя |
| [docs/DOCKER_SETUP.md](docs/DOCKER_SETUP.md) | Настройка Docker |
| [docs/DEPUSER_SETUP.md](docs/DEPUSER_SETUP.md) | Настройка deploy-пользователя |
| [docs/QUICK_START_TESTING.md](docs/QUICK_START_TESTING.md) | Быстрый старт тестирования |
| [docs/STAGING_TESTING.md](docs/STAGING_TESTING.md) | Тестирование на staging |
| [docs/S3_MIGRATION_PLAN.md](docs/S3_MIGRATION_PLAN.md) | План миграции на S3 |
| [docs/HAPROXY_SECURITY.md](docs/HAPROXY_SECURITY.md) | Безопасность HAProxy |
| [docs/PROJECT_REFERENCE.md](docs/PROJECT_REFERENCE.md) | Полная техническая документация проекта |

---

## Безопасность

### Уровень приложения (Django)

- **CSP (Content Security Policy)** — строгая политика ограничения источников скриптов и стилей (django-csp)
- **Rate Limiting** — ограничение попыток входа: 5/мин, загрузки: 20/мин, API: 60/мин, поиск: 30/мин (django-ratelimit)
- **Honeypot** — скрытое поле `website_url` во всех POST-формах для обнаружения ботов (HoneypotMiddleware)
- **Санитизация ввода** — очистка HTML/JS в пользовательском вводе (bleach)
- **Защита медиафайлов** — доступ к файлам только для авторизованных пользователей (ProtectedMediaView + FileResponse)
- **Защита от path traversal** — централизованная валидация `safe_media_path()` в `core/utils/path.py`
- **HTTPS** — автоматическое получение SSL-сертификатов через Let's Encrypt
- **HSTS** — Strict Transport Security в продакшене (Django: 31536000s, Nginx: 63072000s)
- **Защита от XSS** — X-XSS-Protection, Content-Type nosniff
- **Защита от Clickjacking** — X-Frame-Options: DENY (по умолчанию, переопределяется через `.env`)
- **Логирование безопасности** — SecurityLoggingMiddleware обнаруживает подозрительные паттерны (`../`, `<script`, `javascript:`) → `logs/security.log`

### Уровень инфраструктуры (HAProxy)

- **GeoIP-фильтрация** — доступ только для российских IP (RIPE NCC данные, без MaxMind). VPN и ACME без ограничений
- **Rate Limiting** — stick-table: SSL 30 conn/10s, HTTP 50 req/10s, Minecraft 10 conn/10s, RCON 5 conn/10s
- **Блокировка сканеров** — 27 ACL-путей (`/wp-admin`, `/.env`, `/.git`, `/phpmyadmin` и др.) → 403 + автобан
- **BADREQ автобан** — >5 HTTP-ошибок/10s → бан на 30 минут через gpc0
- **Ручной IP-блеклист** — `haproxy/blacklist/blocked_ips.lst` — проверяется ПЕРВЫМ во всех фронтендах
- **Блокировка ICMP** — сервер не отвечает на ping (`net.ipv4.icmp_echo_ignore_all = 1`)

Подробная документация: [docs/HAPROXY_SECURITY.md](docs/HAPROXY_SECURITY.md)

---

## Дорожная карта

### Функционал блога

- [ ] Комментарии — гости/пользователи оставляют комментарии к контенту
- [ ] Лайки/избранное — пользователи сохраняют понравившийся контент
- [ ] Счётчик просмотров — статистика популярности контента
- [ ] Галереи/альбомы — группировка фото в альбомы
- [ ] RSS-лента — подписка на обновления блога
- [ ] Расписание публикаций — отложенный постинг
- [ ] Уведомления — email при новом контенте в избранной категории
- [ ] Шаринг в соцсети — кнопки «Поделиться»

### Инфраструктура

- [ ] Тестирование на VPS — деплой и проверка в боевых условиях
- [ ] Мониторинг — Prometheus + Grafana
- [ ] Бэкапы — автоматическое резервное копирование PostgreSQL и медиафайлов
- [ ] Управление через Ansible
- [ ] Безопасность (fail2ban)
- [x] CI/CD — автодеплой при пуше в репозиторий (GitHub Actions)

---

## Лицензия

MIT

---

## Автор

**riga1897** — [riga1897@yandex.ru](mailto:riga1897@yandex.ru)
