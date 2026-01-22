from django.contrib import admin
from mypet_project.config import settings
from .models import Category, Content, ContentType, Tag, TagGroup


@admin.register(ContentType)
class ContentTypeAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ('name', 'code', 'upload_folder', 'created_at')
    search_fields = ('name', 'code')

    class Media:
        js = ('admin/js/contenttype_transliterate.js',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ('name', 'code', 'slug', 'created_at')
    search_fields = ('name', 'code')
    prepopulated_fields = {'slug': ('name',)}


class TagInline(admin.TabularInline):  # type: ignore[type-arg]
    model = Tag
    extra = 1


@admin.register(TagGroup)
class TagGroupAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ('name', 'slug', 'get_categories', 'created_at')
    list_filter = ('categories',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('categories',)
    inlines = [TagInline]

    def get_categories(self, obj: TagGroup) -> str:
        categories = obj.categories.all()
        if not categories:
            return 'Все'
        return ', '.join(c.name for c in categories)
    get_categories.short_description = 'Категории'  # type: ignore[attr-defined]


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
