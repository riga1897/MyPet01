# Руководство по staging-тестированию MyPet01

## 1. Назначение

Staging-тестирование проводится на локальной машине разработчика с использованием Docker Desktop. Цель -- проверить работоспособность приложения в контейнерной среде перед развертыванием на VPS через CI/CD.

Staging-окружение позволяет:

- убедиться в корректности сборки Docker-образа;
- проверить работу миграций базы данных в контейнере;
- протестировать взаимодействие сервисов (web, db, redis);
- выявить проблемы конфигурации до попадания кода на production;
- проверить загрузку демонстрационных данных и создание суперпользователя.

Порядок работы:

```
Разработка (Replit/локально) -> Staging (Docker Desktop) -> Production (VPS через CI/CD)
```

---

## 2. Предварительные требования

### Docker Desktop

Установите Docker Desktop для вашей операционной системы:

- Windows 10/11: https://www.docker.com/products/docker-desktop/
- macOS: https://www.docker.com/products/docker-desktop/
- Linux: Docker Engine 20.10+ и Docker Compose v2

Проверка установки:

```bash
docker --version
docker compose version
```

### Файл .env

Скопируйте шаблон и при необходимости отредактируйте:

```bash
cp .env.example .env
```

Необходимые переменные:

```
SECRET_KEY=your-secret-key-for-staging
DATABASE_URL=postgresql://postgres:postgres@db:5432/mypet
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CACHE_BACKEND=locmem

DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=admin123
DJANGO_SUPERUSER_EMAIL=admin@example.com

LOAD_DEMO_DATA=true
```

Переменные `DATABASE_URL` содержат имена Docker-сервисов (`db`, `redis`), а не `localhost`.

---

## 3. Запуск staging-окружения

### Структура сервисов docker-compose.yml

| Сервис | Образ / сборка | Порт | Назначение |
|--------|---------------|------|------------|
| web | build: . (runserver) | 5000:5000 | Django development server |
| db | postgres:15-alpine | -- | PostgreSQL |
| redis | redis:7-alpine | -- | Redis (кеширование) |

### Запуск

```bash
docker compose up --build
```

Или в фоновом режиме:

```bash
docker compose up --build -d
```

При первом запуске выполняется `docker-entrypoint.sh`, который последовательно:

1. Применяет миграции (`python manage.py migrate --noinput`).
2. Собирает статические файлы (`python manage.py collectstatic --noinput`).
3. Загружает начальную структуру (`python manage.py loaddata blog/fixtures/initial_structure.json`).
4. Загружает демонстрационный контент (`python manage.py setup_demo_content`), если `LOAD_DEMO_DATA=true`.
5. Создает суперпользователя (`python manage.py createsuperuser --noinput`).
6. Запускает указанную команду (runserver или gunicorn).

### Проверка статуса

```bash
docker compose ps
```

Все сервисы должны иметь статус `Up` или `Up (healthy)`.

### Просмотр логов

```bash
docker compose logs -f
docker compose logs -f web
docker compose logs -f db
```

### Доступ к приложению

После успешного запуска приложение доступно по адресу: http://localhost:5000

### Остановка

```bash
docker compose down
```

Для удаления данных (volumes):

```bash
docker compose down -v
```

---

## 4. Чек-лист тестирования

### 4.1. Функциональное тестирование

| Проверка | URL / действие | Ожидаемый результат |
|----------|---------------|---------------------|
| Главная страница | http://localhost:5000/ | Страница загружается, отображается контент |
| Авторизация | http://localhost:5000/users/login/ | Форма входа отображается, вход выполняется |
| Панель администратора | http://localhost:5000/admin/ | Вход по учетным данным суперпользователя |
| Поиск | Поле поиска на главной странице | Результаты поиска отображаются корректно |
| Контент | Список и детальные страницы контента | Контент отображается с изображениями |
| Медиафайлы | Изображения в карточках контента | Изображения загружаются и отображаются |
| Категории | Фильтрация по категориям | Контент фильтруется по выбранной категории |
| Теги | Фильтрация по тегам | Контент фильтруется по выбранному тегу |

### 4.2. Тестирование безопасности

