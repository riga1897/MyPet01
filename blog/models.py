from typing import Any

from django.db import models
from django.utils.text import slugify

from core.models import BaseModel


class Category(BaseModel):
    """Content category (e.g., 'Йога', 'Эфирные масла')."""

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название',
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name='Слаг',
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Код',
        help_text='Уникальный код для использования в коде (например: yoga, oils)',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


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
    categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='tag_groups',
        verbose_name='Категории',
        help_text='Оставьте пустым для применения ко всем категориям',
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

    def is_visible_for_category(self, category: 'Category | None') -> bool:
        """Check if this tag group should be visible for the given category.
        
        Empty categories = applies to all categories.
        """
        if not self.categories.exists():
            return True
        if category is None:
            return False
        return self.categories.filter(pk=category.pk).exists()


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
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок',
        help_text='Меньшее значение = выше в списке',
    )

    class Meta:
        ordering = ['group', 'order', 'name']
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
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='contents',
        verbose_name='Категория',
        null=True,
        blank=True,
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
