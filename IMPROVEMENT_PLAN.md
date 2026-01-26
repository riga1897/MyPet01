# План дальнейших улучшений MyPet01

**Дата создания:** 26 января 2026  
**Статус:** В работе

---

## Выполненные задачи

### ✅ 3.3 Защита медиа-файлов (Выполнено: 26 января 2026)

**Реализовано:**
- ProtectedMediaView для отдачи медиа только авторизованным пользователям
- Редирект на страницу входа для неавторизованных запросов к /media/
- Защита от path traversal атак (блокировка `..` и абсолютных путей)
- Корректный Content-Type для файлов (video/mp4, image/jpeg и т.д.)
- 5 тестов для ProtectedMediaView

**Файлы:**
- blog/views.py (ProtectedMediaView)
- mypet_project/urls.py (path 'media/<path:path>')
- blog/tests/test_file_views.py (TestProtectedMediaView)

---

### ✅ 3.4 Ограничение доступа к контенту для гостей (Выполнено: 26 января 2026)

**Реализовано:**
- Секция с карточками контента скрыта для неавторизованных пользователей
- Гости видят только Hero и раздел "О блоге"
- Кнопка CTA в Hero: "Войти для просмотра" (гости) / "Смотреть" (авторизованные)
- Тесты обновлены для проверки видимости секций

**Файлы:**
- blog/templates/blog/index.html ({% if user.is_authenticated %})
- blog/templates/blog/partials/_hero.html (условная кнопка)
- blog/tests/test_urls.py, blog/tests/test_views.py

---

### ✅ Рефакторинг: videos → cards (Выполнено: 26 января 2026)

**Реализовано:**
- Переименование HTML id: `videos` → `cards`
- Переименование ссылок: `href="#videos"` → `href="#cards"`
- Переименование контекста view: `context_object_name = 'cards'`
- Переименование переменных в шаблонах: `for card in cards`
- JavaScript: `videosSection` → `cardsSection`
- Обновление тестов

**Файлы:**
- blog/templates/blog/index.html
- blog/templates/blog/partials/_hero.html
- blog/views.py (HomeView.context_object_name)
- blog/tests/test_urls.py, blog/tests/test_views.py

---

### ✅ 2.3 Поиск по контенту (Выполнено: 26 января 2026)

**Реализовано:**
- Динамический клиентский поиск на главной странице
- Поиск по title и description в реальном времени
- Убрана форма поиска из header (консолидировано на главной)

**Файлы:**
- blog/templates/blog/index.html (searchCards, applyFilters)
- blog/templates/blog/partials/_header.html (убрана форма поиска)

---

### ✅ 2.4 Конвертер раскладки клавиатуры (Выполнено: 26 января 2026)

**Реализовано:**
- JavaScript функция convertLayout() для конвертации QWERTY↔ЙЦУКЕН
- Автоматическое определение языка ввода (isLatin)
- Поиск находит "йога" при вводе "qjuf" (и наоборот)

**Файлы:**
- blog/templates/blog/index.html (convertLayout, isLatin, QWERTY_TO_CYRILLIC)
- core/utils/text.py (Python-версия для серверной валидации)

---

### ✅ 2.5 Нечёткий поиск (Выполнено: 26 января 2026)

**Реализовано:**
- JavaScript функция fuzzyMatch() для последовательного сопоставления букв
- matchesSearchQuery() объединяет все стратегии поиска
- Поиск находит "йога" при вводе "йга" (пропущена буква)
- pg_trgm расширение PostgreSQL установлено для будущих улучшений

**Файлы:**
- blog/templates/blog/index.html (fuzzyMatch, matchesSearchQuery)
- blog/migrations/0021_add_pg_trgm_extension.py

---

### ✅ 2.6 Расстояние Левенштейна с двухфазным поиском (Выполнено: 26 января 2026)

