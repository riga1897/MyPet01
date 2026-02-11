import os
import tempfile

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client

from blog.models import Category, Content, ContentType
from blog.views import (
    get_available_thumbnails,
    validate_existing_file,
    validate_existing_thumbnail,
)
from tests.utils_files import safe_remove_file
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
    def test_anonymous_user_redirected(self) -> None:
        content = Content.objects.create(title='Тест')
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

    def test_detach_thumbnail_clears_thumbnail(self, video_type: ContentType) -> None:
        user = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        user.groups.add(group)
        content = Content.objects.create(title='С миниатюрой', content_type=video_type)
        Content.objects.filter(pk=content.pk).update(thumbnail='thumbnails/test.jpg')
        content.refresh_from_db()
        assert content.thumbnail == 'thumbnails/test.jpg'
        client = Client()
        client.force_login(user)
        response = client.post(f'/content/{content.pk}/edit/', {
            'title': 'С миниатюрой',
            'description': '',
            'content_type': video_type.pk,
            'detach_thumbnail': 'true',
        })
        assert response.status_code == 302
        content.refresh_from_db()
        assert content.thumbnail == ''


@pytest.mark.django_db
class TestContentDeleteView:
    def test_anonymous_user_redirected(self) -> None:
        content = Content.objects.create(title='Тест')
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

    def test_delete_view_get_context_data(self, video_type: ContentType) -> None:
        user = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        user.groups.add(group)
        content = Content.objects.create(title='Контент', content_type=video_type)
        client = Client()
        client.force_login(user)
        response = client.get(f'/content/{content.pk}/delete/')
        assert response.status_code == 200
        assert response.context['is_moderator'] is True


@pytest.mark.django_db
class TestGetAvailableThumbnails:
    def test_returns_empty_when_no_dir(self) -> None:
        result = get_available_thumbnails()
        assert result == [] or isinstance(result, list)

    def test_returns_thumbnails_when_exist(self, tmp_path: 'tempfile.TemporaryDirectory[str]') -> None:
        thumbnails_path = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
        os.makedirs(thumbnails_path, exist_ok=True)
        test_file = os.path.join(thumbnails_path, 'test_thumb.jpg')
        with open(test_file, 'w') as f:
            f.write('test')
        try:
            result = get_available_thumbnails()
            assert 'thumbnails/test_thumb.jpg' in result
        finally:
            if os.path.exists(test_file):
                safe_remove_file(test_file)


@pytest.mark.django_db
class TestValidateExistingFile:
    def test_returns_false_when_empty(self, video_type: ContentType) -> None:
        assert validate_existing_file('', video_type) is False

    def test_returns_false_when_no_content_type(self) -> None:
        assert validate_existing_file('videos/test.mp4', None) is False

    def test_returns_false_with_path_traversal(self, video_type: ContentType) -> None:
        assert validate_existing_file('../etc/passwd', video_type) is False
        assert validate_existing_file('/etc/passwd', video_type) is False

    def test_returns_false_wrong_prefix(self, video_type: ContentType) -> None:
        assert validate_existing_file('photos/wrong.jpg', video_type) is False

    def test_returns_false_file_not_exists(self, video_type: ContentType) -> None:
        assert validate_existing_file('videos/nonexistent.mp4', video_type) is False

    def test_returns_true_for_valid_file(self, video_type: ContentType) -> None:
        folder_path = os.path.join(settings.MEDIA_ROOT, video_type.upload_folder)
        os.makedirs(folder_path, exist_ok=True)
        test_file = os.path.join(folder_path, 'valid_test.mp4')
        with open(test_file, 'w') as f:
            f.write('test')
        try:
            result = validate_existing_file('videos/valid_test.mp4', video_type)
            assert result is True
        finally:
            if os.path.exists(test_file):
                safe_remove_file(test_file)


@pytest.mark.django_db
class TestValidateExistingThumbnail:
    def test_returns_false_when_empty(self) -> None:
        assert validate_existing_thumbnail('') is False

    def test_returns_false_with_path_traversal(self) -> None:
        assert validate_existing_thumbnail('../etc/passwd') is False
        assert validate_existing_thumbnail('/etc/passwd') is False

    def test_returns_false_wrong_prefix(self) -> None:
        assert validate_existing_thumbnail('videos/file.mp4') is False

    def test_returns_false_file_not_exists(self) -> None:
        assert validate_existing_thumbnail('thumbnails/nonexistent.jpg') is False

    def test_returns_true_for_valid_thumbnail(self) -> None:
        thumbnails_path = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
        os.makedirs(thumbnails_path, exist_ok=True)
        test_file = os.path.join(thumbnails_path, 'valid_thumb.jpg')
        with open(test_file, 'w') as f:
            f.write('test')
        try:
            result = validate_existing_thumbnail('thumbnails/valid_thumb.jpg')
            assert result is True
        finally:
            if os.path.exists(test_file):
                safe_remove_file(test_file)


