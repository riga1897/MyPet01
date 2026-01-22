import json

import pytest
from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.test import Client

from blog.models import Category, Content, Tag, TagGroup


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    """Clear cache before each test."""
    cache.clear()


@pytest.mark.django_db
class TestHomeView:
    def test_home_displays_content(self, yoga_category: Category) -> None:
        content = Content.objects.create(
            title='Тестовое видео',
            description='Описание тестового видео',
            duration='10:00',
        )
        content.categories.add(yoga_category)
        client = Client()
        response = client.get('/')
        page_content = response.content.decode('utf-8')
        assert 'Тестовое видео' in page_content

    def test_home_displays_max_6_items(self, yoga_category: Category) -> None:
        for i in range(8):
            content = Content.objects.create(
                title=f'Контент {i}',
                description=f'Описание {i}',
            )
            content.categories.add(yoga_category)
        client = Client()
        response = client.get('/')
        assert len(response.context['videos']) == 6

    def test_home_shows_empty_message_when_no_content(self) -> None:
        client = Client()
        response = client.get('/')
        page_content = response.content.decode('utf-8')
        assert 'Контента пока нет' in page_content

    def test_content_card_shows_category_yoga(self, yoga_category: Category) -> None:
        content = Content.objects.create(title='Йога-видео')
        content.categories.add(yoga_category)
        client = Client()
        response = client.get('/')
        page_content = response.content.decode('utf-8')
        assert 'Йога' in page_content

    def test_content_card_shows_category_oils(self, oils_category: Category) -> None:
        content = Content.objects.create(title='Масла-видео')
        content.categories.add(oils_category)
        client = Client()
        response = client.get('/')
        page_content = response.content.decode('utf-8')
        assert 'Эфирные масла' in page_content

    def test_home_shows_categories_from_database(
        self, yoga_category: Category, oils_category: Category
    ) -> None:
        client = Client()
        response = client.get('/')
        page_content = response.content.decode('utf-8')
        assert 'Йога' in page_content
        assert 'Эфирные масла' in page_content


@pytest.fixture
def moderator_user(db: None) -> User:
    """Create a moderator user."""
    user = User.objects.create_user(
        username='moderator',
        password='testpass123',
    )
    group, _ = Group.objects.get_or_create(name='Модераторы')
    user.groups.add(group)
    return user


@pytest.fixture
def tag_group(db: None) -> TagGroup:
    """Create a tag group for testing."""
    return TagGroup.objects.create(name='Месяц практики')


@pytest.mark.django_db
class TestTagReorderView:
    def test_reorder_tags_as_moderator(
        self, moderator_user: User, tag_group: TagGroup
    ) -> None:
        tag1 = Tag.objects.create(name='Первый месяц', group=tag_group, order=0)
        tag2 = Tag.objects.create(name='Второй месяц', group=tag_group, order=1)
        tag3 = Tag.objects.create(name='Третий месяц', group=tag_group, order=2)

        client = Client()
        client.login(username='moderator', password='testpass123')

        response = client.post(
            '/tags/reorder/',
            data=json.dumps({
                'tag_ids': [tag3.pk, tag1.pk, tag2.pk],
                'group_id': tag_group.pk,
            }),
            content_type='application/json',
        )

        assert response.status_code == 200
        assert response.json()['success'] is True

        tag1.refresh_from_db()
        tag2.refresh_from_db()
        tag3.refresh_from_db()
        assert tag3.order == 0
        assert tag1.order == 1
        assert tag2.order == 2

    def test_reorder_requires_authentication(self, tag_group: TagGroup) -> None:
        tag = Tag.objects.create(name='Тег', group=tag_group)
        client = Client()
        response = client.post(
            '/tags/reorder/',
            data=json.dumps({'tag_ids': [tag.pk], 'group_id': tag_group.pk}),
            content_type='application/json',
        )
        assert response.status_code == 302

    def test_reorder_empty_tag_ids(
        self, moderator_user: User, tag_group: TagGroup
    ) -> None:
        client = Client()
        client.login(username='moderator', password='testpass123')
        response = client.post(
            '/tags/reorder/',
            data=json.dumps({'tag_ids': [], 'group_id': tag_group.pk}),
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'error' in response.json()

    def test_reorder_missing_group_id(
        self, moderator_user: User, tag_group: TagGroup
    ) -> None:
        tag = Tag.objects.create(name='Тег', group=tag_group)
        client = Client()
        client.login(username='moderator', password='testpass123')
        response = client.post(
            '/tags/reorder/',
            data=json.dumps({'tag_ids': [tag.pk]}),
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'group' in response.json()['error'].lower()

    def test_reorder_cross_group_rejected(
        self, moderator_user: User, tag_group: TagGroup
    ) -> None:
        other_group = TagGroup.objects.create(name='Другая группа')
        tag1 = Tag.objects.create(name='Тег 1', group=tag_group)
        tag2 = Tag.objects.create(name='Тег 2', group=other_group)

        client = Client()
        client.login(username='moderator', password='testpass123')
        response = client.post(
            '/tags/reorder/',
            data=json.dumps({
                'tag_ids': [tag1.pk, tag2.pk],
                'group_id': tag_group.pk,
            }),
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'group' in response.json()['error'].lower()

    def test_reorder_invalid_json(self, moderator_user: User) -> None:
        client = Client()
        client.login(username='moderator', password='testpass123')
        response = client.post(
            '/tags/reorder/',
            data='not json',
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'error' in response.json()
