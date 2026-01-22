import pytest
from django.core.cache import cache
from django.test import Client
from blog.models import Content


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    """Clear cache before each test."""
    cache.clear()


@pytest.mark.django_db
class TestHomeView:
    def test_home_displays_content(self) -> None:
        Content.objects.create(
            title='Тестовое видео',
            description='Описание тестового видео',
            category='yoga',
            duration='10:00',
        )
        client = Client()
        response = client.get('/')
        page_content = response.content.decode('utf-8')
        assert 'Тестовое видео' in page_content

    def test_home_displays_max_6_items(self) -> None:
        for i in range(8):
            Content.objects.create(
                title=f'Контент {i}',
                description=f'Описание {i}',
                category='yoga',
            )
        client = Client()
        response = client.get('/')
        assert len(response.context['videos']) == 6

    def test_home_shows_empty_message_when_no_content(self) -> None:
        client = Client()
        response = client.get('/')
        page_content = response.content.decode('utf-8')
        assert 'Контента пока нет' in page_content

    def test_content_card_shows_category_yoga(self) -> None:
        Content.objects.create(
            title='Йога-видео',
            category='yoga',
        )
        client = Client()
        response = client.get('/')
        page_content = response.content.decode('utf-8')
        assert 'Йога' in page_content

    def test_content_card_shows_category_oils(self) -> None:
        Content.objects.create(
            title='Масла-видео',
            category='oils',
        )
        client = Client()
        response = client.get('/')
        page_content = response.content.decode('utf-8')
        assert 'Эфирные масла' in page_content
