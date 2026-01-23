# План консолидации .btn-primary

## CSS Классы (добавлены в static/css/components.css)

| Класс | Размер | Использование |
|-------|--------|---------------|
| `.btn-primary` | `px-6 py-2` | Стандартные кнопки форм |
| `.btn-primary-sm` | `px-4 py-2` | Маленькие кнопки в списках, табы |
| `.btn-primary-lg` | `px-8 py-3 rounded-xl` | Hero секция |
| `.btn-primary-full` | `w-full py-2 px-4` | Кнопки на полную ширину (login) |
| `.btn-tab-inactive` | `px-3 py-1.5` | Неактивные табы (файл/миниатюра) |

## Базовые стили (общие для всех):
```css
bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors
```

---

## Чеклист по файлам

### 1. blog/templates/blog/tag_form.html
- [x] Строка 33: Кнопка "Сохранить" → `.btn-primary`

### 2. blog/templates/blog/taggroup_form.html  
- [x] Строка 52: Кнопка "Сохранить" → `.btn-primary`

### 3. blog/templates/blog/content_form.html
- [x] Строка 76: Таб "Загрузить" (file) → `.btn-primary-sm`
- [x] Строка 149: Таб "Загрузить" (thumbnail) → `.btn-primary-sm`
- [x] Строка 230: Кнопка "Сохранить" → `.btn-primary`
- [x] JS: uploadBtn/selectBtn → `.btn-primary-sm` / `.btn-tab-inactive`

### 4. blog/templates/blog/tag_list.html
- [x] Строка 14: Кнопка "+ Тег" → `.btn-primary-sm`

### 5. blog/templates/blog/content_list.html
- [x] Строка 13: Кнопка "+ Добавить контент" → `.btn-primary-sm`

### 6. blog/templates/blog/file_list.html
- [x] Строка 51: Input file → оставить inline (file: pseudo-element)
- [x] Строка 56: Кнопка "Загрузить" → `.btn-primary-sm`

### 7. blog/templates/blog/partials/_hero.html
- [x] Строка 22: Ссылка "Смотреть" → `.btn-primary-lg`

### 8. users/templates/users/login.html
- [x] Строка 36: Кнопка "Войти" → `.btn-primary-full`

### 9. users/templates/users/moderator_list.html
- [x] Строка 47: Бейдж "Модератор" → НЕ КНОПКА, оставить inline

---

## Прогресс

- [x] CSS классы добавлены в components.css
- [x] tag_form.html обновлён
- [x] taggroup_form.html обновлён
- [x] content_form.html обновлён (HTML + JS)
- [x] tag_list.html обновлён
- [x] content_list.html обновлён
- [x] file_list.html обновлён
- [x] _hero.html обновлён
- [x] login.html обновлён
- [x] Визуальная проверка выполнена
