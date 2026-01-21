from django.contrib import admin
from django.urls import path, include, URLPattern, URLResolver
from django.conf import settings
from django.conf.urls.static import static
from typing import Union

urlpatterns: list[Union[URLPattern, URLResolver]] = [
    path('', include('blog.urls')),
    path('admin/', admin.site.urls),
    path('users/', include('users.urls', namespace='users')),
]

if settings.DEBUG:  # pragma: no cover
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
