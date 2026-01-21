from django.views.generic import ListView
from blog.models import Content


class HomeView(ListView):
    model = Content
    template_name = 'blog/index.html'
    context_object_name = 'videos'

    def get_queryset(self) -> list[Content]:
        return Content.objects.all()[:6]
