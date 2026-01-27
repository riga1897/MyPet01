# Local Staging Testing with Docker Desktop

Данная инструкция описывает **staging окружение** для промежуточного тестирования Django LMS приложения на локальной машине перед deployment в production.

**Поддерживаемые платформы:** Windows, macOS, Linux

## Назначение локального staging окружения

Локальная машина с Docker Desktop — это **промежуточный этап** между разработкой и production VPS:

```
Development              →  Staging (локально)        →  Production VPS
(Replit/VSCode/локально)    Docker + live reload         Docker через CI/CD
БЕЗ Docker                  db/redis хосты               db/redis хосты
localhost хосты             Тестирование перед деплоем   Финальный deployment
Быстрая разработка          Валидация Docker setup       Автоматический деплой
```

### Задачи staging окружения:

1. ✅ **Проверка сборки Docker образа** — убедиться что Dockerfile корректный
2. ✅ **Тестирование миграций БД в Docker** — проверить что миграции работают в контейнере
3. ✅ **Отладка production конфигурации** — проверить настройки для VPS локально
4. ✅ **Быстрые правки с live reload** — оперативно исправить проблемы перед push
5. ✅ **Удаление dev-специфичных файлов** — убедиться что `.replit`, `.git`, IDE-файлы не попадут в Docker

---

## Требования

### Windows
- Windows 10/11
- Docker Desktop for Windows
- Git for Windows (опционально)

### macOS
- macOS 10.15 или новее
- Docker Desktop for Mac
- Git (обычно предустановлен)

### Linux
- Docker Engine 20.10+
- Docker Compose v2
- Git

---

## 1. Установка Docker Desktop

### Шаг 1: Скачайте Docker Desktop

Перейдите на официальный сайт и скачайте установщик:
- https://www.docker.com/products/docker-desktop/

### Шаг 2: Установите Docker Desktop

1. Запустите скачанный установщик
2. Следуйте инструкциям мастера установки
3. **Для Windows:** При необходимости включите WSL 2 (Windows Subsystem for Linux)
4. Перезагрузите компьютер после установки

### Шаг 3: Проверьте установку

Откройте терминал и выполните:

```bash
docker --version
docker compose version
```

Должны увидеть версии Docker и Docker Compose.

---

## 2. Подготовка проекта

### Клонирование репозитория (если ещё не сделано)

```bash
git clone https://github.com/riga1897/DRF.git
cd DRF
```

---

## 3. Staging окружение (Рекомендуется)

Этот режим **оптимален для разработки и тестирования** перед деплоем на VPS.

### ✅ Преимущества:

- **Live reload** — изменения в коде видны сразу без пересборки
- **Docker-окружение** — тестируем с теми же хостами что и в production (db, redis)
- **Отладка** — DEBUG=True для удобной разработки
- **Валидация** — проверяем что всё работает в контейнерах перед push

### Шаг 1: Создайте .env файл

```bash
# Скопируйте шаблон для Docker staging
cp .env.docker.example .env
```

> **Для Windows (PowerShell):** Используйте `copy .env.docker.example .env`

### Шаг 2: Отредактируйте .env (опционально)

Файл `.env.docker.example` уже содержит правильные настройки для staging:

```env
DEBUG=True
SECRET_KEY=docker-staging-secret-key-change-me-xyz123abc456def
ALLOWED_HOSTS=localhost,127.0.0.1

# Docker service names (НЕ меняйте!)
POSTGRES_HOST=db
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0

# Тестовые credentials (можете изменить)
POSTGRES_DB=lms_db
POSTGRES_USER=lms_user
POSTGRES_PASSWORD=lms_staging_password
```

**Важно:** `POSTGRES_HOST=db` и `redis://redis:6379` — это имена сервисов из `docker-compose.yml`. НЕ меняйте их на `localhost`!

### Шаг 3: Запустите staging стек

```bash
docker compose up -d
```

Эта команда:
- ✅ Соберёт Docker образ из исходников (`build: .`)
- ✅ Запустит PostgreSQL, Redis, Web, Celery Worker, Celery Beat
- ✅ Применит миграции автоматически (`python manage.py migrate`)
- ✅ Запустит Django development server с **live reload** на порту 8000

### Шаг 4: Проверьте логи

```bash
# Все сервисы
docker compose logs -f

# Только web
docker compose logs -f web

# Только celery
docker compose logs -f celery_worker
```

### Шаг 5: Проверьте работоспособность

