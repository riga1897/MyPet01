# Стратегия развертывания и CI/CD Pipeline

Четырехступенчатая стратегия развертывания MyPet01 от локальной разработки до production с использованием Gitflow.

> **Настройка VPS и секретов:** [VPS_AND_SECRETS.md](VPS_AND_SECRETS.md)
> **Практический гайд по деплою:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

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

## 1. Development (Replit)

- Replit Cloud IDE с Nix (без Docker)
- PostgreSQL и Redis на localhost (встроенные)
- Django runserver на порту 5000
- Ветки: `feature/*`, `develop`

```bash
poetry run python manage.py runserver 0.0.0.0:5000 --noreload
```

## 2. Staging (Docker Desktop)

- Docker Desktop (Windows/Mac/Linux)
- Live reload через volume mounting
- Ветка: `develop`

Подробнее: [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)

## 3. Pre-Production (VPS)

- Docker на VPS `217.147.15.220`
- Домены: `site.mine-craft.su` (веб), `vpn.mine-craft.su` (VPN)
- Триггер: push в `release/*`
- Docker tag: `preprod-latest`
- SSL: Let's Encrypt (staging-сертификаты, `CERTBOT_STAGING=1`)
- HAProxy → Nginx → Gunicorn

## 4. Production (VPS)

- Docker на VPS `91.204.75.25`
- Домены: `www.mine-craft.su` (веб), `mainsrv01.mine-craft.su` (VPN)
- Триггер: push в `main`
- Docker tag: `latest`
- SSL: Let's Encrypt (реальные сертификаты, `STAGING=0` захардкожен)
- HAProxy → Nginx → Gunicorn (4 workers, 2 threads)

---

## Сравнение окружений

