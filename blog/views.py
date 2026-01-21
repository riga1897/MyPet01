from django.views.generic import ListView
from blog.models import Video


class HomeView(ListView):
    model = Video
    template_name = 'blog/index.html'
    context_object_name = 'videos'

    def get_queryset(self) -> list[Video]:
        return Video.objects.all()[:6]
