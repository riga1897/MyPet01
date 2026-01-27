# 🚀 Быстрый старт: Тестирование с покрытием

## Структура тестов в проекте

Проект использует **два вида тестов** согласно договоренности:

1. **Django APITestCase тесты** (в папках приложений):
   - `lms/tests.py` — тесты API приложения LMS (36 тестов)
   - `users/tests.py` — тесты API приложения Users (39 тестов)
   - Запуск: `python manage.py test`

2. **Pytest тесты** (в папке tests/):
   - `tests/lms/` — unit/integration тесты для LMS
   - `tests/users/` — unit/integration тесты для Users
   - `tests/config/` — тесты конфигурации
   - Запуск: `pytest`

**Общее количество тестов: 241** (78 Django + 163 pytest)

## Команды для запуска тестов

### 1. Запуск ВСЕХ тестов (рекомендуется)

```bash
# Сначала Django тесты
poetry run python manage.py test

# Затем pytest тесты
poetry run pytest
```

**Результат**: 241 тест (78 + 163), все должны пройти ✅

### 2. Запуск только Django тестов (в приложениях)

```bash
# Все Django тесты
poetry run python manage.py test

# Только LMS приложение
poetry run python manage.py test lms

# Только Users приложение
poetry run python manage.py test users

# С сохранением базы (ускоренный режим)
poetry run python manage.py test --keepdb
```

**Результат**: 75 Django APITestCase тестов ✅

### 3. Запуск только pytest тестов (в tests/)

```bash
poetry run pytest
```

**Результат**: 163 pytest тестов ✅

### 4. Ускоренный режим с сохранением базы

```bash
# Django тесты
poetry run python manage.py test --keepdb

# Pytest тесты
poetry run pytest --reuse-db
```

**Эффект**: База создаётся один раз, последующие запуски в 5-10 раз быстрее!

### 5. Запуск конкретных pytest тестов

```bash
# Все pytest тесты для LMS
poetry run pytest tests/lms/

# Все pytest тесты для Users
poetry run pytest tests/users/

# Конкретный файл
poetry run pytest tests/lms/test_api.py

# Конкретный тест
poetry run pytest tests/lms/test_api.py::TestCourseViewSet::test_course_list
```

## Отчёты о покрытии кода

> **Важно**: Проект настроен на **объединенное покрытие** от Django и pytest тестов для полной картины.

### 1. Объединенное покрытие от ОБОИХ раннеров (рекомендуется)

```bash
# Очистить старые данные покрытия
poetry run coverage erase

# Запустить Django тесты с измерением покрытия
poetry run coverage run --source='users,lms,config' manage.py test

# Запустить pytest с добавлением к существующему покрытию
# ВАЖНО: используем --no-cov для отключения pytest-cov плагина
poetry run coverage run --append --source='users,lms,config' -m pytest --no-cov

# Показать отчёт в терминале
poetry run coverage report

# HTML отчёт (детальный анализ)
poetry run coverage html
# Откройте htmlcov/index.html в браузере
```

**Результат**: Полное покрытие от всех 241 теста — **96.74%** 🎯

> **Важно**: Флаг `--no-cov` отключает встроенный pytest-cov плагин, чтобы coverage.py корректно собирал данные от обоих раннеров.

### 2. Только pytest покрытие (быстрый вариант)

```bash
poetry run pytest --cov=users --cov=lms --cov=config --cov-report=term-missing
```

**Результат**: Показывает покрытие только от pytest тестов (~94%)

### 3. Короткая команда для объединенного покрытия

```bash
# Одной строкой: все тесты + покрытие
poetry run coverage erase && \
poetry run coverage run --source='users,lms,config' manage.py test && \
poetry run coverage run --append --source='users,lms,config' -m pytest --no-cov && \
poetry run coverage report

# С HTML отчётом
poetry run coverage erase && \
poetry run coverage run --source='users,lms,config' manage.py test && \
poetry run coverage run --append --source='users,lms,config' -m pytest --no-cov && \
poetry run coverage html && \
echo "Отчёт: htmlcov/index.html"
```

