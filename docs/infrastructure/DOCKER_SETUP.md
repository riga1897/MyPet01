# Docker Setup -- локальная разработка MyPet01

## Содержание

1. [Предварительные требования](#предварительные-требования)
2. [Быстрый старт](#быстрый-старт)
3. [Файл .env](#файл-env)
4. [Архитектура Docker Compose](#архитектура-docker-compose)
5. [Полезные команды](#полезные-команды)
6. [Hot Reload](#hot-reload)
7. [Загрузка демо-данных](#загрузка-демо-данных)
8. [Управление базой данных](#управление-базой-данных)
9. [Решение проблем](#решение-проблем)
10. [Сравнение окружений: Docker / Replit / VPS](#сравнение-окружений-docker--replit--vps)

---

## Предварительные требования

Необходимо:

- Docker Desktop (Windows/macOS) или Docker Engine + Docker Compose (Linux)
- Git

Не требуется локально:

- Python
- Poetry
- PostgreSQL
- Redis

Все зависимости устанавливаются внутри Docker-контейнера автоматически.

Проверка установки:

```bash
docker --version
docker compose version
git --version
```

---

## Быстрый старт

Три шага для запуска проекта:

### Шаг 1. Клонирование репозитория

```bash
git clone <repository-url>
cd MyPet01
```

### Шаг 2. Создание файла .env

```bash
cp .env.example .env
```

Или создайте файл `.env` вручную (см. раздел ниже).

### Шаг 3. Запуск

```bash
docker compose up --build -d
```

После запуска приложение доступно по адресу: http://localhost:5000

---

## Файл .env

Скопируйте шаблон и при необходимости отредактируйте:

```bash
cp .env.example .env
```

Минимальные настройки для Docker:

```env
SECRET_KEY=your-secret-key-change-me
DATABASE_URL=postgresql://postgres:postgres@db:5432/mypet
DEBUG=True
ALLOWED_HOSTS=*
CACHE_BACKEND=locmem
```

Дополнительные переменные:

```env
LOAD_DEMO_DATA=true
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=admin
```

---

## Архитектура Docker Compose

Проект состоит из трех сервисов:

```
                     docker compose network
 +-----------------------------------------------------------+
 |                                                           |
 |   +----------------+                                      |
 |   |      web       |                                      |
 |   | Django         |                                      |
 |   | runserver      |                                      |
 |   | port 5000      |                                      |
 |   | build: .       |                                      |
 |   +----+------+----+                                      |
 |        |      |                                           |
 |        |      +---------------------------+               |
 |        |                                  |               |
 |   +----v-----------+          +-----------v----------+    |
 |   |       db       |          |        redis         |    |
 |   | postgres:15-   |          | redis:7-alpine       |    |
 |   | alpine         |          |                      |    |
 |   | healthcheck:   |          | healthcheck:         |    |
 |   |  pg_isready    |          |  redis-cli ping      |    |
 |   +----------------+          +----------------------+    |
 |   | postgres_data  |          | redis_data           |    |
 |   +----------------+          +----------------------+    |
 |                                                           |
 +-----------------------------------------------------------+

 Volumes:
   .:/app              -- исходный код (live reload)
   ./media:/app/media   -- медиафайлы
   ./static:/app/static -- статика
   postgres_data        -- данные PostgreSQL
   redis_data           -- данные Redis
```

### Сервис web

- Dockerfile на основе `python:3.12-slim`
- Установка системных пакетов: `libpq-dev`, `gcc`, `redis-server`
- Зависимости через Poetry (`virtualenvs.create false`)
- Entrypoint (`docker-entrypoint.sh`): migrate, collectstatic, loaddata initial_structure, setup_demo_content (если LOAD_DEMO_DATA=true), createsuperuser
- В docker-compose.yml команда переопределена на `python manage.py runserver 0.0.0.0:5000`
- Запуск зависит от готовности db и redis (condition: service_healthy)

### Сервис db

- Образ: `postgres:15-alpine`
- Healthcheck: `pg_isready -U postgres` (интервал 5 сек, 5 попыток)
- Volume: `postgres_data` для сохранения данных между перезапусками

### Сервис redis

- Образ: `redis:7-alpine`
- Healthcheck: `redis-cli ping` (интервал 5 сек, 5 попыток)
- Volume: `redis_data`

---

## Полезные команды

### Сборка и запуск

```bash
docker compose up --build -d
```

### Пересборка без кэша

```bash
docker compose build --no-cache
docker compose up -d
```

### Просмотр логов

```bash
docker compose logs -f
docker compose logs -f web
docker compose logs -f db
```

### Вход в shell контейнера

```bash
docker compose exec web bash
```

### Django shell

```bash
docker compose exec web python manage.py shell
```

### Применение миграций

```bash
docker compose exec web python manage.py migrate
```

### Создание суперпользователя

```bash
docker compose exec web python manage.py createsuperuser
```

### Запуск тестов

```bash
docker compose exec web poetry run pytest
docker compose exec web python manage.py test
```

### Остановка сервисов

```bash
docker compose down
```

### Остановка с удалением данных

```bash
docker compose down -v
```

---

## Hot Reload

В `docker-compose.yml` текущая директория проекта монтируется в контейнер:

```yaml
volumes:
  - .:/app
```

Это означает, что любые изменения в исходном коде на хост-машине немедленно отражаются внутри контейнера. Django development server (`runserver`) автоматически перезагружается при изменении `.py` файлов.

Для шаблонов и статических файлов перезагрузка сервера не требуется -- достаточно обновить страницу в браузере.

---

## Загрузка демо-данных

### Автоматическая загрузка при старте

Добавьте в файл `.env`:

```env
LOAD_DEMO_DATA=true
```

При запуске контейнера `docker-entrypoint.sh` выполнит:

1. `python manage.py migrate`
2. `python manage.py collectstatic`
3. `python manage.py loaddata blog/fixtures/initial_structure.json`
4. `python manage.py setup_demo_content` (только если LOAD_DEMO_DATA=true)
5. `python manage.py createsuperuser`

### Ручная загрузка

```bash
docker compose exec web python manage.py loaddata blog/fixtures/initial_structure.json
docker compose exec web python manage.py setup_demo_content
```

---

## Управление базой данных

### Сброс базы данных

```bash
docker compose down -v
docker compose up --build -d
```

Volume `postgres_data` будет удален, и при следующем запуске база создается заново. Entrypoint автоматически применит миграции и загрузит начальные данные.

### Создание резервной копии

```bash
docker compose exec db pg_dump -U postgres mypet > backup.sql
```

С компрессией:

```bash
docker compose exec db pg_dump -U postgres mypet | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Восстановление из резервной копии

```bash
docker compose exec -T db psql -U postgres mypet < backup.sql
```

### Подключение к базе данных

```bash
docker compose exec db psql -U postgres -d mypet
```

### Просмотр таблиц

```bash
docker compose exec db psql -U postgres -d mypet -c "\dt"
```

---

## Решение проблем

### Порт 5000 уже занят

Ошибка:

```
Bind for 0.0.0.0:5000 failed: port is already allocated
```

Решение:

```bash
lsof -i :5000
kill -9 <PID>
docker compose up -d
```

На macOS порт 5000 может быть занят AirPlay Receiver. Отключите его в System Settings -> General -> AirDrop & Handoff.

### Ошибки прав доступа к volume

Ошибка:

```
PermissionError: [Errno 13] Permission denied
```

Решение:

```bash
sudo chown -R $(id -u):$(id -g) media/ static/
docker compose down
docker compose up -d
```

### База данных не запускается

Ошибка:

```
db exited with code 1
```

Решение -- удалить volume и пересоздать:

```bash
docker compose down -v
docker compose up --build -d
```

### Контейнер web не стартует

Проверьте логи:

```bash
docker compose logs web
```

Частые причины:

- Отсутствует файл `.env`
- Неверный формат `DATABASE_URL`
- Сервис db не прошел healthcheck

Проверка статуса всех сервисов:

```bash
docker compose ps
```

### Миграции не применяются

```bash
docker compose exec web python manage.py showmigrations
docker compose exec web python manage.py migrate --run-syncdb
```

### Очистка Docker-ресурсов

```bash
docker system prune -a --volumes
```

---

## Сравнение окружений: Docker / Replit / VPS

| Параметр | Docker (локально) | Replit | VPS |
|---|---|---|---|
| Настройка | Установить Docker, запустить docker compose up | Открыть проект в браузере | Настроить сервер, установить зависимости |
| Время старта | 2-5 минут (первая сборка), далее секунды | Мгновенно | 30-60 минут первичная настройка |
| Требования к системе | Docker Desktop, 4+ GB RAM | Браузер | VPS с SSH-доступом |
| Изоляция | Полная (контейнеры) | Полная (облако) | Полная (выделенный сервер) |
| Hot Reload | Да (volume mount) | Да (встроенный) | Требует настройки |
| База данных | PostgreSQL в контейнере | Встроенная PostgreSQL | PostgreSQL на сервере |
| Стоимость | Бесплатно | Зависит от тарифа | Аренда VPS |
| Offline-работа | Да | Нет | Нет (нужен SSH) |
| Приближенность к production | Высокая | Средняя | Максимальная |
| Масштабирование | Локально ограничено | Автоматическое | Ручное |
| Отладка | Полный доступ к контейнерам | Встроенные инструменты | SSH + логи |
| Совместная работа | Через Git | Встроенная | Через Git + CI/CD |

### Когда использовать Docker

- Локальная разработка с полным контролем
- Работа без интернета
- Тестирование в окружении, приближенном к production
- Командная разработка с единообразным окружением

### Когда использовать Replit

- Быстрый старт без установки
- Работа с любого устройства через браузер
- Прототипирование

### Когда использовать VPS

- Production-деплой
- Staging/pre-production окружение
- Нагрузочное тестирование
