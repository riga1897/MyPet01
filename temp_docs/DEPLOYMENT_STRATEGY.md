# Стратегия развёртывания: Development → Staging → Pre-Production → Production (Gitflow)

Этот документ описывает **четырёхступенчатую стратегию миграции** Django LMS приложения от локальной разработки до production deployment с использованием **Gitflow branching strategy**.

**Примеры реализации:** Development (Replit), Staging (Windows + Docker Desktop), Pre-Production (release/* → VPS), Production (main → VPS via GitHub Actions)

**✅ Статус:** Все 4 уровня успешно развернуты и протестированы (November 24, 2025). 
- Pre-production: `http://<PREPROD_SERVER_IP>/api/` (IP из GitHub Secrets `PREPROD_SERVER_IP`, динамический)
- Production: `http://<SERVER_IP>/api/` (IP из GitHub Secrets `SERVER_IP`, динамический) — deployment workflow успешно выполнен через GitHub Actions (main branch).

---

## Обзор стратегии

```
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│  1. DEVELOPMENT   │   │  2. STAGING       │   │ 3. PRE-PRODUCTION │   │  4. PRODUCTION    │
│  Разработка       │──>│  Локальный Docker │──>│  Препрод VPS      │──>│  Финальный VPS    │
│                   │   │                   │   │                   │   │                   │
│  localhost/cloud  │   │  Docker Desktop   │   │  release/* branch │   │  main branch      │
│  БЕЗ Docker       │   │  + live reload    │   │  preprod-latest   │   │  latest tag       │
│  Быстрая итерация │   │  Локальная сборка │   │  Полный CI/CD     │   │  Финальный релиз  │
│  feature/develop  │   │  develop ветка    │   │  + auto PR        │   │  + git tags       │
│  Replit/VSCode/   │   │  Windows/Mac/     │   │  Ubuntu VPS +     │   │  Ubuntu VPS +     │
│  PyCharm          │   │  Linux + Docker   │   │  GitHub Actions   │   │  GitHub Actions   │
└───────────────────┘   └───────────────────┘   └───────────────────┘   └───────────────────┘
```

### Как создать .env файл для каждого окружения

| Окружение | Метод создания .env | Команда | Примечание |
|-----------|-------------------|---------|-----------|
| **Development** | Копирование шаблона | `cp .env.example .env` | Ручное редактирование для localhost<br>Пример: Replit, локальная разработка |
| **Staging** | Копирование шаблона | `copy .env.docker.example .env` | Готовый шаблон с Docker service names<br>Пример: Windows/Mac/Linux + Docker Desktop |
| **Pre-Production** | **Автоматическая генерация** | `scripts/generate-preprod-env.sh` | ✅ Автоматизация через GitHub Actions (release/*)<br>🔑 Генерирует SECRET_KEY, POSTGRES_PASSWORD<br>🔐 Интегрирует PREPROD_* GitHub Secrets<br>🧪 Stripe TEST keys для препрода |
| **Production** | **Автоматическая генерация** | `scripts/generate-production-env.sh` | ✅ Автоматизация через GitHub Actions (main)<br>🔑 Генерирует SECRET_KEY, POSTGRES_PASSWORD<br>🔐 Интегрирует GitHub Secrets (Stripe, SERVER_IP)<br>📋 ~25 переменных из обязательных secrets |

**🚀 Ключевое отличие:** Pre-Production и Production используют **автогенерацию** вместо ручного копирования шаблонов, что устраняет ошибки конфигурации и обеспечивает безопасность. Pre-Production использует `PREPROD_*` secrets и Stripe TEST keys.

---

## 1. Development (Среда разработки)

### Назначение:
- Быстрая итеративная разработка
- Прототипирование новых фич
- Написание и отладка кода

### Примеры реализации:
- **Replit** (cloud IDE с Nix окружением)
- **Локальная разработка** (VSCode, PyCharm, любой IDE)
- **Codespaces** (GitHub Codespaces)

### Технологии (пример: Replit):
- **Окружение:** Nix (не Docker!)
- **Изоляция:** Sandboxed cloud environment
- **БД:** PostgreSQL на localhost
- **Redis:** Redis на localhost
- **Сервер:** Django runserver на порту 5000

### Конфигурация:
**Файл:** `.env` (создаётся из `.env.example`)

```env
# Replit использует localhost хосты
POSTGRES_HOST=localhost
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Запуск:
```bash
# Replit автоматически запускает workflow
# Poetry 2.1.4 используется для управления зависимостями
poetry run python manage.py runserver 0.0.0.0:5000
```

### Особенности:
- ✅ **Nix ≈ Docker** — Replit использует Nix для изоляции вместо Docker
- ✅ **Встроенные сервисы** — PostgreSQL, Redis доступны автоматически
- ✅ **Нет nested virtualization** — Docker не работает в Replit
- ✅ **Replit-специфичные файлы** — `.replit`, `replit.nix`, `replit.md`

### Когда использовать:
- Разработка новых фич
- Быстрые правки
- Отладка логики приложения
- Написание тестов

---

## 2. Staging (Тестовая среда)

### Назначение:
- **Промежуточное тестирование** перед push в production
- Проверка что код работает в Docker окружении
- Валидация production конфигурации локально

### Примеры реализации:
- **Windows + Docker Desktop** (основной пример в этом проекте)
- **macOS + Docker Desktop**
- **Linux + Docker**

### Технологии (пример: Windows + Docker Desktop):
- **Окружение:** Docker Desktop
- **Изоляция:** Docker контейнеры
- **БД:** PostgreSQL 16 в Docker (service name: `db`)
- **Redis:** Redis 7 в Docker (service name: `redis`)
- **Сервер:** Django runserver с **live reload**

### Конфигурация:
**Файл:** `.env` (создаётся из `.env.docker.example`)

```env
# Docker service names (НЕ localhost!)
POSTGRES_HOST=db
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0

DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
SITE_DOMAIN=localhost:8000
```

### Файлы:
- `docker-compose.yml` — staging конфигурация с live reload
- `.env.docker.example` — шаблон для staging окружения

### Запуск:
```powershell
# Скопировать конфигурацию
copy .env.docker.example .env

# Запустить стек
docker compose up -d

# Проверить логи
docker compose logs -f
```

### Особенности:
- ✅ **Live reload** — изменения в коде применяются автоматически (volume mounting: `.:/app`)
- ✅ **Docker хосты** — `db`, `redis` вместо `localhost`
- ✅ **Локальная сборка** — `build: .` вместо pull из registry
- ✅ **DEBUG=True** — удобная отладка
- ✅ **Порт 8000** — единообразие с production окружением

### Задачи staging окружения:
1. ✅ **Проверка сборки Docker образа** — убедиться что `Dockerfile` корректный
2. ✅ **Тестирование миграций БД** — проверить что миграции работают в контейнере
3. ✅ **Отладка production конфигурации** — проверить настройки с `db`/`redis` хостами
4. ✅ **Быстрые правки** — live reload для оперативных исправлений
5. ✅ **Валидация .dockerignore** — убедиться что `.replit`, `replit.nix` не попадают в образ

### Проверка исключения Replit-файлов:
```powershell
# Проверить содержимое образа
docker compose exec web ls -la /app | grep replit
# Не должно быть вывода (файлы исключены через .dockerignore)
```

### Когда использовать:
- Перед push в `main` ветку
- После добавления новых зависимостей
- После изменения Docker конфигурации
- Для проверки миграций БД
- Для тестирования Celery tasks

---

## 3. Pre-Production (Препродакшн окружение)

### Назначение:
- **Полная репетиция production deployment** перед релизом
- Тестирование всего CI/CD pipeline на изолированном сервере
- Валидация deployment процесса без риска для production
- Проверка Stripe TEST keys в production-подобном окружении
- **Финальное тестирование release веток** перед merge в main

### Технологии:
- **Окружение:** Docker на отдельном VPS (Ubuntu/Debian)
- **Изоляция:** Полностью отдельный сервер от production
- **БД:** PostgreSQL 16 в Docker (изолированная от production)
- **Redis:** Redis 7 в Docker
- **Reverse Proxy:** Nginx (порты 80/443)
- **Сервер:** Gunicorn (порт 8000, internal)
- **Git Strategy:** Gitflow с release ветками
- **Триггер:** Push в `release/*` branches
- **Docker tag:** `preprod-latest`

### Конфигурация:
**Файл:** `.env` на препрод VPS (автоматически генерируется через `scripts/generate-preprod-env.sh`)

```env
# Pre-Production настройки
DEBUG=False
SECRET_KEY=<сгенерированный ключ>
ALLOWED_HOSTS=<IP препрод VPS>

# Docker service names (как в production)
POSTGRES_HOST=db
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0

# Pre-Production credentials
POSTGRES_PASSWORD=<безопасный пароль>
STRIPE_SECRET_KEY=sk_test_<тестовый ключ>  # TEST keys!
STRIPE_PUBLISHABLE_KEY=pk_test_<тестовый ключ>
```

### Gitflow Workflow для Pre-Production:

```bash
# 1. Создание release ветки из develop
git checkout -b release/v1.0 develop
git push origin release/v1.0

# 2. CI/CD автоматически:
#    - Запускает тесты (283 теста)
#    - Code quality проверки (ruff, mypy, black, isort, flake8)
#    - Собирает Docker образ (preprod-latest)
#    - Деплоит на preprod VPS
#    - Проверяет health check
#    - Создаёт draft PR: release/v1.0 → main

# 3. Тестирование на препроде
# Открыть http://<PREPROD_IP>/api/ (через Nginx на порту 80)

# 4. Если всё ОК — merge в main через PR
# Или через CLI:
git checkout main
git merge release/v1.0
git push origin main
# → Автоматический production deployment
```

### Deployment через GitHub Actions (release/* branches):
```yaml
# Автоматический workflow при push в release/*:
1. Push в release/* → Trigger CI/CD
2. Запуск тестов (283 теста)
3. Code quality проверки (ruff, mypy, black, isort, flake8)
4. Сборка Docker образа с тегом preprod-latest
5. Push в GitHub Container Registry (GHCR)
6. Deployment на препрод VPS:
   - Копирование nginx.conf и docker-compose.prod.yml
   - Генерация .env через generate-preprod-env.sh
   - Pull образа ghcr.io/${REPO}:preprod-latest
   - docker compose -f docker-compose.prod.yml up -d (6 сервисов)
   - Health checks через Nginx на PREPROD_SERVER_IP:80
7. Автоматическое создание draft PR: release/* → main
```

### GitHub Secrets для препрода:
```
PREPROD_SERVER_IP         - IP адрес препрод сервера
PREPROD_SSH_USER          - SSH пользователь
PREPROD_SSH_KEY           - Приватный SSH ключ
PREPROD_DEPLOY_DIR        - Директория деплоя (/opt/lms-preprod)
PREPROD_STRIPE_SECRET_KEY - Stripe TEST secret key
PREPROD_STRIPE_PUBLISHABLE_KEY - Stripe TEST publishable key
```

### Особенности:
- ✅ **Изоляция от production** — отдельный VPS, БД, secrets
- ✅ **Полный CI/CD тест** — все этапы как в production
- ✅ **Stripe TEST keys** — безопасное тестирование платежей
- ✅ **preprod-latest tag** — отдельный Docker образ для препрода
- ✅ **Gunicorn** — реальный production сервер
- ✅ **DEBUG=False** — production настройки
- ✅ **Auto-restart** — `restart: unless-stopped`
- ✅ **Zero-configuration VPS** — автоматическая установка Docker и зависимостей
- ✅ **Automatic PR creation** — draft PR создаётся после успешного preprod deployment

### Gitflow Workflow (полный цикл):
```
feature/* → develop (разработка)
              ↓
develop → release/v1.0 (создание релиза)
              ↓
          deploy-preprod → Препрод VPS
              ↓
       Тестирование + Автоматический draft PR
              ↓
release/v1.0 → main (ручной merge после тестирования)
              ↓
          deploy-prod → Production VPS
              ↓
release/v1.0 → develop (backmerge изменений)
```

### Когда использовать:
- После завершения фичи перед merge в main
- Для тестирования критичных изменений
- Проверка deployment процесса
- Валидация Stripe интеграции с TEST keys
- QA тестирование в production-подобной среде

---

## 4. Production VPS (Deployment)

### Назначение:
- Финальное окружение для реальных пользователей
- Высокая доступность и стабильность
- Автоматический deployment через CI/CD

### Технологии:
- **Окружение:** Docker на VPS (Ubuntu/Debian)
- **Изоляция:** Docker контейнеры (docker-compose)
- **БД:** PostgreSQL 16 в Docker
- **Redis:** Redis 7 в Docker
- **Reverse Proxy:** Nginx:alpine (порты 80/443, статика + SSL)
- **Сервер:** Gunicorn (4 workers, internal порт 8000)
- **Архитектура:** Client → Nginx:80/443 → Gunicorn:8000

### Конфигурация:
**Файл:** `.env` на VPS сервере (автоматически генерируется через `scripts/generate-production-env.sh`)

```env
# Production настройки
DEBUG=False
SECRET_KEY=<сгенерированный ключ>
ALLOWED_HOSTS=<IP адрес VPS>

# Docker service names (как в staging)
POSTGRES_HOST=db
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0

# Production credentials
POSTGRES_PASSWORD=<безопасный пароль>
STRIPE_SECRET_KEY=sk_live_<production key>

# Security (если есть SSL)
# SECURE_SSL_REDIRECT=True
# SECURE_HSTS_SECONDS=31536000
```

### Файлы:
- `docker-compose.prod.yml` — production конфигурация
- `scripts/generate-production-env.sh` — автогенерация `.env` с секретами

### Deployment через GitHub Actions:
```yaml
# Автоматический workflow:
1. Push в main → Trigger CI/CD
2. Запуск тестов (283 теста)
3. Code quality проверки (ruff, mypy, black)
4. Сборка Docker образа
5. Push в GitHub Container Registry (GHCR)
6. Deployment на VPS:
   - Копирование nginx.conf и docker-compose.prod.yml
   - Генерация .env через generate-production-env.sh
   - Pull образа из GHCR
   - docker compose -f docker-compose.prod.yml up -d (6 сервисов)
   - Health checks через Nginx на SERVER_IP:80
```

### Особенности:
- ✅ **Nginx** — reverse proxy для статики (80/443) и проксирования на Gunicorn
- ✅ **Gunicorn** — production-ready WSGI сервер (4 workers, internal 8000)
- ✅ **DEBUG=False** — отключена отладка
- ✅ **Образ из GHCR** — `ghcr.io/${GITHUB_REPOSITORY}:${IMAGE_TAG}`
- ✅ **Named volumes** — `staticfiles_data`, `media_data`, `logs_data` для persistence
- ✅ **Health checks** — автоматическая проверка работоспособности через Nginx
- ✅ **Auto-restart** — `restart: unless-stopped`
- ✅ **Zero-configuration VPS** — автоматическая установка Docker и зависимостей

### Zero-Configuration VPS Setup:

CI/CD pipeline автоматически настраивает чистый VPS при первом деплое:

**Что устанавливается автоматически:**
1. **Docker CE** — если не установлен, добавляется официальный репозиторий и устанавливается
2. **Docker Compose v2** — plugin для `docker compose` команды
3. **Deployment директория** — `/opt/lms` с правильными правами доступа
4. **Docker named volumes** — `staticfiles_data`, `media_data`, `logs_data` (управляются автоматически)

**Идемпотентность:**
- Скрипт проверяет наличие зависимостей перед установкой
- Повторные запуски не дублируют установку
- Первый деплой: ~2-3 минуты (установка Docker)
- Последующие деплои: ~30-60 секунд (только pull + restart)

**Требования к VPS:**
- Ubuntu 20.04/22.04 или Debian 11/12
- SSH доступ с публичным ключом
- `sudo` права для пользователя
- Минимум 1GB RAM, 10GB диск

**Ручная настройка (единоразово):**
1. Создать VPS с Ubuntu
2. Добавить SSH публичный ключ
3. Настроить GitHub Secrets (SSH_KEY, SSH_USER, SERVER_IP, etc.)

**После этого всё автоматически** при `git push origin main` 🚀

### Когда происходит:
- Автоматически при merge в `main`
- Через GitHub Actions CI/CD pipeline
- После успешного прохождения тестов

---

## Сравнение окружений

| Параметр | Development | Staging | Pre-Production | Production |
|----------|-------------|---------|----------------|------------|
| **Примеры** | Replit, VSCode, PyCharm | Windows/Mac/Linux + Docker | Ubuntu VPS (release/*) | Ubuntu VPS (main) |
| **Docker** | ❌ Нет (опционально) | ✅ Да | ✅ Да | ✅ Да |
| **Хосты БД/Redis** | localhost | db, redis | db, redis | db, redis |
| **Live reload** | ✅ Да | ✅ Да | ❌ Нет | ❌ Нет |
| **DEBUG** | True | True | False | False |
| **Сервер** | runserver | runserver | Nginx→Gunicorn | Nginx→Gunicorn |
| **Порт** | 5000 (пример) | 8000 | 80 (Nginx)→8000 | 80/443→8000 |
| **Docker tag** | N/A | local build | preprod-latest | latest |
| **Сборка образа** | N/A | Локальная (build: .) | GHCR pull | GHCR pull |
| **Stripe keys** | TEST | TEST | TEST | LIVE |
| **CI/CD** | ❌ Нет | ❌ Нет | ✅ Да (release/*) | ✅ Да (main) |
| **.env файл** | .env.example | .env.docker.example | generate-preprod-env.sh | generate-production-env.sh |
| **Celery** | Локальный или Docker | Docker контейнер | Docker контейнер | Docker контейнер |
| **Volumes** | Локальные файлы | Именованные volumes | Named volumes | Named volumes |
| **Назначение** | Разработка | Локальный Docker тест | Препрод тест CI/CD | Финальный релиз |

---

## Философия: Staging vs Production

Понимание разницы между staging (локальная тестовая среда) и production (VPS) критично для эффективной работы с Docker окружениями.

### Staging (docker-compose.yml)
**На локальной машине (Windows/Mac/Linux):**

- 📦 **Локальная сборка:** `build: .` — Docker собирает образ из Dockerfile на вашей машине
- 🔄 **Live reload:** Volume mounting (`.:/app`) позволяет менять код без пересборки
- 🛠️ **Изменяемость:** Вы можете экспериментировать с Dockerfile, зависимостями, конфигурацией
- 🚀 **Цель:** Быстрая итерация, тестирование Docker setup перед production

**Пример docker-compose.yml:**
```yaml
# docker-compose.yml (staging)
web:
  build:  # ← Локальная сборка
    context: .
    dockerfile: Dockerfile
  volumes:
    - .:/app  # ← Live reload
  command: python manage.py runserver 0.0.0.0:8000
```

### Production (docker-compose.prod.yml)
**На VPS через GitHub Actions:**

- 📥 **Pull готовых образов:** `image: ghcr.io/${GITHUB_REPOSITORY}:latest`
- 🏭 **Собранные в CI/CD:** GitHub Actions собирает образ и публикует в GHCR
- 🔒 **Неизменяемость:** Production использует только протестированные образы
- ⚡ **Скорость:** Нет сборки на сервере — только pull и запуск

**Пример docker-compose.prod.yml:**
```yaml
# docker-compose.prod.yml
web:
  image: ghcr.io/${GITHUB_REPOSITORY}:${IMAGE_TAG:-latest}  # ← Pull из GHCR
  # Нет build секции!
  command: gunicorn config.wsgi:application --workers 4 --bind 0.0.0.0:8000
```

### Pipeline Flow

```
1. Разработка в среде разработки (Replit/VSCode/локально)
   ↓
2. git push → GitHub
   ↓
3. GitHub Actions (только для main branch):
   - Запускает тесты (283 теста)
   - Собирает Docker образ
   - Публикует в GHCR (ghcr.io/username/repo:latest)
   ↓
4. GitHub Actions → SSH на VPS:
   - docker pull ghcr.io/username/repo:latest
   - docker compose -f docker-compose.prod.yml up -d
   ↓
5. Production работает на готовых образах ✅
```

### Ключевые преимущества

**Staging (локальная сборка):**
- ✅ Эксперименты с зависимостями
- ✅ Отладка Dockerfile
- ✅ Тестирование миграций
- ✅ Live reload для быстрых правок

**Production (GHCR образы):**
- ✅ Быстрый deployment (нет сборки на VPS)
- ✅ Идентичность с тестами в CI/CD
- ✅ Версионирование через image tags
- ✅ Rollback через предыдущие теги

**Вы можете свободно менять Dockerfile локально, тестировать через `docker compose up --build`, а когда все работает — пушить в main, и GitHub Actions соберет production образ автоматически!** 🚀

---

## Автогенерация .env в Production

### Концепция

Production окружение требует множество секретных ключей и конфигурационных переменных. Вместо ручного создания `.env` файла, используется **автоматическая генерация** через скрипт `scripts/generate-production-env.sh`.

### Как работает

GitHub Actions автоматически:
1. Копирует скрипт на VPS
2. Запускает его с передачей GitHub Secrets
3. Скрипт генерирует `.env` с ~25 переменными
4. Docker Compose использует `.env` при запуске

### Стратегия секретов

| Категория | Источник | Примеры |
|-----------|----------|---------|
| **Автогенерация** | Python/OpenSSL на VPS | `SECRET_KEY`, `POSTGRES_PASSWORD` |
| **GitHub Secrets** | Ручной ввод в GitHub | `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY` |
| **Динамические** | Из GitHub Secrets | `ALLOWED_HOSTS` (← `SERVER_IP`) |
| **Фиксированные** | Константы | `DEBUG=False`, `POSTGRES_HOST=db` |

### Автогенерируемые секреты

```bash
# SECRET_KEY (Django)
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
# Результат: 50 символов, URL-safe, БЕЗ $ символа

# POSTGRES_PASSWORD
POSTGRES_PASSWORD=$(openssl rand -base64 24)
# Результат: 24 байта в base64 кодировке
```

### Секреты из GitHub

Добавляются вручную в GitHub Repository Secrets:

```
GitHub → Settings → Secrets and variables → Actions → New repository secret
```

**Обязательные:**
- `PROD_STRIPE_SECRET_KEY` — Stripe secret key (sk_live_...)
- `PROD_STRIPE_PUBLISHABLE_KEY` — Stripe publishable key (pk_live_...)
- `SERVER_IP` — IP адрес VPS (используется для ALLOWED_HOSTS, SITE_DOMAIN, CORS)
- `SSH_KEY`, `SSH_USER`, `DEPLOY_DIR` — для SSH доступа

**Опциональные:**
- `PROD_EMAIL_HOST_USER` — для реальной email отправки
- `PROD_EMAIL_HOST_PASSWORD` — SMTP пароль

📖 **Подробнее:** см. [GITHUB_SECRETS.md](./GITHUB_SECRETS.md)

### Идемпотентность

**Критично:** Скрипт НЕ перезаписывает существующий `.env`!

```bash
if [ -f ".env" ]; then
    echo "✓ .env already exists. Skipping generation."
    exit 0
fi
```

**Зачем:**
- Сохранение секретов между деплоями
- Защита от случайного сброса конфигурации
- Возможность ручных правок на VPS

**Если нужна пересоздание:**
```bash
# На VPS удалить .env вручную
ssh user@vps-ip "rm /opt/lms/.env"

# Запустить деплой заново
git commit --allow-empty -m "Regenerate .env"
git push origin main
```

### Итоговый .env файл

Автоматически генерируется ~25 переменных:

```env
# Автогенерация
SECRET_KEY=<50 chars URL-safe>
POSTGRES_PASSWORD=<24 bytes base64>

# Из GitHub Secrets
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
ALLOWED_HOSTS=123.45.67.89,localhost,127.0.0.1
SITE_DOMAIN=123.45.67.89:8000

# Фиксированные
DEBUG=False
POSTGRES_HOST=db
REDIS_URL=redis://redis:6379/0
...
```

### Преимущества подхода

| Традиционный способ | Автогенерация |
|---------------------|---------------|
| ❌ Ручное создание .env | ✅ Автоматическая генерация |
| ❌ Риск ошибок при копировании | ✅ Валидация обязательных параметров |
| ❌ Секреты в документации/чатах | ✅ Секреты только в GitHub Secrets |
| ❌ Сложность настройки | ✅ Один git push → готово |
| ❌ Разные .env на разных серверах | ✅ Консистентная конфигурация |

---

## Workflow: Полный цикл разработки

### Шаг 1: Разработка в среде разработки (Development)

```bash
# 1. Создаём .env из шаблона
cp .env.example .env

# 2. Пишем код, тесты
# 3. Запускаем локально
poetry run python manage.py runserver 0.0.0.0:5000

# 4. Тестируем
poetry run python manage.py test
poetry run pytest

# 5. Code quality
poetry run fix   # автоисправление
poetry run check # проверка
```

### Шаг 2: Тестирование в staging среде (локальная машина + Docker)

```powershell
# 1. Скопировать проект на локальную машину (если нужно)
git pull origin feature/your-branch

# 2. Создать .env для staging
copy .env.docker.example .env

# 3. Запустить Docker стек
docker compose up -d

# 4. Проверить логи
docker compose logs -f

# 5. Протестировать в браузере
# http://localhost:5000/api/

# 6. Запустить тесты в контейнере
docker compose exec web bash -c "coverage run --source='users,lms,config' manage.py test && coverage run --append --source='users,lms,config' -m pytest --no-cov && coverage report"

# 7. Code quality проверки
docker compose exec web bash scripts/unix/check.sh

# 8. Проверить что Replit-файлы исключены
docker compose exec web ls -la /app | grep replit
# Не должно быть вывода

# 9. Cleanup
docker compose down
```

### Шаг 3: Push и CI/CD

```bash
# 1. Коммит изменений
git add .
git commit -m "feat: your feature description"

# 2. Push в feature ветку
git push origin feature/your-branch

# 3. Создать Pull Request на GitHub

# 4. GitHub Actions автоматически:
#    - Запустит тесты (283 теста)
#    - Проверит code quality
#    - Соберёт Docker образ (если merge в main)

# 5. Merge в main (после code review)
```

### Шаг 4: Автоматический Deployment на VPS

```yaml
# GitHub Actions автоматически выполнит:

1. Build & Push:
   - Сборка Docker образа
   - Push в ghcr.io/username/repo:latest

2. Deploy:
   - SSH на VPS сервер
   - Копирование docker-compose.prod.yml
   - Pull образа из GHCR
   - docker compose -f docker-compose.prod.yml up -d
   - Health checks

3. Проверка:
   - Все сервисы в статусе "healthy"
   - API доступен: http://VPS_IP/api/ (через Nginx на порту 80)
```

---

## Ключевые отличия в конфигурации

### .env.example (Development)
**Пример: Replit, VSCode, локальная разработка**
```env
POSTGRES_HOST=localhost        # ← Локальная БД
REDIS_URL=redis://localhost:6379/0
DEBUG=True
SITE_DOMAIN=localhost:5000     # ← Порт 5000 (пример для Replit)
```

### .env.docker.example (Staging)
```env
POSTGRES_HOST=db               # ← Docker service name
REDIS_URL=redis://redis:6379/0
DEBUG=True
SITE_DOMAIN=localhost:8000     # ← Порт 8000 (Docker staging)
```

### Production .env (VPS) — автогенерация
**Создаётся автоматически через `scripts/generate-production-env.sh` в GitHub Actions:**
```env
DEBUG=False                    # ← Production режим
POSTGRES_HOST=db               # ← Docker service name
REDIS_URL=redis://redis:6379/0
SITE_DOMAIN=123.45.67.89       # ← IP VPS из GitHub Secrets (Nginx на порту 80)
SECRET_KEY=<автогенерируется>  # ← Python secrets.token_urlsafe(50)
POSTGRES_PASSWORD=<автогенерируется>  # ← openssl rand -base64 24
STRIPE_SECRET_KEY=<из GitHub Secrets>
STRIPE_PUBLISHABLE_KEY=<из GitHub Secrets>
# ... ~25 переменных всего
```
**📋 Полный список:** см. `docs/GITHUB_SECRETS.md`

---

## Частые вопросы

### Q: Зачем нужен промежуточный этап (Staging)?

**A:** Staging окружение решает несколько критических задач:

1. **Проверка Docker сборки** — убедиться что Dockerfile корректный до CI/CD
2. **Тестирование миграций** — проверить миграции БД в контейнерах
3. **Валидация конфигурации** — убедиться что `db`/`redis` хосты работают
4. **Быстрые правки** — live reload для оперативных исправлений
5. **Исключение dev-файлов** — проверить что `.replit`, `.git`, IDE-файлы не попали в образ

### Q: Почему в среде разработки нет Docker?

**A:** Среда разработки может использовать разные подходы к изоляции:
- **Replit**: использует **Nix** вместо Docker (sandboxed cloud environment)
- **VSCode/локально**: может использовать виртуальные окружения (venv, conda)
- **Codespaces**: использует контейнеры GitHub
- Общая черта: локальные сервисы (PostgreSQL, Redis) доступны через localhost
- Docker появляется только на этапе Staging для проверки production-конфигурации

### Q: Как переключаться между окружениями?

**A:**

| Окружение | Действия |
|-----------|----------|
| **Development → Staging** | 1. `git push`<br>2. `git pull` на локальной машине<br>3. `copy .env.docker.example .env`<br>4. `docker compose up -d` |
| **Staging → Production** | 1. `git push origin main`<br>2. GitHub Actions автоматически задеплоит |
| **Production → Staging (rollback test)** | 1. `git checkout main`<br>2. `docker compose up -d` локально<br>3. Тестируйте на staging |

### Q: Что делать если изменения не видны в staging?

**A:** Staging использует **live reload** через volume mounting:

```powershell
# Проверить volume mounting
docker compose ps
docker compose exec web ls -la /app

# Перезапустить web
docker compose restart web

# Проверить логи
docker compose logs -f web
```

### Q: Как протестировать production конфигурацию локально?

**A:** Используйте `docker-compose.prod.yml`:

```powershell
# 1. Создать .env файл вручную или использовать скрипт
# Вариант A: Запустить скрипт генерации (требует переменные окружения)
$env:SERVER_IP="localhost"
$env:STRIPE_SECRET_KEY="sk_test_..."
$env:STRIPE_PUBLISHABLE_KEY="pk_test_..."
bash scripts/generate-production-env.sh

# Вариант B: Скопировать staging шаблон и изменить DEBUG
copy .env.docker.example .env
# Отредактировать .env: установить DEBUG=False

# 2. Собрать образ локально
docker build -t ghcr.io/username/repo:local .

# 3. Установить переменные
$env:GITHUB_REPOSITORY="username/repo"
$env:IMAGE_TAG="local"

# 4. Запустить production-like стек
docker compose -f docker-compose.prod.yml up -d
```

---

## Troubleshooting

### Проблема: Разные хосты в Development и Docker

**Симптомы:**
```
django.db.utils.OperationalError: could not connect to server: Connection refused
```

**Решение:**
- **Development (localhost):** используйте `POSTGRES_HOST=localhost` в `.env`
- **Docker (staging/production):** используйте `POSTGRES_HOST=db` в `.env`

### Проблема: Dev-специфичные файлы попали в Docker образ

**Симптомы:**
```
docker compose exec web ls -la /app | grep -E "replit|\.git"
.replit
replit.nix
replit.md
```

**Решение:**
Проверьте `.dockerignore`:
```dockerignore
# Replit-specific files
.replit
replit.md
replit.nix
```

Пересоберите образ:
```powershell
docker compose down
docker compose up -d --build
```

### Проблема: Миграции не применяются в Docker

**Решение:**
```powershell
# Вручную запустить миграции
docker compose exec web python manage.py migrate

# Проверить состояние миграций
docker compose exec web python manage.py showmigrations
```

### Проблема: Automatic PR creation fails после preprod deployment

**Симптомы:**
- `GitHub Actions is not permitted to create or approve pull requests`
- `Base ref must be a branch` (если используете master вместо main)
- `No commits between main and release/*`
- `Head sha can't be blank`

**Решение:**

1. **Переименуйте master → main:**
   ```bash
   # На GitHub: Settings → Branches → Default branch → Rename: master → main
   
   # Локально:
   git branch -m master main
   git fetch origin
   git branch -u origin/main main
   git remote set-head origin -a
   ```

2. **Включите разрешение для GitHub Actions:**
   - Repository Settings → Actions → General → Workflow permissions
   - ☑️ Allow GitHub Actions to create and approve pull requests

3. **Убедитесь что в workflow есть:**
   ```yaml
   - name: Check out code
     uses: actions/checkout@v4
     with:
       fetch-depth: 0  # Полная история
   
   - name: Fetch main branch for comparison
     run: git fetch origin main:main
   ```

Подробнее см. [CI_CD.md - Troubleshooting: Automatic PR creation fails](./CI_CD.md#проблема-automatic-pr-creation-fails)

---

## Дополнительные ресурсы

- [STAGING_TESTING.md](./STAGING_TESTING.md) — детальные инструкции для локального staging окружения
- [CI_CD.md](./CI_CD.md) — Infrastructure as Code для production deployment
- [DEVELOPMENT.md](../DEVELOPMENT.md) — стандарты разработки
- [docker-compose.yml](../docker-compose.yml) — staging конфигурация
- [docker-compose.prod.yml](../docker-compose.prod.yml) — production конфигурация

---

## Заключение

Четырёхступенчатая стратегия обеспечивает:

1. ✅ **Быструю разработку** в среде разработки без Docker (Development)
2. ✅ **Надёжное тестирование** в staging среде с Docker (Staging)
3. ✅ **Полную валидацию** deployment pipeline перед production (Pre-Production)
4. ✅ **Автоматический deployment** на VPS через Gitflow CI/CD (Production)

Каждое окружение имеет **своё назначение** и **свою конфигурацию**, что позволяет:
- Быстро итерироваться в разработке (feature/* → develop)
- Тщательно проверять в Docker перед деплоем (develop → staging)
- Тестировать полный цикл deployment на preprod VPS (develop → release/*)
- Безопасно развёртывать в production после review (release/* → main)

**Следуйте этой стратегии с Gitflow workflow** чтобы избежать путаницы с окружениями и конфигурациями!
