import logging
from io import BytesIO
from typing import Any

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.db import models
from django.utils.text import slugify
from PIL import Image, UnidentifiedImageError

from blog.services import (
    generate_thumbnail_from_image,
    generate_thumbnail_from_video,
    get_video_duration,
)
from core.models import BaseModel

logger = logging.getLogger(__name__)

THUMBNAIL_MAX_SIZE = (800, 600)
THUMBNAIL_QUALITY = 85


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


def content_file_upload_path(instance: 'Content', filename: str) -> str:
    """Generate upload path based on content type."""
    content_types = list(instance.content_types.all()) if instance.pk else []
    if content_types:
        first_type = content_types[0]
        if first_type.upload_folder:
            folder = first_type.upload_folder.strip('/')
            return f'{folder}/{filename}'
    return f'content/{filename}'


class ContentType(BaseModel):
    """Type of content (e.g., 'Видео', 'Фото', 'Аудио')."""

    VIDEO_CODE = 'video'
    PHOTO_CODE = 'photo'

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название',
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Код',
        help_text='Уникальный код для использования в коде (например: video, photo, audio)',
    )
    upload_folder = models.CharField(
        max_length=100,
        verbose_name='Папка для файлов',
        help_text='Папка для сохранения файлов (по умолчанию = код)',
        blank=True,
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Тип контента'
        verbose_name_plural = 'Типы контента'

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.upload_folder:
            self.upload_folder = self.code
        self._ensure_upload_folder_exists()
        super().save(*args, **kwargs)

    def _ensure_upload_folder_exists(self) -> None:
        """Create upload folder in media directory if it doesn't exist."""
        from django.conf import settings
        import os
        folder_path = os.path.join(settings.MEDIA_ROOT, self.upload_folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)

    @property
    def is_video(self) -> bool:
        return self.code == self.VIDEO_CODE

    @property
    def is_photo(self) -> bool:
        return self.code == self.PHOTO_CODE


class Content(BaseModel):
    title = models.CharField(
        max_length=200,
        default='Без названия',
        verbose_name='Название',
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    content_types = models.ManyToManyField(
        ContentType,
        blank=True,
        related_name='contents',
        verbose_name='Типы контента',
    )
    video_file = models.FileField(
        upload_to=content_file_upload_path,
        blank=True,
        verbose_name='Файл контента',
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

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.thumbnail and self._is_new_thumbnail():
            self._compress_thumbnail()
        super().save(*args, **kwargs)
        self._process_auto_fields_after_save()

    def _has_content_type_code(self, code: str) -> bool:
        """Check if content has a specific content type by code."""
        if not self.pk:
            return False
        return self.content_types.filter(code=code).exists()

    def has_video_type(self) -> bool:
        """Check if content has video type."""
        return self._has_content_type_code(ContentType.VIDEO_CODE)

    def has_photo_type(self) -> bool:
        """Check if content has photo type."""
        return self._has_content_type_code(ContentType.PHOTO_CODE)

    def _process_auto_fields_after_save(self) -> None:
        """Process auto-duration and auto-thumbnail after initial save."""
        needs_update = False
        
        if self.has_video_type() and self.video_file:
            if not self.duration:
                duration = get_video_duration(self.video_file)
                if duration:
                    self.duration = duration
                    needs_update = True
            
            if not self.thumbnail:
                thumbnail = generate_thumbnail_from_video(self.video_file)
                if thumbnail:
                    self.thumbnail = thumbnail
                    needs_update = True
        
        elif self.has_photo_type() and self.video_file:
            if not self.thumbnail:
                thumbnail = generate_thumbnail_from_image(self.video_file)
                if thumbnail:
                    self.thumbnail = thumbnail
                    needs_update = True
        
        if needs_update:
            super().save(update_fields=['duration', 'thumbnail'])

    def _is_new_thumbnail(self) -> bool:
        """Check if thumbnail is a newly uploaded file."""
        return isinstance(self.thumbnail.file, UploadedFile)

    def _compress_thumbnail(self) -> None:
        """Compress and resize thumbnail image for optimal web performance."""
        if not self.thumbnail.name:
            return
        try:
            pil_img = Image.open(self.thumbnail)
            if pil_img.mode in ('RGBA', 'P'):
                pil_img = pil_img.convert('RGB')  # type: ignore[assignment]
            pil_img.thumbnail(THUMBNAIL_MAX_SIZE, Image.Resampling.LANCZOS)
            output = BytesIO()
            pil_img.save(output, format='JPEG', quality=THUMBNAIL_QUALITY, optimize=True)
            output.seek(0)
            original_name = self.thumbnail.name.split('/')[-1]
            name_without_ext = original_name.rsplit('.', 1)[0]
            new_name = f"{name_without_ext}.jpg"
            self.thumbnail = ContentFile(output.read(), name=new_name)
        except UnidentifiedImageError:
            logger.warning('Failed to compress thumbnail: not a valid image file')
        except OSError as e:
            logger.warning('Failed to compress thumbnail: %s', e)

    def has_playable_video(self) -> bool:
        """Check if content has a playable video file."""
        return bool(self.has_video_type() and self.video_file)
