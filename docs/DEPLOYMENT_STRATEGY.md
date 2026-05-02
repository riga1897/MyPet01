# Стратегия развертывания и CI/CD Pipeline

Четырехступенчатая стратегия развертывания MyPet01 от локальной разработки до production с использованием Gitflow.

> **Настройка VPS и секретов:** [VPS_AND_SECRETS.md](VPS_AND_SECRETS.md)
> **Практический гайд по деплою:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

## Обзор стратегии

```
+-------------------+   +-------------------+   +-------------------+   +-------------------+
|  1. DEVELOPMENT   |   |  2. STAGING       |   |  3. VPS2          |   |  4. VPS1          |
|  Разработка       |-->|  Локальный Docker |-->|  Pre-Production   |-->|  Production       |
|                   |   |                   |   |                   |   |                   |
|  Replit Cloud IDE |   |  Docker Desktop   |   |  release/* branch |   |  main branch      |
|  БЕЗ Docker       |   |  + live reload    |   |  vps2-latest      |   |  vps1-latest      |
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

## 3. VPS2 — Pre-Production

- Docker на VPS2 (IP из секрета `VPS2_SERVER_IP`)
- Домены: `site.mine-craft.su` (веб), `vpn.mine-craft.su` (VPN)
- Триггер: push в `release/*`
- Docker tag: `vps2-latest`
- SSL: Let's Encrypt (staging-сертификаты, `CERTBOT_STAGING=1`)
- HAProxy → Nginx → Gunicorn

## 4. VPS1 — Production

- Docker на VPS1 (IP из секрета `VPS1_SERVER_IP`)
- Домены: `www.mine-craft.su` (веб), `mainsrv01.mine-craft.su` (VPN)
- Триггер: push в `main`
- Docker tag: `vps1-latest`
- SSL: Let's Encrypt (реальные сертификаты, `STAGING=0` захардкожен)
- HAProxy → Nginx → Gunicorn (4 workers, 2 threads)

---

## Сравнение окружений

| Параметр | Development | Staging | VPS2 (Pre-Prod) | VPS1 (Production) |
|----------|-------------|---------|-----------------|-------------------|
| Docker | Нет (Nix) | Да (Docker Desktop) | Да (VPS) | Да (VPS) |
| Хосты БД/Redis | localhost | db, redis | db, redis | db, redis |
| Live reload | Да | Да (volume mount) | Нет | Нет |
| DEBUG | True | True | False | False |
| Сервер | runserver | runserver | HAProxy→Nginx→Gunicorn | HAProxy→Nginx→Gunicorn |
| Порт | 5000 | 5000 | 80/443→8080→8000 | 80/443→8080→8000 |
| Docker tag | N/A | local build | vps2-latest | vps1-latest |
| CI/CD | Нет | Нет | Да (release/*) | Да (main) |
| .env | Ручное | Ручное | generate-vps2-env.sh | generate-vps1-env.sh |

---

## Gitflow Workflow

```
feature/* → develop → release/* → main
                          ↓           ↓
                       VPS2        VPS1
                    (ci-cd.yml)  (ci.yml)
```

### Полный цикл релиза

```
1. feature/* → develop        (разработка новых функций)
2. develop → release/v1.0     (создание release-ветки)
3. push release/v1.0          (триггер CI/CD: test → lint → build → deploy на VPS2)
4. Тестирование на VPS2       (site.mine-craft.su)
5. Автоматический draft PR    (release/v1.0 → main)
6. Merge PR в main            (ручное подтверждение)
7. push main                  (триггер CI/CD: build → deploy на VPS1)
8. VPS1 работает              (www.mine-craft.su)
9. release/v1.0 → develop     (backmerge изменений)
```

---

## CI/CD Pipeline

### Workflow файлы

| Файл | Триггер | Назначение |
|------|---------|------------|
| `.github/workflows/ci-cd.yml` | Push в `release/*` | Тесты + линтеры + сборка + деплой на VPS2 |
| `.github/workflows/ci-cd.yml` | Push в `main` | Сборка + деплой на VPS1 |

> **Примечание:** VPS1-деплой не включает Test и Lint, так как код в `main` попадает только через проверенный merge из `release/*`.

### VPS2 Pipeline (release/*)

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
[build-and-push] Docker образ → GHCR (vps2-latest)
    │
    ▼
[deploy → VPS2]
    ├── Setup VPS (Docker, UFW, fail2ban) — идемпотентно
    ├── scp файлов на VPS2
    ├── generate-vps2-env.sh
    ├── docker compose pull + up -d
    ├── Health check (12 × 5 сек)
    ├── init-letsencrypt.sh (CERTBOT_STAGING)
    ├── migrate + collectstatic + loaddata + setup_demo_content + createsuperuser
    └── Создание draft PR: release/* → main
    ▼
VPS2 доступен: site.mine-craft.su
```

### VPS1 Pipeline (main)

```
Push в main
    │
    ▼
[build-and-push] Docker образ → GHCR (vps1-latest)
    │
    ▼
[deploy → VPS1]
    ├── Setup VPS (идемпотентно)
    ├── scp файлов на VPS1
    ├── generate-vps1-env.sh
    ├── docker compose pull + up -d
    ├── Health check (12 × 5 сек)
    ├── init-letsencrypt.sh (STAGING=0, реальные сертификаты)
    └── migrate + collectstatic + loaddata + createsuperuser
    ▼
VPS1 доступен: www.mine-craft.su
```

> **VPS1** не загружает демо-данные (`LOAD_DEMO_DATA` отсутствует в `.env`).

---

## Zero-Configuration VPS

Подготовка VPS в два этапа:

**1. `setup_vps.sh` (root, один раз):**
- Создаёт `depuser` с ограниченным sudo
- Генерирует SSH-ключ

Подробнее: [VPS_AND_SECRETS.md](VPS_AND_SECRETS.md)

**2. GitHub Actions (depuser, при первом деплое):**
- Создаёт директорию деплоя
- Устанавливает UFW: порты 22, 80, 443, 992, 5555, 500/udp, 4500/udp, 1701/udp, 1194/udp
- Устанавливает fail2ban
- Устанавливает Docker CE и Compose v2
- Добавляет `depuser` в группу `docker`
- Настраивает unprivileged port binding (для HAProxy)

**Идемпотентность:**
- Повторные запуски не дублируют установку
- Первый деплой: 2-3 минуты
- Последующие: 30-60 секунд

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

---

## Время выполнения

| Job | Время |
|-----|-------|
| Test | ~3-5 мин |
| Lint | ~2-3 мин |
| Build | ~2-5 мин (с кэшем) |
| Deploy | ~2-3 мин |

**VPS2 (полный цикл):** ~10-15 минут
**VPS1:** ~5-8 минут (без тестов и линтеров)
