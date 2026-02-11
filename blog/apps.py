from django.apps import AppConfig


class BlogConfig(AppConfig):
    name = 'blog'
    verbose_name = 'Блог'

    def ready(self) -> None:
        import blog.signals  # noqa: F401
