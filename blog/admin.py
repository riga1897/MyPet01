from django.contrib import admin
from .models import Content


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ('title', 'content_type', 'category', 'duration', 'created_at')
    list_filter = ('content_type', 'category', 'created_at')
    search_fields = ('title', 'description')
