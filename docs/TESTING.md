# Тестирование MyPet01

> **Локальное тестирование в Docker:** [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)

---

## Быстрый запуск

```bash
poetry run pytest
poetry run ruff check .
poetry run mypy .
```

---

## Структура тестов

```
tests/
    e2e/
        test_user_flows.py
    integration/
        test_django_setup.py
    load/
        locustfile.py
blog/tests/
    conftest.py
    test_admin.py
    test_cache.py
    test_content_views.py
    test_csp.py
    test_file_views.py
    test_forms.py
    test_management_commands.py
    test_models.py
    test_ratelimit.py
    test_services.py
    test_sitemaps.py
    test_tags.py
    test_templatetags.py
    test_urls.py
    test_utils.py
    test_views.py
core/tests/
    test_context_processors.py
    test_middleware.py
    test_mixins.py
    test_models.py
    test_security.py
    test_text_utils.py
users/tests/
    test_models.py
    test_signals.py
    test_views.py
mypet_project/tests/
    test_config.py
```

---

## Запуск тестов

```bash
# Все тесты
poetry run pytest

# Конкретный каталог
poetry run pytest blog/tests/

# Конкретный файл
poetry run pytest blog/tests/test_models.py

# Конкретный тест
poetry run pytest blog/tests/test_models.py::TestPostModel::test_str_method

# Подробный вывод
poetry run pytest -v

# С HTML-отчётом о покрытии
poetry run pytest --cov-report=html
# Отчёт: htmlcov/index.html
```

---

## Требования к покрытию

Покрытие **100%** является обязательным. CI/CD проверяет:

```bash
poetry run coverage report --fail-under=100
```

Измеряемые модули (addopts в pytest):

```
--cov=mypet_project --cov=blog --cov=core --cov=users --cov-report=term-missing
```

Исключения из покрытия (`tool.coverage.run.omit`):
- `*/migrations/*`, `*/__init__.py`, `*/tests/*`, `tests/*`
- `mypet_project/wsgi.py`, `mypet_project/asgi.py`, `manage.py`

Исключаемые строки (`tool.coverage.report.exclude_lines`):
- `pragma: no cover`, `if TYPE_CHECKING:`, `def __repr__`
- `if self.debug:`, `if __name__ == .__main__.:`
- `raise AssertionError`, `raise NotImplementedError`

---

## Линтеры

### Ruff

```bash
poetry run ruff check .
poetry run ruff check . --fix  # автоисправление
```

Конфигурация (pyproject.toml): `line-length=119`, `preview=true`.

Правила: B (flake8-bugbear), E (pycodestyle), F (pyflakes), C90 (mccabe), UP (pyupgrade), SIM (flake8-simplify).

### Mypy

```bash
poetry run mypy .
```

Конфигурация: `strict=true`, плагины: `mypy_django_plugin`, `mypy_drf_plugin`.

---

## E2E-тесты

```bash
poetry run playwright install
poetry run pytest tests/e2e/
```

Тесты в `tests/e2e/` используют Django test client для проверки сценариев: загрузка страниц, навигация, аутентификация, поиск.

---

## Нагрузочные тесты

Файл: `tests/load/locustfile.py`.

```bash
# С веб-интерфейсом (http://localhost:8089)
poetry run locust -f tests/load/locustfile.py --host=http://localhost:5000

# Headless
poetry run locust -f tests/load/locustfile.py --host=http://localhost:5000 \
    --headless -u 10 -r 2 --run-time 60s
```

Типы пользователей:
- `GuestUser` — просмотр главной, sitemap, поиск
- `AuthenticatedUser` — поиск, панель модератора
- `APIUser` — API-эндпоинты
- `MixedUser` (weight=3) — смешанное поведение

---

## Написание новых тестов

- Файлы: `test_*.py` или `*_tests.py`
- Классы: `TestИмяМодуля` (например `TestPostModel`)
- Методы: `test_что_делает` (например `test_str_method`)

```python
@pytest.mark.django_db
class TestPostModel:
    def test_str_method(self, post):
        assert str(post) == post.title
```

Для работы с БД: `@pytest.mark.django_db`.

Фикстуры в `conftest.py` на уровне каталога тестов. Корневой `conftest.py` — общие фикстуры (`temp_media_root`).

Переменная: `DJANGO_SETTINGS_MODULE=mypet_project.settings` (автоматически из `pyproject.toml`).

---

## Рабочий процесс TDD

1. Написать тест (ожидаемое поведение)
2. Запустить — убедиться что не проходит (red)
3. Написать минимальную реализацию
4. Запустить — убедиться что проходит (green)
5. Рефакторинг (не нарушая тесты)
6. Проверить линтерами: `ruff check .` и `mypy .`
7. Убедиться в покрытии 100%: `poetry run pytest && coverage report --fail-under=100`

---

## Интеграция с CI/CD

Pipeline (`.github/workflows/ci-cd.yml`) запускается при push в `release/*`.

### Job: test

- Сервисы: PostgreSQL 15, Redis 7
- Python 3.12, Poetry
- pytest + coverage 100%
- Артефакт `coverage-report` (htmlcov/) — 30 дней

### Job: lint

- После успешных тестов
- `ruff check .` и `mypy .` параллельно

Порядок: test → lint → build-and-push → deploy-preprod

Подробнее: [DEPLOYMENT_STRATEGY.md](DEPLOYMENT_STRATEGY.md)

---

## Устранение неполадок

**ModuleNotFoundError: No module named 'mypet_project'**
— Запускайте из корня проекта через Poetry: `poetry run pytest`

**django.core.exceptions.ImproperlyConfigured**
— Убедитесь что `DJANGO_SETTINGS_MODULE=mypet_project.settings` (автоматически из `pyproject.toml`)

**Тесты не находят базу данных**
— Проверьте `DATABASE_URL` для доступной PostgreSQL. В CI настраивается автоматически.

**Coverage ниже 100%**
— `poetry run pytest --cov-report=term-missing` покажет непокрытые строки.

**Ruff или mypy выдают ошибки**
— Ruff: `poetry run ruff check . --fix`. Mypy: проверьте типы, установите `django-stubs` и `djangorestframework-stubs`.

**Playwright: browser not installed**
— `poetry run playwright install`

**Locust: Connection refused**
— Убедитесь что приложение запущено на указанном `--host`.