Откройте браузер и перейдите:

- **API Root**: http://localhost:8000/api/
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Admin Panel**: http://localhost:8000/admin/

### Шаг 6: Live reload в действии

Попробуйте изменить любой файл в проекте — изменения применятся **автоматически**!

```bash
# Откройте любой Python файл в редакторе и сохраните
# Проверьте логи — увидите автоматический перезапуск сервера
docker compose logs -f web
```

### Шаг 7: Создайте суперпользователя (опционально)

```bash
docker compose exec web python manage.py createsuperuser
```

### Шаг 8: Запуск тестов

```bash
# Все тесты (283 теста с coverage анализом)
docker compose exec web bash -c "coverage run --source='users,lms,config' manage.py test && coverage run --append --source='users,lms,config' -m pytest --no-cov && coverage report"

# Только Django APITestCase (78 тестов)
docker compose exec web python manage.py test

# Только Pytest (205 тестов)
docker compose exec web pytest
```

### Шаг 9: Code Quality проверки

```bash
# Запустить все проверки качества кода
docker compose exec web bash scripts/unix/check.sh

# Автоматическое исправление форматирования
docker compose exec web bash scripts/unix/fix.sh
```

### Шаг 10: Cleanup

```bash
# Остановить и удалить контейнеры
docker compose down

# Удалить также volumes (БД будет очищена)
docker compose down -v
```

---

## 4. Production-like тестирование (Опционально)

⚠️ **ВАЖНО:** Этот режим предназначен **только для локального тестирования** production конфигурации. Реальный production deployment использует **автоматическую генерацию .env** через `scripts/generate-production-env.sh` в GitHub Actions (см. `docs/GITHUB_SECRETS.md`).

Этот режим **максимально близок к production** для финальной проверки перед деплоем.

### ⚙️ Когда использовать:

- Перед merge в `main` ветку
- Для проверки Gunicorn конфигурации
- Для валидации production настроек
- Для локального тестирования образа который пойдёт на VPS

### Отличия от staging:

| Параметр | Staging (docker-compose.yml) | Production-like (docker-compose.prod.yml) |
|----------|------------------------------|-------------------------------------------|
| Сервер | Django runserver | Gunicorn (4 workers) |
| Live reload | ✅ Да (volume mounting) | ❌ Нет |
| DEBUG | True | False |
| Сборка | Локальная (`build: .`) | Pull из GHCR или локальная |
| Порт | 8000 | 8000 |

### Шаг 1: Создайте .env файл (ТОЛЬКО для локального тестирования)

**Вариант A: Из staging шаблона (рекомендуется)**
```bash
# Скопируйте staging шаблон и измените DEBUG на False
cp .env.docker.example .env
# Отредактируйте .env: установите DEBUG=False, SECRET_KEY, POSTGRES_PASSWORD
```

> **Для Windows (PowerShell):** Используйте `copy .env.docker.example .env`

**Вариант B: Через скрипт генерации (симуляция production workflow)**
```bash
# Установите переменные окружения
export SERVER_IP="localhost"
export STRIPE_SECRET_KEY="sk_test_..."
export STRIPE_PUBLISHABLE_KEY="pk_test_..."

# Запустите скрипт
bash scripts/generate-production-env.sh
```

> **Для Windows (PowerShell):**
> ```powershell
> $env:SERVER_IP="localhost"
> $env:STRIPE_SECRET_KEY="sk_test_..."
> $env:STRIPE_PUBLISHABLE_KEY="pk_test_..."
> bash scripts/generate-production-env.sh
> ```

**📌 Напоминание:** На реальном VPS файл `.env` создаётся **автоматически** GitHub Actions через `scripts/generate-production-env.sh`. Этот шаг используется ТОЛЬКО для локального тестирования на staging среде.

### Шаг 2: Отредактируйте .env для тестирования

```env
# Django Settings
DEBUG=False
SECRET_KEY=test-secret-key-for-production-testing
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (Docker service names)
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=lms_db
POSTGRES_USER=lms_user
POSTGRES_PASSWORD=test-password-change-in-real-production

# Redis (Docker service names)
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Static & Media
STATIC_ROOT=/app/staticfiles
MEDIA_ROOT=/app/media
STATIC_URL=/static/
MEDIA_URL=/media/
```

### Шаг 3: Соберите Docker образ с правильным тегом

```bash
# Собираем образ локально (вместо pull из GHCR)
docker build -t ghcr.io/riga1897/drf:local .
```

