from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Post(BaseModel):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.title

class Video(BaseModel):
    post = models.ForeignKey(Post, related_name='videos', on_delete=models.CASCADE)
    video_file = models.FileField(upload_to='videos/')
    description = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f"Video for {self.post.title}"

class Comment(BaseModel):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self) -> str:
        return f"Comment by {self.author} on {self.post.title}"
