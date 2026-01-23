# План рефакторинга MyPet01

**Дата аудита:** 23 января 2026  
**Версия:** 1.0

---

## Резюме

По результатам аудита выявлены области для улучшения в четырёх категориях:
производительность, качество кода, безопасность и дублирование.

---

## 1. Производительность

### 1.1 Оптимизация запросов к БД (Приоритет: Высокий)

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

### 1.2 Оптимизация кэширования (Приоритет: Средний)

**Проблема:** `HomeView` кэширует полные объекты модели Content — неоптимально по памяти.

**Решение:**
- Кэшировать только ID контента, а не полные объекты
- Добавить явный TTL для кэша
- Использовать сериализованные данные вместо ORM-объектов

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

### 1.3 Кэширование контекста фильтров (Приоритет: Низкий)

**Проблема:** `get_filter_context()` вызывается на каждый запрос.

**Решение:**
- Кэшировать результат `get_filter_context()` с инвалидацией при изменении категорий/тегов

**Файлы:** `blog/views.py`

---

## 2. Качество кода

### 2.1 Устранение дублирования ModeratorRequiredMixin (Приоритет: Высокий)

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

### 2.2 Консолидация get_context_data (Приоритет: Средний)

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

### 2.3 Улучшение типизации (Приоритет: Низкий)

**Проблема:** Много `# type: ignore` комментариев, неполная совместимость с mypy.

**Решение:**
- Использовать generic типы для Django views
- Добавить proper type hints для QuerySet возвратов

```python
# Было:
class ContentListView(ModeratorRequiredMixin, ListView):  # type: ignore[type-arg]

# Стало:
class ContentListView(ModeratorRequiredMixin, ListView[Content]):
    model = Content
```

**Файлы:** `blog/views.py`, `users/views.py`

---

## 3. Безопасность

### 3.1 Ограничения FFmpeg (Приоритет: Высокий)

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

### 3.2 Валидация размера файлов (Приоритет: Средний)

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

### 4.0 Создание единого CSS (Приоритет: Средний)

**Проблема:** Стили разбросаны по шаблонам в виде Tailwind-классов, нет единого CSS-файла для переиспользуемых компонентов.

**Решение:**
- Создать `static/css/components.css` с CSS-классами для повторяющихся компонентов
- Определить классы для: dropdown-menu, card, button, form-input и др.
- Использовать @apply директивы Tailwind или чистый CSS
- Заменить повторяющиеся inline-классы на CSS-классы

```css
/* static/css/components.css */
.dropdown-menu {
    @apply absolute top-full left-0 mt-1 min-w-[180px];
    @apply bg-card border border-border rounded-lg;
    @apply shadow-xl z-50 py-1;
}

.btn-primary {
    @apply bg-primary text-primary-foreground px-4 py-2;
    @apply rounded-lg hover:bg-primary/90 transition-colors;
}
```

**Файлы:** `static/css/components.css` (новый), `templates/base.html`, все partials

---

### 4.1 Шаблоны загрузки файлов (Приоритет: Средний)

**Проблема:** Блоки выбора файла и миниатюры в `content_form.html` почти идентичны.

**Решение:**
- Создать переиспользуемый partial `_file_upload_field.html`

```html
<!-- blog/templates/blog/partials/_file_upload_field.html -->
<div id="{{ field_id }}-section">
    <label class="block text-sm font-medium text-foreground mb-1">
        {{ label }}{% if optional %} (необязательно){% endif %}
    </label>
    <!-- Единый шаблон для обоих типов -->
</div>
```

**Файлы:** `blog/templates/blog/partials/_file_upload_field.html` (новый), `blog/templates/blog/content_form.html`

---

### 4.2 Логика обработки файлов в views (Приоритет: Низкий)

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
