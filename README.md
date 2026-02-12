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
- Полнотекстовый поиск на базе PostgreSQL SearchVector
- Защищённая отдача медиафайлов (FileResponse + @login_required)
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
│   ├── views.py
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
| [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) | Деплой на VPS (CI/CD, Docker, ручной) |
| [docs/DEPLOYMENT_STRATEGY.md](docs/DEPLOYMENT_STRATEGY.md) | Стратегия развертывания и CI/CD pipeline |
| [docs/VPS_AND_SECRETS.md](docs/VPS_AND_SECRETS.md) | Настройка VPS, depuser, GitHub Secrets |
| [docs/LOCAL_DEVELOPMENT.md](docs/LOCAL_DEVELOPMENT.md) | Локальная разработка с Docker |
| [docs/TESTING.md](docs/TESTING.md) | Тестирование, линтеры, покрытие |
| [docs/planning/S3_MIGRATION_PLAN.md](docs/planning/S3_MIGRATION_PLAN.md) | План миграции на S3 |

---

## Безопасность

- **CSP (Content Security Policy)** — строгая политика ограничения источников скриптов и стилей (django-csp)
- **Rate Limiting** — ограничение попыток входа: 5 запросов/минуту на IP (django-ratelimit)
- **Honeypot** — скрытое поле в форме авторизации для обнаружения ботов
- **Санитизация ввода** — очистка HTML/JS в пользовательском вводе (bleach)
- **Защита медиафайлов** — доступ к файлам только для авторизованных пользователей (FileResponse + @login_required)
- **HTTPS** — автоматическое получение SSL-сертификатов через Let's Encrypt
- **HSTS** — Strict Transport Security в продакшене
- **Защита от XSS** — X-XSS-Protection, Content-Type nosniff
- **Защита от Clickjacking** — X-Frame-Options: DENY
- **Логирование** — все подозрительные запросы и события аутентификации записываются в `logs/security.log`

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
- [x] CI/CD — автодеплой при пуше в репозиторий (GitHub Actions)

---

## Лицензия

MIT

---

## Автор

**riga1897** — [riga1897@yandex.ru](mailto:riga1897@yandex.ru)