| Параметр | Development | Staging | Pre-Production | Production |
|----------|-------------|---------|----------------|------------|
| Docker | Нет (Nix) | Да (Docker Desktop) | Да (VPS) | Да (VPS) |
| Хосты БД/Redis | localhost | db, redis | db, redis | db, redis |
| Live reload | Да | Да (volume mount) | Нет | Нет |
| DEBUG | True | True | False | False |
| Сервер | runserver | runserver | HAProxy→Nginx→Gunicorn | HAProxy→Nginx→Gunicorn |
| Порт | 5000 | 5000 | 80/443→8080→8000 | 80/443→8080→8000 |
| Docker tag | N/A | local build | preprod-latest | latest |
| CI/CD | Нет | Нет | Да (release/*) | Да (main) |
| .env | Ручное | Ручное | generate-preprod-env.sh | generate-production-env.sh |

---

## Gitflow Workflow

```
feature/* → develop → release/* → main
                          ↓           ↓
                     preprod VPS   prod VPS
                    (ci-cd.yml)   (ci.yml)
```

### Полный цикл релиза

```
1. feature/* → develop        (разработка новых функций)
2. develop → release/v1.0     (создание release-ветки)
3. push release/v1.0          (триггер CI/CD: test → lint → build → deploy на preprod)
4. Тестирование на препроде   (site.mine-craft.su)
5. Автоматический draft PR    (release/v1.0 → main)
6. Merge PR в main            (ручное подтверждение)
7. push main                  (триггер CI/CD: build → deploy на production)
8. Production работает        (www.mine-craft.su)
9. release/v1.0 → develop     (backmerge изменений)
```

---

## CI/CD Pipeline

### Workflow файлы

| Файл | Триггер | Назначение |
|------|---------|------------|
| `.github/workflows/ci-cd.yml` | Push в `release/*` | Тесты + линтеры + сборка + деплой на препрод |
| `.github/workflows/ci.yml` | Push в `main` | Сборка + деплой на production |

> **Примечание:** Production-деплой не включает Test и Lint, так как код в `main` попадает только через проверенный merge из `release/*`.

### Pre-Production Pipeline (release/*)

```
Push в release/*
    │
    ▼
[test] pytest + coverage 100% (PostgreSQL 15, Redis 7)
    │
    ▼
[lint] ruff + mypy (параллельно)
    │
    ▼
[build-and-push] Docker образ → GHCR (preprod-latest)
    │
    ▼
[deploy-preprod]
    ├── Setup VPS (Docker, UFW, fail2ban) — идемпотентно
    ├── cp haproxy-preprod.cfg → haproxy.cfg
    ├── cp nginx-preprod.conf → nginx.conf
    ├── scp файлов на VPS
    ├── generate-preprod-env.sh
    ├── docker compose pull + up -d
    ├── Health check (12 × 5 сек)
    ├── init-letsencrypt.sh (CERTBOT_STAGING)
    ├── migrate + collectstatic + loaddata + setup_demo_content + createsuperuser
    └── Создание draft PR: release/* → main
    ▼
Препрод доступен: site.mine-craft.su
```

### Production Pipeline (main)

```
Push в main
    │
    ▼
[build-and-push] Docker образ → GHCR (latest)
    │
    ▼
[deploy-production]
    ├── Setup VPS (идемпотентно)
    ├── cp haproxy-prod.cfg → haproxy.cfg
    ├── cp nginx-prod.conf → nginx.conf
    ├── scp файлов на VPS
    ├── generate-production-env.sh
    ├── docker compose pull + up -d
    ├── Health check (12 × 5 сек)
    ├── init-letsencrypt.sh (STAGING=0, реальные сертификаты)
    └── migrate + collectstatic + loaddata + createsuperuser
    ▼
Production доступен: www.mine-craft.su
```

> **Production** не загружает демо-данные (`LOAD_DEMO_DATA` отсутствует в `.env`).

### Job: Test

- Сервисы: PostgreSQL 15, Redis 7
- Python 3.12 + Poetry
- Шаги: checkout → setup → cache → install → wait DB → migrate → pytest (coverage 100%)

### Job: Lint

- `ruff check .` и `mypy .` (параллельно)
- Зависимость: после `test`

### Job: Build and Push

- Docker образ → GHCR
- Теги: `{branch}-{SHA}` + `preprod-latest` (release) / `latest` (main)

### Job: Deploy

- SSH подключение → настройка инфраструктуры → копирование файлов → pull образа → запуск стека → health check → SSL → миграции → данные

---

## docker-entrypoint.sh

При запуске контейнера entrypoint автоматически:
1. `migrate` — применение миграций БД
2. `collectstatic` — сбор статических файлов
3. `loaddata initial_structure.json` — начальная структура (категории, типы, теги)
4. `setup_demo_content` — демо-данные (**только если `LOAD_DEMO_DATA=true`**)
5. `createsuperuser` — суперпользователь (если не существует)
6. Запуск Gunicorn

> CI/CD pipeline также выполняет эти шаги как отдельные jobs — двойная гарантия.

---

## Zero-Configuration VPS

Подготовка VPS в два этапа:

**1. `setup_vps.sh` (root, один раз):**
- Создаёт `depuser` с ограниченным sudo
- Генерирует SSH-ключ

Подробнее: [VPS_AND_SECRETS.md](VPS_AND_SECRETS.md)

**2. GitHub Actions (depuser, при первом деплое):**
- Создаёт директорию деплоя
- Устанавливает UFW (файрвол): порты 22, 80, 443, 992, 5555, 500/udp, 4500/udp, 1701/udp, 1194/udp
- Устанавливает fail2ban
- Устанавливает Docker CE и Compose v2
- Добавляет `depuser` в группу `docker`
- Настраивает unprivileged port binding (для HAProxy)

**Идемпотентность:**
- Повторные запуски не дублируют установку
- Первый деплой: 2-3 минуты
- Последующие: 30-60 секунд

---

## Конфигурации по окружениям

### HAProxy

- `haproxy/haproxy-preprod.cfg` — препрод (site.mine-craft.su, vpn.mine-craft.su)
- `haproxy/haproxy-prod.cfg` — production (www.mine-craft.su, mainsrv01.mine-craft.su)
- `haproxy/haproxy.cfg` — генерик, копируется CI/CD, не в git

### Nginx

- `nginx/nginx-preprod.conf` — препрод
- `nginx/nginx-prod.conf` — production
- `nginx/nginx.conf` — генерик, копируется CI/CD, не в git

### SSL

- Pre-Production: staging-сертификаты Let's Encrypt (`CERTBOT_STAGING=1`)
- Production: реальные сертификаты (`STAGING=0`, захардкожен)
- Автоматическое получение через `scripts/init-letsencrypt.sh`
- Автоматическое обновление через контейнер certbot

---

## Стек сервисов (docker-compose.prod.yml)

```
Client → HAProxy:80/443 (SNI routing)
              │
              ├── web-домен → Nginx:8080 → Gunicorn:8000 (web)
              │
              └── vpn-домен → SoftEther:4443 (VPN)
```

Сервисы: haproxy, nginx, web, db, redis, certbot, softether.

Named volumes: `static_volume`, `media_volume`, `postgres_data`, `redis_data`.

Health checks, auto-restart: `unless-stopped`.

---

## Медиафайлы

Обслуживаются через Django `FileResponse` в `ProtectedMediaView`:
- Доступ только для аутентифицированных пользователей (`@login_required`)
- Защита от path traversal
- Проверка существования файла

---

## Время выполнения

| Job | Время |
|-----|-------|
| Test | ~3-5 мин |
| Lint | ~2-3 мин |
| Build | ~2-5 мин (с кэшем) |
| Deploy | ~2-3 мин |

**Preprod (полный цикл):** ~10-15 минут
**Production:** ~5-8 минут (без тестов и линтеров)