### Шаг 4: Установите переменные окружения

```bash
# Linux/macOS
export GITHUB_REPOSITORY="riga1897/drf"
export IMAGE_TAG="local"
```

> **Для Windows (PowerShell):**
> ```powershell
> $env:GITHUB_REPOSITORY="riga1897/drf"
> $env:IMAGE_TAG="local"
> ```

> **Для Windows (Command Prompt):**
> ```cmd
> set GITHUB_REPOSITORY=riga1897/drf
> set IMAGE_TAG=local
> ```

### Шаг 5: Запустите production-like стек

```bash
docker compose -f docker-compose.prod.yml up -d
```

### Шаг 6: Проверьте работоспособность

Откройте браузер и перейдите:

- **API Root**: http://localhost:8000/api/
- **Swagger UI**: http://localhost:8000/api/docs/

**Обратите внимание:** Production-like режим использует порт **8000** (не 5000).

### Шаг 7: Проверьте статус сервисов

```bash
docker compose -f docker-compose.prod.yml ps
```

Все сервисы должны быть в статусе `Up` или `Up (healthy)`.

### Шаг 8: Cleanup

```bash
# Остановить и удалить контейнеры
docker compose -f docker-compose.prod.yml down

# Удалите тестовый образ (опционально)
docker rmi ghcr.io/riga1897/drf:local

# Очистите переменные окружения (Linux/macOS)
unset GITHUB_REPOSITORY
unset IMAGE_TAG
```

> **Для Windows (PowerShell):**
> ```powershell
> Remove-Item Env:\GITHUB_REPOSITORY
> Remove-Item Env:\IMAGE_TAG
> ```

---

## 5. Полезные команды

### Просмотр логов

```bash
# Все сервисы
docker compose logs -f

# Конкретный сервис
docker compose logs -f web
docker compose logs -f celery_worker
docker compose logs -f db
```

### Выполнение команд в контейнере

```bash
# Django management команды
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py shell

# Bash shell
docker compose exec web bash
```

### Проверка статуса

```bash
# Список запущенных контейнеров
docker compose ps

# Использование ресурсов
docker stats
```

### Перезапуск сервиса

```bash
# Перезапустить web (без пересборки)
docker compose restart web

# Пересобрать и перезапустить web
docker compose up -d --build web
```

### Просмотр базы данных

```bash
# PostgreSQL shell
docker compose exec db psql -U lms_user -d lms_db

# Список таблиц
docker compose exec db psql -U lms_user -d lms_db -c "\dt"

# Проверка данных
docker compose exec db psql -U lms_user -d lms_db -c "SELECT * FROM users_user LIMIT 5;"
```

---

## 6. Troubleshooting

### Проблема: Порт уже занят

**Ошибка:**
```
Error response from daemon: Ports are not available
```

**Решение:**
1. Проверьте какой процесс использует порт:
```bash
# Linux/macOS
lsof -i :5000

# Или универсальный способ
docker compose ps
```

> **Для Windows (PowerShell):**
> ```powershell
> netstat -ano | findstr :5000
> ```

2. Остановите процесс или измените порт в `docker-compose.yml`:
```yaml
ports:
  - "5001:5000"  # Используйте другой внешний порт
```

### Проблема: Docker daemon не запущен

**Ошибка:**
```
error during connect: This error may indicate that the docker daemon is not running
```

**Решение:**
- Запустите Docker Desktop
  - **Windows:** Из меню Пуск
  - **macOS:** Из Applications
  - **Linux:** Убедитесь что Docker daemon запущен: `sudo systemctl start docker`
- Подождите пока Docker полностью загрузится

### Проблема: Контейнеры постоянно перезапускаются

**Решение:**
1. Проверьте логи:
```bash
docker compose logs web
```

2. Убедитесь что `.env` файл заполнен корректно
3. Проверьте что PostgreSQL и Redis запустились успешно:
```bash
docker compose logs db
docker compose logs redis
```

### Проблема: Миграции не применились

**Решение:**
```bash
# Вручную запустите миграции
docker compose exec web python manage.py migrate
```

### Проблема: Static файлы не загружаются (production-like режим)

**Решение:**
```bash
# Соберите static файлы (только для production-like режима)
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### Проблема: "Permission denied" при работе с volumes

**Решение:**
- **Windows:** Убедитесь что Docker Desktop имеет доступ к нужному диску
  - Settings → Resources → File Sharing → включите нужный диск
- **Linux:** Проверьте права доступа к директориям проекта
  ```bash
  sudo chown -R $USER:$USER .
  ```

### Проблема: Изменения в коде не применяются (staging режим)

**Решение:**
```bash
# Убедитесь что используете docker-compose.yml (не docker-compose.prod.yml)
docker compose ps

