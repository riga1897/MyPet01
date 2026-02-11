# 🚀 CI/CD Pipeline Documentation

## Обзор

Проект использует **GitHub Actions** для автоматизации тестирования, сборки Docker образов и развёртывания на pre-production и production серверы. Pipeline запускается при каждом push с условным выполнением build/deploy jobs для `main` (production) и `release/*` (pre-production) веток.

**Pipeline включает:**
- ✅ Автоматическое тестирование (283 тестов, 98.23% coverage)
- ✅ Code quality checks (ruff, black, mypy, isort, flake8)
- ✅ Docker build & push в GitHub Container Registry
- ✅ **Zero-configuration VPS:** автоматическая установка Docker и зависимостей
- ✅ Автоматический deployment на pre-production (`release/*`) и production (`main`)
- ✅ Health checks после развёртывания
- ✅ **Автоматическое создание draft PR** после успешного preprod deployment

---

## Архитектура Pipeline

```
┌─────────────────┐
│   Git Push/PR   │
│  (main/develop) │
└────────┬────────┘
         │
         ▼
┌────────────────────────────────────────────────────────┐
│              GitHub Actions Workflow                   │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐         │
│  │   Test   │──▶│   Lint   │──▶│  Build   │         │
│  │  Job     │   │   Job    │   │  & Push  │         │
│  └──────────┘   └──────────┘   └──────────┘         │
│       │              │               │                │
│       │              │               ▼                │
│       │              │         ┌──────────┐          │
│       │              │         │  Deploy  │          │
│       │              │         │   Job    │          │
│       │              │         └──────────┘          │
│       │              │               │                │
│       ▼              ▼               ▼                │
│  Coverage       Lint Report    Docker Image          │
│  Reports        Artifacts      → GHCR                │
│  (artifacts)                   → Production          │
└────────────────────────────────────────────────────────┘
```

---

## 📋 Jobs Breakdown

### Job 1: Test (Тестирование)

**Цель:** Запуск всех тестов с проверкой покрытия кода

**Стек:**
- Ubuntu Latest
- Python 3.12
- PostgreSQL 16 (GitHub Actions service)
- Redis 7 (GitHub Actions service)

**Шаги:**
1. Checkout кода
2. Setup Python 3.12
3. Установка Poetry
4. Кэширование Poetry dependencies (ускорение на 2-3 минуты)
5. Установка system dependencies (libpq-dev, postgresql-client, redis-tools)
6. Установка Python dependencies через Poetry
7. Ожидание готовности баз данных
8. Применение миграций
9. **Django APITestCase тесты** (78 tests)
   ```bash
   poetry run coverage run --source='users,lms,config' manage.py test
   ```
10. **Pytest тесты** (205 tests) с параллельным запуском
    ```bash
    poetry run pytest --cov=users --cov=lms --cov=config --cov-append -v -n auto
    ```
    **Важно:** Используется `pytest-cov` плагин вместо `coverage run` для корректной работы с `pytest-xdist` (`-n auto`). Плагин автоматически инструментирует все worker процессы и агрегирует coverage данные.
11. **Coverage report** с threshold 85% (достигаемый результат: ~98%)
12. Upload coverage artifacts (хранятся 30 дней)

**Coverage Aggregation:**
- Django tests используют `coverage run` → создает `.coverage`
- Pytest использует `pytest-cov` с `--cov-append` → добавляет к `.coverage`
- `pytest-cov` корректно обрабатывает параллельные worker'ы от `pytest-xdist`
- Итоговый `coverage report` читает объединенный `.coverage` файл (~98.22% coverage)

**Условия запуска:** Всегда (при любом push/PR)

**Время выполнения:** ~3-5 минут

---

### Job 2: Lint (Code Quality)

**Цель:** Проверка стандартов кода

**Стек:**
- Ubuntu Latest
- Python 3.12
- Poetry

**Проверки:**
- `ruff check .` — быстрый линтер (замена flake8 + pylint)
- `black --check .` — форматирование кода
- `isort --check-only .` — сортировка импортов
- `mypy .` — проверка типов (100% type coverage)
- `flake8 .` — дополнительные lint правила

