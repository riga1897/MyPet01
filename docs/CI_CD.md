# CI/CD Pipeline Documentation

## Обзор

MyPet01 использует **GitHub Actions** для автоматизации тестирования, сборки и развёртывания.

**Pipeline включает:**
- Автоматическое тестирование (pytest с coverage)
- Code quality checks (ruff, mypy)
- Docker build & push в GitHub Container Registry
- Zero-configuration VPS (автоустановка Docker)
- Деплой на pre-production (`release/*`) и production (`main`)
- Health checks после развёртывания
- Автоматическое создание draft PR

## Архитектура Pipeline

```
┌─────────────────┐
│   Git Push/PR   │
└────────┬────────┘
         │
         ▼
┌────────────────────────────────────────────────────────┐
│              GitHub Actions Workflow                   │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐          │
│  │   Test   │──▶│   Lint   │──▶│  Build   │          │
│  │  Job     │   │   Job    │   │  & Push  │          │
│  └──────────┘   └──────────┘   └──────────┘          │
│                                      │                │
│                        ┌─────────────┴─────────────┐  │
│                        │                           │  │
│                        ▼                           ▼  │
│                 ┌────────────┐              ┌──────────┐
│                 │  Deploy    │              │  Deploy  │
│                 │  Preprod   │              │  Prod    │
│                 │ release/*  │              │  main    │
│                 └────────────┘              └──────────┘
└────────────────────────────────────────────────────────┘
```

## Jobs

### Job 1: Test

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
8. Запуск pytest с coverage (threshold 80%)
9. Upload coverage artifacts

### Job 2: Lint

**Цель:** Проверка качества кода

**Проверки (параллельно):**
- `ruff check .` — линтер
- `mypy .` — проверка типов

**Зависимости:** После `test`

### Job 3: Build and Push

**Цель:** Сборка Docker образа и публикация в GHCR

**Теги:**
- `{branch}-{SHA}` — для каждого коммита
- `latest` — для main
- `preprod-latest` — для release/*

**Условия:** Только `push` в `main` или `release/*`

### Job 4: Deploy Pre-Production

**Цель:** Деплой на препрод сервер

**Триггер:** Push в `release/*`

**Шаги:**
1. SSH подключение
2. Автоустановка Docker (если нужно)
3. Копирование docker-compose.prod.yml, nginx, haproxy
4. Генерация .env
5. Pull образа `preprod-latest`
6. Запуск стека
7. Health check
8. Создание draft PR в main

### Job 5: Deploy Production

**Цель:** Деплой на production

**Триггер:** Push в `main`

**Шаги:**
1. SSH подключение
2. Автоустановка Docker (если нужно)
3. Копирование файлов
4. Генерация .env
5. Pull образа `latest`
6. Запуск стека
7. Health check

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
1. Запускает тесты
2. Собирает Docker образ
3. Деплоит на препрод
4. Создаёт draft PR в main

### Релиз в production

```bash
git checkout main
git merge release/v1.0
git push origin main
```

## GitHub Secrets

**Обязательные секреты:**
- `GHCR_TOKEN` — Personal Access Token с `read:packages`
- `SSH_KEY` / `PREPROD_SSH_KEY` — SSH ключи для VPS
- `SSH_USER` / `PREPROD_SSH_USER` — пользователи SSH
- `SERVER_IP` / `PREPROD_SERVER_IP` — IP адреса серверов
- `DEPLOY_DIR` / `PREPROD_DEPLOY_DIR` — пути деплоя

Подробнее: [GITHUB_SECRETS.md](./GITHUB_SECRETS.md)

## Zero-Configuration VPS

Подготовка VPS выполняется в два этапа:

**1. `setup_vps.sh` (root, один раз):**
- Создаёт пользователя `depuser` с ограниченным sudo
- Генерирует SSH-ключ для GitHub Actions
- Создаёт директорию деплоя
- Настраивает файрвол (UFW)

**2. GitHub Actions (depuser, при первом деплое):**
- Устанавливает Docker CE и Docker Compose v2
- Добавляет `depuser` в группу `docker`
- Запускает Docker-сервис (`systemctl enable/start docker`)

При последующих деплоях шаг установки Docker пропускается.

**Требования к VPS:**
- Ubuntu 20.04/22.04 или Debian 11/12
- SSH доступ по ключу
- sudo права (ограниченные, настраиваются setup_vps.sh)
- Минимум 1GB RAM, 10GB диск

## Health Checks

После деплоя проверяется доступность:
- 12 попыток с интервалом 5 секунд
- При ошибке — вывод логов для диагностики

## Особенности MyPet01

- **HAProxy** с network_mode: host для SNI роутинга
- **SoftEther VPN** с SSL сертификатами
- **Nginx** для статики и проксирования
- **Redis** для кэширования

## Время выполнения

| Job | Время |
|-----|-------|
| Test | ~3-5 мин |
| Lint | ~2-3 мин |
| Build | ~2-5 мин (с кэшем) |
| Deploy | ~2-3 мин |

**Общее время:** ~10-15 минут для полного цикла
