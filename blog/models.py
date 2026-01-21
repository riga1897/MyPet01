from django.db import models
from core.models import BaseModel


class Content(BaseModel):
    class ContentType(models.TextChoices):
        VIDEO = 'video', 'Видео'
        PHOTO = 'photo', 'Фото'

    class Category(models.TextChoices):
        YOGA = 'yoga', 'Йога'
        OILS = 'oils', 'Эфирные масла'

    title = models.CharField(max_length=200, default='Без названия')
    description = models.TextField(blank=True)
    content_type = models.CharField(
        max_length=10,
        choices=ContentType.choices,
        default=ContentType.VIDEO,
    )
    video_file = models.FileField(upload_to='videos/', blank=True)
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True)
    duration = models.CharField(max_length=10, blank=True, help_text='Формат: MM:SS')
    category = models.CharField(
        max_length=10,
        choices=Category.choices,
        default=Category.YOGA,
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Контент'
        verbose_name_plural = 'Контент'

    def __str__(self) -> str:
        return self.title
