from typing import Any

from django.db import models
from django.utils.text import slugify

from core.models import BaseModel


class TagGroup(BaseModel):
    """Group of related tags (e.g., 'Месяц практики', 'Настроение')."""

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название группы',
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name='Слаг',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Группа тегов'
        verbose_name_plural = 'Группы тегов'

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class Tag(BaseModel):
    """Tag for content filtering (e.g., 'Первый месяц', 'Расслабление')."""

    name = models.CharField(
        max_length=100,
        verbose_name='Название тега',
    )
    slug = models.SlugField(
        max_length=100,
        blank=True,
        verbose_name='Слаг',
    )
    group = models.ForeignKey(
        TagGroup,
        on_delete=models.CASCADE,
        related_name='tags',
        verbose_name='Группа',
    )

    class Meta:
        ordering = ['group', 'name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        unique_together = ['group', 'name']

    def __str__(self) -> str:
        return f'{self.group.name}: {self.name}'

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


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
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='contents',
        verbose_name='Теги',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Контент'
        verbose_name_plural = 'Контент'

    def __str__(self) -> str:
        return self.title
