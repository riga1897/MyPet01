# Быстрый старт: тестирование MyPet01

## 1. Быстрый запуск

```bash
poetry run pytest
poetry run ruff check .
poetry run mypy .
```

## 2. Структура тестов

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

## 3. Запуск тестов

Все тесты:

```bash
poetry run pytest
```

Конкретный каталог:

```bash
poetry run pytest blog/tests/
```

Конкретный файл:

```bash
poetry run pytest blog/tests/test_models.py
```

Конкретный тест:

```bash
poetry run pytest blog/tests/test_models.py::TestPostModel::test_str_method
```

Подробный вывод:

```bash
poetry run pytest -v
```

С отчетом о покрытии (HTML):

```bash
poetry run pytest --cov-report=html
```

HTML-отчет сохраняется в `htmlcov/index.html`.

## 4. Требования к покрытию

Покрытие 100% является обязательным. CI/CD проверяет это командой:

```bash
poetry run coverage report --fail-under=100
```

Настройки покрытия задаются в `pyproject.toml`.

Измеряемые модули (addopts в pytest):

```
--cov=mypet_project --cov=blog --cov=core --cov=users --cov-report=term-missing
```

Исключения из покрытия (tool.coverage.run.omit):

- `*/migrations/*`
- `*/__init__.py`
- `*/tests/*`
- `tests/*`
- `mypet_project/wsgi.py`
- `mypet_project/asgi.py`
- `manage.py`

Строки, исключаемые из анализа (tool.coverage.report.exclude_lines):

```
pragma: no cover
if TYPE_CHECKING:
def __repr__
if self.debug:
if __name__ == .__main__.:
raise AssertionError
raise NotImplementedError
```

## 5. Линтеры

### Ruff

Проверка:

```bash
poetry run ruff check .
```

Автоматическое исправление:

```bash
poetry run ruff check . --fix
```

Конфигурация (pyproject.toml): line-length=119, preview=true.

Активные правила: B (flake8-bugbear), E (pycodestyle), F (pyflakes), C90 (mccabe), UP (pyupgrade), SIM (flake8-simplify).

### Mypy

```bash
poetry run mypy .
```

Конфигурация: strict=true, плагины: mypy_django_plugin, mypy_drf_plugin.

## 6. E2E-тесты

Установка Playwright:

```bash
poetry run playwright install
```

Запуск E2E-тестов:

```bash
poetry run pytest tests/e2e/
```

Тесты расположены в `tests/e2e/` и используют Django test client для проверки пользовательских сценариев: загрузка страниц, навигация, аутентификация, поиск.

## 7. Нагрузочные тесты

Файл: `tests/load/locustfile.py`.

С веб-интерфейсом (по умолчанию на http://localhost:8089):

```bash
poetry run locust -f tests/load/locustfile.py --host=http://localhost:5000
```

Без веб-интерфейса (headless):

```bash
poetry run locust -f tests/load/locustfile.py --host=http://localhost:5000 \
    --headless -u 10 -r 2 --run-time 60s
```

Типы пользователей, определенные в locustfile.py:

- `GuestUser` -- неавторизованный пользователь, просматривает главную, sitemap, выполняет поиск.
- `AuthenticatedUser` -- авторизованный пользователь, выполняет поиск, заходит в панель модератора.
- `APIUser` -- обращается к API-эндпоинтам проверки кодов и файлов.
- `MixedUser` (weight=3) -- смешанное поведение: просмотр, поиск, API.

## 8. Написание новых тестов

Именование файлов: `test_*.py` или `*_tests.py`.

Именование классов: `TestИмяМодуля`, например `TestPostModel`.

Именование методов: `test_что_делает`, например `test_str_method`.

Маркеры pytest:

```python
@pytest.mark.django_db
class TestPostModel:
    def test_str_method(self, post):
        assert str(post) == post.title
```

Для тестов, работающих с базой данных, обязательно используйте `@pytest.mark.django_db`.

Фикстуры размещаются в файлах `conftest.py` на уровне каталога тестов. Корневой `conftest.py` содержит общие фикстуры, например `temp_media_root`.

Тесты приложений размещаются в каталогах `<app>/tests/`, интеграционные -- в `tests/integration/`, E2E -- в `tests/e2e/`.

Переменная окружения для настроек Django:

```
DJANGO_SETTINGS_MODULE=mypet_project.settings
```

## 9. Рабочий процесс TDD

1. Написать тест, описывающий ожидаемое поведение.
2. Запустить тест, убедиться что он не проходит (red).
3. Написать минимальную реализацию.
4. Запустить тест, убедиться что он проходит (green).
5. Провести рефакторинг, не нарушая тесты.
6. Проверить линтерами:

```bash
poetry run ruff check .
poetry run mypy .
```

7. Убедиться что покрытие остается 100%:

```bash
poetry run pytest
poetry run coverage report --fail-under=100
```

## 10. Интеграция с CI/CD

Пайплайн определен в `.github/workflows/ci-cd.yml` и запускается при push и pull request в ветки `release/*`.

### Job: test

- Сервисы: PostgreSQL 15 (alpine), Redis 7 (alpine).
- Python 3.12, Poetry.
- Выполняет миграции, затем:

```bash
poetry run pytest --cov=blog --cov=users --cov=core --cov-report=html -v
poetry run coverage report --fail-under=100
```

- Артефакт `coverage-report` (htmlcov/) сохраняется на 30 дней.

### Job: lint

- Запускается после успешного прохождения тестов.
- Выполняет параллельно:

```bash
poetry run ruff check .
poetry run mypy .
```

### Порядок выполнения

test --> lint --> build-and-push --> deploy-preprod

## 11. Устранение неполадок

**ModuleNotFoundError: No module named 'mypet_project'**

Убедитесь что вы запускаете тесты из корня проекта и через Poetry:

```bash
poetry run pytest
```

**django.core.exceptions.ImproperlyConfigured**

Убедитесь что переменная DJANGO_SETTINGS_MODULE задана:

```bash
export DJANGO_SETTINGS_MODULE=mypet_project.settings
```

При использовании pytest это значение автоматически берется из `pyproject.toml`.

**Тесты не находят базу данных**

Для локальных тестов убедитесь что переменная DATABASE_URL указывает на доступную базу PostgreSQL. В CI это настраивается автоматически через сервис PostgreSQL.

**Coverage ниже 100%**

Выполните:

```bash
poetry run pytest --cov-report=term-missing
```

В столбце `Missing` будут указаны номера непокрытых строк. Добавьте тесты для этих строк или используйте `pragma: no cover` для строк, которые невозможно протестировать.

**Ruff или mypy выдают ошибки**

Для ruff попробуйте автоматическое исправление:

```bash
poetry run ruff check . --fix
```

Для mypy проверьте типы и аннотации в указанных файлах. Убедитесь что установлены плагины django-stubs и djangorestframework-stubs.

**Playwright: browser not installed**

Установите браузеры:

```bash
poetry run playwright install
```

**Locust: Connection refused**

Убедитесь что приложение запущено на указанном в --host адресе перед запуском нагрузочных тестов.
