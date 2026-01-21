from typing import TYPE_CHECKING
from django.contrib import admin
from .models import Post, Video, Comment

if TYPE_CHECKING:
    _BaseVideoInline = admin.TabularInline[Video, Post]
    _BaseCommentInline = admin.TabularInline[Comment, Post]
    _BaseModelAdmin = admin.ModelAdmin[Post]
    _VideoModelAdmin = admin.ModelAdmin[Video]
    _CommentModelAdmin = admin.ModelAdmin[Comment]
else:
    _BaseVideoInline = admin.TabularInline
    _BaseCommentInline = admin.TabularInline
    _BaseModelAdmin = admin.ModelAdmin
    _VideoModelAdmin = admin.ModelAdmin
    _CommentModelAdmin = admin.ModelAdmin

class VideoInline(_BaseVideoInline):
    model = Video
    extra = 1

class CommentInline(_BaseCommentInline):
    model = Comment
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Post)
class PostAdmin(_BaseModelAdmin):
    list_display = ('title', 'author', 'created_at')
    search_fields = ('title', 'content')
    list_filter = ('created_at', 'author')
    inlines = [VideoInline, CommentInline]

@admin.register(Video)
class VideoAdmin(_VideoModelAdmin):
    list_display = ('description', 'post')

@admin.register(Comment)
class CommentAdmin(_CommentModelAdmin):
    list_display = ('author', 'post', 'created_at')
    list_filter = ('created_at', 'author')