**Реализовано:**
- levenshteinDistance() — классический DP-алгоритм для поиска опечаток
- Двухфазный поиск: быстрая фаза (мгновенно) + медленная фаза (150мс в фоне)
- Порог: 1 символ для слов до 4 букв, 2 символа для длинных слов
- Защита от race condition через searchVersion и querySnapshot
- Нормализация токенов (удаление пунктуации)
- Пример: "пога" → находит "йога" (замена буквы)

**Файлы:**
- blog/templates/blog/index.html (levenshteinDistance, applyFiltersFast, applyFiltersSlow)

---

## 1. Производительность

### ✅ 1.1 Индексы базы данных (Выполнено: 26 января 2026)

**Реализовано:**
- Индекс на `-updated_at` для быстрой сортировки
- Индекс на `content_type` для фильтрации
- Изменена сортировка на `-updated_at` (обновлённый контент выше)
- HomeView явно использует `.order_by('-updated_at')`

**Файлы:**
- blog/models.py (Meta.ordering, indexes)
- blog/views.py (HomeView.get_queryset)
- blog/migrations/0022_add_updated_at_index.py

---

### 1.2 Redis для кэширования (Приоритет: Средний)

**Задача:** Настроить Redis для production-окружения.

**Решение:**
```python
# settings.py (production)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379'),
    }
}
```

**Оценка:** 2 часа

---

## 2. Улучшения UX

### 2.1 Пагинация на главной (Приоритет: Высокий)

**Задача:** Добавить infinite scroll или пагинацию для контента.

**Решение:**
- Добавить `paginate_by = 12` в HomeView
- Реализовать AJAX-загрузку следующих страниц
- Добавить кнопку "Загрузить ещё"

**Оценка:** 3 часа

---

### 2.2 Lazy Loading изображений (Приоритет: Средний)

**Задача:** Ленивая загрузка миниатюр для ускорения первичной загрузки.

**Решение:**
```html
<img loading="lazy" src="{{ content.thumbnail.url }}" alt="{{ content.title }}">
```

**Оценка:** 30 минут

---

### 2.3 Поиск по контенту (Приоритет: Средний) ✅ ВЫПОЛНЕНО

**Задача:** Реализовать полнотекстовый поиск.

**Решение:**
- Использовать PostgreSQL Full-Text Search
- Добавить SearchVector для title и description
- Создать поисковую форму в header

**Оценка:** 4 часа

---

### 2.4 Конвертер раскладки клавиатуры (Приоритет: Средний)

**Задача:** Определять текст, набранный в неправильной раскладке (EN↔RU).

**Пример:** Пользователь вводит "ntcn" вместо "тест" (забыл переключить раскладку).

**Решение:**
- Создать модуль `core/utils/text.py`
- Функция `convert_layout(text, direction='auto')` — конвертация QWERTY↔ЙЦУКЕН
- Вынести `transliterate()` из JS в Python для серверного использования
- Интегрировать в SearchView: если нет результатов → попробовать альтернативную раскладку
- Показывать подсказку: *"Возможно, вы искали: тест"*

**Таблица соответствия клавиш:**
```python
QWERTY_TO_CYRILLIC = {
    'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н', 'u': 'г',
    'i': 'ш', 'o': 'щ', 'p': 'з', '[': 'х', ']': 'ъ', 'a': 'ф', 's': 'ы',
    'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р', 'j': 'о', 'k': 'л', 'l': 'д',
    ';': 'ж', "'": 'э', 'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 'b': 'и',
    'n': 'т', 'm': 'ь', ',': 'б', '.': 'ю', '/': '.', '`': 'ё'
}
```

**Оценка:** 2 часа

---

### 2.5 Нечёткий поиск (Приоритет: Средний)

**Задача:** Находить контент даже при опечатках в запросе.

**Пример:** Пользователь вводит "тст" вместо "тест" — система предлагает результаты для "тест".

**Решение:**
- Включить расширение PostgreSQL `pg_trgm` (триграммы)
- Использовать `TrigramSimilarity` для поиска похожих слов
- Показывать подсказки: *"Возможно, вы искали: ..."*
- Порог похожести: 0.3 (настраиваемый)

**Алгоритм поиска:**
1. Точный поиск (Full-Text Search)
2. Если нет результатов → поиск по альтернативной раскладке
3. Если всё ещё нет → нечёткий поиск (TrigramSimilarity)

```python
from django.contrib.postgres.search import TrigramSimilarity

