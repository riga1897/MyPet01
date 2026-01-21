from django.urls import path

from blog.views import (
    ContentCreateView,
    ContentDeleteView,
    ContentListView,
    ContentUpdateView,
    HomeView,
)

app_name = 'blog'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('content/', ContentListView.as_view(), name='content_list'),
    path('content/create/', ContentCreateView.as_view(), name='content_create'),
    path('content/<int:pk>/edit/', ContentUpdateView.as_view(), name='content_edit'),
    path('content/<int:pk>/delete/', ContentDeleteView.as_view(), name='content_delete'),
]
