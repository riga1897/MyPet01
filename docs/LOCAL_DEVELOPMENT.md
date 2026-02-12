# Локальная разработка с Docker

Руководство по запуску MyPet01 в Docker Desktop для локальной разработки и staging-тестирования.

> **Тестирование:** [TESTING.md](TESTING.md)
> **Деплой на VPS:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

## Предварительные требования

Необходимо:
- Docker Desktop (Windows/macOS) или Docker Engine + Docker Compose (Linux)
- Git

Не требуется локально: Python, Poetry, PostgreSQL, Redis — всё внутри контейнера.

```bash
docker --version
docker compose version
git --version
```

---

## Быстрый старт

```bash
git clone <repository-url>
cd MyPet01
cp .env.example .env
docker compose up --build -d
```

Приложение доступно: http://localhost:5000

---

## Файл .env

```bash
cp .env.example .env
```

Минимальные настройки:

```env
SECRET_KEY=your-secret-key-change-me
DATABASE_URL=postgresql://postgres:postgres@db:5432/mypet
DEBUG=True
ALLOWED_HOSTS=*
CACHE_BACKEND=locmem
```

Дополнительные:

```env
LOAD_DEMO_DATA=true
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=admin
```

> `DATABASE_URL` содержит имена Docker-сервисов (`db`, `redis`), а не `localhost`.

---

## Архитектура Docker Compose

```
                     docker compose network
 +-----------------------------------------------------------+
 |   +----------------+                                      |
 |   |      web       |                                      |
 |   | Django runserver|                                      |
 |   | port 5000      |                                      |
 |   +----+------+----+                                      |
 |        |      |                                           |
 |   +----v-----------+          +-----------v----------+    |
 |   |       db       |          |        redis         |    |
 |   | postgres:15-   |          | redis:7-alpine       |    |
 |   | alpine         |          |                      |    |
 |   +----------------+          +----------------------+    |
 +-----------------------------------------------------------+

 Volumes:
   .:/app              -- исходный код (live reload)
   ./media:/app/media   -- медиафайлы
   ./static:/app/static -- статика
   postgres_data        -- данные PostgreSQL
   redis_data           -- данные Redis
```

### Сервисы

| Сервис | Образ | Healthcheck |
|--------|-------|-------------|
| web | build: . (python:3.12-slim) | — |
| db | postgres:15-alpine | `pg_isready -U postgres` (5 сек, 5 попыток) |
| redis | redis:7-alpine | `redis-cli ping` (5 сек, 5 попыток) |

При запуске `docker-entrypoint.sh` выполняет:
1. `migrate` — применение миграций
2. `collectstatic` — сбор статики
3. `loaddata initial_structure.json` — категории, типы, теги
4. `setup_demo_content` — демо-данные (если `LOAD_DEMO_DATA=true`)
5. `createsuperuser` — суперпользователь
6. Запуск указанной команды (runserver)

---

## Hot Reload

Текущая директория монтируется в контейнер (`volumes: .:/app`). Изменения в `.py` файлах автоматически перезагружают Django. Шаблоны и статика — достаточно обновить браузер.

---

## Полезные команды

```bash
# Сборка и запуск
docker compose up --build -d

# Пересборка без кэша
docker compose build --no-cache && docker compose up -d

# Логи
docker compose logs -f
docker compose logs -f web

# Shell контейнера
docker compose exec web bash

# Django shell
docker compose exec web python manage.py shell

# Миграции
docker compose exec web python manage.py migrate

# Суперпользователь
docker compose exec web python manage.py createsuperuser

# Тесты и линтеры
docker compose exec web poetry run pytest
docker compose exec web poetry run ruff check .
docker compose exec web poetry run mypy .

# Остановка
docker compose down

# Остановка с удалением данных
docker compose down -v
```

---

## Загрузка демо-данных

### Автоматически при старте

Установите `LOAD_DEMO_DATA=true` в `.env`.

### Вручную

```bash
docker compose exec web python manage.py loaddata blog/fixtures/initial_structure.json
docker compose exec web python manage.py setup_demo_content
```

Для тестирования без демо-данных: `LOAD_DEMO_DATA=false` или удалите переменную.

---

## Управление базой данных

```bash
# Сброс БД (удаление volume)
docker compose down -v && docker compose up --build -d

# Резервная копия
docker compose exec db pg_dump -U postgres mypet > backup.sql
docker compose exec db pg_dump -U postgres mypet | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Восстановление
docker compose exec -T db psql -U postgres mypet < backup.sql

# Подключение к БД
docker compose exec db psql -U postgres -d mypet

# Просмотр таблиц
docker compose exec db psql -U postgres -d mypet -c "\dt"
```

---

## Staging-тестирование (production-подобный режим)

Для проверки работы с gunicorn и nginx:

```bash
docker compose -f docker-compose.prod.yml up --build web db redis nginx
```

> Запускаются только нужные сервисы, без haproxy, certbot, softether.

