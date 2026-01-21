import pytest
from django.contrib.auth import get_user_model
from blog.models import Post, Video, Comment

User = get_user_model()

@pytest.mark.django_db
def test_create_post() -> None:
    user = User.objects.create_user(username='testuser1', password='password')
    post = Post.objects.create(title='Test Post', content='Content', author=user)
    assert post.title == 'Test Post'
    assert str(post) == 'Test Post'

@pytest.mark.django_db
def test_create_video() -> None:
    user = User.objects.create_user(username='testuser2', password='password')
    post = Post.objects.create(title='Post with Video', content='Content', author=user)
    video = Video.objects.create(post=post, title='Мое видео', description='Test Video')
    assert video.description == 'Test Video'
    assert str(video) == 'Мое видео'

@pytest.mark.django_db
def test_create_comment() -> None:
    user = User.objects.create_user(username='testuser3', password='password')
    post = Post.objects.create(title='Post with Comment', content='Content', author=user)
    comment = Comment.objects.create(post=post, author=user, text='Test Comment')
    assert comment.text == 'Test Comment'
    assert str(comment) == f"Comment by {user} on {post.title}"
