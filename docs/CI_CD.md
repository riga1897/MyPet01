# CI/CD Pipeline Documentation

## Обзор

MyPet01 использует **GitHub Actions** для автоматизации тестирования, сборки и развёртывания.

**Pipeline включает:**
- Автоматическое тестирование (pytest с coverage 100%)
- Code quality checks (ruff, mypy)
- Docker build & push в GitHub Container Registry
- Zero-configuration VPS (автоустановка Docker, UFW, fail2ban)
- Деплой на pre-production (`release/*`) и production (`main`)
- Автоматическая настройка SSL (Let's Encrypt)
- Миграции БД, загрузка начальных данных и демо-контента
- Health checks после развёртывания
- Автоматическое создание draft PR (preprod → main)

## Архитектура Pipeline

### Pre-Production (`ci-cd.yml`)

```
Git Push release/* →
  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────┐
  │   Test   │──▶│   Lint   │──▶│  Build   │──▶│   Deploy     │
  │ (pytest) │   │(ruff+mypy│   │ & Push   │   │  Preprod     │
  │ cov=100% │   │)         │   │ (GHCR)   │   │  VPS         │
  └──────────┘   └──────────┘   └──────────┘   └──────────────┘
```

### Production (`ci.yml`)

```
Git Push main →
  ┌──────────┐   ┌──────────────┐
  │  Build   │──▶│   Deploy     │
  │ & Push   │   │  Production  │
  │ (GHCR)   │   │  VPS         │
  └──────────┘   └──────────────┘
```

> **Примечание:** Production-деплой (`ci.yml`) не включает шаги Test и Lint, так как код в `main` попадает только через проверенный merge из `release/*`.

## Workflow файлы

| Файл | Триггер | Назначение |
|------|---------|------------|
| `.github/workflows/ci-cd.yml` | Push в `release/*` | Тесты + линтеры + сборка + деплой на препрод |
| `.github/workflows/ci.yml` | Push в `main` | Сборка + деплой на production |

## Jobs

### ci-cd.yml (Pre-Production)

#### Job 1: Test

**Цель:** Запуск тестов с проверкой покрытия

**Сервисы:**
- PostgreSQL 15
- Redis 7

**Шаги:**
1. Checkout кода
2. Setup Python 3.12
3. Установка Poetry
4. Кэширование зависимостей
5. Установка зависимостей
6. Ожидание готовности БД
7. Применение миграций
8. Запуск pytest с coverage (**threshold 100%**)
9. Upload coverage artifacts

#### Job 2: Lint

**Цель:** Проверка качества кода

**Проверки (параллельно):**
- `ruff check .` — линтер
- `mypy .` — проверка типов

**Зависимости:** После `test`

#### Job 3: Build and Push

**Цель:** Сборка Docker образа и публикация в GHCR

**Теги:**
- `{branch}-{SHA}` — для каждого коммита
- `preprod-latest` — для release/*

**Условия:** Только `push` в `release/*`

#### Job 4: Deploy Pre-Production

**Цель:** Деплой на препрод сервер

**Триггер:** Push в `release/*`

**Шаги:**
1. SSH подключение
2. Настройка инфраструктуры VPS (директория, UFW, fail2ban, Docker — если нужно)
3. Копирование docker-compose.prod.yml, nginx, haproxy, скриптов
4. Генерация .env (с передачей `LOAD_DEMO_DATA` из GitHub Variables)
5. Pull образа `preprod-latest`
6. Запуск стека
7. Health check (12 попыток × 5 сек)
8. Автоматическая настройка SSL (staging/production — зависит от `CERTBOT_STAGING`)
9. Миграции БД, создание суперпользователя, загрузка начальных данных
10. Загрузка демо-контента (`setup_demo_content`)
11. Сбор статики (`collectstatic`)
12. Создание draft PR в main

### ci.yml (Production)

#### Job 1: Build and Push

**Цель:** Сборка Docker образа и публикация в GHCR

**Теги:**
- `main-{SHA}` — для каждого коммита
- `latest` — всегда

#### Job 2: Deploy Production

**Цель:** Деплой на production сервер

**Триггер:** Push в `main`

**Шаги:**
1. SSH подключение
2. Настройка инфраструктуры VPS (если нужно)
3. Копирование файлов
4. Генерация .env
5. Pull образа `latest`
6. Запуск стека
7. Health check (12 попыток × 5 сек)
8. Автоматическая настройка SSL (**всегда реальный сертификат**, `STAGING=0`)
9. Миграции БД, создание суперпользователя, загрузка начальных данных
10. Сбор статики (`collectstatic`)

> **Важно:** В production **не загружаются** демо-данные.

## Gitflow Workflow

```
feature/* → develop → release/* → main
                          ↓           ↓
                     preprod VPS   prod VPS
```

### Создание релиза

```bash
git checkout -b release/v1.0 develop
git push origin release/v1.0
```

После этого CI/CD автоматически:
1. Запускает тесты (coverage 100%)
2. Проверяет линтеры (ruff + mypy)
3. Собирает Docker образ
4. Деплоит на препрод
5. Настраивает SSL
6. Загружает данные и демо-контент
7. Создаёт draft PR в main

### Релиз в production

```bash
git checkout main
git merge release/v1.0
git push origin main
```

## GitHub Secrets и Variables

### Secrets (обязательные)

| Secret | Описание |
|--------|----------|
| `GHCR_TOKEN` | Personal Access Token с `read:packages` |
| `SSH_KEY` / `PREPROD_SSH_KEY` | SSH ключи для VPS |
| `SSH_USER` / `PREPROD_SSH_USER` | Пользователи SSH |
| `SERVER_IP` / `PREPROD_SERVER_IP` | IP адреса серверов |
| `DEPLOY_DIR` / `PREPROD_DEPLOY_DIR` | Пути деплоя |

### Variables (опциональные)

| Variable | Описание | Значения | По умолчанию |
|----------|----------|----------|--------------|
| `LOAD_DEMO_DATA` | Загрузка демо-данных на препроде | `true` / `false` | `false` |
| `CERTBOT_STAGING` | Staging сертификат Let's Encrypt (**только препрод**) | `0` / `1` | `0` |
| `CREATE_PR_ON_PREDEPLOY` | Создание draft PR при деплое на препрод | `true` / `false` | `true` |

> **Примечание:** `CERTBOT_STAGING` влияет только на препрод. В production **всегда** используется реальный сертификат (`STAGING=0` захардкожен).

Подробнее: [GITHUB_SECRETS.md](./GITHUB_SECRETS.md)

## docker-entrypoint.sh

При старте контейнера entrypoint автоматически выполняет:
1. `migrate` — применение миграций БД
2. `collectstatic` — сбор статических файлов
3. `loaddata initial_structure.json` — загрузка начальной структуры (категории, типы контента, теги)
4. `setup_demo_content` — загрузка демо-данных (**только если `LOAD_DEMO_DATA=true`**)
5. `createsuperuser` — создание суперпользователя (если не существует)
6. Запуск Gunicorn

> **Примечание:** CI/CD pipeline также выполняет миграции, загрузку данных и SSL-настройку как отдельные шаги после запуска контейнеров. Это обеспечивает двойную гарантию: данные загрузятся и через entrypoint, и через CI/CD.

> **Production:** В `.env` production-сервера переменная `LOAD_DEMO_DATA` отсутствует (не генерируется `generate-production-env.sh`), поэтому демо-данные не загружаются ни через entrypoint, ни через CI/CD.

## Zero-Configuration VPS

Подготовка VPS выполняется в два этапа:

**1. `setup_vps.sh` (root, один раз):**
- Создаёт пользователя `depuser` с ограниченным sudo
- Генерирует SSH-ключ для GitHub Actions

**2. GitHub Actions (depuser, при первом деплое):**
- Создаёт директорию деплоя
- Устанавливает и настраивает UFW (файрвол)
- Устанавливает fail2ban (защита от брутфорса)
- Устанавливает Docker CE и Docker Compose v2
- Добавляет `depuser` в группу `docker`
- Настраивает unprivileged port binding (для HAProxy)

При последующих деплоях все проверки пропускаются — инфраструктура уже настроена.

**Требования к VPS:**
- Ubuntu 20.04/22.04 или Debian 11/12
- SSH доступ по ключу
- sudo права (ограниченные, настраиваются setup_vps.sh)
- Минимум 1GB RAM, 10GB диск

## Медиафайлы

Медиафайлы (фото, видео, превью) обслуживаются через Django `FileResponse` в `ProtectedMediaView`:
- Доступ только для аутентифицированных пользователей (`@login_required`)
- Защита от path traversal (`..` в путях)
- Проверка существования файла

## Health Checks

После деплоя проверяется доступность:
- 12 попыток с интервалом 5 секунд
- При ошибке — вывод логов для диагностики

## Стек сервисов

- **HAProxy** с network_mode: host для SNI роутинга (HTTP/HTTPS/VPN)
- **Nginx** для статики и проксирования к Django
- **SoftEther VPN** с SSL сертификатами
- **Redis** для кэширования
- **PostgreSQL** для хранения данных
- **Certbot** для автообновления SSL сертификатов

## Время выполнения

| Job | Время |
|-----|-------|
| Test | ~3-5 мин |
| Lint | ~2-3 мин |
| Build | ~2-5 мин (с кэшем) |
| Deploy | ~2-3 мин |

**Общее время:** ~10-15 минут для полного цикла (preprod)
**Production:** ~5-8 минут (без тестов и линтеров)
