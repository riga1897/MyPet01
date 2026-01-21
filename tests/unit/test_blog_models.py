import pytest
from django.contrib.auth import get_user_model
from blog.models import Post, Video, Comment

User = get_user_model()


@pytest.mark.django_db
class TestVideoModel:
    def test_video_str_returns_title(self) -> None:
        video = Video.objects.create(
            title='Утренняя йога',
            category='yoga',
        )
        assert str(video) == 'Утренняя йога'

    def test_video_default_category_is_yoga(self) -> None:
        video = Video.objects.create(title='Тест')
        assert video.category == 'yoga'

    def test_video_ordering_by_created_at_desc(self) -> None:
        v1 = Video.objects.create(title='Первое')
        v2 = Video.objects.create(title='Второе')
        videos = list(Video.objects.all())
        assert videos[0] == v2
        assert videos[1] == v1

    def test_video_category_choices(self) -> None:
        assert Video.Category.YOGA == 'yoga'
        assert Video.Category.OILS == 'oils'


@pytest.mark.django_db
class TestPostModel:
    def test_post_str_returns_title(self) -> None:
        user = User.objects.create_user(username='testuser', password='pass')
        post = Post.objects.create(
            title='Тестовый пост',
            content='Содержимое',
            author=user,
        )
        assert str(post) == 'Тестовый пост'


@pytest.mark.django_db
class TestCommentModel:
    def test_comment_str_format(self) -> None:
        user = User.objects.create_user(username='testuser', password='pass')
        post = Post.objects.create(
            title='Тестовый пост',
            content='Содержимое',
            author=user,
        )
        comment = Comment.objects.create(
            post=post,
            author=user,
            text='Комментарий',
        )
        assert str(comment) == 'Comment by testuser on Тестовый пост'
