# План консолидации кнопок — ЗАВЕРШЕНО

## CSS Классы (components.css)

| Класс | min-width | Использование |
|-------|-----------|---------------|
| `.btn-primary` | 140px | Стандартные кнопки форм (Сохранить) |
| `.btn-secondary` | 140px | Вторичные кнопки форм (Отмена) |
| `.btn-primary-sm` | 120px | Маленькие кнопки списков (+Тег, Загрузить) |
| `.btn-secondary-sm` | 120px | Вторичные маленькие (+Группа) |
| `.btn-primary-lg` | 160px | Большие кнопки hero (Смотреть) |
| `.btn-secondary-lg` | 160px | Вторичные большие (Узнать больше) |
| `.btn-primary-full` | 100% | Кнопки на полную ширину (Войти) |
| `.btn-tab-inactive` | — | Неактивные табы |

---

## Обновлённые файлы

- [x] `static/css/components.css` — добавлены min-width и secondary классы
- [x] `blog/templates/blog/partials/_hero.html` — btn-secondary-lg
- [x] `blog/templates/blog/tag_list.html` — btn-secondary-sm для "+ Группа"
- [x] `blog/templates/blog/tag_form.html` — btn-secondary + justify-between
- [x] `blog/templates/blog/taggroup_form.html` — btn-secondary + justify-between
- [x] `blog/templates/blog/content_form.html` — btn-secondary + justify-between
- [x] `blog/templates/blog/file_list.html` — secondary стили для input file

---

## Статус: ЗАВЕРШЕНО ✓
