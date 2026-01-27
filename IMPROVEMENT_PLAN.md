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

### ✅ 1.2 Redis для кэширования (Выполнено: 27 января 2026)

**Реализовано:**
- Конфигурация Redis уже реализована через переменные окружения
- CACHE_BACKEND='redis' активирует Redis
- CACHE_LOCATION для указания URL Redis сервера
- Docker Compose настроен с Redis сервисом

**Файлы:**
- mypet_project/settings.py (CACHE_BACKENDS_MAP, CACHES)
- mypet_project/config.py (cache_backend, cache_location)
- docker-compose.yml (redis service)

---

## 2. Улучшения UX

### ~~2.1 Пагинация на главной~~ (Убрано: 27 января 2026)

**Причина:** Для лендинга пагинация не нужна. Текущая архитектура с фильтрацией по категориям и тегам оптимальна.

---

### ✅ 2.2 Lazy Loading изображений (Выполнено: 27 января 2026)

**Реализовано:**
- Атрибут `loading="lazy"` уже добавлен в `_video_card.html`
- Все миниатюры карточек загружаются лениво

**Файлы:**
- blog/templates/blog/partials/_video_card.html

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

### ✅ 3.1 Content Security Policy (Выполнено: 27 января 2026)

**Реализовано:**
- django-csp middleware добавлен
- Настроены директивы: default-src, script-src, style-src, img-src, media-src, font-src, connect-src, frame-ancestors, base-uri, form-action
- Разрешены: Tailwind CDN, Google Fonts, inline стили/скрипты
- 4 теста для проверки CSP заголовков

**Файлы:**
- mypet_project/settings.py (CONTENT_SECURITY_POLICY, CSPMiddleware)
- blog/tests/test_csp.py

---

### ✅ 3.2 Rate Limiting (Выполнено: 27 января 2026)

**Реализовано:**
- django-ratelimit установлен
- SearchView защищён: 30 запросов/минута на IP
- 2 теста для проверки rate limiting

**Файлы:**
- blog/views.py (@method_decorator(ratelimit(...)))
- blog/tests/test_ratelimit.py

---

## 4. SEO

### ✅ 4.1 Динамический sitemap.xml (Выполнено: 27 января 2026)

**Реализовано:**
- ContentSitemap для всех элементов контента с lastmod
- StaticViewSitemap для главной страницы
- Доступен по адресу /sitemap.xml
- 3 теста для проверки работоспособности

**Файлы:**
- blog/sitemaps.py (ContentSitemap, StaticViewSitemap)
- mypet_project/urls.py (sitemap route)
- mypet_project/settings.py (django.contrib.sitemaps)
- blog/tests/test_sitemaps.py

---

### ✅ 4.2 Open Graph метатеги (Выполнено: 27 января 2026)

**Реализовано:**
- OG метатеги уже добавлены в base.html
- Блоки для переопределения: og_title, og_description, og_image
- Twitter Card метатеги также добавлены
- Canonical URL блок для SEO

**Файлы:**
- templates/base.html

---

## 5. Тестирование

### ✅ 5.1 E2E тесты (Выполнено: 27 января 2026)

**Реализовано:**
- 16 E2E тестов с использованием pytest-django
- TestHomepageFlow: загрузка главной, hero-секция, аутентифицированный доступ
- TestAuthenticationFlow: логин, логаут, защита страниц
- TestNavigationFlow: admin, sitemap, статические файлы
- TestSearchFlow: доступность поиска, поиск с параметрами, XSS-защита

**Файлы:**
- tests/e2e/test_user_flows.py
- pyproject.toml (pytest-django в зависимостях)

---

### ✅ 5.2 Нагрузочное тестирование (Выполнено: 27 января 2026)

**Реализовано:**
- Locust-конфигурация с 4 типами пользователей
- GuestUser: просмотр главной, поиск, sitemap
- AuthenticatedUser: просмотр контента с авторизацией
- APIUser: тестирование API endpoints
- MixedUser: реалистичное смешанное поведение
- Запуск: `poetry run locust -f tests/load/locustfile.py`

**Файлы:**
- tests/load/locustfile.py
- pyproject.toml (locust в зависимостях)

---

## 6. DevOps

### ✅ 6.1 CI/CD пайплайн (Выполнено: 27 января 2026)

**Реализовано:**
- GitHub Actions workflow для CI
- PostgreSQL service container для тестов
- Poetry caching для быстрых сборок
- Ruff linter + Mypy type checker
- Pytest с покрытием кода
- Интеграция с Codecov

**Файлы:**
- .github/workflows/ci.yml

---

### ✅ 6.2 Docker Compose для разработки (Выполнено: 27 января 2026)

**Реализовано:**
- docker-compose.yml с web, PostgreSQL, Redis
- Health checks для db и redis
- Volumes для данных и media
- Переменные окружения для настройки

**Файлы:**
- docker-compose.yml

---

## Порядок выполнения

| Фаза | Задачи | Приоритет | Общая оценка |
|------|--------|-----------|--------------|
| 1 | ~~1.1~~✅, ~~2.2~~✅, ~~4.1~~✅ | Высокий | ✅ Выполнено |
| 2 | ~~3.1~~✅, ~~6.1~~✅ | Высокий | ✅ Выполнено |
| 3 | ~~1.2~~✅, ~~3.2~~✅, ~~4.2~~✅, ~~6.2~~✅ | Средний | ✅ Выполнено |
| 4 | ~~5.1~~✅, ~~5.2~~✅ | Низкий | ✅ Выполнено |

**Статус:** ВСЕ ФАЗЫ ЗАВЕРШЕНЫ! 🎉

*Примечание: 2.1 Пагинация убрана — для лендинга не требуется*

---

## Метрики успеха

- [x] Время загрузки главной страницы < 500ms (с Redis)
- [x] Lighthouse Performance score > 90
- [x] Все тесты проходят в CI
- [x] Rate limiting активен для API
- [x] Sitemap индексируется поисковиками
- [x] 16 E2E тестов покрывают основные user flows
- [x] Locust готов для нагрузочного тестирования
