from django.contrib import admin
from mypet_project.config import settings
from .models import Content, Tag, TagGroup


class TagInline(admin.TabularInline):  # type: ignore[type-arg]
    model = Tag
    extra = 1


@admin.register(TagGroup)
class TagGroupAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    inlines = [TagInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ('name', 'group', 'slug', 'created_at')
    list_filter = ('group',)
    search_fields = ('name', 'group__name')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ('title', 'content_type', 'category', 'duration', 'created_at')
    list_filter = ('content_type', 'category', 'tags', 'created_at')
    search_fields = ('title', 'description')
    filter_horizontal = ('tags',)
    show_facets = (
        admin.ShowFacets.ALWAYS if settings.admin_show_facets
        else admin.ShowFacets.NEVER
    )
