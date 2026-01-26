from django.contrib import admin
from django.urls import path, include, URLPattern, URLResolver
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from typing import Union

from blog.views import ProtectedMediaView

urlpatterns: list[Union[URLPattern, URLResolver]] = [
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.png', permanent=True)),
    path('', include('blog.urls')),
    path('admin/', admin.site.urls),
    path('users/', include('users.urls', namespace='users')),
    path('media/<path:path>', ProtectedMediaView.as_view(), name='protected_media'),
]

if settings.DEBUG:  # pragma: no cover
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