**Эффект**: Все 241 тест + объединенный отчёт о покрытии **96.74%** 🎯

## Полная проверка перед сдачей

```bash
# 1. Форматирование кода
./scripts/fix.sh

# 2. Проверка качества (mypy, flake8, ruff)
./scripts/check.sh

# 3. Запуск ВСЕХ тестов с объединенным покрытием
poetry run coverage erase && \
poetry run coverage run --source='users,lms,config' manage.py test && \
poetry run coverage run --append --source='users,lms,config' -m pytest --no-cov && \
poetry run coverage report && \
poetry run coverage html

# 4. Проверьте HTML отчёт: htmlcov/index.html
```

**Альтернатива (раздельно)**:

```bash
# Форматирование + проверка
./scripts/fix.sh && ./scripts/check.sh

# Django тесты
poetry run python manage.py test

# Pytest тесты с покрытием
poetry run pytest -v --cov=users --cov=lms --cov=config --cov-report=html
```

## Текущие показатели проекта

### ✅ Всего: 241 тест прошёл успешно 🎉

#### Django APITestCase (в приложениях) — 78 тестов

**lms/tests.py (36 тестов):**
- LessonCRUDTestCase: CRUD операции для уроков
- CoursePermissionsTestCase: права доступа владельцев и модераторов
- SubscriptionTestCase: подписки на курсы
- PaginationTestCase: пагинация API
- ModelStringRepresentationTestCase: __str__ методы
- ValidatorTestCase: валидация YouTube URL

**users/tests.py (42 теста):**
- UserManagerTestCase: кастомный менеджер пользователей
- PaymentModelTestCase: модель платежей
- PaymentViewSetTestCase: CRUD платежей
- UserViewSetTestCase: управление пользователями
- UserViewSetCreateTestCase: создание через API (AllowAny permission)
- PaymentCheckStatusTestCase: проверка статуса Stripe платежа
- JWTAuthenticationTestCase: JWT токены

#### Pytest (в tests/) — 163 теста

**tests/lms/:**
- Тесты моделей и сериализаторов
- Email сервисы (`test_lms_services.py`)
- Celery задачи (`test_lms_tasks.py`)
- Management commands

**tests/users/:**
- Stripe интеграция (`test_stripe_services.py`)
- User сервисы — блокировка пользователей (`test_user_services.py`)
- JWT аутентификация (`test_jwt.py`)
- Permissions — кастомные права (`test_permissions.py`)
- Celery задачи (`test_user_tasks.py`)
- Модели (`test_models.py`)

**tests/config/:**
- API Root, настройки, URL routing

### ✅ Покрытие кода

- **Django тесты** (в приложениях): ~87% (78 тестов)
- **Pytest тесты** (в tests/): ~94% (163 теста)
- **Объединенное**: **96.74%** 🎯 (241 тест)

**Основные модули:**
- **users/services.py**: 100% (Stripe API + блокировка пользователей)
- **lms/services.py**: 100% (Email уведомления)
- **users/permissions.py**: 100%
- **users/tasks.py**: 100%
- **users/views.py**: 99%
- **lms/models.py**: 98%
- **lms/serializers.py**: 96%
- **lms/views.py**: 85%

### ✅ Качество кода: 100%
- **Mypy**: 100% type coverage
- **Flake8**: 0 ошибок
- **Ruff**: 0 ошибок
- **Black**: код отформатирован
- **Isort**: импорты отсортированы

## Особенности

✅ **Pytest** - современный и быстрый тестовый фреймворк
✅ **SQLite** автоматически используется для тестов (PostgreSQL не требуется!)
✅ **--reuse-db** флаг для ускорения повторных запусков
✅ **Кроссплатформенность**: работает на Windows, Linux, macOS
✅ **Celery eager mode**: задачи выполняются синхронно в тестах (без Redis)

**Создано**: 16 ноября 2025
**Версия проекта**: Django 5.2.7, DRF 3.16.1, Python 3.12
