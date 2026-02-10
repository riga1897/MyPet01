"""Tests for management commands."""

from io import StringIO
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from blog.models import Category, Content, ContentType, Tag, TagGroup


User: Any = get_user_model()


@pytest.mark.django_db
class TestCreateSuperuserIfNotExists:
    """Tests for create_superuser_if_not_exists command."""

    def test_creates_superuser_when_not_exists(self) -> None:
        """Test superuser creation when user doesn't exist."""
        out = StringIO()

        call_command(
            'create_superuser_if_not_exists',
            '--username=testadmin',
            '--email=test@example.com',
            '--password=testpass123',
            stdout=out,
        )

        assert User.objects.filter(username='testadmin').exists()
        user = User.objects.get(username='testadmin')
        assert user.is_superuser
        assert user.is_staff
        assert user.email == 'test@example.com'
        assert 'created successfully' in out.getvalue()

    def test_skips_when_user_exists(self) -> None:
        """Test command skips creation when user already exists."""
        User.objects.create_superuser(
            username='existingadmin',
            email='existing@example.com',
            password='existingpass',
        )
        out = StringIO()

        call_command(
            'create_superuser_if_not_exists',
            '--username=existingadmin',
            '--email=new@example.com',
            '--password=newpass123',
            stdout=out,
        )

        assert 'already exists' in out.getvalue()
        assert User.objects.filter(username='existingadmin').count() == 1

    def test_error_when_no_password(self) -> None:
        """Test command shows error when password not provided."""
        err = StringIO()

        with patch.dict('os.environ', {}, clear=True):
            call_command(
                'create_superuser_if_not_exists',
                '--username=nopwdadmin',
                '--email=nopwd@example.com',
                stderr=err,
            )

        assert 'Password is required' in err.getvalue()
        assert not User.objects.filter(username='nopwdadmin').exists()

    def test_uses_env_variables(self) -> None:
        """Test command uses environment variables."""
        out = StringIO()

        with patch.dict('os.environ', {
            'DJANGO_SUPERUSER_USERNAME': 'envadmin',
            'DJANGO_SUPERUSER_EMAIL': 'env@example.com',
            'DJANGO_SUPERUSER_PASSWORD': 'envpass123',
        }):
            call_command('create_superuser_if_not_exists', stdout=out)

        assert User.objects.filter(username='envadmin').exists()
        user = User.objects.get(username='envadmin')
        assert user.email == 'env@example.com'


@pytest.mark.django_db
class TestSetupInitialStructure:
    """Tests for setup_initial_structure command."""

    def test_loads_initial_structure(self) -> None:
        """Test loading initial structure from fixtures."""
        out = StringIO()

        call_command('setup_initial_structure', '--force', stdout=out)

        assert ContentType.objects.exists()
        assert Category.objects.exists()
        assert TagGroup.objects.exists()
        assert Tag.objects.exists()
        assert 'Loaded:' in out.getvalue()

    def test_skips_when_data_exists(self) -> None:
        """Test command skips when data already exists."""
        Category.objects.create(name='Existing', code='existing')
        out = StringIO()

        call_command('setup_initial_structure', stdout=out)

        assert 'already exists' in out.getvalue()

    def test_force_reloads_data(self) -> None:
        """Test --force flag reloads data."""
        Category.objects.create(name='Existing', code='existing')
        out = StringIO()

        call_command('setup_initial_structure', '--force', stdout=out)

        assert 'Loaded:' in out.getvalue()


@pytest.mark.django_db
class TestSetupDemoContent:
    """Tests for setup_demo_content command."""

    def test_loads_demo_content(self) -> None:
        """Test loading demo content from fixtures."""
        call_command('setup_initial_structure', '--force')
        out = StringIO()

        call_command('setup_demo_content', '--force', stdout=out)

        assert Content.objects.exists()
        assert 'Loaded' in out.getvalue()
        assert 'demo content items' in out.getvalue()

    def test_skips_when_content_exists(self) -> None:
        """Test command skips when content already exists but still copies media."""
        call_command('setup_initial_structure', '--force')
        call_command('setup_demo_content', '--force')
        out = StringIO()

        call_command('setup_demo_content', stdout=out)

        output = out.getvalue()
        assert 'already exists' in output
        assert 'Copying demo media files' in output

    def test_force_reloads_content(self) -> None:
        """Test --force flag reloads content."""
        call_command('setup_initial_structure', '--force')
        call_command('setup_demo_content', '--force')
        out = StringIO()

        call_command('setup_demo_content', '--force', stdout=out)

        assert 'Loaded' in out.getvalue()

    def test_auto_loads_initial_structure_when_missing(self) -> None:
        """Test command auto-loads initial structure if missing (covers lines 36-37)."""
        from blog.models import Category, ContentType, Tag, TagGroup

        Content.objects.all().delete()
        Tag.objects.all().delete()
        TagGroup.objects.all().delete()
        Category.objects.all().delete()
        ContentType.objects.all().delete()

        out = StringIO()

        call_command('setup_demo_content', stdout=out)

        output = out.getvalue()
        assert 'Loading initial structure first' in output
        assert Content.objects.exists()

    def test_copies_demo_media_files(self, tmp_path: Path) -> None:
        """Test demo media files are copied to MEDIA_ROOT."""
        demo_media = tmp_path / 'demo_media' / 'thumbnails'
        demo_media.mkdir(parents=True)
        test_file = demo_media / 'test_image.jpg'
        test_file.write_bytes(b'fake image data')

        media_root = tmp_path / 'media'
        media_root.mkdir()

        with patch(
            'blog.management.commands.setup_demo_content.DEMO_MEDIA_DIR',
            tmp_path / 'demo_media',
        ), patch('django.conf.settings.MEDIA_ROOT', str(media_root)):
            call_command('setup_initial_structure', '--force')
            out = StringIO()
            call_command('setup_demo_content', '--force', stdout=out)

        assert (media_root / 'thumbnails' / 'test_image.jpg').exists()
        assert 'Copied 1 media files' in out.getvalue()

    def test_skips_existing_media_files(self, tmp_path: Path) -> None:
        """Test existing media files are not overwritten."""
        demo_media = tmp_path / 'demo_media' / 'thumbnails'
        demo_media.mkdir(parents=True)
        (demo_media / 'existing.jpg').write_bytes(b'new data')

        media_root = tmp_path / 'media' / 'thumbnails'
        media_root.mkdir(parents=True)
        (media_root / 'existing.jpg').write_bytes(b'old data')

        with patch(
            'blog.management.commands.setup_demo_content.DEMO_MEDIA_DIR',
            tmp_path / 'demo_media',
        ), patch('django.conf.settings.MEDIA_ROOT', str(tmp_path / 'media')):
            call_command('setup_initial_structure', '--force')
            out = StringIO()
            call_command('setup_demo_content', '--force', stdout=out)

        assert (media_root / 'existing.jpg').read_bytes() == b'old data'
        assert 'Copied 0 media files' in out.getvalue()

    def test_handles_missing_demo_media_dir(self, tmp_path: Path) -> None:
        """Test graceful handling when demo_media directory doesn't exist."""
        with patch(
            'blog.management.commands.setup_demo_content.DEMO_MEDIA_DIR',
            tmp_path / 'nonexistent',
        ):
            call_command('setup_initial_structure', '--force')
            out = StringIO()
            call_command('setup_demo_content', '--force', stdout=out)

        assert 'Demo media directory not found' in out.getvalue()
