from django.contrib import admin
from .models import Post, Video, Comment

class VideoInline(admin.TabularInline):  # type: ignore[type-arg]
    model = Video
    extra = 1

class CommentInline(admin.TabularInline):  # type: ignore[type-arg]
    model = Comment
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ('title', 'author', 'created_at')
    search_fields = ('title', 'content')
    list_filter = ('created_at', 'author')
    inlines = [VideoInline, CommentInline]

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ('description', 'post')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ('author', 'post', 'created_at')
    list_filter = ('created_at', 'author')
