# План консолидации CSS (пункт 4.0)

**Дата:** 23 января 2026  
**Цель:** Создать единый CSS-файл для переиспользуемых компонентов

---

## Анализ компонентов по влиянию

| # | Компонент | Файлов затронуто | Использований | Влияние |
|---|-----------|------------------|---------------|---------|
| 1 | `.btn-primary` | 7 файлов | 13 мест | **Высокое** |
| 2 | `.dropdown-menu` | 6 файлов | 6 мест | Среднее |
| 3 | `.dropdown-toggle` | 6 файлов | 6 мест | Среднее |
| 4 | `.btn-secondary` | 6 файлов | 6 мест | Среднее |
| 5 | `.btn-danger` | 3 файла | 3 места | Низкое |
| 6 | `.form-input` | 1 файл | 2 места | Низкое |
| 7 | `.alert-success` | 2 файла | 2 места | Низкое |
| 8 | `.mode-btn` / `.mode-btn-active` | 1 файл (JS) | 8 мест | **Высокое** |

---

## Детальный план по компонентам

### 1. `.btn-primary` — **Наибольшее влияние**

**Текущий паттерн:**
```html
bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors
```

**Затронутые файлы (7):**
- `content_form.html` — 7 использований (включая JS!)
- `tag_list.html` — 1
- `content_list.html` — 1
- `tag_form.html` — 1
- `file_list.html` — 1
- `partials/_hero.html` — 1
- `taggroup_form.html` — 1

**Особенность:** В `content_form.html` класс используется в JavaScript для динамического переключения состояния кнопок. Потребуется обновить JS-код.

---

### 2. `.mode-btn` / `.mode-btn-active` — **Высокое влияние (JS)**

**Текущий паттерн:**
```javascript
// Неактивная:
'px-3 py-1.5 text-sm rounded-lg border border-border bg-card text-foreground hover:bg-muted'
// Активная:
'px-3 py-1.5 text-sm rounded-lg border border-primary bg-primary text-primary-foreground'
```

**Затронутые файлы (1):**
- `content_form.html` — 8 использований в JS (setFileMode, setThumbMode)

**Сложность:** Требуется рефакторинг JavaScript — переход от замены всего className на toggle классов.

---

### 3. `.dropdown-menu` — Среднее влияние

**Текущий паттерн:**
```html
hidden absolute top-full left-0 mt-1 min-w-[180px] bg-card border border-border rounded-lg shadow-xl dark:ring-1 dark:ring-white/20 z-50 py-1
```

**Затронутые файлы (6):**
- `partials/_tag_select_dropdowns.html`
- `partials/_category_filter_dropdown.html`
- `partials/_content_type_select_dropdown.html`
- `partials/_category_select_dropdown.html`
- `partials/_tag_filter_dropdowns.html`
- `tag_list.html`

**Примечание:** Разница в `min-w-[180px]` vs `min-w-[200px]` — унифицируем до 180px.

---

### 4. `.dropdown-toggle` — Среднее влияние

**Текущий паттерн:**
```html
dropdown-toggle flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-card text-sm hover:bg-muted transition-colors
```

**Затронутые файлы (6):** те же, что и dropdown-menu

---

### 5. `.btn-secondary` — Среднее влияние

**Текущий паттерн:**
```html
bg-muted text-foreground px-6 py-2 rounded-lg hover:bg-muted/80 transition-colors
```

**Затронутые файлы (6):**
- `content_form.html` — 1
- `tag_confirm_delete.html` — 1
- `taggroup_confirm_delete.html` — 1
- `content_confirm_delete.html` — 1
- `tag_form.html` — 1
- `taggroup_form.html` — 1

---

### 6. `.btn-danger` — Низкое влияние

**Текущий паттерн:**
```html
bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 transition-colors
```

**Затронутые файлы (3):**
- `tag_confirm_delete.html`
- `taggroup_confirm_delete.html`
- `content_confirm_delete.html`

---

### 7. `.form-input` — Низкое влияние

**Текущий паттерн:**
```html
w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary bg-card
```

**Затронутые файлы (1):**
- `content_form.html` — 2 места (select для файлов и миниатюр)

---

### 8. `.alert-success` — Низкое влияние

**Текущий паттерн:**
```html
bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg
```

**Затронутые файлы (2):**
- `tag_list.html`
- `content_list.html`

---

## Рекомендуемый порядок выполнения

| Фаза | Компоненты | Файлов | Сложность | Время |
|------|------------|--------|-----------|-------|
| 1 | Создать `components.css`, подключить | 2 | Низкая | 15 мин |
| 2 | `.btn-danger`, `.alert-success` | 5 | Низкая | 20 мин |
| 3 | `.dropdown-menu`, `.dropdown-toggle` | 6 | Средняя | 30 мин |
| 4 | `.btn-primary`, `.btn-secondary` | 10 | Средняя | 40 мин |
| 5 | `.form-input` | 1 | Низкая | 10 мин |
| 6 | `.mode-btn` (рефакторинг JS) | 1 | **Высокая** | 45 мин |

**Общее время:** ~2.5 часа

---

## Вывод: Что влияет сильнее?

### По количеству файлов:
1. **`.btn-primary`** — 7 файлов, 13 использований
2. **`.dropdown-*`** — 6 файлов каждый
3. **`.btn-secondary`** — 6 файлов

### По сложности изменений:
1. **`.mode-btn`** — требует рефакторинга JavaScript (не просто замена классов)
2. **`.btn-primary`** — часть использований в JS коде

### Рекомендация:
Начать с простых компонентов (фаза 2-3), затем перейти к кнопкам (фаза 4-5), и в конце — рефакторинг JS для mode-btn (фаза 6). Это минимизирует риск поломки функционала.

---

## CSS-классы для создания

```css
/* static/css/components.css */

/* Кнопки */
.btn-primary {
    @apply bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors;
}

.btn-secondary {
    @apply bg-muted text-foreground px-6 py-2 rounded-lg hover:bg-muted/80 transition-colors;
}

.btn-danger {
    @apply bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 transition-colors;
}

/* Dropdown */
.dropdown-menu {
    @apply hidden absolute top-full left-0 mt-1 min-w-[180px];
    @apply bg-card border border-border rounded-lg;
    @apply shadow-xl dark:ring-1 dark:ring-white/20 z-50 py-1;
}

.dropdown-toggle {
    @apply flex items-center gap-2 px-3 py-1.5 rounded-full;
    @apply border border-border bg-card text-sm;
    @apply hover:bg-muted transition-colors;
}

/* Формы */
.form-input {
    @apply w-full px-4 py-2 border border-border rounded-lg;
    @apply focus:outline-none focus:ring-2 focus:ring-primary bg-card;
}

/* Алерты */
.alert-success {
    @apply bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg;
}

/* Переключатели режимов (upload/select) */
.mode-btn {
    @apply px-3 py-1.5 text-sm rounded-lg border transition-colors;
}

.mode-btn:not(.active) {
    @apply border-border bg-card text-foreground hover:bg-muted;
}

.mode-btn.active {
    @apply border-primary bg-primary text-primary-foreground;
}
```