# Проверьте что volume mounting работает
docker compose exec web ls -la /app

# Перезапустите web сервис
docker compose restart web
```

---

## 7. Сравнение окружений

| Параметр | Replit (DEV) | Локальный Staging | Локальный Production-like | Production VPS |
|----------|--------------|-------------------|---------------------------|----------------|
| Docker | ❌ Нет (Nix) | ✅ Да | ✅ Да | ✅ Да |
| Хосты | localhost | db, redis | db, redis | db, redis |
| Live reload | ✅ Да | ✅ Да | ❌ Нет | ❌ Нет |
| DEBUG | True | True | False | False |
| Сервер | runserver | runserver | Gunicorn | Gunicorn |
| Порт | 5000 | 8000 | 8000 | 8000 |
| Назначение | Разработка | Тестирование Docker | Проверка production | Деплой |

---

## 8. Workflow: От Replit до Production

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. Разработка в Replit                                              │
│    - Пишем код БЕЗ Docker                                           │
│    - localhost хосты (.env.example)                                 │
│    - poetry run python manage.py runserver                          │
│    - Быстрые итерации                                               │
└────────────────────────────┬────────────────────────────────────────┘
                             │ git push to feature branch
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. Тестирование на локальной машине (Staging)                       │
│    - Скопировали .env.docker.example → .env                         │
│    - docker compose up -d                                           │
│    - Проверили Docker сборку                                        │
│    - Протестировали миграции                                        │
│    - Убедились что .replit, replit.nix не попали в образ            │
│    - Исправили проблемы с live reload                               │
└────────────────────────────┬────────────────────────────────────────┘
                             │ git push (после проверок)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. GitHub Actions CI/CD                                             │
│    - Запускает тесты (283 теста)                                    │
│    - Проверяет качество кода (ruff, mypy, black)                    │
│    - Собирает Docker образ                                          │
│    - Пушит в GitHub Container Registry                              │
└────────────────────────────┬────────────────────────────────────────┘
                             │ (если merge в main)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. Production VPS Deployment                                        │
│    - Pull образа из GHCR                                            │
│    - docker compose -f docker-compose.prod.yml up -d                │
│    - Gunicorn + PostgreSQL + Redis + Celery                         │
│    - Приложение доступно на http://IP:8000                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 9. Следующие шаги

После успешного локального тестирования:

1. **Убедитесь что Replit-файлы исключены из Docker:**
```bash
# Проверьте содержимое образа
docker compose exec web ls -la /app | grep replit
# Не должно быть вывода (файлы должны быть исключены)
```

2. **Запустите финальные проверки:**
```bash
# Code quality
docker compose exec web bash scripts/unix/check.sh

# Все тесты с coverage
docker compose exec web bash -c "coverage run --source='users,lms,config' manage.py test && coverage run --append --source='users,lms,config' -m pytest --no-cov && coverage report"
```

3. **Создайте Pull Request:**
```bash
git add .
git commit -m "Your changes description"
git push origin feature/your-branch-name
```

4. **GitHub Actions автоматически:**
   - Запустит все тесты (283 теста)
   - Проверит code quality (Ruff, Mypy, Black, etc.)
   - Проверит coverage (минимум 98%)
   - Соберёт Docker образ
   - Задеплоит на production (если merge в main)

---

## 10. Дополнительные ресурсы

- [Docker Desktop Documentation](https://docs.docker.com/desktop/windows/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Django Documentation](https://docs.djangoproject.com/)
- [Deployment Strategy](./DEPLOYMENT_STRATEGY.md) — полное описание четырёхступенчатой миграции (Development → Staging → Pre-Production → Production)
- [CI/CD Pipeline](./CI_CD.md) — Infrastructure as Code для production
- [Development Guide](../DEVELOPMENT.md) — стандарты разработки

---

**Полезные ссылки проекта:**
- GitHub Repository: https://github.com/riga1897/DRF
- API Documentation (local staging): http://localhost:8000/api/docs/
- API Documentation (local production-like): http://localhost:8000/api/docs/
- Admin Panel (staging): http://localhost:8000/admin/
- Admin Panel (production-like): http://localhost:8000/admin/