**Зависимости:** Запускается **после** успешного `test` job

**Условия запуска:** Всегда (при любом push/PR)

**Время выполнения:** ~2-3 минуты

---

### Job 3: Build and Push (Docker Image)

**Цель:** Сборка production Docker образа и публикация в GitHub Container Registry

**Стек:**
- Ubuntu Latest
- Docker Buildx
- GitHub Container Registry (ghcr.io)

**Шаги:**
1. Checkout кода
2. Setup Docker Buildx (multi-platform builds support)
3. Login в GHCR с `GITHUB_TOKEN`
4. Извлечение metadata для tagging:
   - `{branch}-{SHA}` — коммит SHA с префиксом ветки
   - `{branch}` — имя ветки
   - `latest` — только для main branch
   - `preprod-latest` — только для release/* branches
5. **Build & Push Docker image**:
   - Multi-stage Dockerfile (builder + runtime)
   - Gunicorn для production (не runserver)
   - Collectstatic автоматически при запуске
6. Layer caching через GitHub Actions cache (ускорение на 5-10 минут)
7. Print image info (tags, registry URL)

**Зависимости:** Запускается **после** успешных `test` и `lint` jobs

**Условия запуска:** Только при `push` в `main` или `release/*` branches (не для PR)

**Время выполнения:** ~5-8 минут (первый раз), ~2-3 минуты (с кэшем)

---

### Job 4: Deploy Pre-Production (release/* branches)

**Цель:** Автоматическое развёртывание на pre-production сервер

**Стек:**
- Ubuntu Latest
- SSH client
- Pre-production server (Docker host)

**Шаги:**
1. Checkout кода
2. Setup SSH agent с приватным ключом (`PREPROD_SSH_KEY` secret)
3. **Zero-configuration VPS setup** (автоматическая установка зависимостей):
   - Проверка и установка Docker CE (если не установлен)
   - Проверка и установка Docker Compose v2 plugin
   - Создание deployment директории (`/opt/lms-preprod`)
   - Настройка прав доступа
4. **Копирование docker-compose.prod.yml на preprod сервер**
5. **Копирование и запуск generate-preprod-env.sh**:
   ```bash
   # Копирование скрипта на preprod VPS
   scp scripts/generate-preprod-env.sh $PREPROD_SSH_USER@$PREPROD_SERVER_IP:$PREPROD_DEPLOY_DIR/
   
   # Запуск с передачей GitHub Secrets
   ssh $PREPROD_SSH_USER@$PREPROD_SERVER_IP << 'EOF'
     cd $PREPROD_DEPLOY_DIR
     chmod +x generate-preprod-env.sh
     
     # Автогенерация .env (идемпотентная операция)
     PREPROD_SERVER_IP=$PREPROD_SERVER_IP \
     PREPROD_STRIPE_SECRET_KEY=$PREPROD_STRIPE_SECRET_KEY \
     PREPROD_STRIPE_PUBLISHABLE_KEY=$PREPROD_STRIPE_PUBLISHABLE_KEY \
     ./generate-preprod-env.sh
   EOF
   ```
6. **SSH deployment на preprod:**
   ```bash
   # Логин в GHCR
   docker login ghcr.io
   
   # Pull новых образов (preprod-latest)
   docker compose -f docker-compose.prod.yml pull
   
   # Запуск всего стека
   docker compose -f docker-compose.prod.yml up -d --remove-orphans
   ```
7. **Health check** с retry loop (12 попыток по 5 секунд)
8. **Automatic draft PR creation:** `release/* → main` через GitHub CLI
   - **Формат:** Минималистичный (только заголовок "Release to Production")
   - **Без markdown body** для избежания YAML parsing conflicts
   - **Draft режим:** PR создается как черновик для ревью перед production merge

**Permissions:** `contents: write`, `pull-requests: write`

**Зависимости:** Запускается **после** успешного `build-and-push` job

**Условия запуска:** Только при `push` в `release/*` branches

**Время выполнения:** ~2-3 минуты (или ~3-5 минут при первой установке Docker)

---

### Job 5: Deploy Production (main branch)

**Цель:** Автоматическое развёртывание на production сервер

**Стек:**
- Ubuntu Latest
- SSH client
- Production server (Docker host)

**Шаги:**
1. Checkout кода
2. Setup SSH agent с приватным ключом (`SSH_KEY` secret)
3. **Zero-configuration VPS setup** (автоматическая установка зависимостей):
   - Проверка и установка Docker CE (если не установлен)
   - Проверка и установка Docker Compose v2 plugin
   - Создание deployment директории (`/opt/lms`)
   - Настройка прав доступа
4. **Копирование файлов на сервер**:
   - `docker-compose.prod.yml` — конфигурация 6 сервисов (nginx, db, redis, web, celery_worker, celery_beat)
   - `nginx.conf` — Nginx конфигурация для reverse proxy и статики
5. **Копирование и запуск generate-production-env.sh**:
   ```bash
   # Копирование скрипта на VPS
   scp scripts/generate-production-env.sh $SSH_USER@$SERVER_IP:$DEPLOY_DIR/
   
   # Запуск с передачей GitHub Secrets
   ssh $SSH_USER@$SERVER_IP << 'EOF'
     cd $DEPLOY_DIR
     chmod +x generate-production-env.sh
     
     # Автогенерация .env (идемпотентная операция)
     SERVER_IP=$SERVER_IP \
     STRIPE_SECRET_KEY=$PROD_STRIPE_SECRET_KEY \
     STRIPE_PUBLISHABLE_KEY=$PROD_STRIPE_PUBLISHABLE_KEY \
     ./generate-production-env.sh
   EOF
   ```
5. **SSH deployment на production (Infrastructure as Code):**
   ```bash
   # Логин в GHCR
   docker login ghcr.io
   
   # Pull новых образов через docker-compose.prod.yml
   docker compose -f docker-compose.prod.yml pull
   
   # Запуск всего стека (Nginx, PostgreSQL, Redis, Web, Celery)
   docker compose -f docker-compose.prod.yml up -d --remove-orphans
   
   # Cleanup старых образов
   docker image prune -af
   ```
6. **Health check:**
   - Sleep 45 секунд (инициализация БД + миграции + collectstatic)
   - `curl http://{SERVER_IP}:80/api/` — проверка API через Nginx с retry loop (12 попыток)
   - При ошибке — вывод логов всех контейнеров для диагностики

**Production Architecture:**
```
Client Request → Nginx:80/443 → Gunicorn:8000 (internal)
                   ├─ /static/ → Direct serve (30d cache)
                   ├─ /media/  → Direct serve (7d cache)
                   └─ /api/    → Proxy to web:8000
```

**Зависимости:** Запускается **после** успешного `build-and-push` job

**Условия запуска:** Только при `push` в `main` branch

**Время выполнения:** ~2-3 минуты

---

## 🔄 Deployment Flow с автогенерацией .env

**Новая фича:** Production `.env` генерируется автоматически через скрипт `scripts/generate-production-env.sh`

```
┌────────────────────────────────────────────────────────────┐
│           GitHub Actions Deploy Job (main branch)          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  1. SSH Setup                                              │
│     └─▶ Настройка SSH agent с приватным ключом            │
│                                                            │
│  2. Copy Files to VPS                                      │
│     ├─▶ docker-compose.prod.yml → /opt/lms/               │
│     ├─▶ nginx.conf → /opt/lms/                            │
│     └─▶ generate-production-env.sh → /opt/lms/            │
│                                                            │
│  3. Generate .env (АВТОМАТИЧЕСКИ)                          │
│     ├─▶ Передача GitHub Secrets:                          │
│     │   • PROD_STRIPE_SECRET_KEY → STRIPE_SECRET_KEY      │
│     │   • PROD_STRIPE_PUBLISHABLE_KEY → ...               │
│     │   • SERVER_IP → ALLOWED_HOSTS, SITE_DOMAIN          │
│     ├─▶ Автогенерация:                                    │
│     │   • SECRET_KEY (Python secrets, 50 chars)           │
│     │   • POSTGRES_PASSWORD (openssl, 24 bytes)           │
│     ├─▶ Фиксированные значения:                           │
│     │   • DEBUG=False, POSTGRES_HOST=db, ...              │
│     └─▶ Проверка идемпотентности:                         │
│         • Если .env существует → skip                     │
│         • Если .env нет → создать                         │
│                                                            │
│  4. Docker Login & Pull                                    │
│     └─▶ docker login ghcr.io                              │
│     └─▶ docker compose pull (GHCR images)                 │
│                                                            │
│  5. Start Services                                         │
│     └─▶ docker compose up -d (6 сервисов)                 │
│         ├─▶ Nginx (reverse proxy, ports 80/443)           │
│         ├─▶ PostgreSQL 16                                 │
│         ├─▶ Redis 7                                       │
│         ├─▶ Web (Gunicorn, internal port 8000)            │
│         ├─▶ Celery Worker                                 │
│         └─▶ Celery Beat                                   │
│                                                            │
│  6. Health Checks                                          │
│     └─▶ curl http://SERVER_IP:80/api/ (через Nginx)       │
│         (retry loop: 12 попыток × 5 сек)                  │
│                                                            │
│  📊 Production Architecture:                               │
│     Client → Nginx (80/443) → Gunicorn (8000, internal)   │
│     ├─▶ /static/ → Nginx (direct serve, 30d cache)        │
│     ├─▶ /media/  → Nginx (direct serve, 7d cache)         │
│     └─▶ /api/    → Proxy to Gunicorn (web:8000)           │
│                                                            │
└────────────────────────────────────────────────────────────┘
                           │
                           ▼
                    ✅ DEPLOYMENT OK
```

### Преимущества автогенерации:

| Традиционный подход | Автогенерация |
|---------------------|---------------|
| ❌ Ручное создание .env на VPS | ✅ Автоматическая генерация |
| ❌ Риск ошибок при копировании | ✅ Валидация обязательных параметров |
| ❌ Секреты в документации | ✅ Секреты только в GitHub Secrets |
| ❌ Сложность настройки | ✅ Один `git push main` → готово |

---

## 🔐 GitHub Secrets

Для работы CI/CD pipeline необходимы следующие secrets в GitHub:

### Обязательные секреты:

| Secret | Категория | Описание | Пример |
|--------|-----------|----------|--------|
| `SSH_KEY` | SSH доступ | Приватный SSH ключ для доступа к серверу | `-----BEGIN OPENSSH PRIVATE KEY-----` |
| `SSH_USER` | SSH доступ | Имя пользователя SSH | `deploy` или `ubuntu` |
| `SERVER_IP` | SSH доступ | IP-адрес production сервера | `192.168.1.100` |
| `DEPLOY_DIR` | SSH доступ | Директория на сервере для приложения | `/opt/lms` |
| `PROD_STRIPE_SECRET_KEY` | **Автогенерация .env** | Stripe secret key для payments | `sk_live_...` |
| `PROD_STRIPE_PUBLISHABLE_KEY` | **Автогенерация .env** | Stripe publishable key | `pk_live_...` |

### Опциональные секреты:

| Secret | Когда нужен | Описание |
|--------|-------------|----------|
| `PROD_EMAIL_HOST_USER` | Реальная email отправка | SMTP email для notifications |
| `PROD_EMAIL_HOST_PASSWORD` | Реальная email отправка | SMTP пароль (Gmail App Password) |

### Автогенерируемые значения (НЕ нужны в GitHub):

Эти значения генерируются автоматически скриптом на VPS:
- ✅ `SECRET_KEY` — Django secret (Python secrets.token_urlsafe(50))
- ✅ `POSTGRES_PASSWORD` — БД пароль (openssl rand -base64 24)
- ✅ ~20 других переменных (DEBUG, хосты, Redis, Celery, пути)

**Настройка secrets:**

1. Перейдите в GitHub: `Settings` → `Secrets and variables` → `Actions`
2. Нажмите `New repository secret`
3. Добавьте каждый обязательный secret из таблицы выше

📖 **Подробная инструкция:** см. [docs/GITHUB_SECRETS.md](./GITHUB_SECRETS.md)

---

## 🛠️ Настройка Production Server

### Требования:

- ✅ Docker и Docker Compose v2+ установлены
- ✅ Nginx настроен как reverse proxy
- ✅ SSH доступ по ключу (не по паролю!)
- ✅ Пользователь в группе `docker`
- ✅ Созданная директория `${DEPLOY_DIR}` с правами

### Подход Infrastructure as Code:

Проект использует **docker-compose.prod.yml** для автоматизации всей инфраструктуры. Это обеспечивает:
- ✅ Воспроизводимость — один файл описывает весь стек
- ✅ Автоматизацию — GitHub Actions автоматически разворачивает всё
- ✅ Версионирование — docker-compose.prod.yml в git
- ✅ Простоту — нет ручных `docker run` команд

### Подготовка сервера (One-time Setup):

```bash
# 1. Установка Docker и Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Перезайдите в систему для применения прав

# 2. Проверка версии Docker Compose (требуется v2+)
docker compose version
# Должно быть: Docker Compose version v2.x.x

# 3. Создание рабочей директории
sudo mkdir -p /opt/lms/{media,staticfiles,logs,postgres-data}
sudo chown -R $USER:$USER /opt/lms

# 4. ✅ .env файл создастся АВТОМАТИЧЕСКИ при первом деплое!
# GitHub Actions запустит generate-production-env.sh который:
# - Сгенерирует SECRET_KEY и POSTGRES_PASSWORD
# - Подставит STRIPE ключи из GitHub Secrets
# - Создаст ~25 переменных автоматически
#
# Ничего НЕ нужно делать вручную!

# 5. Генерация SSH ключа для GitHub Actions
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy

# Добавьте публичный ключ в ~/.ssh/authorized_keys
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys

# Скопируйте приватный ключ и добавьте в GitHub Secrets (SSH_KEY)
cat ~/.ssh/github_deploy
# Перейдите в GitHub: Settings → Secrets → Actions → New secret
# Имя: SSH_KEY
# Значение: вставьте содержимое приватного ключа

# 6. Настройка GitHub Secrets
# В GitHub repository → Settings → Secrets and variables → Actions
# Добавьте следующие secrets:
# - SSH_KEY: приватный ключ (из шага 5)
# - SSH_USER: ваш username на сервере
# - SERVER_IP: IP адрес сервера
# - DEPLOY_DIR: /opt/lms

# 7. Первый deployment через GitHub Actions
# Push в main branch → GitHub Actions автоматически:
# - Скопирует docker-compose.prod.yml на сервер
# - Pull образов из GHCR
# - Запустит весь стек (PostgreSQL, Redis, Web, Celery)
```

**Важно:**
- **Инфраструктура управляется через docker-compose.prod.yml** — никаких ручных команд!
- **GitHub Actions автоматически** разворачивает весь стек при push в `main`
- **Data persistence** через host volumes: `/opt/lms/postgres-data`
- **Все сервисы автоматически перезапускаются** при ребуте сервера (`restart: unless-stopped`)

### Что происходит при deployment (автоматически):

GitHub Actions выполняет следующие шаги:

1. **Copy docker-compose.prod.yml** → на сервер в `/opt/lms/`
2. **Validation** → проверка `.env` файла и прав
3. **Pull images** → скачивание образов из GHCR
4. **Start services** → `docker compose up -d --remove-orphans`
   - PostgreSQL 16 с persistent volume
   - Redis 7 для Celery broker
   - Web (Gunicorn с 4 workers)
   - Celery Worker (асинхронные задачи)
   - Celery Beat (периодические задачи)
5. **Health checks** → проверка доступности API
6. **Cleanup** → удаление старых образов

### Управление production стеком:

```bash
# На production сервере:
cd /opt/lms

# Просмотр статуса всех сервисов
docker compose -f docker-compose.prod.yml ps

# Просмотр логов
docker compose -f docker-compose.prod.yml logs -f

# Просмотр логов конкретного сервиса
docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml logs -f celery_worker

# Перезапуск сервиса
docker compose -f docker-compose.prod.yml restart web

# Остановка всего стека
docker compose -f docker-compose.prod.yml down

# Запуск стека вручную (обычно не требуется, GitHub Actions делает это автоматически)
export GITHUB_REPOSITORY=username/repo
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### Nginx Configuration:

```nginx
# /etc/nginx/sites-available/lms
server {
    listen 80;
    server_name your-domain.com;

    # Max upload size для media files
    client_max_body_size 10M;

    # Static files (served by Nginx directly)
    location /static/ {
        alias /opt/lms/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /opt/lms/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Proxy to Django (Gunicorn)
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Websocket support (если используется)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts для длинных запросов
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

```bash
# Активация конфигурации
sudo ln -s /etc/nginx/sites-available/lms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**SSL/HTTPS (рекомендуется для production):**

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx

# Получение SSL сертификата
sudo certbot --nginx -d your-domain.com
```

---

## 🔄 Workflow Triggers

| Событие | Ветки | Jobs | Deploy |
|---------|-------|------|--------|
| `push` | `main`, `develop` | test, lint, build, deploy | ✅ (только main) |
| `pull_request` | `main`, `develop` | test, lint | ❌ |

**Примеры:**

- ✅ `git push origin main` → полный pipeline + deployment
- ✅ `git push origin develop` → test + lint (без deployment)
- ✅ Open PR to `main` → test + lint (без deployment)
- ❌ `git push origin feature/new-api` → ничего не запускается

---

## 📊 Мониторинг Pipeline

### Просмотр статуса:

1. **GitHub Actions Tab:**
   - Откройте репозиторий → `Actions`
   - Выберите workflow run
   - Просмотрите каждый job и его логи

2. **Badges в README:**
   ```markdown
   ![CI/CD](https://github.com/username/repo/actions/workflows/ci-cd.yml/badge.svg)
   ```

3. **Email уведомления:**
   - GitHub отправляет email при failed runs
   - Настраивается в `Settings` → `Notifications`

### Просмотр артефактов:

```bash
# Coverage reports доступны в GitHub Actions
# Artifacts → coverage-report → Download
```

---

## 🐛 Troubleshooting

### Проблема: Test job fails

**Симптомы:** Тесты падают с ошибками БД или Redis

**Решение:**
```yaml
# Проверьте что services правильно настроены:
services:
  postgres:
    image: postgres:16
    env:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: test_db
```

**Debug:**
```bash
# Локально запустите тесты с теми же ENV:
export DATABASE_URL=postgres://postgres:postgres@localhost:5432/test_db
export REDIS_URL=redis://localhost:6379/0
poetry run pytest
```

---

### Проблема: Lint job fails

**Симптомы:** Ruff/Black/Mypy ошибки

**Решение:**
```bash
# Локально запустите проверки:
poetry run ruff check .
poetry run black --check .
poetry run mypy .

# Автофикс:
poetry run black .
poetry run ruff check --fix .
```

---

### Проблема: Build job fails

**Симптомы:** Docker build ошибки, missing dependencies

**Решение:**
```bash
# Локально проверьте Dockerfile:
docker build -t lms-test .

# Проверьте логи:
docker build --progress=plain --no-cache -t lms-test .
```

**Частые ошибки:**
- `poetry install` fails → проверьте `pyproject.toml` и `poetry.lock`
- `COPY` fails → убедитесь что файлы не в `.dockerignore`

---

### Проблема: Deploy job fails

**Симптомы:** SSH connection refused, deployment errors

**Решение:**

1. **Проверка SSH ключа:**
   ```bash
   # Локально проверьте SSH:
   ssh -i ~/.ssh/github_deploy user@server_ip
   ```

2. **Проверка secrets:**
   ```bash
   # Убедитесь что все secrets установлены:
   - SSH_KEY (приватный ключ)
   - SSH_USER
   - SERVER_IP
   - DEPLOY_DIR
   ```

3. **Проверка Docker на сервере:**
   ```bash
   # На сервере:
   docker ps
   docker logs lms-app
   docker network ls | grep lms_network
   ```

4. **Проверка .env файла:**
   ```bash
   # На сервере:
   cat ${DEPLOY_DIR}/.env
   ```

---

### Проблема: Health check fails

**Симптомы:** `curl` не может достучаться до API

**Решение:**

1. **Проверьте порт:**
   ```bash
   # На сервере:
   docker ps | grep lms-app
   netstat -tulpn | grep 8000
   ```

2. **Проверьте логи:**
   ```bash
   docker logs lms-app --tail 100
   ```

3. **Проверьте Gunicorn:**
   ```bash
   # В контейнере должен быть Gunicorn, не runserver:
   docker exec lms-app ps aux | grep gunicorn
   ```

4. **Проверьте ALLOWED_HOSTS:**
   ```python
   # В .env на сервере:
   ALLOWED_HOSTS=your-domain.com,${SERVER_IP},localhost
   ```

---

### Проблема: Automatic PR creation fails

**Симптомы:** `gh pr create` падает с ошибками:
- `GitHub Actions is not permitted to create or approve pull requests`
- `No commits between main and release/*`
- `Base ref must be a branch`
- `Head sha can't be blank, Base sha can't be blank`

**Решение:**

1. **Включите разрешение для GitHub Actions:**
   ```
   Repository Settings → Actions → General → Workflow permissions
   ☑️ Allow GitHub Actions to create and approve pull requests
   ```
   Если в организации — сначала включите на уровне organization, потом на уровне repository.

2. **Переименуйте master → main (если используете master):**
   ```bash
   # На GitHub:
   Settings → Branches → Default branch → Rename: master → main
   
   # Локально:
   git branch -m master main
   git fetch origin
   git branch -u origin/main main
   git remote set-head origin -a
   ```

3. **Добавьте полную историю в checkout:**
   ```yaml
   - name: Check out code
     uses: actions/checkout@v4
     with:
       fetch-depth: 0  # Полная история для сравнения веток
   ```

4. **Добавьте явный fetch main перед созданием PR:**
   ```yaml
   - name: Fetch main branch for comparison
     run: |
       git fetch origin main:main
       echo "✅ Fetched main branch for PR creation"

   - name: Create Pull Request to main
     env:
       GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
     run: |
       gh pr create \
         --repo ${{ github.repository }} \
         --base main \
         --head ${{ github.ref_name }} \
         --title "Release to Production" \
         --body "$(git log -1 --pretty=%B)" \
         --draft
   ```

**Важно:** 
- `fetch-depth: 0` скачивает полную историю, необходимую для сравнения веток
- `git fetch origin main:main` гарантирует наличие локальной копии main branch
- `--repo ${{ github.repository }}` явно указывает репозиторий для корректного разрешения refs

---

## 📈 Оптимизация Pipeline

### Ускорение тестов:

```yaml
# Кэширование Poetry dependencies (уже реализовано):
- uses: actions/cache@v3
  with:
    path: .venv
    key: ${{ runner.os }}-poetry-${{ hashFiles('**/poetry.lock') }}
