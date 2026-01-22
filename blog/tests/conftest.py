import pytest
from blog.models import Category, ContentType


@pytest.fixture
def yoga_category() -> Category:
    """Create and return the yoga category."""
    category, _ = Category.objects.get_or_create(
        code='yoga',
        defaults={'name': 'Йога', 'slug': 'yoga'},
    )
    return category


@pytest.fixture
def oils_category() -> Category:
    """Create and return the oils category."""
    category, _ = Category.objects.get_or_create(
        code='oils',
        defaults={'name': 'Эфирные масла', 'slug': 'oils'},
    )
    return category


@pytest.fixture
def video_type() -> ContentType:
    """Create and return the video content type."""
    content_type, _ = ContentType.objects.get_or_create(
        code='video',
        defaults={'name': 'Видео', 'slug': 'video', 'upload_folder': 'videos'},
    )
    return content_type


@pytest.fixture
def photo_type() -> ContentType:
    """Create and return the photo content type."""
    content_type, _ = ContentType.objects.get_or_create(
        code='photo',
        defaults={'name': 'Фото', 'slug': 'photo', 'upload_folder': 'photos'},
    )
    return content_type
