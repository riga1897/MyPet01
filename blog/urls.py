from django.urls import path
from blog.views import HomeView

app_name = 'blog'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
]
