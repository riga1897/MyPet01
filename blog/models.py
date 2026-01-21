from django.db import models
from core.models import BaseModel


class Content(BaseModel):
    class ContentType(models.TextChoices):
        VIDEO = 'video', 'Видео'
        PHOTO = 'photo', 'Фото'

    class Category(models.TextChoices):
        YOGA = 'yoga', 'Йога'
        OILS = 'oils', 'Эфирные масла'

    title = models.CharField(
        max_length=200,
        default='Без названия',
        verbose_name='Название',
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    content_type = models.CharField(
        max_length=10,
        choices=ContentType.choices,
        default=ContentType.VIDEO,
        verbose_name='Тип',
    )
    video_file = models.FileField(
        upload_to='videos/',
        blank=True,
        verbose_name='Видео файл',
    )
    thumbnail = models.ImageField(
        upload_to='thumbnails/',
        blank=True,
        verbose_name='Обложка',
    )
    duration = models.CharField(
        max_length=10,
        blank=True,
        help_text='Формат: MM:SS',
        verbose_name='Длительность',
    )
    category = models.CharField(
        max_length=10,
        choices=Category.choices,
        default=Category.YOGA,
        verbose_name='Категория',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Контент'
        verbose_name_plural = 'Контент'

    def __str__(self) -> str:
        return self.title
