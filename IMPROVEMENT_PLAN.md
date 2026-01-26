# План дальнейших улучшений MyPet01

**Дата создания:** 26 января 2026  
**Статус:** Планирование

---

## 1. Производительность

### 1.1 Индексы базы данных (Приоритет: Высокий)

**Задача:** Добавить индексы для часто используемых полей.

**Решение:**
```python
# blog/models.py
class Content(BaseModel):
    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['content_type']),
        ]
```

**Оценка:** 1 час

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

### 2.3 Поиск по контенту (Приоритет: Средний)

**Задача:** Реализовать полнотекстовый поиск.

**Решение:**
- Использовать PostgreSQL Full-Text Search
- Добавить SearchVector для title и description
- Создать поисковую форму в header

**Оценка:** 4 часа

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
