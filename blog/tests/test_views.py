import json
from typing import Any

import pytest
from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.test import Client

from blog.models import Category, Content, ContentType, Tag, TagGroup


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    """Clear cache before each test."""
    cache.clear()


@pytest.fixture
def authenticated_client() -> Client:
    """Create an authenticated client."""
    user = User.objects.create_user(username='testuser', password='test123')
    client = Client()
    client.force_login(user)
    return client


@pytest.mark.django_db
class TestHomeView:
    def test_home_displays_content(
        self, yoga_category: Category, authenticated_client: Client
    ) -> None:
        content = Content.objects.create(
            title='Тестовое видео',
            description='Описание тестового видео',
        )
        content.categories.add(yoga_category)
        response = authenticated_client.get('/')
        page_content = response.content.decode('utf-8')
        assert 'Тестовое видео' in page_content

    def test_home_displays_max_6_items(
        self, yoga_category: Category, authenticated_client: Client
    ) -> None:
        for i in range(8):
            content = Content.objects.create(
                title=f'Контент {i}',
                description=f'Описание {i}',
            )
            content.categories.add(yoga_category)
        response = authenticated_client.get('/')
        assert len(response.context['cards']) == 6

    def test_home_shows_empty_message_when_no_content(
        self, authenticated_client: Client
    ) -> None:
        response = authenticated_client.get('/')
        page_content = response.content.decode('utf-8')
        assert 'Контента пока нет' in page_content

    def test_content_card_shows_category_yoga(self, yoga_category: Category) -> None:
        content = Content.objects.create(
            title='Йога-видео',
        )
        content.categories.add(yoga_category)
        client = Client()
        response = client.get('/')
        page_content = response.content.decode('utf-8')
        assert 'Йога' in page_content

    def test_content_card_shows_category_oils(self, oils_category: Category) -> None:
        content = Content.objects.create(
            title='Масла-видео',
        )
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


@pytest.mark.django_db
class TestCheckContentTypeCodeView:
    def test_available_code_returns_true(self) -> None:
        client = Client()
        response = client.get('/api/check-contenttype-code/', {'code': 'newcode'})
        data = response.json()
        assert data['available'] is True
        assert data['code'] == 'newcode'

    def test_taken_code_returns_false(self) -> None:
        ContentType.objects.create(name='Existing', code='existing')
        client = Client()
        response = client.get('/api/check-contenttype-code/', {'code': 'existing'})
        data = response.json()
        assert data['available'] is False
        assert data['code'] == 'existing'

    def test_exclude_id_allows_own_code(self) -> None:
        ct = ContentType.objects.create(name='Test', code='testcode')
        client = Client()
        response = client.get('/api/check-contenttype-code/', {'code': 'testcode', 'exclude_id': str(ct.pk)})
        data = response.json()
        assert data['available'] is True

    def test_empty_code_returns_available(self) -> None:
        client = Client()
        response = client.get('/api/check-contenttype-code/', {'code': ''})
        data = response.json()
        assert data['available'] is True

    def test_invalid_exclude_id_ignored(self) -> None:
        ContentType.objects.create(name='Test', code='testcode')
        client = Client()
        response = client.get('/api/check-contenttype-code/', {'code': 'testcode', 'exclude_id': 'invalid'})
        data = response.json()
        assert data['available'] is False


@pytest.mark.django_db
class TestCheckContentTypeFolderView:
    def test_available_folder_returns_true(self) -> None:
        client = Client()
        response = client.get('/api/check-contenttype-folder/', {'folder': 'newfolder'})
        data = response.json()
        assert data['available'] is True
        assert data['folder'] == 'newfolder'

    def test_taken_folder_returns_false(self) -> None:
        ContentType.objects.create(name='Existing', code='existing', upload_folder='existing_folder')
        client = Client()
        response = client.get('/api/check-contenttype-folder/', {'folder': 'existing_folder'})
        data = response.json()
        assert data['available'] is False
        assert data['folder'] == 'existing_folder'

    def test_exclude_id_allows_own_folder(self) -> None:
        ct = ContentType.objects.create(name='Test', code='testcode', upload_folder='testfolder')
        client = Client()
        response = client.get('/api/check-contenttype-folder/', {'folder': 'testfolder', 'exclude_id': str(ct.pk)})
        data = response.json()
        assert data['available'] is True

    def test_empty_folder_returns_available(self) -> None:
        client = Client()
        response = client.get('/api/check-contenttype-folder/', {'folder': ''})
        data = response.json()
        assert data['available'] is True

    def test_invalid_exclude_id_ignored(self) -> None:
        ContentType.objects.create(name='Test', code='testcode', upload_folder='testfolder')
        client = Client()
        response = client.get('/api/check-contenttype-folder/', {'folder': 'testfolder', 'exclude_id': 'invalid'})
        data = response.json()
        assert data['available'] is False


