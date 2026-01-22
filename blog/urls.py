from django.urls import path

from blog.views import (
    CheckCategoryCodeView,
    CheckContentTypeCodeView,
    CheckContentTypeFolderView,
    ContentCreateView,
    ContentDeleteView,
    ContentListView,
    ContentUpdateView,
    HomeView,
    TagCreateView,
    TagDeleteView,
    TagGroupCreateView,
    TagGroupDeleteView,
    TagGroupUpdateView,
    TagListView,
    TagReorderView,
    TagUpdateView,
)

app_name = 'blog'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('content/', ContentListView.as_view(), name='content_list'),
    path('content/create/', ContentCreateView.as_view(), name='content_create'),
    path('content/<int:pk>/edit/', ContentUpdateView.as_view(), name='content_edit'),
    path('content/<int:pk>/delete/', ContentDeleteView.as_view(), name='content_delete'),
    path('tags/', TagListView.as_view(), name='tag_list'),
    path('tags/group/create/', TagGroupCreateView.as_view(), name='taggroup_create'),
    path('tags/group/<int:pk>/edit/', TagGroupUpdateView.as_view(), name='taggroup_edit'),
    path('tags/group/<int:pk>/delete/', TagGroupDeleteView.as_view(), name='taggroup_delete'),
    path('tags/create/', TagCreateView.as_view(), name='tag_create'),
    path('tags/<int:pk>/edit/', TagUpdateView.as_view(), name='tag_edit'),
    path('tags/<int:pk>/delete/', TagDeleteView.as_view(), name='tag_delete'),
    path('tags/reorder/', TagReorderView.as_view(), name='tag_reorder'),
    path('api/check-contenttype-code/', CheckContentTypeCodeView.as_view(), name='check_contenttype_code'),
    path('api/check-contenttype-folder/', CheckContentTypeFolderView.as_view(), name='check_contenttype_folder'),
    path('api/check-category-code/', CheckCategoryCodeView.as_view(), name='check_category_code'),
]
