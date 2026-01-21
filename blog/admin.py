from django.contrib import admin
from mypet_project.config import settings
from .models import Content


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ('title', 'content_type', 'category', 'duration',
                    'created_at')
    list_filter = ('content_type', 'category', 'created_at')
    search_fields = ('title', 'description')
    show_facets = (
        admin.ShowFacets.ALWAYS if settings.admin_show_facets
        else admin.ShowFacets.NEVER
    )