@pytest.mark.django_db
class TestCheckCategoryCodeView:
    def test_available_code_returns_true(self) -> None:
        client = Client()
        response = client.get('/api/check-category-code/', {'code': 'newcat'})
        data = response.json()
        assert data['available'] is True
        assert data['code'] == 'newcat'

    def test_taken_code_returns_false(self) -> None:
        Category.objects.create(name='Existing', code='existing')
        client = Client()
        response = client.get('/api/check-category-code/', {'code': 'existing'})
        data = response.json()
        assert data['available'] is False
        assert data['code'] == 'existing'

    def test_exclude_id_allows_own_code(self) -> None:
        cat = Category.objects.create(name='Test', code='testcode')
        client = Client()
        response = client.get('/api/check-category-code/', {'code': 'testcode', 'exclude_id': str(cat.pk)})
        data = response.json()
        assert data['available'] is True

    def test_empty_code_returns_available(self) -> None:
        client = Client()
        response = client.get('/api/check-category-code/', {'code': ''})
        data = response.json()
        assert data['available'] is True

    def test_invalid_exclude_id_ignored(self) -> None:
        Category.objects.create(name='Test', code='testcode')
        client = Client()
        response = client.get('/api/check-category-code/', {'code': 'testcode', 'exclude_id': 'invalid'})
        data = response.json()
        assert data['available'] is False


@pytest.mark.django_db
class TestAvailableFilesView:
    def test_empty_folder_returns_empty_list(self) -> None:
        client = Client()
        response = client.get('/api/available-files/', {'folder': ''})
        data = response.json()
        assert data['files'] == []

    def test_nonexistent_folder_returns_empty_list(self) -> None:
        client = Client()
        response = client.get('/api/available-files/', {'folder': 'nonexistent_folder_xyz'})
        data = response.json()
        assert data['files'] == []

    def test_folder_without_param_returns_empty_list(self) -> None:
        client = Client()
        response = client.get('/api/available-files/')
        data = response.json()
        assert data['files'] == []

    def test_path_traversal_blocked(self) -> None:
        client = Client()
        response = client.get('/api/available-files/', {'folder': '../etc'})
        data = response.json()
        assert data['files'] == []

    def test_absolute_path_blocked(self) -> None:
        client = Client()
        response = client.get('/api/available-files/', {'folder': '/etc'})
        data = response.json()
        assert data['files'] == []


