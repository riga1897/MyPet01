"""Tests for blog caching functionality."""
from __future__ import annotations

from django.core.cache import cache
from django.test import TestCase

from blog.cache import (
    CONTENT_LIST_CACHE_KEY,
    FILTER_CONTEXT_CACHE_KEY,
    get_cached_content_ids,
    get_cached_filter_context,
    invalidate_content_cache,
    invalidate_filter_context_cache,
    set_cached_content_ids,
    set_cached_filter_context,
)
from blog.models import Category, Content, ContentType, Tag, TagGroup


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
            defaults={'name': 'Видео', 'upload_folder': 'videos'},
        )
        self.photo_type, _ = ContentType.objects.get_or_create(
            code='photo',
            defaults={'name': 'Фото', 'upload_folder': 'photos'},
        )
        self.content = Content.objects.create(
            title='Test Content',
            description='Test Description',
            content_type=self.video_type,
        )
        self.content.categories.add(self.yoga_category)

    def tearDown(self) -> None:
        cache.clear()

    def test_get_cached_content_ids_returns_none_when_empty(self) -> None:
        """Test that get_cached_content_ids returns None when cache is empty."""
        result = get_cached_content_ids()
        self.assertIsNone(result)

    def test_set_cached_content_ids_caches_ids(self) -> None:
        """Test that set_cached_content_ids caches content IDs."""
        queryset = Content.objects.all()
        result = set_cached_content_ids(queryset, limit=6)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.content.id)

        cached = cache.get(CONTENT_LIST_CACHE_KEY)
        self.assertIsNotNone(cached)
        self.assertEqual(len(cached), 1)

    def test_get_cached_content_ids_returns_cached_data(self) -> None:
        """Test that get_cached_content_ids returns cached data."""
        queryset = Content.objects.all()
        set_cached_content_ids(queryset, limit=6)

        result = get_cached_content_ids()
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.content.id)

    def test_invalidate_content_cache_clears_cache(self) -> None:
        """Test that invalidate_content_cache clears the cache."""
        queryset = Content.objects.all()
        set_cached_content_ids(queryset, limit=6)

        invalidate_content_cache()

        result = get_cached_content_ids()
        self.assertIsNone(result)

    def test_set_cached_content_ids_respects_limit(self) -> None:
        """Test that set_cached_content_ids respects the limit parameter."""
        for i in range(10):
            content = Content.objects.create(
                title=f'Content {i}',
                description=f'Description {i}',
                content_type=self.video_type,
            )
            content.categories.add(self.yoga_category)

        queryset = Content.objects.all()
        result = set_cached_content_ids(queryset, limit=5)

        self.assertEqual(len(result), 5)


