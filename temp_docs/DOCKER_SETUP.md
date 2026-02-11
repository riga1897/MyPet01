# 🐳 Docker Development Setup

**Версия:** 1.1  
**Последнее обновление:** 23 ноября 2025

## 📋 Содержание

1. [Обзор](#обзор)
2. [Архитектура](#архитектура)
3. [Предварительные требования](#предварительные-требования)
4. [Быстрый старт](#быстрый-старт)
5. [Переменные окружения](#переменные-окружения)
6. [Volumes и персистентность данных](#volumes-и-персистентность-данных)
7. [Проверка работоспособности сервисов](#проверка-работоспособности-сервисов)
8. [Тестирование в Docker](#тестирование-в-docker)
9. [Управление сервисами](#управление-сервисами)
10. [Troubleshooting](#troubleshooting)
11. [Мониторинг и логи](#мониторинг-и-логи)
12. [Production Roadmap](#production-roadmap)

---

## Обзор

Проект LMS использует **Docker Compose** для разработки, обеспечивая изолированное окружение со всеми необходимыми сервисами.

### Ключевые особенности

- **5 сервисов**: Django Web, PostgreSQL, Redis, Celery Worker, Celery Beat
- **Development/Staging конфигурация**: Django runserver, DEBUG=True
- **Единый .env файл**: работает для разных окружений разработки
- **Автоматические миграции**: применяются через entrypoint script
- **Health checks**: мониторинг состояния всех сервисов
- **Named volumes**: персистентность данных PostgreSQL и media файлов

### Когда использовать Docker

✅ **Используйте Docker когда:**
- Работаете в команде (единообразное окружение)
- Тестируете Celery worker и beat локально
- Нужна полная изоляция от системных пакетов
- Подготовка к production deployment

❌ **Используйте разработку вне Docker когда:**
- Быстрая итерация и debugging
- Работаете только с Django (без Celery)
- Ограниченные ресурсы системы

---

## Архитектура

### Диаграмма сервисов

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Network                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Web (Django│    │  PostgreSQL  │    │    Redis     │  │
│  │   runserver) │───▶│   Database   │    │Message Broker│  │
│  │  Port: 8000  │    │  Port: 5433  │    │  Port: 6379  │  │
│  └──────┬───────┘    └──────────────┘    └──────┬───────┘  │
│         │                                         │          │
│         │          ┌──────────────┐              │          │
│         └─────────▶│Celery Worker │◀─────────────┘          │
│                    │ (async tasks)│                          │
│                    └──────┬───────┘                          │
│                           │                                  │
│                    ┌──────▼───────┐                          │
│                    │ Celery Beat  │                          │
│                    │  (scheduler) │                          │
│                    └──────────────┘                          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Описание сервисов

#### 1. **web** — Django Application

- **Образ**: Custom (build from Dockerfile)
- **Команда**: `python manage.py runserver 0.0.0.0:8000`
- **Порт**: `8000:8000`
- **Зависимости**: PostgreSQL (db), Redis
- **Volumes**: `media_volume`, `static_volume`
- **Healthcheck**: HTTP GET `/api/`
- **Entrypoint**: Автоматически применяет миграции и collectstatic

**Особенности:**
- Multi-stage Dockerfile (builder + runtime)
- Non-root пользователь `django`
- Python 3.12 slim base image

#### 2. **db** — PostgreSQL Database

- **Образ**: `postgres:16`
- **Порт**: `5433:5432` (избегание конфликта с локальным PostgreSQL)
- **Volume**: `postgres_data` (персистентное хранилище)
- **Healthcheck**: `pg_isready`
- **Переменные**: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`

**Особенности:**
- Стандартный Debian-based образ для максимальной совместимости
- Health check каждые 10 секунд
- Автоматическое создание базы данных при первом запуске

#### 3. **redis** — Message Broker

- **Образ**: `redis`
- **Порт**: `6379:6379`
- **Healthcheck**: `redis-cli ping`
- **База данных №0**: Celery broker и results

**Особенности:**
- Без персистентности (in-memory)
- Health check через ping
- Используется для Celery и будущего кэширования (база №1)

#### 4. **celery_worker** — Async Task Processor

- **Образ**: Custom (build from Dockerfile)
- **Команда**: `celery -A config worker --loglevel=info`
- **Зависимости**: PostgreSQL, Redis, Web
- **Volume**: `media_volume`
- **Healthcheck**: `celery inspect ping`

**Обрабатывает:**
- Email уведомления об обновлениях курсов
- Stripe webhook события (будущее)
- Асинхронные операции с файлами

#### 5. **celery_beat** — Task Scheduler

- **Образ**: Custom (build from Dockerfile)
- **Команда**: `celery -A config beat --scheduler django_celery_beat.schedulers:DatabaseScheduler`
- **Зависимости**: PostgreSQL, Redis, Web
- **Healthcheck**: Disabled (scheduler doesn't respond to ping)

**Планирует:**
- Блокировка неактивных пользователей (каждые 24 часа)
- Другие периодические задачи из django-celery-beat

---

## Предварительные требования

### Установка Docker

Установите Docker Desktop (Windows/macOS) или Docker Engine (Linux) следуя официальной документации для вашей платформы:

**Docker Desktop (Windows/macOS):**
1. Скачайте [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. Запустите установщик и следуйте инструкциям
3. Перезагрузите систему при необходимости
4. Проверьте установку: `docker --version` и `docker-compose --version`

**Docker Engine (Linux):**
```bash
# Установка Docker Engine (пример для Ubuntu/Debian)
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Проверка установки
docker --version
docker compose version
```

> **Примечание**: Для других дистрибутивов Linux см. [официальную документацию Docker](https://docs.docker.com/engine/install/).

### Минимальные требования

- **RAM**: 4 GB (рекомендуется 8 GB)
- **Disk**: 10 GB свободного места
- **CPU**: 2 cores (рекомендуется 4 cores)

---

## Быстрый старт

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd lms-project
```

### 2. Настройка переменных окружения

```bash
# Скопируйте шаблон .env
cp .env.example .env

# Убедитесь, что настройки указывают на localhost (для разработки вне Docker)
# Docker Compose автоматически переопределит хосты для контейнеров
```

**Важные переменные в .env:**
```env
POSTGRES_HOST=localhost      # Для разработки вне Docker
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 3. Запуск всех сервисов

```bash
# Сборка образов и запуск в фоновом режиме
docker-compose up --build -d

# Просмотр логов
docker-compose logs -f
```

### 4. Первоначальная настройка

```bash
# Применение миграций (автоматически выполняется через entrypoint)
# Но можно запустить вручную:
docker-compose exec web python manage.py migrate

# Загрузка демо-данных
docker-compose exec web python manage.py loaddata lms/fixtures/courses.json
docker-compose exec web python manage.py loaddata lms/fixtures/lessons.json
docker-compose exec web python manage.py loaddata users/fixtures/payments.json

# Создание суперпользователя
docker-compose exec web python manage.py createsuperuser
```

### 5. Проверка работы

Откройте в браузере:
- **API Root**: http://localhost:8000/api/
- **Swagger UI**: http://localhost:8000/api/docs/
- **Django Admin**: http://localhost:8000/admin/

---

## Переменные окружения

### Стратегия конфигурации

Проект использует **двухуровневую систему** переменных окружения:

1. **`.env` файл** — базовые настройки для разработки вне Docker (localhost)
2. **`docker-compose.yaml`** — переопределяет хосты для Docker контейнеров

### Переменные в .env

#### Django Settings
```env
SECRET_KEY=django-insecure-CHANGE-IN-PRODUCTION
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

#### PostgreSQL Database
```env
POSTGRES_DB=lms_db
POSTGRES_USER=lms_user
POSTGRES_PASSWORD=lms_password
POSTGRES_HOST=localhost          # ← для разработки вне Docker
POSTGRES_PORT=5432
```

#### Redis & Celery
```env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

#### Email Settings
```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_NOTIFICATION_COOLDOWN_HOURS=4
```

#### Celery Tasks
```env
INACTIVE_USER_DAYS=30
```

#### Stripe Integration
```env
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
```

### Переопределение в docker-compose.yaml

Docker Compose автоматически переопределяет хосты для контейнеров:

```yaml
environment:
  - POSTGRES_HOST=db                    # ← вместо localhost
  - CELERY_BROKER_URL=redis://redis:6379/0
  - CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### Как это работает

1. **Разработка вне Docker** (нативное окружение):
   - `config/settings.py` читает переменные из `.env`
   - Использует `localhost` для PostgreSQL и Redis

2. **Docker окружение**:
   - Контейнеры читают переменные из `.env` через `env_file`
   - `docker-compose.yaml` переопределяет хосты через `environment` секцию
   - Контейнеры используют Docker DNS: `db`, `redis`

### Приоритет переменных

```
docker-compose.yaml environment > .env > config/settings.py defaults
```

---

## Volumes и персистентность данных

### Named Volumes

Проект использует 3 named volumes для персистентности:

#### 1. `postgres_data`

- **Путь**: `/var/lib/postgresql/data` (внутри контейнера)
- **Содержимое**: База данных PostgreSQL
- **Персистентность**: Данные сохраняются при перезапуске контейнеров

```bash
# Просмотр информации о volume
docker volume inspect lms-project_postgres_data

# Backup базы данных
docker-compose exec db pg_dump -U lms_user lms_db > backup.sql

# Restore базы данных
docker-compose exec -T db psql -U lms_user lms_db < backup.sql
```

#### 2. `media_volume`

- **Путь**: `/app/media` (внутри контейнера)
- **Содержимое**: Загруженные файлы (превью курсов/уроков)
- **Доступ**: web, celery_worker

```bash
# Копирование файлов из volume
docker cp lms_web:/app/media ./media_backup

# Копирование файлов в volume
docker cp ./media_backup lms_web:/app/media
```

#### 3. `static_volume`

- **Путь**: `/app/static` (внутри контейнера)
- **Содержимое**: Собранные статические файлы (CSS, JS, images)
- **Генерация**: `python manage.py collectstatic`

### Управление Volumes

```bash
# Список всех volumes
docker volume ls

# Детальная информация
docker volume inspect lms-project_postgres_data

# Удаление volumes (ОСТОРОЖНО: удалит все данные!)
docker-compose down -v

# Очистка неиспользуемых volumes
docker volume prune
```

### Backup стратегия

**Рекомендуемый workflow:**

1. **Регулярный backup БД**:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T db pg_dump -U lms_user lms_db | gzip > backups/db_$DATE.sql.gz
```

2. **Backup media файлов**:
```bash
docker cp lms_web:/app/media ./backups/media_$DATE
```

3. **Версионирование fixtures**:
```bash
docker-compose exec web python manage.py dumpdata lms --indent 2 > backups/lms_$DATE.json
```

---

## Проверка работоспособности сервисов

### 1. PostgreSQL Database

```bash
# Проверка статуса контейнера
docker-compose ps db

# Подключение к БД
docker-compose exec db psql -U lms_user -d lms_db

# Список таблиц
docker-compose exec db psql -U lms_user -d lms_db -c "\dt"

# Проверка логов
docker-compose logs db
```

**Критерии успеха:**
- ✅ Контейнер в статусе `Up (healthy)`
- ✅ Таблицы Django созданы
- ✅ Нет ошибок в логах

### 2. Redis Message Broker

```bash
# Проверка статуса
docker-compose ps redis

# Ping тест
docker-compose exec redis redis-cli ping

# Проверка активных подключений
docker-compose exec redis redis-cli CLIENT LIST

# Мониторинг команд в реальном времени
docker-compose exec redis redis-cli MONITOR
```

**Критерии успеха:**
- ✅ Контейнер в статусе `Up (healthy)`
- ✅ Команда `ping` возвращает `PONG`
- ✅ Redis принимает подключения от Celery

### 3. Django Web Application

```bash
# Проверка статуса
docker-compose ps web

# HTTP запрос к API
curl http://localhost:8000/api/

# Проверка логов запросов
docker-compose logs -f web

# Проверка применения миграций
docker-compose exec web python manage.py showmigrations
```

**Критерии успеха:**
- ✅ Контейнер в статусе `Up`
- ✅ API возвращает JSON response
- ✅ Все миграции применены (показаны `[X]`)
- ✅ Статические файлы собраны

**Endpoints для проверки:**
- http://localhost:8000/api/ — API Root
- http://localhost:8000/api/docs/ — Swagger UI
- http://localhost:8000/admin/ — Django Admin
- http://localhost:8000/api/users/ — Users API
- http://localhost:8000/api/courses/ — Courses API

### 4. Celery Worker

```bash
# Проверка статуса
docker-compose ps celery_worker

# Проверка активных worker'ов
docker-compose exec celery_worker celery -A config inspect active

# Список зарегистрированных задач
docker-compose exec celery_worker celery -A config inspect registered

# Проверка логов
docker-compose logs -f celery_worker
```

**Критерии успеха:**
- ✅ Контейнер в статусе `Up (healthy)`
- ✅ Worker зарегистрирован и активен
- ✅ Задачи `lms.tasks.send_course_update_email` зарегистрированы
- ✅ Нет ошибок подключения к Redis

### 5. Celery Beat

```bash
# Проверка статуса
docker-compose ps celery_beat

# Проверка логов (должен показывать расписание задач)
docker-compose logs celery_beat | grep "Scheduler"

# Проверка расписания задач
docker-compose exec web python manage.py shell
>>> from django_celery_beat.models import PeriodicTask
>>> PeriodicTask.objects.all()
```

**Критерии успеха:**
- ✅ Контейнер в статусе `Up`
- ✅ Логи показывают загруженное расписание
- ✅ Периодические задачи запланированы в БД

### Комплексная проверка

```bash
# Проверка всех контейнеров
docker-compose ps

# Ожидаемый вывод:
# lms_postgres       Up (healthy)
# lms_redis          Up (healthy)
# lms_web            Up (healthy)
# lms_celery_worker  Up (healthy)
# lms_celery_beat    Up

# Проверка сетевого взаимодействия
docker-compose exec web python manage.py check --deploy

# Healthcheck всех сервисов
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
```

---

## Тестирование в Docker

### Запуск всех тестов

**Вариант 1: Прямой запуск (рекомендуется для Docker)**
```bash
# Django APITestCase тесты (78 tests)
docker-compose exec web python manage.py test

# Pytest тесты (187 tests)
docker-compose exec web pytest

# Все тесты с coverage (265 tests total)
docker-compose exec web bash -c "
  coverage run --source='users,lms,config' manage.py test && \
  coverage run --append --source='users,lms,config' -m pytest --no-cov && \
  coverage report
"
```

**Вариант 2: Через Poetry (для соответствия локальному workflow)**
```bash
# Django APITestCase тесты (78 tests)
docker-compose exec web poetry run python manage.py test

# Pytest тесты (187 tests)
docker-compose exec web poetry run pytest --no-cov

# Скрипты Poetry для code quality
docker-compose exec web poetry run fix   # Автоформатирование
docker-compose exec web poetry run check # Полная проверка кода
```

**Примечание:** 
- Poetry доступен в runtime контейнере для поддержки dev workflow
- Флаг `--no-cov` отключает pytest-cov для избежания конфликта с coverage.py
- Pytest cache хранится в `/tmp/.pytest_cache` (не засоряет проект, автоочистка при перезапуске)

**Ожидаемый результат:**
```
Tests: 265 passed
Coverage: 98.22%
```

### Использование скрипта

```bash
# Unix (внутри контейнера)
docker-compose exec web ./scripts/unix/test_all.sh

# Результат будет включать:
# - Django tests
# - Pytest tests
# - Combined coverage report
```

### Тестирование отдельных компонентов

```bash
# Только API тесты
docker-compose exec web python manage.py test lms.tests users.tests

# Только Celery тесты
docker-compose exec web pytest tests/test_celery_tasks.py -v

# Только Service Layer тесты
docker-compose exec web pytest tests/test_services.py -v

# Тесты с подробным выводом
docker-compose exec web pytest -v --tb=short
```

### CI/CD интеграция

```yaml
# Пример для GitHub Actions
- name: Run tests in Docker
  run: |
    docker-compose up -d
    docker-compose exec -T web python manage.py test
    docker-compose exec -T web pytest
    docker-compose down
```

---

## Управление сервисами

### Основные команды

```bash
# Запуск всех сервисов
docker-compose up -d

# Запуск с live логами
docker-compose up

# Остановка всех сервисов
docker-compose down

# Остановка с удалением volumes (ОСТОРОЖНО!)
docker-compose down -v

# Перезапуск всех сервисов
docker-compose restart

# Перезапуск одного сервиса
docker-compose restart web
```

### Rebuild образов

```bash
# Пересборка после изменения Dockerfile или зависимостей
docker-compose up --build

# Принудительная пересборка без cache
docker-compose build --no-cache

# Пересборка только одного сервиса
docker-compose build web
```

### Масштабирование

```bash
# Запуск нескольких worker'ов
docker-compose up -d --scale celery_worker=3

# Проверка
docker-compose exec celery_worker celery -A config inspect active
```

### Выполнение команд

```bash
# Интерактивная shell
docker-compose exec web python manage.py shell

# Создание миграций
docker-compose exec web python manage.py makemigrations

# Применение миграций
docker-compose exec web python manage.py migrate

# Создание суперпользователя
docker-compose exec web python manage.py createsuperuser

# Произвольная команда
docker-compose exec web python manage.py <command>
```

### Доступ к shell контейнера

```bash
# Bash в web контейнере
docker-compose exec web bash

# Bash в db контейнере
docker-compose exec db bash

# PostgreSQL console
docker-compose exec db psql -U lms_user -d lms_db

# Redis CLI
docker-compose exec redis redis-cli
```

---

## Troubleshooting

### Проблема: Контейнеры не запускаются

**Симптомы:**
```bash
docker-compose up -d
# ERROR: ... port is already allocated
```

**Решение:**
```bash
# Проверка занятых портов
lsof -i :8000
lsof -i :5433
lsof -i :6379

# Остановка конфликтующих процессов
kill -9 <PID>

# Или изменить порты в docker-compose.yaml
ports:
  - "8001:8000"  # Вместо 8000:8000
```

---

### Проблема: База данных не доступна

**Симптомы:**
```
django.db.utils.OperationalError: could not connect to server
```

**Решение:**
```bash
# 1. Проверка статуса БД
docker-compose ps db

# 2. Проверка логов
docker-compose logs db

# 3. Проверка healthcheck
docker inspect lms_postgres | grep -A 10 Health

# 4. Перезапуск БД
docker-compose restart db

# 5. Проверка переменных окружения
docker-compose exec web env | grep POSTGRES
```

---

### Проблема: Миграции не применяются

**Симптомы:**
```
You have 42 unapplied migration(s)
```

**Решение:**
```bash
# 1. Ручное применение миграций
docker-compose exec web python manage.py migrate

# 2. Проверка статуса миграций
docker-compose exec web python manage.py showmigrations

# 3. Фиктивное применение (если миграции уже применены)
docker-compose exec web python manage.py migrate --fake

# 4. Сброс миграций (ОСТОРОЖНО!)
docker-compose down -v
docker-compose up -d
docker-compose exec web python manage.py migrate
```

---

### Проблема: Celery задачи не выполняются

**Симптомы:**
```
Task lms.tasks.send_course_update_email received but not executed
```

**Решение:**
```bash
# 1. Проверка worker'а
docker-compose logs celery_worker

# 2. Проверка подключения к Redis
docker-compose exec celery_worker redis-cli -h redis ping

# 3. Проверка зарегистрированных задач
docker-compose exec celery_worker celery -A config inspect registered

# 4. Ручной запуск задачи для отладки
docker-compose exec web python manage.py shell
>>> from lms.tasks import send_course_update_email
>>> send_course_update_email.delay(course_id=1)

# 5. Перезапуск worker'а
docker-compose restart celery_worker
```

---

### Проблема: Медленная работа Docker

**Симптомы:**
- Долгая сборка образов
- Медленные I/O операции

**Решение:**
```bash
# 1. Выделить больше ресурсов в Docker Desktop
# Settings → Resources → Adjust CPU/Memory

# 2. Для Windows: включить WSL 2 backend
# Settings → General → Use WSL 2 based engine

# 3. Исключить volumes из антивирусного сканирования
# Добавить Docker volumes в исключения

# 4. Использовать Docker volumes вместо bind mounts
# (уже реализовано в проекте)

# 5. Для Linux: проверить disk I/O
# Использовать overlay2 storage driver (по умолчанию)
```

---

### Проблема: Ошибка "No space left on device"

**Решение:**
```bash
# 1. Очистка неиспользуемых образов
docker system prune -a

# 2. Очистка volumes
docker volume prune

# 3. Очистка всего (ОСТОРОЖНО!)
docker system prune -a --volumes

# 4. Проверка использования места
docker system df
```

---

### Проблема: Изменения в коде не применяются

**Симптомы:**
- Код изменен, но контейнер использует старую версию

**Решение:**
```bash
# 1. Пересборка образа (не используем bind mounts)
docker-compose up --build

# 2. Полная пересборка без cache
docker-compose build --no-cache web

# 3. Перезапуск контейнера
docker-compose restart web

# 4. Проверка, что код скопирован
docker-compose exec web ls -la /app
```

---

## Мониторинг и логи

### Просмотр логов

```bash
# Все сервисы
docker-compose logs

# Следить за логами в реальном времени
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs web
docker-compose logs celery_worker

# Последние N строк
docker-compose logs --tail=100 web

# Логи с временными метками
docker-compose logs -t web
```

### Мониторинг ресурсов

```bash
# Использование ресурсов всех контейнеров
docker stats

# Использование ресурсов конкретного контейнера
docker stats lms_web

# Детальная информация
docker inspect lms_web
```

### Health Status

```bash
# Статус всех контейнеров
docker-compose ps

# Только health status
docker ps --format "table {{.Names}}\t{{.Status}}"

# Healthcheck конкретного контейнера
docker inspect --format='{{json .State.Health}}' lms_web | jq
```

### Экспорт логов

```bash
# Сохранение логов в файл
docker-compose logs > logs/docker-compose-$(date +%Y%m%d).log

# Логи за последний час
docker-compose logs --since 1h > logs/recent.log

# Логи с фильтрацией по уровню (ERROR)
docker-compose logs | grep ERROR > logs/errors.log
```

---

## 🧪 Тестирование в Docker

### Обзор стратегии тестирования

Проект использует **гибридную стратегию** тестирования для оптимального баланса между скоростью разработки и надёжностью:

- **Development (нативное окружение)**: `poetry run pytest` вне Docker — быстрая итерация, мгновенная обратная связь
- **CI/CD pipeline**: `poetry run pytest` в runner (без Docker) — простота и скорость
- **Staging/Docker**: финальная проверка совместимости окружения перед deployment

**Статистика тестов:**
- **Django APITestCase**: 78 тестов (`lms/tests.py`, `users/tests.py`)
- **Pytest**: 187 тестов (`tests/` папка)
- **Всего**: 265 тестов с покрытием 98.22%

### Проблемы с правами при bind mount

При запуске pytest в Docker могут возникать ошибки прав доступа:

```
PermissionError: [Errno 13] Permission denied: '.pytest_cache'
PermissionError: [Errno 13] Permission denied: '.coverage'
PermissionError: [Errno 13] Permission denied: 'htmlcov'
```

**Причина**: Bind mount (`.:/app`) может монтировать файлы с правами хост-системы, из-за чего пользователь `django` в контейнере не может создавать файлы в `/app`.

**Решение**: Pytest и coverage настроены на использование `/tmp` директории (доступна для записи всем пользователям):

```toml
# pyproject.toml
[tool.pytest.ini_options]
cache_dir = "/tmp/.pytest_cache"

[tool.coverage.run]
data_file = "/tmp/.coverage"

[tool.coverage.html]
directory = "/tmp/htmlcov"
```

> **Примечание**: Эти настройки работают на всех платформах (Linux, macOS, Windows).

### Особенности .dockerignore

Папка `tests/` по умолчанию закомментирована в `.dockerignore` для поддержки тестирования в Docker:

```dockerignore
# Testing
.coverage
.pytest_cache/
htmlcov/
.tox/
# tests/           # ← Закомментировано для работы pytest в Docker
*.test.py
```

Если вы **не планируете** запускать тесты в Docker, можете раскомментировать `tests/` для оптимизации размера образа.

### Запуск тестов в Docker

#### Django APITestCase (78 тестов)

```bash
# Полный запуск
docker-compose exec web poetry run python manage.py test

# С coverage
docker-compose exec web poetry run coverage run --source='users,lms,config' manage.py test
docker-compose exec web poetry run coverage report
```

**Результат:**
```
Found 78 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
...............................................................................
----------------------------------------------------------------------
Ran 78 tests in ~90s

OK
```

#### Pytest (187 тестов)

```bash
# Полный запуск
docker-compose exec web poetry run pytest

# Без coverage отчёта (быстрее)
docker-compose exec web poetry run pytest --no-cov

# Конкретный файл
docker-compose exec web poetry run pytest tests/lms/test_services.py

# С фильтром по имени
docker-compose exec web poetry run pytest -k "test_stripe"
```

**Результат:**
```
platform linux -- Python 3.12.12, pytest-8.4.2, pluggy-1.6.0
cachedir: /tmp/.pytest_cache
collected 187 items

tests/lms/test_models.py ........................  [ 12%]
tests/lms/test_serializers.py ...................  [ 23%]
...
================= 187 passed in 45.23s =================
```

#### Объединённый coverage (Django + Pytest)

```bash
# Комплексный отчёт по всем 265 тестам
docker-compose exec web bash -c "coverage run --source='users,lms,config' manage.py test && \
  coverage run --append --source='users,lms,config' -m pytest --no-cov && \
  coverage report"
```

**Результат:**
```
Name                   Stmts   Miss   Cover   Missing
-----------------------------------------------------
config/celery.py           6      0 100.00%
config/urls.py            11      0 100.00%
config/views.py           24      0 100.00%
lms/admin.py              14      0 100.00%
lms/apps.py                4      0 100.00%
lms/constants.py           3      0 100.00%
lms/models.py             43      0 100.00%
lms/paginators.py          5      0 100.00%
lms/serializers.py        27      0 100.00%
lms/services.py           62      0 100.00%
lms/tasks.py               5      0 100.00%
lms/urls.py                7      0 100.00%
lms/validators.py          8      0 100.00%
lms/views.py              62      0 100.00%
users/admin.py            15      0 100.00%
users/apps.py              4      0 100.00%
users/models.py           59      0 100.00%
users/permissions.py      37      0 100.00%
users/serializers.py      62      0 100.00%
users/services.py         71      3  95.77%   277-281
users/tasks.py             5      0 100.00%
users/urls.py              8      0 100.00%
users/views.py            77      8  89.61%   248-253, 291, 295-296
-----------------------------------------------------
TOTAL                    619     11  98.22%
```

### Доступ к coverage отчётам

После запуска тестов с coverage, HTML отчёт генерируется в `/tmp/htmlcov` внутри контейнера.

**Копирование отчёта на хост:**

```bash
# Создать папку для отчётов
mkdir -p coverage-reports

# Скопировать из контейнера
docker cp lms_web:/tmp/htmlcov ./coverage-reports/

# Открыть в браузере (выберите команду для вашей платформы)
# Windows: start coverage-reports/htmlcov/index.html
# macOS: open coverage-reports/htmlcov/index.html
# Linux: xdg-open coverage-reports/htmlcov/index.html
```

### Рекомендации

#### ✅ Development (нативное окружение, рекомендуется для TDD)

```bash
# Быстрая итерация при разработке
poetry run pytest tests/lms/test_services.py -v
poetry run pytest -k "test_create_course" --reuse-db
```

**Преимущества:**
- ⚡ Мгновенный запуск (без overhead Docker)
- 🔧 IDE интеграция (coverage, debugging)
- 🚀 Быстрый TDD цикл (RED-GREEN-REFACTOR)

#### ✅ Staging/Docker (финальная проверка перед коммитом)

```bash
# Полная проверка окружения
docker-compose exec web poetry run pytest
docker-compose exec web poetry run python manage.py test
```

**Преимущества:**
- ✅ 100% идентичность с production окружением
- ✅ Проверка зависимостей и конфигурации
- ✅ Изоляция от локальных настроек

#### ✅ CI/CD (GitHub Actions / GitLab CI)

```yaml
# .github/workflows/test.yml (пример)
- name: Install dependencies
  run: poetry install

- name: Run tests
  run: |
    poetry run python manage.py test
    poetry run pytest --no-cov

- name: Coverage report
  run: |
    coverage run --source='users,lms,config' manage.py test
    coverage run --append --source='users,lms,config' -m pytest --no-cov
    coverage report
```

**Преимущества:**
- ⚡ Быстрее чем Docker build
- 🔄 Простое кэширование зависимостей
- 📊 Легкая интеграция с coverage сервисами

### Troubleshooting

#### Проблема: "No files were found in testpaths"

```
PytestConfigWarning: No files were found in testpaths
```

**Причина**: Папка `tests/` исключена в `.dockerignore`.

**Решение**: Закомментируйте `tests/` в `.dockerignore`:

```dockerignore
# tests/  # ← Закомментировать эту строку
```

Затем пересоздайте контейнер:

```bash
docker-compose down
docker-compose up -d
```

#### Проблема: Permission denied для coverage/cache

```
PermissionError: [Errno 13] Permission denied: '.coverage'
```

**Решение**: Убедитесь что `pyproject.toml` содержит настройки `/tmp`:

```toml
[tool.pytest.ini_options]
cache_dir = "/tmp/.pytest_cache"

[tool.coverage.run]
data_file = "/tmp/.coverage"

[tool.coverage.html]
directory = "/tmp/htmlcov"
```

Перезапустите контейнер после изменений.

#### Проблема: Изменения в pyproject.toml не применяются

**Причина**: Docker может кэшировать bind mount файлы.

**Решение**:

```bash
# Полная перезагрузка контейнеров
docker-compose down
docker-compose up -d

# Проверка что настройки применились
docker-compose exec web grep "cache_dir" pyproject.toml
```

Если проблема сохраняется, перезапустите Docker Desktop (Windows/macOS) или Docker service (Linux).

---

## Production Roadmap

### Текущее состояние: Development Setup

- ✅ Django runserver (port 8000)
- ✅ DEBUG=True
- ✅ Console email backend
- ✅ SQLite для тестов
- ✅ Автоматические миграции через entrypoint

### Планируемые улучшения для Production

#### Phase 1: Application Server

- [ ] Замена runserver на **Gunicorn** WSGI server
- [ ] Настройка workers: `--workers 4 --timeout 120`
- [ ] Graceful reload при deployment
- [ ] Access и error логи

#### Phase 2: Security & Performance

- [ ] DEBUG=False
- [ ] ALLOWED_HOSTS с реальными доменами
- [ ] SECRET_KEY из environment/secrets manager
- [ ] HTTPS через reverse proxy (nginx)
- [ ] Static files через CDN или nginx
- [ ] Database connection pooling

#### Phase 3: Monitoring & Reliability

- [ ] Health check endpoints (/health/, /ready/)
- [ ] Structured logging (JSON format)
- [ ] Prometheus metrics для мониторинга
- [ ] Sentry для error tracking
- [ ] Automated backups (БД + media)

#### Phase 4: Scalability

- [ ] Horizontal scaling: множественные web workers
- [ ] Redis persistence (RDB + AOF)
- [ ] Celery autoscaling
- [ ] Database read replicas
- [ ] Load balancer (nginx/HAProxy)

### Пример production docker-compose.yaml

```yaml
version: '3.8'

services:
  web:
    command: gunicorn config.wsgi:application \
      --bind 0.0.0.0:8000 \
      --workers 4 \
      --timeout 120 \
      --access-logfile - \
      --error-logfile -
    environment:
      - DEBUG=False
      - ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/app/static:ro
    depends_on:
      - web
```

### Checklist для production deployment

- [ ] Переменные окружения через secrets/vault
- [ ] DEBUG=False
- [ ] Реальный SECRET_KEY (минимум 50 символов)
- [ ] ALLOWED_HOSTS настроен
- [ ] CSRF_TRUSTED_ORIGINS настроен
- [ ] CORS настроен для production доменов
- [ ] Stripe production keys
- [ ] SMTP настроен для реальной отправки email
- [ ] PostgreSQL с persistent volume
- [ ] Redis с persistence (если нужно)
- [ ] Backup стратегия
- [ ] Monitoring и alerting
- [ ] SSL сертификаты

---

## Дополнительные ресурсы

### Документация проекта

- [README.md](../README.md) — Основная документация
- [docs/lms_roadmap.md](lms_roadmap.md) — Архитектура и roadmap
- [docs/CELERY_SETUP.md](CELERY_SETUP.md) — Celery & Redis integration
- [docs/STRIPE_INTEGRATION.md](STRIPE_INTEGRATION.md) — Stripe payments
- [docs/QUICK_START_TESTING.md](QUICK_START_TESTING.md) — Testing guide

### Внешние ресурсы

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/configure.html)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [Redis Docker Hub](https://hub.docker.com/_/redis)

---

**Последнее обновление:** 23 ноября 2025  
**Версия документа:** 1.1  
**Статус:** Development/Staging Setup (Production roadmap в планах)
