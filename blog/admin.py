from django.contrib import admin
from .models import Content


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ('title', 'content_type', 'category', 'duration',
                    'created_at')
    list_filter = ('content_type', 'category', 'created_at', 'published_at')
    search_fields = ('title', 'description')

    class Meta:
        verbose_name = 'Пост'  # Единственное число
        verbose_name_plural = 'Посты'  # Множественное число
        # Сортировка по умолчанию в админке (переопределяет ordering из модели)
        ordering = ['-published_at']  # Новые сверху

        # Делаем поле даты кликабельным для сортировки
        list_display_links = ('title', )

        # Добавляем сортировку по другим полям через интерфейс
        sortable_by = ['created_at', 'updated_at', 'published_at']