| Проверка | Способ проверки | Ожидаемый результат |
|----------|----------------|---------------------|
| Rate limiting входа | Многократные неудачные попытки входа | Блокировка после превышения лимита |
| Honeypot | Заполнение скрытого поля в форме | Запрос отклоняется |
| Защита от XSS | Ввод `<script>alert(1)</script>` в поля форм | Скрипт экранируется, не выполняется |
| CSRF-защита | Отправка POST-запроса без CSRF-токена | Запрос отклоняется с ошибкой 403 |
| CSP-заголовки | Инструменты разработчика браузера, вкладка Network | Заголовок Content-Security-Policy присутствует |

### 4.3. Тестирование производительности

| Проверка | Способ проверки | Ожидаемый результат |
|----------|----------------|---------------------|
| Скорость загрузки страниц | Инструменты разработчика, вкладка Network | Страницы загружаются менее чем за 2 секунды |
| Сжатие изображений | Проверка размеров thumbnails | Thumbnails имеют уменьшенный размер |
| Кеширование | Повторные запросы к одной странице | Ответы кешируются (Redis) |

### 4.4. Тестирование адаптивности

| Проверка | Размер экрана | Ожидаемый результат |
|----------|--------------|---------------------|
| Мобильные устройства | 375x667 (iPhone SE) | Корректное отображение, навигация работает |
| Планшеты | 768x1024 (iPad) | Корректное отображение, сетка адаптируется |
| Десктоп | 1920x1080 | Полная версия интерфейса |

Для проверки адаптивности используйте инструменты разработчика браузера (F12) и режим эмуляции устройств.

---

## 5. Запуск автоматических тестов в Docker

### Запуск всех тестов

```bash
docker compose exec web poetry run pytest
```

### Запуск тестов с подробным выводом

```bash
docker compose exec web poetry run pytest -v
```

### Запуск тестов конкретного приложения

```bash
docker compose exec web poetry run pytest blog/tests/
docker compose exec web poetry run pytest users/tests/
docker compose exec web poetry run pytest core/tests/
docker compose exec web poetry run pytest tests/
```

### Запуск линтеров

```bash
docker compose exec web poetry run ruff check .
docker compose exec web poetry run mypy .
```

### Запуск линтеров одной командой

```bash
docker compose exec web poetry run ruff check . && docker compose exec web poetry run mypy .
```

---

## 6. Тестирование с демонстрационными данными

Для загрузки демонстрационного контента установите в файле `.env`:

```
LOAD_DEMO_DATA=true
```

При запуске контейнера `docker-entrypoint.sh` выполнит:

1. Загрузку фикстуры `blog/fixtures/initial_structure.json` (категории, типы контента, группы тегов).
2. Команду `setup_demo_content`, которая создает демонстрационные записи с изображениями из `blog/fixtures/demo_media/`.

Для перезагрузки демонстрационных данных без пересоздания контейнера:

```bash
docker compose exec web python manage.py loaddata blog/fixtures/initial_structure.json
docker compose exec web python manage.py setup_demo_content
```

Для тестирования без демонстрационных данных установите `LOAD_DEMO_DATA=false` или удалите эту переменную из `.env`.

---

## 7. Тестирование production-подобной конфигурации

Для проверки работы приложения с gunicorn вместо runserver используйте `docker-compose.prod.yml`.

### Структура сервисов docker-compose.prod.yml

| Сервис | Назначение | Примечание для локального тестирования |
|--------|-----------|---------------------------------------|
| web | gunicorn на порту 8000 | Основной сервис для проверки |
| db | PostgreSQL 15 | Используется |
| redis | Redis 7 | Используется |
| nginx | Проксирование и статика | Используется |
| haproxy | SNI-маршрутизация | Пропустить (требует VPS) |
| certbot | SSL-сертификаты | Пропустить (требует домен) |
| softether | VPN-сервер | Пропустить (требует VPS) |

### Запуск

```bash
docker compose -f docker-compose.prod.yml up --build web db redis nginx
```

Запуск только нужных сервисов (web, db, redis, nginx), без haproxy, certbot и softether, которые требуют VPS-инфраструктуры.

### Доступ к приложению

Через nginx: http://localhost:8080

Напрямую к gunicorn: http://localhost:8000

### Проверки в production-подобном режиме

- Статические файлы раздаются nginx (не Django).
- Gunicorn работает с 4 воркерами и 2 потоками.
- `DEBUG=False` в `.env`.
- Медиафайлы доступны через nginx.

### Остановка

