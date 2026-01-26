# План консолидации Mixin-классов (пункт 2.1)

**Дата:** 26 января 2026  
**Цель:** Устранить дублирование ModeratorRequiredMixin  
**Статус:** ⏳ В работе

---

## Анализ текущего состояния

### Дублирование

| Файл | Класс | Проверка |
|------|-------|----------|
| `blog/views.py:69` | `ModeratorRequiredMixin` | `is_moderator(user)` |
| `users/views.py:24` | `ModeratorRequiredMixin` | `can_manage_moderators(user)` |

**Вывод:** Это два **разных** миксина с одинаковым названием:
- `is_moderator` — проверяет, является ли пользователь модератором
- `can_manage_moderators` — проверяет, может ли пользователь управлять модераторами (админ)

---

## План действий

### 1. Создать `core/mixins.py`

- [ ] Создать файл `core/mixins.py`
- [ ] Определить `ModeratorRequiredMixin` (использует `is_moderator`)
- [ ] Определить `AdminRequiredMixin` (использует `can_manage_moderators`)
- [ ] Добавить типизацию (mypy-совместимость)
- [ ] Добавить docstrings

**Код:**
```python
# core/mixins.py
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from users.models import can_manage_moderators, is_moderator


class ModeratorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Миксин для проверки прав модератора."""
    request: Any

    def test_func(self) -> bool:
        return is_moderator(self.request.user)


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Миксин для проверки прав администратора."""
    request: Any

    def test_func(self) -> bool:
        return can_manage_moderators(self.request.user)
```

---

### 2. Обновить `blog/views.py`

- [ ] Удалить локальный класс `ModeratorRequiredMixin` (строки 69-73)
- [ ] Добавить импорт: `from core.mixins import ModeratorRequiredMixin`
- [ ] Проверить, что все views продолжают работать

---

### 3. Обновить `users/views.py`

- [ ] Удалить локальный класс `ModeratorRequiredMixin` (строки 24-28)
- [ ] Добавить импорт: `from core.mixins import AdminRequiredMixin`
- [ ] Переименовать использование: `ModeratorRequiredMixin` → `AdminRequiredMixin`
- [ ] Проверить, что все views продолжают работать

---

### 4. Тесты

- [ ] Создать `core/tests/test_mixins.py`
- [ ] Тест `ModeratorRequiredMixin` — доступ для модератора
- [ ] Тест `ModeratorRequiredMixin` — редирект для гостя
- [ ] Тест `AdminRequiredMixin` — доступ для админа
- [ ] Тест `AdminRequiredMixin` — отказ для обычного модератора

---

### 5. Проверка качества

- [ ] `poetry run ruff check .` — без ошибок
- [ ] `poetry run mypy .` — без ошибок
- [ ] `poetry run pytest` — все тесты проходят
- [ ] Проверить работу views вручную

---

### 6. Документация

- [ ] Обновить `REFACTORING_PLAN.md` — отметить пункт 2.1 как выполненный

---

## Файлы затронутые изменениями

| Файл | Действие |
|------|----------|
| `core/mixins.py` | Создать |
| `core/tests/test_mixins.py` | Создать |
| `blog/views.py` | Изменить (удалить класс, добавить импорт) |
| `users/views.py` | Изменить (удалить класс, добавить импорт, переименовать) |
| `REFACTORING_PLAN.md` | Обновить статус |

---

## Оценка времени

| Шаг | Время |
|-----|-------|
| Создать core/mixins.py | 10 мин |
| Обновить blog/views.py | 5 мин |
| Обновить users/views.py | 5 мин |
| Написать тесты | 20 мин |
| Проверка качества | 10 мин |
| Документация | 5 мин |
| **Итого** | **~55 мин** |