@pytest.mark.django_db
class TestContentCreateViewExistingFiles:
    def test_create_with_existing_file(self, video_type: ContentType) -> None:
        user = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        user.groups.add(group)
        folder_path = os.path.join(settings.MEDIA_ROOT, video_type.upload_folder)
        os.makedirs(folder_path, exist_ok=True)
        test_file = os.path.join(folder_path, 'existing.mp4')
        with open(test_file, 'w') as f:
            f.write('test')
        try:
            client = Client()
            client.force_login(user)
            response = client.post('/content/create/', {
                'title': 'С существующим файлом',
                'description': 'Описание',
                'content_type': video_type.pk,
                'existing_file': 'videos/existing.mp4',
            })
            assert response.status_code == 302
            content = Content.objects.get(title='С существующим файлом')
            assert str(content.video_file) == 'videos/existing.mp4'
        finally:
            if os.path.exists(test_file):
                safe_remove_file(test_file)

    def test_create_with_invalid_existing_file(self, video_type: ContentType) -> None:
        user = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        user.groups.add(group)
        client = Client()
        client.force_login(user)
        response = client.post('/content/create/', {
            'title': 'С несуществующим файлом',
            'description': 'Описание',
            'content_type': video_type.pk,
            'existing_file': 'videos/nonexistent.mp4',
        })
        assert response.status_code == 200
        form = response.context['form']
        assert 'Выбранный файл недоступен' in str(form.errors)

    def test_create_with_existing_thumbnail(self, video_type: ContentType) -> None:
        user = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        user.groups.add(group)
        thumbnails_path = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
        os.makedirs(thumbnails_path, exist_ok=True)
        test_file = os.path.join(thumbnails_path, 'existing_thumb.jpg')
        with open(test_file, 'w') as f:
            f.write('test')
        try:
            client = Client()
            client.force_login(user)
            response = client.post('/content/create/', {
                'title': 'С миниатюрой',
                'description': 'Описание',
                'content_type': video_type.pk,
                'existing_thumbnail': 'thumbnails/existing_thumb.jpg',
            })
            assert response.status_code == 302
            content = Content.objects.get(title='С миниатюрой')
            assert str(content.thumbnail) == 'thumbnails/existing_thumb.jpg'
        finally:
            if os.path.exists(test_file):
                safe_remove_file(test_file)

    def test_create_with_invalid_existing_thumbnail(self, video_type: ContentType) -> None:
        user = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        user.groups.add(group)
        client = Client()
        client.force_login(user)
        response = client.post('/content/create/', {
            'title': 'С несуществующей миниатюрой',
            'description': 'Описание',
            'content_type': video_type.pk,
            'existing_thumbnail': 'thumbnails/nonexistent.jpg',
        })
        assert response.status_code == 200
        form = response.context['form']
        assert 'Выбранная миниатюра недоступна' in str(form.errors)


@pytest.mark.django_db
class TestContentUpdateViewExistingFiles:
    def test_update_with_existing_file(self, video_type: ContentType) -> None:
        user = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        user.groups.add(group)
        content = Content.objects.create(title='Контент', content_type=video_type)
        folder_path = os.path.join(settings.MEDIA_ROOT, video_type.upload_folder)
        os.makedirs(folder_path, exist_ok=True)
        test_file = os.path.join(folder_path, 'update_existing.mp4')
        with open(test_file, 'w') as f:
            f.write('test')
        try:
            client = Client()
            client.force_login(user)
            response = client.post(f'/content/{content.pk}/edit/', {
                'title': 'Контент',
                'description': '',
                'content_type': video_type.pk,
                'existing_file': 'videos/update_existing.mp4',
            })
            assert response.status_code == 302
            content.refresh_from_db()
            assert str(content.video_file) == 'videos/update_existing.mp4'
        finally:
            if os.path.exists(test_file):
                safe_remove_file(test_file)

    def test_update_with_invalid_existing_file(self, video_type: ContentType) -> None:
        user = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        user.groups.add(group)
        content = Content.objects.create(title='Контент', content_type=video_type)
        client = Client()
        client.force_login(user)
        response = client.post(f'/content/{content.pk}/edit/', {
            'title': 'Контент',
            'description': '',
            'content_type': video_type.pk,
            'existing_file': 'videos/bad_path.mp4',
        })
        assert response.status_code == 200
        form = response.context['form']
        assert 'Выбранный файл недоступен' in str(form.errors)

    def test_update_detach_file(self, video_type: ContentType) -> None:
        user = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        user.groups.add(group)
        content = Content.objects.create(title='С файлом', content_type=video_type)
        Content.objects.filter(pk=content.pk).update(video_file='videos/old.mp4')
        content.refresh_from_db()
        client = Client()
        client.force_login(user)
        response = client.post(f'/content/{content.pk}/edit/', {
            'title': 'С файлом',
            'description': '',
            'content_type': video_type.pk,
            'detach_file': 'true',
        })
        assert response.status_code == 302
        content.refresh_from_db()
        assert content.video_file == ''

    def test_update_with_existing_thumbnail(self, video_type: ContentType) -> None:
        user = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        user.groups.add(group)
        content = Content.objects.create(title='Контент', content_type=video_type)
        thumbnails_path = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
        os.makedirs(thumbnails_path, exist_ok=True)
        test_file = os.path.join(thumbnails_path, 'update_thumb.jpg')
        with open(test_file, 'w') as f:
            f.write('test')
        try:
            client = Client()
            client.force_login(user)
            response = client.post(f'/content/{content.pk}/edit/', {
                'title': 'Контент',
                'description': '',
                'content_type': video_type.pk,
                'existing_thumbnail': 'thumbnails/update_thumb.jpg',
            })
            assert response.status_code == 302
            content.refresh_from_db()
            assert str(content.thumbnail) == 'thumbnails/update_thumb.jpg'
        finally:
            if os.path.exists(test_file):
                safe_remove_file(test_file)

    def test_update_with_invalid_existing_thumbnail(self, video_type: ContentType) -> None:
        user = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        user.groups.add(group)
        content = Content.objects.create(title='Контент', content_type=video_type)
        client = Client()
        client.force_login(user)
        response = client.post(f'/content/{content.pk}/edit/', {
            'title': 'Контент',
            'description': '',
            'content_type': video_type.pk,
            'existing_thumbnail': 'thumbnails/bad_thumb.jpg',
        })
        assert response.status_code == 200
        form = response.context['form']
        assert 'Выбранная миниатюра недоступна' in str(form.errors)
