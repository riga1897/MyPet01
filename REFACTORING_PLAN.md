# План рефакторинга MyPet01

**Дата аудита:** 23 января 2026  
**Версия:** 1.0

---

## Резюме

По результатам аудита выявлены области для улучшения в четырёх категориях:
производительность, качество кода, безопасность и дублирование.

---

## 1. Производительность

### 1.1 Оптимизация запросов к БД (Приоритет: Высокий) ✅ ВЫПОЛНЕНО

**Проблема:** `TagGroup.is_visible_for_category` вызывает `.exists()` в цикле Python — N+1 запросы.

**Решение:**
```python
# Было (в шаблоне/view):
for group in tag_groups:
    if group.is_visible_for_category(category_code):
        ...

# Стало (предзагрузка в view):
tag_groups = TagGroup.objects.prefetch_related('categories').all()

# В шаблоне использовать предзагруженные данные:
{% if category_code in group.category_codes %}
```

**Файлы:** `blog/views.py`, `blog/models.py`

---

### 1.2 Оптимизация кэширования (Приоритет: Средний) ✅ ВЫПОЛНЕНО

**Проблема:** `HomeView` кэширует полные объекты модели Content — неоптимально по памяти.

**Решение:**
- Кэшировать только ID контента, а не полные объекты
- Добавить явный TTL для кэша (CACHE_TTL = 300 секунд)
- Использовать `get_cached_content_ids()` / `set_cached_content_ids()`

```python
# Было:
cache.set('home_videos', list(queryset), timeout=300)

# Стало:
video_ids = list(queryset.values_list('id', flat=True))
cache.set('home_video_ids', video_ids, timeout=300)
# При чтении: Content.objects.filter(id__in=cached_ids)
```

**Файлы:** `blog/views.py`, `blog/cache.py`

---

### 1.3 Кэширование контекста фильтров (Приоритет: Низкий) ✅ ВЫПОЛНЕНО

**Проблема:** `get_filter_context()` вызывается на каждый запрос.

**Решение:**
- Кэшировать результат `get_filter_context()` с инвалидацией при изменении категорий/тегов
- Добавлены функции `get_cached_filter_context()`, `set_cached_filter_context()`, `invalidate_filter_context_cache()`
- Сигналы инвалидации при изменении Category, Tag, TagGroup, TagGroup.categories

**Файлы:** `blog/views.py`, `blog/cache.py`, `blog/signals.py`

---

## 2. Качество кода

### 2.1 Устранение дублирования ModeratorRequiredMixin (Приоритет: Высокий) ✅ ВЫПОЛНЕНО

**Проблема:** Миксин дублируется в `blog/views.py` и `users/views.py`.

**Решение:**
- Переместить в `core/mixins.py`
- Импортировать из единого места

```python
# core/mixins.py
from users.models import is_moderator

class ModeratorRequiredMixin(LoginRequiredMixin):
    def test_func(self) -> bool:
        return is_moderator(self.request.user)
```

**Файлы:** `core/mixins.py` (новый), `blog/views.py`, `users/views.py`

---

### 2.2 Консолидация get_context_data (Приоритет: Средний) ✅ ВЫПОЛНЕНО

**Проблема:** Повторяющийся паттерн добавления `get_filter_context()` в 10+ views.

**Решение:**
- Создать базовый миксин `FilterContextMixin`

```python
class FilterContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_filter_context())
        context['is_moderator'] = True
        return context
```

**Файлы:** `blog/views.py`

---

### 2.3 Улучшение типизации (Приоритет: Низкий) ✅ ВЫПОЛНЕНО (частично)

**Проблема:** Много `# type: ignore` комментариев, неполная совместимость с mypy.

**Решение:**
- Попытка использовать generic типы для Django views (`ListView[Content]`, `CreateView[Content, ContentForm]`)
- **Проблема:** Django generic views не поддерживают subscripting во время выполнения (`TypeError: type 'ListView' is not subscriptable`)
- **Решение:** Оставлены `# type: ignore[type-arg]` комментарии — это стандартная практика для Django проектов
- **Результат:** Mypy проходит успешно (`Success: no issues found in 82 source files`)

**Альтернативы:**
- Использовать `django-stubs` для полной поддержки типизации Django (требует дополнительной настройки)
- Использовать условный импорт с `TYPE_CHECKING` (усложняет код)

**Файлы:** `blog/views.py`, `users/views.py`

---

## 3. Безопасность

### 3.1 Ограничения FFmpeg (Приоритет: Высокий) ✅ ВЫПОЛНЕНО

**Проблема:** FFmpeg обрабатывает пользовательские файлы без ограничений ресурсов — риск DoS.

**Решение:**
- Добавить валидацию размера файла перед обработкой
- Установить ограничения CPU/памяти для FFmpeg
- Добавить таймаут для обработки

