import pytest
from django.test import Client
from blog.models import Video


@pytest.mark.django_db
class TestHomeViewWithVideos:
    def test_home_displays_videos(self) -> None:
        Video.objects.create(
            title='Тестовое видео',
            description='Описание тестового видео',
            category='yoga',
            duration='10:00',
        )
        client = Client()
        response = client.get('/')
        content = response.content.decode('utf-8')
        assert 'Тестовое видео' in content

    def test_home_displays_max_6_videos(self) -> None:
        for i in range(8):
            Video.objects.create(
                title=f'Видео {i}',
                description=f'Описание {i}',
                category='yoga',
            )
        client = Client()
        response = client.get('/')
        assert response.context['videos'].count() == 6

    def test_home_shows_empty_message_when_no_videos(self) -> None:
        client = Client()
        response = client.get('/')
        content = response.content.decode('utf-8')
        assert 'Видео пока нет' in content

    def test_video_card_shows_category_yoga(self) -> None:
        Video.objects.create(
            title='Йога-видео',
            category='yoga',
        )
        client = Client()
        response = client.get('/')
        content = response.content.decode('utf-8')
        assert 'Йога' in content

    def test_video_card_shows_category_oils(self) -> None:
        Video.objects.create(
            title='Масла-видео',
            category='oils',
        )
        client = Client()
        response = client.get('/')
        content = response.content.decode('utf-8')
        assert 'Эфирные масла' in content
