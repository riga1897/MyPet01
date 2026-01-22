"""Tests for blog caching functionality."""
from __future__ import annotations

from django.core.cache import cache
from django.test import TestCase

from blog.cache import (
    CONTENT_LIST_CACHE_KEY,
    get_cached_content_list,
    invalidate_content_cache,
    set_cached_content_list,
)
from blog.models import Category, Content, ContentType


class CacheUtilsTestCase(TestCase):
    """Tests for cache utility functions."""

    def setUp(self) -> None:
        cache.clear()
        self.yoga_category, _ = Category.objects.get_or_create(
            code='yoga',
            defaults={'name': 'Йога', 'slug': 'yoga'},
        )
        self.video_type, _ = ContentType.objects.get_or_create(
            code='video',
            defaults={'name': 'Видео', 'slug': 'video', 'upload_folder': 'videos'},
        )
        self.photo_type, _ = ContentType.objects.get_or_create(
            code='photo',
            defaults={'name': 'Фото', 'slug': 'photo', 'upload_folder': 'photos'},
        )
        self.content = Content.objects.create(
            title='Test Content',
            description='Test Description',
            content_type=self.video_type,
            category=self.yoga_category,
        )

    def tearDown(self) -> None:
        cache.clear()

    def test_get_cached_content_list_returns_none_when_empty(self) -> None:
        """Test that get_cached_content_list returns None when cache is empty."""
        result = get_cached_content_list()
        self.assertIsNone(result)

    def test_set_cached_content_list_caches_queryset(self) -> None:
        """Test that set_cached_content_list caches the queryset."""
        queryset = Content.objects.all()
        result = set_cached_content_list(queryset, limit=6)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, 'Test Content')

        cached = cache.get(CONTENT_LIST_CACHE_KEY)
        self.assertIsNotNone(cached)
        self.assertEqual(len(cached), 1)

    def test_get_cached_content_list_returns_cached_data(self) -> None:
        """Test that get_cached_content_list returns cached data."""
        queryset = Content.objects.all()
        set_cached_content_list(queryset, limit=6)

        result = get_cached_content_list()
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(len(result), 1)

    def test_invalidate_content_cache_clears_cache(self) -> None:
        """Test that invalidate_content_cache clears the cache."""
        queryset = Content.objects.all()
        set_cached_content_list(queryset, limit=6)

        invalidate_content_cache()

        result = get_cached_content_list()
        self.assertIsNone(result)

    def test_set_cached_content_list_respects_limit(self) -> None:
        """Test that set_cached_content_list respects the limit parameter."""
        for i in range(10):
            Content.objects.create(
                title=f'Content {i}',
                description=f'Description {i}',
                content_type=self.video_type,
                category=self.yoga_category,
            )

        queryset = Content.objects.all()
        result = set_cached_content_list(queryset, limit=5)

        self.assertEqual(len(result), 5)


class CacheSignalsTestCase(TestCase):
    """Tests for cache invalidation signals."""

    def setUp(self) -> None:
        cache.clear()
        self.yoga_category, _ = Category.objects.get_or_create(
            code='yoga',
            defaults={'name': 'Йога', 'slug': 'yoga'},
        )
        self.oils_category, _ = Category.objects.get_or_create(
            code='oils',
            defaults={'name': 'Эфирные масла', 'slug': 'oils'},
        )
        self.video_type, _ = ContentType.objects.get_or_create(
            code='video',
            defaults={'name': 'Видео', 'slug': 'video', 'upload_folder': 'videos'},
        )
        self.photo_type, _ = ContentType.objects.get_or_create(
            code='photo',
            defaults={'name': 'Фото', 'slug': 'photo', 'upload_folder': 'photos'},
        )

    def tearDown(self) -> None:
        cache.clear()

    def test_cache_invalidated_on_content_save(self) -> None:
        """Test that cache is invalidated when content is saved."""
        content = Content.objects.create(
            title='Test Content',
            description='Test Description',
            content_type=self.video_type,
            category=self.yoga_category,
        )

        queryset = Content.objects.all()
        set_cached_content_list(queryset, limit=6)
        self.assertIsNotNone(get_cached_content_list())

        content.title = 'Updated Title'
        content.save()

        self.assertIsNone(get_cached_content_list())

    def test_cache_invalidated_on_content_create(self) -> None:
        """Test that cache is invalidated when content is created."""
        queryset = Content.objects.all()
        set_cached_content_list(queryset, limit=6)

        Content.objects.create(
            title='New Content',
            description='New Description',
            content_type=self.photo_type,
            category=self.oils_category,
        )

        self.assertIsNone(get_cached_content_list())

    def test_cache_invalidated_on_content_delete(self) -> None:
        """Test that cache is invalidated when content is deleted."""
        content = Content.objects.create(
            title='Test Content',
            description='Test Description',
            content_type=self.video_type,
            category=self.yoga_category,
        )

        queryset = Content.objects.all()
        set_cached_content_list(queryset, limit=6)
        self.assertIsNotNone(get_cached_content_list())

        content.delete()

        self.assertIsNone(get_cached_content_list())