```python
# blog/services.py
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500 MB
MAX_PROCESSING_TIME = 60  # секунд

def generate_video_thumbnail(video_path: str) -> str | None:
    if os.path.getsize(video_path) > MAX_VIDEO_SIZE:
        return None
    
    try:
        result = subprocess.run(
            ffmpeg_cmd,
            timeout=MAX_PROCESSING_TIME,
            capture_output=True
        )
    except subprocess.TimeoutExpired:
        return None
```

**Файлы:** `blog/services.py`

---

### 3.2 Валидация размера файлов (Приоритет: Средний) ✅ ВЫПОЛНЕНО

**Проблема:** Нет валидации размера файла на уровне формы.

**Решение:**
- Добавить валидатор размера в ContentForm

```python
# blog/forms.py
from django.core.validators import FileExtensionValidator

def validate_file_size(file):
    max_size = 500 * 1024 * 1024  # 500 MB
    if file.size > max_size:
        raise ValidationError(f'Файл слишком большой. Максимум: 500 MB')
```

**Файлы:** `blog/forms.py`

---

## 4. Дублирование кода

### 4.0 Создание единого CSS (Приоритет: Средний) ✅ ВЫПОЛНЕНО

**Проблема:** Стили разбросаны по шаблонам в виде Tailwind-классов, нет единого CSS-файла для переиспользуемых компонентов.

**Решение:**
- Расширен `static/css/components.css` с CSS-классами для всех повторяющихся компонентов
- Добавлены классы: `form-label`, `form-error`, `form-hint`, `file-upload-area`, `file-selected-display`, `current-file-info`, `card`, `card-lg`, `mode-toggle-buttons`, `btn-icon-danger`, `progress-bar-container`, `progress-bar`
- Заменены inline Tailwind-классы на CSS-классы в `content_form.html`, `tag_form.html`, `taggroup_form.html`

**Файлы:** `static/css/components.css`, `blog/templates/blog/content_form.html`, `blog/templates/blog/tag_form.html`, `blog/templates/blog/taggroup_form.html`

---

### 4.1 Шаблоны загрузки файлов (Приоритет: Средний) ✅ ВЫПОЛНЕНО (через CSS)

**Проблема:** Блоки выбора файла и миниатюры в `content_form.html` почти идентичны.

**Решение:**
- Вместо создания переиспользуемого partial, стили унифицированы через CSS-классы
- Создание единого partial нецелесообразно из-за разных JS-функций и ID элементов для file/thumbnail
- CSS-классы (`file-upload-area`, `file-selected-display`, `current-file-info`, `btn-icon-danger`, `mode-toggle-buttons`) устраняют стилевое дублирование

**Файлы:** `static/css/components.css`, `blog/templates/blog/content_form.html`

---

### 4.2 Логика обработки файлов в views (Приоритет: Низкий) ✅ ВЫПОЛНЕНО

**Проблема:** Повторяющаяся логика `existing_file`/`existing_thumbnail` в ContentCreateView и ContentUpdateView.

**Решение:**
- Вынести в метод миксина или базового класса

```python
class FileHandlingMixin:
    def handle_file_fields(self, form):
        # Общая логика для existing_file, detach_file
        # existing_thumbnail, detach_thumbnail
        pass
```

**Файлы:** `blog/views.py`

---

## Порядок выполнения

| Фаза | Задачи | Приоритет | Оценка |
|------|--------|-----------|--------|
| 1 | 2.1 Устранение дублирования ModeratorRequiredMixin | Высокий | 1 час |
| 2 | 3.1 Ограничения FFmpeg | Высокий | 2 часа |
| 3 | 1.1 Оптимизация N+1 запросов | Высокий | 2 часа |
| 4 | 3.2 Валидация размера файлов | Средний | 1 час |
| 5 | 2.2 Консолидация get_context_data | Средний | 1 час |
| 6 | 1.2 Оптимизация кэширования | Средний | 2 часа |
| 7 | 4.0 Создание единого CSS | Средний | 3 часа |
| 8 | 4.1 Шаблоны загрузки файлов | Средний | 2 часа |
| 9 | 2.3 Улучшение типизации | Низкий | 3 часа |
| 10 | 1.3 Кэширование контекста фильтров | Низкий | 1 час |
| 11 | 4.2 Логика обработки файлов | Низкий | 1 час |

**Общая оценка:** ~19 часов

---

## Метрики успеха

- [ ] Все тесты проходят (`poetry run pytest`)
- [ ] Линтеры без ошибок (`poetry run ruff check .`)
- [ ] Типизация без ошибок (`poetry run mypy .`)
- [ ] Покрытие кода 100%
- [ ] Время загрузки главной страницы < 200ms
- [ ] Отсутствие N+1 запросов (проверка через django-debug-toolbar)

---

## Примечания

- Все изменения должны сопровождаться тестами
- Рефакторинг проводить поэтапно с промежуточными коммитами
- После каждой фазы запускать полный тест-сьют