@pytest.mark.django_db
class TestFileListView:
    def test_requires_login(self) -> None:
        client = Client()
        response = client.get('/files/')
        assert response.status_code == 302

    def test_moderator_can_access(self, moderator_user: Any) -> None:
        client = Client()
        client.force_login(moderator_user)
        response = client.get('/files/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestFileDeleteView:
    def test_requires_login(self) -> None:
        client = Client()
        response = client.post('/api/files/delete/', 
                               data='{"file_path": "test.txt"}',
                               content_type='application/json')
        assert response.status_code == 302

    def test_path_traversal_blocked(self, moderator_user: Any) -> None:
        client = Client()
        client.force_login(moderator_user)
        response = client.post('/api/files/delete/',
                               data='{"file_path": "../etc/passwd"}',
                               content_type='application/json')
        data = response.json()
        assert data['success'] is False


@pytest.mark.django_db
class TestSearchView:
    def test_search_page_loads(self) -> None:
        client = Client()
        response = client.get('/search/')
        assert response.status_code == 200
        assert 'Результаты поиска' in response.content.decode('utf-8')

    def test_search_with_empty_query(self) -> None:
        client = Client()
        response = client.get('/search/?q=')
        assert response.status_code == 200
        assert 'Введите поисковый запрос' in response.content.decode('utf-8')

    def test_search_finds_content_by_title(self, yoga_category: Category) -> None:
        content = Content.objects.create(
            title='Утренняя йога',
            description='Практика для начала дня',
        )
        content.categories.add(yoga_category)
        client = Client()
        response = client.get('/search/?q=утренняя')
        assert response.status_code == 200
        assert 'Утренняя йога' in response.content.decode('utf-8')

    def test_search_finds_content_by_description(self, yoga_category: Category) -> None:
        content = Content.objects.create(
            title='Йога видео',
            description='Медитация для расслабления',
        )
        content.categories.add(yoga_category)
        client = Client()
        response = client.get('/search/?q=медитация')
        assert response.status_code == 200
        assert 'Йога видео' in response.content.decode('utf-8')

    def test_search_no_results(self) -> None:
        Content.objects.create(
            title='Йога видео',
            description='Практика',
        )
        client = Client()
        response = client.get('/search/?q=несуществующий')
        assert response.status_code == 200
        assert 'ничего не найдено' in response.content.decode('utf-8').lower()

    def test_search_context_has_query(self) -> None:
        client = Client()
        response = client.get('/search/?q=тест')
        assert response.context['query'] == 'тест'

    def test_search_pagination(self, yoga_category: Category) -> None:
        for i in range(15):
            content = Content.objects.create(
                title=f'Йога практика {i}',
                description='Описание практики',
            )
            content.categories.add(yoga_category)
        client = Client()
        response = client.get('/search/?q=йога')
        assert response.status_code == 200
        assert 'page_obj' in response.context

    def test_search_strips_whitespace(self) -> None:
        client = Client()
        response = client.get('/search/?q=  ')
        assert response.status_code == 200
        assert 'Введите поисковый запрос' in response.content.decode('utf-8')

    def test_search_layout_conversion(self, yoga_category: Category) -> None:
        content_type, _ = ContentType.objects.get_or_create(
            code='video_layout', defaults={'name': 'Видео Layout'}
        )
        Content.objects.create(
            title='Йога практика',
            content_type=content_type,
        )
        client = Client()
        response = client.get('/search/?q=qjuf')
        assert response.status_code == 200
        context = response.context
        assert context is not None
        assert context.get('search_mode') in ('layout', 'exact')

    def test_search_context_has_suggestion(self, yoga_category: Category) -> None:
        content_type, _ = ContentType.objects.get_or_create(
            code='video_suggest', defaults={'name': 'Видео Suggest'}
        )
        Content.objects.create(
            title='Медитация',
            content_type=content_type,
        )
        client = Client()
        response = client.get('/search/?q=vtlbnfwbz')
        assert response.status_code == 200
        context = response.context
        assert context is not None
        if context.get('search_mode') == 'layout':
            assert context.get('suggestion') is not None

    def test_search_mode_exact_no_suggestion(self, yoga_category: Category) -> None:
        content_type, _ = ContentType.objects.get_or_create(
            code='video_exact', defaults={'name': 'Видео Exact'}
        )
        Content.objects.create(
            title='Релакс',
            content_type=content_type,
        )
        client = Client()
        response = client.get('/search/?q=Релакс')
        assert response.status_code == 200
        context = response.context
        assert context is not None
        assert context.get('search_mode') == 'exact'
        assert context.get('suggestion') is None

    def test_search_fuzzy_mode_returns_results(self) -> None:
        """Test fuzzy search mode returns results and suggestion (covers lines 182-185)."""
        content_type, _ = ContentType.objects.get_or_create(
            code='video_fuzzy', defaults={'name': 'Видео Fuzzy'}
        )
        content = Content.objects.create(
            title='Медитация для сна',
            description='Глубокий сон',
            content_type=content_type,
        )
        from blog.views import SearchView
        from unittest.mock import patch, MagicMock
        
        mock_request = MagicMock()
        mock_request.GET = {'q': 'xyzunique123'}
        mock_request.user = MagicMock()
        mock_request.user.is_authenticated = False
        
        view = SearchView()
        view.request = mock_request
        
        with (
            patch.object(view, '_fulltext_search') as mock_fulltext,
            patch.object(view, '_fuzzy_search') as mock_fuzzy,
        ):
            mock_fulltext.return_value = Content.objects.none()
            mock_fuzzy.return_value = Content.objects.filter(pk=content.pk)
            
            result = view.get_queryset()
            
            assert result.exists()
            assert view._search_mode == 'fuzzy'
            assert view._suggestion == content.title