Content.objects.annotate(
    similarity=TrigramSimilarity('title', query)
).filter(similarity__gt=0.3).order_by('-similarity')
```

**Зависимости:** расширение pg_trgm в PostgreSQL

**Оценка:** 3 часа

---

## 3. Безопасность

### 3.1 Content Security Policy (Приоритет: Высокий)

**Задача:** Настроить CSP заголовки.

**Решение:**
```python
# settings.py
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_SCRIPT_SRC = ("'self'",)
CSP_IMG_SRC = ("'self'", "data:", "https:")
```

**Зависимости:** `django-csp`

**Оценка:** 2 часа

---

### 3.2 Rate Limiting (Приоритет: Средний)

**Задача:** Ограничить частоту запросов к API.

**Решение:**
```python
# Использовать django-ratelimit
@ratelimit(key='ip', rate='100/h', block=True)
def api_view(request):
    ...
```

**Зависимости:** `django-ratelimit`

**Оценка:** 2 часа

---

## 4. SEO

### 4.1 Динамический sitemap.xml (Приоритет: Высокий)

**Задача:** Генерировать sitemap автоматически.

**Решение:**
```python
# blog/sitemaps.py
class ContentSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Content.objects.all()
```

**Оценка:** 1 час

---

### 4.2 Open Graph метатеги (Приоритет: Средний)

**Задача:** Добавить метатеги для соцсетей.

**Решение:**
```html
<meta property="og:title" content="{{ content.title }}">
<meta property="og:description" content="{{ content.description }}">
<meta property="og:image" content="{{ content.thumbnail.url }}">
```

**Оценка:** 1 час

---

## 5. Тестирование

### 5.1 E2E тесты (Приоритет: Низкий)

**Задача:** Добавить интеграционные тесты для UI.

**Решение:**
- Использовать Playwright или Selenium
- Покрыть основные user flows
- Интегрировать в CI/CD

**Оценка:** 8 часов

---

### 5.2 Нагрузочное тестирование (Приоритет: Низкий)

**Задача:** Проверить производительность под нагрузкой.

**Решение:**
- Использовать Locust или k6
- Тестировать главную страницу и API endpoints
- Определить bottlenecks

**Оценка:** 4 часа

---

## 6. DevOps

### 6.1 CI/CD пайплайн (Приоритет: Высокий)

**Задача:** Автоматизировать тестирование и деплой.

**Решение:**
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: poetry run pytest
      - name: Run linters
        run: poetry run ruff check . && poetry run mypy .
```

**Оценка:** 3 часа

---

### 6.2 Docker Compose для разработки (Приоритет: Средний)

**Задача:** Упростить локальную разработку.

**Решение:**
```yaml
# docker-compose.yml
services:
  web:
    build: .
    ports:
      - "5000:5000"
    depends_on:
      - db
      - redis
  db:
    image: postgres:15
  redis:
    image: redis:7
```

**Оценка:** 2 часа

---

## Порядок выполнения

| Фаза | Задачи | Приоритет | Общая оценка |
|------|--------|-----------|--------------|
| 1 | 1.1, 2.2, 4.1 | Высокий | 2.5 часа |
| 2 | 2.1, 3.1, 6.1 | Высокий | 8 часов |
| 3 | 1.2, 2.3, 3.2, 4.2, 6.2 | Средний | 11 часов |
| 4 | 5.1, 5.2 | Низкий | 12 часов |

**Общая оценка:** ~33.5 часа

---

## Метрики успеха

- [ ] Время загрузки главной страницы < 500ms (с Redis)
- [ ] Lighthouse Performance score > 90
- [ ] Все тесты проходят в CI
- [ ] Rate limiting активен для API
- [ ] Sitemap индексируется поисковиками