```bash
docker compose -f docker-compose.prod.yml down
```

---

## 8. Тестирование базы данных

### Проверка миграций

```bash
docker compose exec web python manage.py showmigrations
```

Все миграции должны быть отмечены как примененные (`[X]`).

### Проверка отсутствия непримененных миграций

```bash
docker compose exec web python manage.py makemigrations --check --dry-run
```

Команда должна завершиться без ошибок и без создания новых файлов миграций.

### Проверка фикстур

```bash
docker compose exec web python manage.py loaddata blog/fixtures/initial_structure.json
```

Фикстура должна загружаться без ошибок.

### Проверка целостности данных

Подключение к PostgreSQL внутри контейнера:

```bash
docker compose exec db psql -U postgres -d mypet
```

Проверка таблиц:

```sql
\dt
SELECT COUNT(*) FROM blog_content;
SELECT COUNT(*) FROM blog_category;
SELECT COUNT(*) FROM blog_tag;
SELECT COUNT(*) FROM auth_user;
```

### Проверка отката миграций

```bash
docker compose exec web python manage.py migrate blog 0020
docker compose exec web python manage.py migrate blog
```

Миграции должны откатываться и применяться повторно без ошибок.

---

## 9. Частые проблемы и решения

### Порт 5000 занят

Ошибка: `Ports are not available: exposing port TCP 0.0.0.0:5000`

Решение: завершите процесс, занимающий порт, или измените маппинг в `docker-compose.yml`:

```yaml
ports:
  - "5001:5000"
```

На macOS порт 5000 может быть занят службой AirPlay Receiver. Отключите её в System Settings -> General -> AirDrop & Handoff.

### Docker daemon не запущен

Ошибка: `Cannot connect to the Docker daemon`

Решение: запустите Docker Desktop и дождитесь полной инициализации.

### Контейнер web не запускается

Проверьте логи:

```bash
docker compose logs web
```

Частые причины:

- Ошибки в файле `.env` (отсутствуют обязательные переменные).
- Сервис `db` не прошел healthcheck (подождите 10-15 секунд).
- Ошибки в миграциях (проверьте файлы миграций).

### Статические файлы не загружаются

В режиме staging (runserver) Django раздает статику самостоятельно при `DEBUG=True`.

В production-подобном режиме выполните:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### База данных в неконсистентном состоянии

Пересоздайте volume:

```bash
docker compose down -v
docker compose up --build
```

### Ошибка "Permission denied" при работе с volumes

Linux:

```bash
sudo chown -R $USER:$USER .
```

Windows: убедитесь, что Docker Desktop имеет доступ к диску проекта (Settings -> Resources -> File Sharing).

---

## 10. Чек-лист перед развертыванием через CI/CD

Перед отправкой кода в репозиторий для автоматического развертывания убедитесь в следующем:

| N | Проверка | Команда / действие |
|---|----------|-------------------|
| 1 | Docker-образ собирается без ошибок | `docker compose up --build` |
| 2 | Все миграции применяются | `docker compose exec web python manage.py showmigrations` |
| 3 | Нет неучтенных изменений моделей | `docker compose exec web python manage.py makemigrations --check --dry-run` |
| 4 | Фикстуры загружаются | `docker compose exec web python manage.py loaddata blog/fixtures/initial_structure.json` |
| 5 | Автоматические тесты проходят | `docker compose exec web poetry run pytest` |
| 6 | Линтеры не выдают ошибок | `docker compose exec web poetry run ruff check .` |
| 7 | Проверка типов проходит | `docker compose exec web poetry run mypy .` |
| 8 | Главная страница загружается | http://localhost:5000/ |
| 9 | Авторизация работает | Вход и выход через браузер |
| 10 | Панель администратора доступна | http://localhost:5000/admin/ |
| 11 | Статические файлы отображаются | CSS, изображения загружаются |
| 12 | Демонстрационные данные загружаются | `LOAD_DEMO_DATA=true` в `.env` |
| 13 | Суперпользователь создается автоматически | Переменные `DJANGO_SUPERUSER_*` в `.env` |
| 14 | Production-подобный режим работает | `docker compose -f docker-compose.prod.yml up --build web db redis nginx` |
| 15 | Контейнеры останавливаются корректно | `docker compose down` |

После успешного прохождения всех проверок код готов к отправке в репозиторий для развертывания через CI/CD.
