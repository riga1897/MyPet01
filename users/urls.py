from django.urls import path
from django.contrib.auth import views as auth_views

from users import views

app_name = 'users'

urlpatterns = [
    path('login/', views.RateLimitedLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('moderators/', views.ModeratorListView.as_view(), name='moderator_list'),
    path('moderators/add/<int:user_id>/', views.add_moderator, name='add_moderator'),
    path('moderators/remove/<int:user_id>/', views.remove_moderator, name='remove_moderator'),
]
