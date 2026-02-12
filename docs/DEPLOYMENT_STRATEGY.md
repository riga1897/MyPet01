# Стратегия развертывания: Development -> Staging -> Pre-Production -> Production (Gitflow)

Этот документ описывает четырехступенчатую стратегию развертывания проекта MyPet01 (блог о домашних животных) от локальной разработки до production deployment с использованием Gitflow branching strategy.

Стек проекта: Python 3.12, Django 5.1+, Django REST Framework, PostgreSQL 15, Redis 7, Poetry (управление зависимостями), Pillow (миниатюры), bleach (санитизация), django-ratelimit, django-csp.

Примеры реализации: Development (Replit), Staging (Windows/Mac/Linux + Docker Desktop), Pre-Production (release/* -> VPS), Production (main -> VPS via GitHub Actions).

---

## Обзор стратегии

```
+-------------------+   +-------------------+   +-------------------+   +-------------------+
|  1. DEVELOPMENT   |   |  2. STAGING       |   | 3. PRE-PRODUCTION |   |  4. PRODUCTION    |
|  Разработка       |-->|  Локальный Docker |-->|  Препрод VPS      |-->|  Финальный VPS    |
|                   |   |                   |   |                   |   |                   |
|  Replit Cloud IDE |   |  Docker Desktop   |   |  release/* branch |   |  main branch      |
|  БЕЗ Docker       |   |  + live reload    |   |  preprod-latest   |   |  latest tag       |
|  Быстрая итерация |   |  Локальная сборка |   |  Полный CI/CD     |   |  Финальный релиз  |
|  feature/develop  |   |  develop ветка    |   |  + auto PR        |   |  Ubuntu VPS +     |
|  Nix окружение    |   |  Windows/Mac/     |   |  Ubuntu VPS +     |   |  GitHub Actions   |
|                   |   |  Linux + Docker   |   |  GitHub Actions   |   |                   |
+-------------------+   +-------------------+   +-------------------+   +-------------------+
```

---

## 1. Development (Среда разработки)

### Назначение

- Быстрая итеративная разработка
- Прототипирование новых функций
- Написание и отладка кода
- Запуск тестов

### Технологии

- Окружение: Replit Cloud IDE с Nix (без Docker)
- БД: PostgreSQL на localhost (встроенный в Replit)
- Кеш: Redis на localhost
- Сервер: Django runserver на порту 5000
- Зависимости: Poetry

### Конфигурация

```env
POSTGRES_HOST=localhost
REDIS_URL=redis://localhost:6379/0
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Запуск

```bash
poetry run python manage.py runserver 0.0.0.0:5000 --noreload
```

### Особенности

- Nix используется для изоляции вместо Docker
- PostgreSQL и Redis доступны автоматически через Replit
- Docker не поддерживается в Replit (нет nested virtualization)
- Порт 5000 для доступа через Replit webview

---

## 2. Staging (Локальная тестовая среда)

### Назначение

- Промежуточное тестирование перед push в удаленный репозиторий
- Проверка работы кода в Docker окружении
- Валидация Docker-сборки и миграций БД

### Технологии

- Окружение: Docker Desktop (Windows/Mac/Linux)
- Изоляция: Docker контейнеры
- БД: PostgreSQL 15 в Docker (service name: db)
- Кеш: Redis 7 в Docker (service name: redis)
- Сервер: Django runserver с live reload

### Конфигурация

Файл: docker-compose.yml

```yaml
services:
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:5000
    ports:
      - "5000:5000"
    volumes:
      - .:/app
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: mypet

  redis:
    image: redis:7-alpine
```

```env
POSTGRES_HOST=db
REDIS_URL=redis://redis:6379/0
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Запуск

```bash
docker compose up -d
docker compose logs -f
```

### Особенности

- Live reload через volume mounting (.:/app) -- изменения в коде применяются автоматически
- Docker хосты (db, redis) вместо localhost
- Локальная сборка образа (build: .)
- DEBUG=True для удобной отладки
- Порт 5000

---

## 3. Pre-Production (Препродакшн окружение)

### Назначение

- Полная репетиция production deployment перед релизом
- Тестирование всего CI/CD pipeline на изолированном сервере
- Валидация deployment процесса без риска для production
- Финальное тестирование release веток перед merge в main
- Загрузка демонстрационных данных (LOAD_DEMO_DATA=true)

### Технологии

- Окружение: Docker на отдельном VPS (Ubuntu)
- VPS: 217.147.15.220
- Домены: site.mine-craft.su (веб), vpn.mine-craft.su (VPN)
- БД: PostgreSQL 15 в Docker
- Кеш: Redis 7 в Docker
- Reverse Proxy: HAProxy (SNI-маршрутизация) -> Nginx -> Gunicorn
- VPN: SoftEther VPN Server
- SSL: Let's Encrypt (staging-сертификаты, CERTBOT_STAGING=1)
- Сервер: Gunicorn (порт 8000, internal)
- Docker tag: preprod-latest
- Триггер: push в release/* branches

### Архитектура сервисов (docker-compose.prod.yml)

```
Client -> HAProxy:80/443 (SNI routing)
              |
              +-- site.mine-craft.su --> Nginx:8080 --> Gunicorn:8000 (web)
              |
              +-- vpn.mine-craft.su  --> SoftEther:4443 (VPN)
```

Сервисы: haproxy, nginx, web, db, redis, certbot, softether.

### CI/CD Pipeline (.github/workflows/ci-cd.yml)

Триггер: push в release/* branches.

```
1. test     -- pytest + 100% coverage (PostgreSQL 15, Redis 7 в CI)
2. lint     -- ruff, mypy (параллельно)
3. build    -- Docker образ с тегом preprod-latest -> GHCR
4. deploy   -- SSH на VPS, pull образа, docker compose up
5. health   -- curl проверка через Nginx
6. ssl      -- init-letsencrypt.sh (staging-сертификаты)
7. setup    -- migrate, collectstatic, loaddata, setup_demo_content, createsuperuser
8. pr       -- автоматическое создание draft PR: release/* -> main
```

### Конфигурация окружения

Файл .env автоматически генерируется на VPS через scripts/generate-preprod-env.sh.

Конфиги окружения копируются CI/CD pipeline:

```
haproxy/haproxy-preprod.cfg --> haproxy/haproxy.cfg
nginx/nginx-preprod.conf   --> nginx/nginx.conf
```

Генерик-файлы (haproxy.cfg, nginx.conf) не хранятся в git (добавлены в .gitignore).

### GitHub Secrets

```
PREPROD_SSH_KEY       -- приватный SSH ключ
PREPROD_SSH_USER      -- SSH пользователь
PREPROD_SERVER_IP     -- IP адрес препрод сервера
PREPROD_DEPLOY_DIR    -- директория деплоя на VPS
```

### Автонастройка VPS

При первом деплое CI/CD автоматически устанавливает:

- Docker CE и Docker Compose v2
- UFW (файрвол) с разрешенными портами (22, 80, 443, 992, 5555, 500/udp, 4500/udp, 1701/udp, 1194/udp)
- fail2ban (защита от brute-force)
- Создание deploy-директории

Первоначальная настройка VPS: scripts/setup-github.sh -> scripts/setup_vps.sh (создание пользователей depuser, useradmin, настройка SSH ключей).

### Особенности

- Изоляция от production -- отдельный VPS, БД, secrets
- Полный CI/CD тест -- все этапы как в production
- preprod-latest tag -- отдельный Docker образ
- DEBUG=False -- production-подобные настройки
- Демонстрационные данные загружаются автоматически
- Автоматическое создание draft PR после успешного деплоя
- SSL staging-сертификаты (CERTBOT_STAGING=1)

---

## 4. Production (Финальное окружение)

### Назначение

- Финальное окружение для реальных пользователей
- Высокая доступность и стабильность
- Автоматический deployment через CI/CD

### Технологии

- Окружение: Docker на VPS (Ubuntu)
- VPS: 91.204.75.25
- Домены: www.mine-craft.su (веб), mainsrv01.mine-craft.su (VPN)
- БД: PostgreSQL 15 в Docker
- Кеш: Redis 7 в Docker
- Reverse Proxy: HAProxy (SNI-маршрутизация) -> Nginx -> Gunicorn
- VPN: SoftEther VPN Server
- SSL: Let's Encrypt (реальные сертификаты, STAGING=0 hardcoded)
- Сервер: Gunicorn (4 workers, 2 threads, порт 8000, internal)
- Docker tag: latest
- Триггер: push в main branch

### CI/CD Pipeline (.github/workflows/ci.yml)

Триггер: push в main branch.

```
1. build    -- Docker образ с тегом latest -> GHCR
2. deploy   -- SSH на VPS, pull образа, docker compose up
3. health   -- curl проверка через Nginx
4. ssl      -- init-letsencrypt.sh (реальные сертификаты, STAGING=0)
5. setup    -- migrate, collectstatic, loaddata, createsuperuser
```

### Конфигурация окружения

Файл .env автоматически генерируется на VPS через scripts/generate-production-env.sh.

Конфиги окружения копируются CI/CD pipeline:

```
haproxy/haproxy-prod.cfg --> haproxy/haproxy.cfg
nginx/nginx-prod.conf   --> nginx/nginx.conf
```

### GitHub Secrets

```
SSH_KEY       -- приватный SSH ключ
SSH_USER      -- SSH пользователь
SERVER_IP     -- IP адрес production сервера
DEPLOY_DIR    -- директория деплоя на VPS
```

### docker-entrypoint.sh

Последовательность действий при запуске контейнера web:

```
1. migrate            -- применение миграций БД
2. collectstatic      -- сбор статических файлов
3. loaddata           -- загрузка initial_structure.json
4. setup_demo_content -- загрузка демо-данных (только если LOAD_DEMO_DATA=true)
5. createsuperuser    -- создание суперпользователя (если не существует)
6. exec gunicorn      -- запуск Gunicorn
```

### Особенности

- Nginx как reverse proxy для статики (80/443) и проксирования на Gunicorn
- Gunicorn -- production-ready WSGI сервер (4 workers, internal порт 8000)
- DEBUG=False
- Образ из GHCR: ghcr.io/${GITHUB_REPOSITORY}:latest
- Named volumes: static_volume, media_volume, postgres_data, redis_data
- Health checks -- автоматическая проверка работоспособности
- Auto-restart: restart: unless-stopped
- Zero-configuration VPS -- автоматическая установка Docker, UFW, fail2ban при первом деплое
- SSL: всегда реальные сертификаты Let's Encrypt (STAGING=0)

---

## Сравнение окружений

| Параметр | Development | Staging | Pre-Production | Production |
|----------|-------------|---------|----------------|------------|
| Docker | Нет (Nix) | Да (Docker Desktop) | Да (Docker на VPS) | Да (Docker на VPS) |
| Хосты БД/Redis | localhost | db, redis | db, redis | db, redis |
| Live reload | Да | Да (volume mount) | Нет | Нет |
| DEBUG | True | True | False | False |
| Сервер | runserver | runserver | HAProxy->Nginx->Gunicorn | HAProxy->Nginx->Gunicorn |
| Порт | 5000 | 5000 | 80/443 (HAProxy)->8080 (Nginx)->8000 (Gunicorn) | 80/443 (HAProxy)->8080 (Nginx)->8000 (Gunicorn) |
| Docker tag | N/A | local build | preprod-latest | latest |
| Сборка | N/A | Локальная (build: .) | GHCR pull | GHCR pull |
| CI/CD | Нет | Нет | Да (release/*) | Да (main) |
| .env | Ручное создание | Ручное создание | generate-preprod-env.sh | generate-production-env.sh |
| Назначение | Разработка и отладка | Локальный Docker тест | Препрод тест CI/CD | Финальный релиз |

---

## Gitflow Workflow

```
feature/* --> develop --> release/* --> main
                              |            |
                              v            v
                         preprod VPS   prod VPS
                       (ci-cd.yml)    (ci.yml)
```

### Полный цикл релиза

```
1. feature/* --> develop        (разработка новых функций)
2. develop --> release/v1.0     (создание release-ветки)
3. push release/v1.0            (триггер CI/CD: test -> lint -> build -> deploy на preprod)
4. Тестирование на препроде     (site.mine-craft.su)
5. Автоматический draft PR      (release/v1.0 -> main)
6. Merge PR в main              (ручное подтверждение после тестирования)
7. push main                    (триггер CI/CD: build -> deploy на production)
8. Production работает          (www.mine-craft.su)
9. release/v1.0 --> develop     (backmerge изменений)
```

---

## Pipeline Flow

### Pre-Production Pipeline (release/* -> VPS)

```
Push в release/*
    |
    v
[test] pytest + coverage 100%
    |
    v
[lint] ruff + mypy (параллельно)
    |
    v
[build-and-push] Docker образ -> GHCR (preprod-latest)
    |
    v
[deploy-preprod]
    |-- Setup VPS (Docker, UFW, fail2ban) -- идемпотентно
    |-- cp haproxy-preprod.cfg -> haproxy.cfg
    |-- cp nginx-preprod.conf -> nginx.conf
    |-- scp файлов на VPS
    |-- generate-preprod-env.sh (генерация .env)
    |-- docker compose pull + up -d
    |-- Health check (curl localhost:8080)
    |-- init-letsencrypt.sh (CERTBOT_STAGING=1)
    |-- migrate + collectstatic + loaddata + setup_demo_content + createsuperuser
    |-- Создание draft PR: release/* -> main
    v
Препрод доступен: site.mine-craft.su
```

### Production Pipeline (main -> VPS)

```
Push в main (merge из release/*)
    |
    v
[build-and-push] Docker образ -> GHCR (latest)
    |
    v
[deploy-production]
    |-- Setup VPS (Docker, UFW, fail2ban) -- идемпотентно
    |-- cp haproxy-prod.cfg -> haproxy.cfg
    |-- cp nginx-prod.conf -> nginx.conf
    |-- scp файлов на VPS
    |-- generate-production-env.sh (генерация .env)
    |-- docker compose pull + up -d
    |-- Health check (curl localhost:8080)
    |-- init-letsencrypt.sh (STAGING=0, реальные сертификаты)
    |-- migrate + collectstatic + loaddata + createsuperuser
    v
Production доступен: www.mine-craft.su
```

---

## Конфигурации по окружениям

### HAProxy

- haproxy/haproxy-preprod.cfg -- конфигурация для препрода (site.mine-craft.su, vpn.mine-craft.su)
- haproxy/haproxy-prod.cfg -- конфигурация для production (www.mine-craft.su, mainsrv01.mine-craft.su)
- haproxy/haproxy.cfg -- генерик-файл, копируется CI/CD pipeline, не хранится в git

HAProxy выполняет SNI-маршрутизацию:
- Веб-домен -> Nginx (порт 8080/8443)
- VPN-домен -> SoftEther (порт 4443)

### Nginx

- nginx/nginx-preprod.conf -- конфигурация для препрода
- nginx/nginx-prod.conf -- конфигурация для production
- nginx/nginx.conf -- генерик-файл, копируется CI/CD pipeline, не хранится в git

### SSL

- Pre-Production: staging-сертификаты Let's Encrypt (CERTBOT_STAGING=1)
- Production: реальные сертификаты Let's Encrypt (STAGING=0, hardcoded)
- Автоматическое получение через scripts/init-letsencrypt.sh
- Автоматическое обновление через контейнер certbot

---

## Zero-Configuration VPS

CI/CD pipeline автоматически настраивает чистый VPS при первом деплое.

Что устанавливается автоматически:

1. Docker CE -- если не установлен, добавляется официальный репозиторий
2. Docker Compose v2 -- plugin для docker compose
3. UFW -- файрвол с разрешенными портами
4. fail2ban -- защита от brute-force атак
5. Deploy-директория -- с правильными правами доступа
6. Unprivileged port binding -- для HAProxy в режиме network_mode: host

Идемпотентность:
- Скрипт проверяет наличие зависимостей перед установкой
- Повторные запуски не дублируют установку
- Первый деплой: 2-3 минуты (установка Docker и зависимостей)
- Последующие деплои: 30-60 секунд (только pull + restart)

Требования к VPS:
- Ubuntu 20.04/22.04
- SSH доступ с публичным ключом
- sudo права для пользователя
- Минимум 1GB RAM, 10GB диск