```

**Результат:** ~2-3 минуты экономии на каждом run

### Ускорение Docker build:

```yaml
# Layer caching через GHA (уже реализовано):
cache-from: type=gha
cache-to: type=gha,mode=max
```

**Результат:** ~5-10 минут экономии при повторных сборках

### Параллельное выполнение:

```yaml
# Jobs test и lint могут быть параллельными если убрать:
needs: test  # Убрать эту строку в lint job
```

**Результат:** ~2-3 минуты экономии (но coverage artifacts не будут готовы для lint)

---

## 🎯 Best Practices

1. **Никогда не коммитьте secrets в код** — используйте GitHub Secrets
2. **Тестируйте локально** перед push в main
3. **Используйте feature branches** для новых функций
4. **Создавайте PR** для code review перед merge в main
5. **Мониторьте failed runs** и фиксите сразу
6. **Обновляйте dependencies** регулярно (Poetry update)
7. **Backup production БД** перед каждым deployment

---

## 📚 Связанная документация

- [Docker Setup](DOCKER_SETUP.md) — локальная разработка с Docker
- [DEVELOPMENT.md](../DEVELOPMENT.md) — стандарты разработки
- [README.md](../README.md) — общая информация о проекте

---

## 🔗 Полезные ссылки

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [SSH Agent Action](https://github.com/webfactory/ssh-agent)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Gunicorn Documentation](https://docs.gunicorn.org/en/stable/)
