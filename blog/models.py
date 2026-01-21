from django.db import models
from django.contrib.auth import get_user_model
from core.models import BaseModel

User = get_user_model()


class Post(BaseModel):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.title


class Video(BaseModel):
    class Category(models.TextChoices):
        YOGA = 'yoga', 'Йога'
        OILS = 'oils', 'Эфирные масла'

    title = models.CharField(max_length=200, default='Без названия')
    description = models.TextField(blank=True)
    video_file = models.FileField(upload_to='videos/', blank=True)
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True)
    duration = models.CharField(max_length=10, blank=True, help_text='Формат: MM:SS')
    category = models.CharField(
        max_length=10,
        choices=Category.choices,
        default=Category.YOGA,
    )
    post = models.ForeignKey(
        Post,
        related_name='videos',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.title


class Comment(BaseModel):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self) -> str:
        return f"Comment by {self.author} on {self.post.title}"