Доступ:
- Через nginx: http://localhost:8080
- Напрямую к gunicorn: http://localhost:8000

Проверки:
- Статика раздаётся nginx (не Django)
- Gunicorn: 4 воркера, 2 потока
- `DEBUG=False`

---

## Чек-лист тестирования

### Функциональное

| Проверка | URL / действие | Ожидаемый результат |
|----------|---------------|---------------------|
| Главная страница | http://localhost:5000/ | Страница загружается |
| Авторизация | http://localhost:5000/users/login/ | Форма входа, вход работает |
| Админка | http://localhost:5000/admin/ | Вход по учётным данным |
| Поиск | Поле поиска | Результаты отображаются |
| Контент | Список и детальные страницы | Контент с изображениями |
| Категории | Фильтрация по категориям | Фильтрация работает |
| Теги | Фильтрация по тегам | Фильтрация работает |

### Безопасность

| Проверка | Ожидаемый результат |
|----------|---------------------|
| Rate limiting входа | Блокировка после превышения лимита |
| Honeypot | Запрос отклоняется |
| XSS (`<script>alert(1)</script>`) | Скрипт экранируется |
| CSRF (POST без токена) | Ошибка 403 |
| CSP-заголовки | Content-Security-Policy присутствует |

### Производительность

| Проверка | Ожидаемый результат |
|----------|---------------------|
| Скорость загрузки | Менее 2 секунд |
| Thumbnails | Уменьшенный размер |
| Кеширование | Ответы кешируются (Redis) |

### Адаптивность

| Размер экрана | Ожидаемый результат |
|--------------|---------------------|
| 375x667 (iPhone SE) | Корректное отображение, навигация |
| 768x1024 (iPad) | Сетка адаптируется |
| 1920x1080 | Полная версия |

---

## Тестирование базы данных

```bash
# Проверка миграций
docker compose exec web python manage.py showmigrations

# Проверка отсутствия непримененных миграций
docker compose exec web python manage.py makemigrations --check --dry-run

# Проверка фикстур
docker compose exec web python manage.py loaddata blog/fixtures/initial_structure.json

# Целостность данных
docker compose exec db psql -U postgres -d mypet -c "\dt"
docker compose exec db psql -U postgres -d mypet -c "SELECT COUNT(*) FROM blog_content;"

# Откат миграций
docker compose exec web python manage.py migrate blog 0020
docker compose exec web python manage.py migrate blog
```

---

## Чек-лист перед CI/CD деплоем

| N | Проверка | Команда |
|---|----------|---------|
| 1 | Docker-образ собирается | `docker compose up --build` |
| 2 | Миграции применяются | `showmigrations` |
| 3 | Нет неучтённых изменений моделей | `makemigrations --check --dry-run` |
| 4 | Фикстуры загружаются | `loaddata initial_structure.json` |
| 5 | Тесты проходят | `poetry run pytest` |
| 6 | Ruff чист | `poetry run ruff check .` |
| 7 | Mypy чист | `poetry run mypy .` |
| 8 | Главная загружается | http://localhost:5000/ |
| 9 | Авторизация работает | Вход/выход |
| 10 | Админка доступна | http://localhost:5000/admin/ |
| 11 | Статика отображается | CSS, изображения |
| 12 | Демо-данные загружаются | `LOAD_DEMO_DATA=true` |
| 13 | Production-подобный режим | `docker-compose.prod.yml` |

---

## Сравнение окружений

| Параметр | Docker (локально) | Replit | VPS |
|---|---|---|---|
| Настройка | Docker + `docker compose up` | Открыть в браузере | Настроить сервер |
| Время старта | 2-5 мин (первая сборка) | Мгновенно | 30-60 мин |
| Требования | Docker Desktop, 4+ GB RAM | Браузер | VPS с SSH |
| Изоляция | Контейнеры | Облако | Выделенный сервер |
| Hot Reload | Да (volume mount) | Да | Требует настройки |
| Offline | Да | Нет | Нет |
| Приближенность к production | Высокая | Средняя | Максимальная |

---

## Решение проблем

### Порт 5000 занят

```bash
lsof -i :5000
kill -9 <PID>
```

На macOS: отключите AirPlay Receiver (System Settings → General → AirDrop & Handoff).

### Docker daemon не запущен

Запустите Docker Desktop и дождитесь инициализации.

### Контейнер web не стартует

```bash
docker compose logs web
```

Частые причины: нет `.env`, неверный `DATABASE_URL`, db не прошёл healthcheck.

### Статика не загружается

В staging (runserver) Django раздаёт статику при `DEBUG=True`. В production-режиме: `collectstatic --noinput`.

### БД в неконсистентном состоянии

```bash
docker compose down -v && docker compose up --build
```

### Permission denied (volumes)

```bash
# Linux
sudo chown -R $USER:$USER .

# Windows: Docker Desktop → Settings → Resources → File Sharing
```

### Очистка Docker-ресурсов

```bash
docker system prune -a --volumes
```
