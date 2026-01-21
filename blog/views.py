from __future__ import annotations
from typing import TYPE_CHECKING

from django.views.generic import ListView
from blog.models import Content

if TYPE_CHECKING:
    from django.db.models import QuerySet


class HomeView(ListView):  # type: ignore[type-arg]
    model = Content
    template_name = 'blog/index.html'
    context_object_name = 'videos'

    def get_queryset(self) -> QuerySet[Content]:
        return Content.objects.all()[:6]
