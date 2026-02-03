"""Tests for file management views."""
import json
import os

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from blog.models import Content, ContentType
from users.models import get_or_create_moderators_group


@pytest.fixture
def video_type() -> ContentType:
    """Create and return the video content type."""
    content_type, _ = ContentType.objects.get_or_create(
        code='video',
        defaults={'name': 'Видео', 'upload_folder': 'videos'},
    )
    return content_type


@pytest.fixture
def moderator_client() -> tuple[Client, User]:
    """Create a logged-in moderator client."""
    user = User.objects.create_user(username='mod', password='test123')
    group = get_or_create_moderators_group()
    user.groups.add(group)
    client = Client()
    client.force_login(user)
    return client, user


@pytest.mark.django_db
class TestAvailableFilesView:
    def test_returns_empty_when_invalid_folder(self, moderator_client: tuple[Client, User]) -> None:
        client, _ = moderator_client
        response = client.get('/api/available-files/', {'folder': '../etc'})
        data = response.json()
        assert data['files'] == []

    def test_returns_empty_when_folder_not_exists(self, moderator_client: tuple[Client, User]) -> None:
        client, _ = moderator_client
        response = client.get('/api/available-files/', {'folder': 'nonexistent_folder'})
        data = response.json()
        assert data['files'] == []

    def test_returns_empty_when_no_folder(self, moderator_client: tuple[Client, User]) -> None:
        client, _ = moderator_client
        response = client.get('/api/available-files/', {'folder': ''})
        data = response.json()
        assert data['files'] == []

    def test_returns_empty_with_absolute_path(self, moderator_client: tuple[Client, User]) -> None:
        client, _ = moderator_client
        response = client.get('/api/available-files/', {'folder': '/etc/passwd'})
        data = response.json()
        assert data['files'] == []

    def test_returns_files_from_folder(
        self, moderator_client: tuple[Client, User], video_type: ContentType
    ) -> None:
        client, _ = moderator_client
        folder_path = os.path.join(settings.MEDIA_ROOT, 'videos')
        os.makedirs(folder_path, exist_ok=True)
        test_file = os.path.join(folder_path, 'available_test.mp4')
        with open(test_file, 'w') as f:
            f.write('test')
        try:
            response = client.get('/api/available-files/', {'folder': 'videos'})
            data = response.json()
            filenames = [f['name'] for f in data['files']]
            assert 'available_test.mp4' in filenames
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_excludes_used_files(
        self, moderator_client: tuple[Client, User], video_type: ContentType
    ) -> None:
        client, _ = moderator_client
        folder_path = os.path.join(settings.MEDIA_ROOT, 'videos')
        os.makedirs(folder_path, exist_ok=True)
        test_file = os.path.join(folder_path, 'used_file.mp4')
        with open(test_file, 'w') as f:
            f.write('test')
        content = Content.objects.create(title='Контент', content_type=video_type)
        Content.objects.filter(pk=content.pk).update(video_file='videos/used_file.mp4')
        try:
            response = client.get('/api/available-files/', {'folder': 'videos'})
            data = response.json()
            filenames = [f['name'] for f in data['files']]
            assert 'used_file.mp4' not in filenames
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_includes_file_for_current_content(
        self, moderator_client: tuple[Client, User], video_type: ContentType
    ) -> None:
        client, _ = moderator_client
        folder_path = os.path.join(settings.MEDIA_ROOT, 'videos')
        os.makedirs(folder_path, exist_ok=True)
        test_file = os.path.join(folder_path, 'own_file.mp4')
        with open(test_file, 'w') as f:
            f.write('test')
        content = Content.objects.create(title='Контент', content_type=video_type)
        Content.objects.filter(pk=content.pk).update(video_file='videos/own_file.mp4')
        try:
            response = client.get(
                '/api/available-files/',
                {'folder': 'videos', 'content_id': str(content.pk)},
            )
            data = response.json()
            filenames = [f['name'] for f in data['files']]
            assert 'own_file.mp4' in filenames
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_handles_invalid_content_id(
        self, moderator_client: tuple[Client, User], video_type: ContentType
    ) -> None:
        client, _ = moderator_client
        folder_path = os.path.join(settings.MEDIA_ROOT, 'videos')
        os.makedirs(folder_path, exist_ok=True)
        response = client.get(
            '/api/available-files/',
            {'folder': 'videos', 'content_id': 'invalid'},
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestAvailableThumbnailsView:
    def test_returns_empty_when_no_thumbnails_dir(
        self, moderator_client: tuple[Client, User]
    ) -> None:
        client, _ = moderator_client
        response = client.get('/api/available-thumbnails/')
        data = response.json()
        assert 'files' in data

    def test_returns_thumbnails(self, moderator_client: tuple[Client, User]) -> None:
        client, _ = moderator_client
        thumbnails_path = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
        os.makedirs(thumbnails_path, exist_ok=True)
        test_file = os.path.join(thumbnails_path, 'test_thumb_api.jpg')
        with open(test_file, 'w') as f:
            f.write('test')
        try:
            response = client.get('/api/available-thumbnails/')
            data = response.json()
            filenames = [f['name'] for f in data['files']]
            assert 'test_thumb_api.jpg' in filenames
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_excludes_used_thumbnails(
        self, moderator_client: tuple[Client, User], video_type: ContentType
    ) -> None:
        client, _ = moderator_client
        thumbnails_path = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
        os.makedirs(thumbnails_path, exist_ok=True)
        test_file = os.path.join(thumbnails_path, 'used_thumb.jpg')
        with open(test_file, 'w') as f:
            f.write('test')
        content = Content.objects.create(title='Контент', content_type=video_type)
        Content.objects.filter(pk=content.pk).update(thumbnail='thumbnails/used_thumb.jpg')
        try:
            response = client.get('/api/available-thumbnails/')
            data = response.json()
            filenames = [f['name'] for f in data['files']]
            assert 'used_thumb.jpg' not in filenames
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_includes_thumb_for_current_content(
        self, moderator_client: tuple[Client, User], video_type: ContentType
    ) -> None:
        client, _ = moderator_client
        thumbnails_path = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
        os.makedirs(thumbnails_path, exist_ok=True)
        test_file = os.path.join(thumbnails_path, 'own_thumb.jpg')
        with open(test_file, 'w') as f:
            f.write('test')
        content = Content.objects.create(title='Контент', content_type=video_type)
        Content.objects.filter(pk=content.pk).update(thumbnail='thumbnails/own_thumb.jpg')
        try:
            response = client.get(
                '/api/available-thumbnails/',
                {'content_id': str(content.pk)},
            )
            data = response.json()
            filenames = [f['name'] for f in data['files']]
            assert 'own_thumb.jpg' in filenames
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_handles_invalid_content_id(
        self, moderator_client: tuple[Client, User]
    ) -> None:
        client, _ = moderator_client
        thumbnails_path = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
        os.makedirs(thumbnails_path, exist_ok=True)
        response = client.get(
            '/api/available-thumbnails/',
            {'content_id': 'invalid'},
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestFileListView:
    def test_requires_login(self) -> None:
        client = Client()
        response = client.get('/files/')
        assert response.status_code == 302

    def test_accessible_by_moderator(self, moderator_client: tuple[Client, User]) -> None:
        client, _ = moderator_client
        response = client.get('/files/')
        assert response.status_code == 200
        assert response.context['is_moderator'] is True


@pytest.mark.django_db
class TestFileUploadView:
    def test_requires_content_type(self, moderator_client: tuple[Client, User]) -> None:
        client, _ = moderator_client
        response = client.post('/api/files/upload/')
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False

    def test_requires_file(
        self, moderator_client: tuple[Client, User], video_type: ContentType
    ) -> None:
        client, _ = moderator_client
        response = client.post('/api/files/upload/', {'content_type_id': video_type.pk})
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False

    def test_rejects_nonexistent_content_type(
        self, moderator_client: tuple[Client, User]
    ) -> None:
        client, _ = moderator_client
        uploaded = SimpleUploadedFile('test.mp4', b'content', content_type='video/mp4')
        response = client.post('/api/files/upload/', {
            'content_type_id': 99999,
            'file': uploaded,
        })
        assert response.status_code == 404

    def test_successful_upload(
        self, moderator_client: tuple[Client, User], video_type: ContentType
    ) -> None:
        client, _ = moderator_client
        folder_path = os.path.join(settings.MEDIA_ROOT, 'videos')
        os.makedirs(folder_path, exist_ok=True)
        content = b'test video content for upload'
        uploaded = SimpleUploadedFile('upload_test.mp4', content, content_type='video/mp4')
        response = client.post('/api/files/upload/', {
            'content_type_id': video_type.pk,
            'file': uploaded,
        })
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'upload_test' in data['filename']
        uploaded_path = os.path.join(folder_path, data['filename'])
        if os.path.exists(uploaded_path):
            os.remove(uploaded_path)

    def test_upload_existing_file_returns_existing(
        self, moderator_client: tuple[Client, User], video_type: ContentType
    ) -> None:
        client, _ = moderator_client
        folder_path = os.path.join(settings.MEDIA_ROOT, 'videos')
        os.makedirs(folder_path, exist_ok=True)
        content = b'test video content duplicate'
        uploaded1 = SimpleUploadedFile('dup_test.mp4', content, content_type='video/mp4')
        response1 = client.post('/api/files/upload/', {
            'content_type_id': video_type.pk,
            'file': uploaded1,
        })
        assert response1.status_code == 200
        data1 = response1.json()
        filename = data1['filename']
        uploaded2 = SimpleUploadedFile('dup_test.mp4', content, content_type='video/mp4')
        response2 = client.post('/api/files/upload/', {
            'content_type_id': video_type.pk,
            'file': uploaded2,
        })
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2['success'] is True
        assert data2.get('existing') is True
        uploaded_path = os.path.join(folder_path, filename)
        if os.path.exists(uploaded_path):
            os.remove(uploaded_path)


@pytest.mark.django_db
class TestFileDeleteView:
    def test_requires_valid_json(self, moderator_client: tuple[Client, User]) -> None:
        client, _ = moderator_client
        response = client.post(
            '/api/files/delete/',
            'invalid json',
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_rejects_empty_path(self, moderator_client: tuple[Client, User]) -> None:
        client, _ = moderator_client
        response = client.post(
            '/api/files/delete/',
            json.dumps({'file_path': ''}),
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_rejects_path_traversal(self, moderator_client: tuple[Client, User]) -> None:
        client, _ = moderator_client
        response = client.post(
            '/api/files/delete/',
            json.dumps({'file_path': '../etc/passwd'}),
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_rejects_absolute_path(self, moderator_client: tuple[Client, User]) -> None:
        client, _ = moderator_client
        response = client.post(
            '/api/files/delete/',
            json.dumps({'file_path': '/etc/passwd'}),
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_rejects_used_file(
        self, moderator_client: tuple[Client, User], video_type: ContentType
    ) -> None:
        client, _ = moderator_client
        folder_path = os.path.join(settings.MEDIA_ROOT, 'videos')
        os.makedirs(folder_path, exist_ok=True)
        test_file = os.path.join(folder_path, 'used_for_delete.mp4')
        with open(test_file, 'w') as f:
            f.write('test')
        content = Content.objects.create(title='Контент', content_type=video_type)
        Content.objects.filter(pk=content.pk).update(video_file='videos/used_for_delete.mp4')
        try:
            response = client.post(
                '/api/files/delete/',
                json.dumps({'file_path': 'videos/used_for_delete.mp4'}),
                content_type='application/json',
            )
            assert response.status_code == 400
            assert os.path.exists(test_file)
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_rejects_nonexistent_file(
        self, moderator_client: tuple[Client, User]
    ) -> None:
        client, _ = moderator_client
        response = client.post(
            '/api/files/delete/',
            json.dumps({'file_path': 'videos/nonexistent.mp4'}),
            content_type='application/json',
        )
        assert response.status_code == 404

    def test_successful_delete(
        self, moderator_client: tuple[Client, User], video_type: ContentType
    ) -> None:
        client, _ = moderator_client
        folder_path = os.path.join(settings.MEDIA_ROOT, 'videos')
        os.makedirs(folder_path, exist_ok=True)
        test_file = os.path.join(folder_path, 'to_delete.mp4')
        with open(test_file, 'w') as f:
            f.write('test')
        try:
            response = client.post(
                '/api/files/delete/',
                json.dumps({'file_path': 'videos/to_delete.mp4'}),
                content_type='application/json',
            )
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert not os.path.exists(test_file)
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)


@pytest.mark.django_db
class TestProtectedMediaView:
    """Tests for protected media file serving."""

    def test_unauthenticated_redirect_to_login(self) -> None:
        """Unauthenticated users should be redirected to login."""
        client = Client()
        response = client.get('/media/videos/test.mp4')
        assert response.status_code == 302
        assert '/users/login/' in str(response.headers.get('Location', ''))

    def test_path_traversal_blocked(
        self, moderator_client: tuple[Client, User]
    ) -> None:
        """Path traversal attempts should return 404."""
        client, _ = moderator_client
        response = client.get('/media/../etc/passwd')
        assert response.status_code == 404

    def test_absolute_path_blocked(
        self, moderator_client: tuple[Client, User]
    ) -> None:
        """Absolute paths should return 404."""
        client, _ = moderator_client
        response = client.get('/media//etc/passwd')
        assert response.status_code == 404

    def test_nonexistent_file_returns_404(
        self, moderator_client: tuple[Client, User]
    ) -> None:
        """Non-existent files should return 404."""
        client, _ = moderator_client
        response = client.get('/media/videos/nonexistent.mp4')
        assert response.status_code == 404

    def test_successful_file_serve(
        self, moderator_client: tuple[Client, User]
    ) -> None:
        """Authenticated users can access media files."""
        client, _ = moderator_client
        folder_path = os.path.join(settings.MEDIA_ROOT, 'videos')
        os.makedirs(folder_path, exist_ok=True)
        test_file = os.path.join(folder_path, 'protected_test.mp4')
        with open(test_file, 'wb') as f:
            f.write(b'test video content')
        try:
            response = client.get('/media/videos/protected_test.mp4')
            assert response.status_code == 200
            assert response.get('Content-Type') == 'video/mp4'
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)


@pytest.mark.django_db
class TestPathTraversalProtection:
    """Tests for path traversal protection (covers lines 226, 241, 589, 707, 766, 787)."""

    def test_list_folder_files_path_traversal(
        self, moderator_client: tuple[Client, User]
    ) -> None:
        """Test path traversal protection in list folder files (line 589)."""
        client, _ = moderator_client
        response = client.get('/api/available-files/', {'folder': '../../../etc'})
        data = response.json()
        assert data['files'] == []

    def test_available_thumbnails_no_folder(
        self, moderator_client: tuple[Client, User]
    ) -> None:
        """Test available thumbnails when thumbnails folder doesn't exist (line 627)."""
        client, _ = moderator_client
        import shutil
        thumbnails_path = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
        backup_path = None
        if os.path.exists(thumbnails_path):
            backup_path = thumbnails_path + '_backup'
            shutil.move(thumbnails_path, backup_path)
        try:
            response = client.get('/api/available-thumbnails/')
            data = response.json()
            assert data['files'] == []
        finally:
            if backup_path and os.path.exists(backup_path):
                shutil.move(backup_path, thumbnails_path)

    def test_serve_media_path_traversal(self) -> None:
        """Test path traversal protection in serve_media (line 787)."""
        client = Client()
        response = client.get('/media/../../../etc/passwd')
        assert response.status_code == 404

    def test_file_delete_path_traversal(
        self, moderator_client: tuple[Client, User]
    ) -> None:
        """Test path traversal protection in file delete (line 766)."""
        client, _ = moderator_client
        response = client.post(
            '/api/file-delete/',
            data=json.dumps({'file_path': '../../../etc/passwd'}),
            content_type='application/json',
        )
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False


@pytest.mark.django_db
class TestFileUploadEdgeCases:
    """Tests for file upload edge cases (covers lines 707, 713, 716, 742-745)."""

    def test_upload_invalid_filename_with_dots(
        self, moderator_client: tuple[Client, User], video_type: ContentType
    ) -> None:
        """Test upload rejects filename with path traversal (line 713)."""
        client, _ = moderator_client
        file = SimpleUploadedFile(
            name='../evil.mp4',
            content=b'test content',
            content_type='video/mp4',
        )
        response = client.post(
            '/api/file-upload/',
            {'file': file, 'content_type_id': video_type.pk},
        )
        if response.status_code == 400:
            data = response.json()
            assert data['success'] is False

    def test_upload_empty_filename(
        self, moderator_client: tuple[Client, User], video_type: ContentType
    ) -> None:
        """Test upload rejects empty filename (line 716)."""
        client, _ = moderator_client
        file = SimpleUploadedFile(
            name='',
            content=b'test content',
            content_type='video/mp4',
        )
        response = client.post(
            '/api/file-upload/',
            {'file': file, 'content_type_id': video_type.pk},
        )
        assert response.status_code in (400, 200)


@pytest.mark.django_db
class TestSaveTagsEdgeCases:
    """Tests for save_tags edge cases (covers lines 481, 498-499)."""

    def test_save_tags_nonexistent_tags(
        self, moderator_client: tuple[Client, User]
    ) -> None:
        """Test save_tags with nonexistent tag IDs (line 481)."""
        from blog.models import TagGroup
        client, _ = moderator_client
        group = TagGroup.objects.create(name='Test Group')
        response = client.post(
            '/api/save-tags/',
            data=json.dumps({
                'group_id': group.pk,
                'tag_ids': [99999, 99998],
            }),
            content_type='application/json',
        )
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
