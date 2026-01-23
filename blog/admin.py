from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from mypet_project.config import settings
from .models import Category, Content, ContentType, Tag, TagGroup


@admin.register(ContentType)
class ContentTypeAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ('name', 'code', 'upload_folder', 'content_count', 'created_at')
    search_fields = ('name', 'code')

    class Media:
        js = ('admin/js/contenttype_transliterate.js',)

    def content_count(self, obj: ContentType) -> int:
        """Display count of content using this type."""
        return obj.get_related_content_count()
    content_count.short_description = 'Контента'  # type: ignore[attr-defined]

    def delete_model(self, request: HttpRequest, obj: ContentType) -> None:
        """Handle single object deletion with error message."""
        try:
            obj.delete()
            messages.success(request, f"Тип контента '{obj.name}' и папка удалены.")
        except ValueError as e:
            messages.error(request, str(e))

    def delete_queryset(
        self, request: HttpRequest, queryset: QuerySet[ContentType]
    ) -> None:
        """Handle bulk deletion with error messages for items with content."""
        deleted = 0
        for obj in queryset:
            try:
                obj.delete()
                deleted += 1
            except ValueError as e:
                messages.error(request, str(e))
        if deleted:
            messages.success(request, f"Удалено типов контента: {deleted}")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')

    class Media:
        js = ('admin/js/category_transliterate.js',)


class TagInline(admin.TabularInline):  # type: ignore[type-arg]
    model = Tag
    extra = 1


@admin.register(TagGroup)
class TagGroupAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ('name', 'get_categories', 'created_at')
    list_filter = ('categories',)
    search_fields = ('name',)
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
    list_display = ('name', 'group', 'created_at')
    list_filter = ('group',)
    search_fields = ('name', 'group__name')


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ('title', 'content_type', 'get_categories', 'duration', 'created_at')
    list_filter = ('content_type', 'categories', 'tags', 'created_at')
    search_fields = ('title', 'description')
    filter_horizontal = ('categories', 'tags')
    show_facets = (
        admin.ShowFacets.ALWAYS if settings.admin_show_facets
        else admin.ShowFacets.NEVER
    )

    @admin.display(description='Категории')
    def get_categories(self, obj: Content) -> str:
        return ', '.join(cat.name for cat in obj.categories.all())
