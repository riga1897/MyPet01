# План консолидации .btn-primary

## CSS Классы (добавить в static/css/components.css)

| Класс | Размер | Использование |
|-------|--------|---------------|
| `.btn-primary` | `px-6 py-2` | Стандартные кнопки форм |
| `.btn-primary-sm` | `px-4 py-2` или `px-3 py-1.5 text-sm` | Маленькие кнопки в списках, табы |
| `.btn-primary-lg` | `px-8 py-3 rounded-xl` | Hero секция |
| `.btn-primary-full` | `w-full py-2 px-4` | Кнопки на полную ширину (login) |

## Базовые стили (общие для всех):
```css
bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors
```

---

## Чеклист по файлам

### 1. blog/templates/blog/tag_form.html
- [ ] Строка 33: Кнопка "Сохранить" → `.btn-primary`

### 2. blog/templates/blog/taggroup_form.html  
- [ ] Строка 52: Кнопка "Сохранить" → `.btn-primary`

### 3. blog/templates/blog/content_form.html
- [ ] Строка 76: Таб "Загрузить" (file) → `.btn-primary-sm`
- [ ] Строка 149: Таб "Загрузить" (thumbnail) → `.btn-primary-sm`
- [ ] Строка 230: Кнопка "Сохранить" → `.btn-primary`
- [ ] Строка 291 (JS): uploadBtn → `.btn-primary-sm`
- [ ] Строка 298 (JS): selectBtn → `.btn-primary-sm`
- [ ] Строка 315 (JS): uploadBtn → `.btn-primary-sm`
- [ ] Строка 322 (JS): selectBtn → `.btn-primary-sm`

### 4. blog/templates/blog/tag_list.html
- [ ] Строка 14: Кнопка "Добавить" → `.btn-primary-sm`

### 5. blog/templates/blog/content_list.html
- [ ] Строка 13: Кнопка "Добавить" → `.btn-primary-sm`

### 6. blog/templates/blog/file_list.html
- [ ] Строка 51: Input file → оставить inline (file: pseudo-element)
- [ ] Строка 56: Кнопка "Загрузить" → `.btn-primary-sm`

### 7. blog/templates/blog/partials/_hero.html
- [ ] Строка 22: Ссылка "Смотреть" → `.btn-primary-lg`

### 8. users/templates/users/login.html
- [ ] Строка 36: Кнопка "Войти" → `.btn-primary-full`

### 9. users/templates/users/moderator_list.html
- [ ] Строка 47: Бейдж "Модератор" → НЕ КНОПКА, оставить inline

---

## Прогресс

- [ ] CSS классы добавлены в components.css
- [ ] tag_form.html обновлён
- [ ] taggroup_form.html обновлён
- [ ] content_form.html обновлён (HTML + JS)
- [ ] tag_list.html обновлён
- [ ] content_list.html обновлён
- [ ] file_list.html обновлён
- [ ] _hero.html обновлён
- [ ] login.html обновлён
- [ ] Визуальная проверка выполнена
