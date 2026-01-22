import pytest
from django.contrib.auth.models import User
from django.test import Client

from blog.models import Category, Content, ContentType
from users.models import get_or_create_moderators_group


@pytest.mark.django_db
class TestContentListView:
    def test_anonymous_user_redirected(self) -> None:
        client = Client()
        response = client.get('/content/')
        assert response.status_code == 302
        assert '/users/login/' in response.url  # type: ignore[attr-defined]

    def test_regular_user_gets_403(self) -> None:
        user = User.objects.create_user(username='regular', password='test123')
        client = Client()
        client.force_login(user)
        response = client.get('/content/')
        assert response.status_code == 403

    def test_moderator_can_access(self) -> None:
        user = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        user.groups.add(group)
        client = Client()
        client.force_login(user)
        response = client.get('/content/')
        assert response.status_code == 200

    def test_shows_all_content(self, video_type: ContentType) -> None:
        admin = User.objects.create_superuser(username='admin', password='test123')
        Content.objects.create(title='Контент 1', content_type=video_type)
        Content.objects.create(title='Контент 2', content_type=video_type)
        client = Client()
        client.force_login(admin)
        response = client.get('/content/')
        content = response.content.decode('utf-8')
        assert 'Контент 1' in content
        assert 'Контент 2' in content


@pytest.mark.django_db
class TestContentCreateView:
    def test_anonymous_user_redirected(self) -> None:
        client = Client()
        response = client.get('/content/create/')
        assert response.status_code == 302

    def test_moderator_can_access_form(self) -> None:
        user = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        user.groups.add(group)
        client = Client()
        client.force_login(user)
        response = client.get('/content/create/')
        assert response.status_code == 200

    def test_moderator_can_create_content(self, yoga_category: Category, video_type: ContentType) -> None:
        user = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        user.groups.add(group)
        client = Client()
        client.force_login(user)
        response = client.post('/content/create/', {
            'title': 'Новый контент',
            'description': 'Описание',
            'content_type': video_type.pk,
            'category': yoga_category.pk,
        })
        assert response.status_code == 302
        assert Content.objects.filter(title='Новый контент').exists()


@pytest.mark.django_db
class TestContentUpdateView:
    def test_anonymous_user_redirected(self, video_type: ContentType) -> None:
        content = Content.objects.create(title='Тест', content_type=video_type)
        client = Client()
        response = client.get(f'/content/{content.pk}/edit/')
        assert response.status_code == 302

    def test_moderator_can_access_edit_form(self, video_type: ContentType) -> None:
        user = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        user.groups.add(group)
        content = Content.objects.create(title='Тест', content_type=video_type)
        client = Client()
        client.force_login(user)
        response = client.get(f'/content/{content.pk}/edit/')
        assert response.status_code == 200
        assert 'Редактировать' in response.content.decode('utf-8')

    def test_moderator_can_update_content(self, yoga_category: Category, video_type: ContentType) -> None:
        user = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        user.groups.add(group)
        content = Content.objects.create(title='Старый заголовок', content_type=video_type)
        client = Client()
        client.force_login(user)
        response = client.post(f'/content/{content.pk}/edit/', {
            'title': 'Новый заголовок',
            'description': 'Описание',
            'content_type': video_type.pk,
            'category': yoga_category.pk,
        })
        assert response.status_code == 302
        content.refresh_from_db()
        assert content.title == 'Новый заголовок'


@pytest.mark.django_db
class TestContentDeleteView:
    def test_anonymous_user_redirected(self, video_type: ContentType) -> None:
        content = Content.objects.create(title='Тест', content_type=video_type)
        client = Client()
        response = client.get(f'/content/{content.pk}/delete/')
        assert response.status_code == 302

    def test_moderator_can_delete_content(self, video_type: ContentType) -> None:
        user = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        user.groups.add(group)
        content = Content.objects.create(title='Удалить меня', content_type=video_type)
        client = Client()
        client.force_login(user)
        response = client.post(f'/content/{content.pk}/delete/')
        assert response.status_code == 302
        assert not Content.objects.filter(title='Удалить меня').exists()
