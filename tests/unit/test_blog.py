import pytest
from blog.models import Content


@pytest.mark.django_db
def test_create_content_video() -> None:
    content = Content.objects.create(
        title='Мое видео',
        description='Test Video',
        content_type='video',
    )
    assert content.description == 'Test Video'
    assert content.content_type == 'video'
    assert str(content) == 'Мое видео'


@pytest.mark.django_db
def test_create_content_photo() -> None:
    content = Content.objects.create(
        title='Моя фотография',
        description='Test Photo',
        content_type='photo',
    )
    assert content.description == 'Test Photo'
    assert content.content_type == 'photo'
    assert str(content) == 'Моя фотография'