class FilterContextCacheTestCase(TestCase):
    """Tests for filter context caching."""

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
            defaults={'name': 'Видео', 'upload_folder': 'videos'},
        )
        self.tag_group = TagGroup.objects.create(name='Месяц')
        self.tag_group.categories.add(self.yoga_category)

    def tearDown(self) -> None:
        cache.clear()

    def test_get_cached_filter_context_returns_none_when_empty(self) -> None:
        """Test that get_cached_filter_context returns None when cache is empty."""
        result = get_cached_filter_context()
        self.assertIsNone(result)

    def test_set_cached_filter_context_caches_data(self) -> None:
        """Test that set_cached_filter_context caches the context."""
        tag_groups = TagGroup.objects.prefetch_related('tags', 'categories').all()
        categories = Category.objects.all()
        content_types = ContentType.objects.all()

        result = set_cached_filter_context(tag_groups, categories, content_types)

        self.assertIn('tag_groups', result)
        self.assertIn('categories', result)
        self.assertIn('content_types', result)

        cached = cache.get(FILTER_CONTEXT_CACHE_KEY)
        self.assertIsNotNone(cached)

    def test_get_cached_filter_context_returns_cached_data(self) -> None:
        """Test that get_cached_filter_context returns cached data."""
        tag_groups = TagGroup.objects.prefetch_related('tags', 'categories').all()
        categories = Category.objects.all()
        content_types = ContentType.objects.all()

        set_cached_filter_context(tag_groups, categories, content_types)

        result = get_cached_filter_context()
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(len(result['categories']), 2)

    def test_invalidate_filter_context_cache_clears_cache(self) -> None:
        """Test that invalidate_filter_context_cache clears the cache."""
        tag_groups = TagGroup.objects.prefetch_related('tags', 'categories').all()
        categories = Category.objects.all()
        content_types = ContentType.objects.all()

        set_cached_filter_context(tag_groups, categories, content_types)
        self.assertIsNotNone(get_cached_filter_context())

        invalidate_filter_context_cache()

        self.assertIsNone(get_cached_filter_context())


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
            defaults={'name': 'Видео', 'upload_folder': 'videos'},
        )
        self.photo_type, _ = ContentType.objects.get_or_create(
            code='photo',
            defaults={'name': 'Фото', 'upload_folder': 'photos'},
        )

    def tearDown(self) -> None:
        cache.clear()

    def test_cache_invalidated_on_content_save(self) -> None:
        """Test that cache is invalidated when content is saved."""
        content = Content.objects.create(
            title='Test Content',
            description='Test Description',
            content_type=self.video_type,
        )
        content.categories.add(self.yoga_category)

        queryset = Content.objects.all()
        set_cached_content_ids(queryset, limit=6)
        self.assertIsNotNone(get_cached_content_ids())

        content.title = 'Updated Title'
        content.save()

        self.assertIsNone(get_cached_content_ids())

    def test_cache_invalidated_on_content_create(self) -> None:
        """Test that cache is invalidated when content is created."""
        queryset = Content.objects.all()
        set_cached_content_ids(queryset, limit=6)

        content = Content.objects.create(
            title='New Content',
            description='New Description',
            content_type=self.photo_type,
        )
        content.categories.add(self.oils_category)

        self.assertIsNone(get_cached_content_ids())

    def test_cache_invalidated_on_content_delete(self) -> None:
        """Test that cache is invalidated when content is deleted."""
        content = Content.objects.create(
            title='Test Content',
            description='Test Description',
            content_type=self.video_type,
        )
        content.categories.add(self.yoga_category)

        queryset = Content.objects.all()
        set_cached_content_ids(queryset, limit=6)
        self.assertIsNotNone(get_cached_content_ids())

        content.delete()

        self.assertIsNone(get_cached_content_ids())


class FilterContextSignalsTestCase(TestCase):
    """Tests for filter context cache invalidation signals."""

    def setUp(self) -> None:
        cache.clear()
        self.yoga_category, _ = Category.objects.get_or_create(
            code='yoga',
            defaults={'name': 'Йога', 'slug': 'yoga'},
        )
        self.video_type, _ = ContentType.objects.get_or_create(
            code='video',
            defaults={'name': 'Видео', 'upload_folder': 'videos'},
        )

    def tearDown(self) -> None:
        cache.clear()

    def _populate_filter_cache(self) -> None:
        """Helper to populate filter context cache."""
        tag_groups = TagGroup.objects.prefetch_related('tags', 'categories').all()
        categories = Category.objects.all()
        content_types = ContentType.objects.all()
        set_cached_filter_context(tag_groups, categories, content_types)

    def test_filter_cache_invalidated_on_category_create(self) -> None:
        """Test that filter cache is invalidated when category is created."""
        self._populate_filter_cache()
        self.assertIsNotNone(get_cached_filter_context())

        Category.objects.create(code='new', name='Новая')

        self.assertIsNone(get_cached_filter_context())

    def test_filter_cache_invalidated_on_category_delete(self) -> None:
        """Test that filter cache is invalidated when category is deleted."""
        category = Category.objects.create(code='temp', name='Временная')
        self._populate_filter_cache()
        self.assertIsNotNone(get_cached_filter_context())

        category.delete()

        self.assertIsNone(get_cached_filter_context())

    def test_filter_cache_invalidated_on_tag_create(self) -> None:
        """Test that filter cache is invalidated when tag is created."""
        tag_group = TagGroup.objects.create(name='Месяц')
        self._populate_filter_cache()
        self.assertIsNotNone(get_cached_filter_context())

        Tag.objects.create(name='Январь', group=tag_group)

        self.assertIsNone(get_cached_filter_context())

    def test_filter_cache_invalidated_on_taggroup_create(self) -> None:
        """Test that filter cache is invalidated when tag group is created."""
        self._populate_filter_cache()
        self.assertIsNotNone(get_cached_filter_context())

        TagGroup.objects.create(name='Новая группа')

        self.assertIsNone(get_cached_filter_context())

    def test_filter_cache_invalidated_on_taggroup_categories_change(self) -> None:
        """Test that filter cache is invalidated when tag group categories change."""
        tag_group = TagGroup.objects.create(name='Тестовая группа')
        self._populate_filter_cache()
        self.assertIsNotNone(get_cached_filter_context())

        tag_group.categories.add(self.yoga_category)

        self.assertIsNone(get_cached_filter_context())
