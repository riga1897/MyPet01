"""Tests for tag functionality."""
from __future__ import annotations

import pytest
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from blog.forms import TagForm, TagGroupForm
from blog.models import Category, Content, Tag, TagGroup
from users.models import get_or_create_moderators_group


class TestTagGroupModel:
    """Tests for TagGroup model."""

    @pytest.mark.django_db
    def test_create_tag_group(self) -> None:
        """Test creating a tag group."""
        group = TagGroup.objects.create(name='Месяц практики')
        assert group.name == 'Месяц практики'
        assert group.slug == 'месяц-практики'

    @pytest.mark.django_db
    def test_tag_group_str(self) -> None:
        """Test tag group string representation."""
        group = TagGroup.objects.create(name='Настроение')
        assert str(group) == 'Настроение'

    @pytest.mark.django_db
    def test_tag_group_slug_auto_generated(self) -> None:
        """Test that slug is auto-generated from name."""
        group = TagGroup.objects.create(name='Test Group')
        assert group.slug == 'test-group'

    @pytest.mark.django_db
    def test_tag_group_custom_slug(self) -> None:
        """Test that custom slug is preserved."""
        group = TagGroup.objects.create(name='Test Group', slug='custom-slug')
        assert group.slug == 'custom-slug'

    @pytest.mark.django_db
    def test_is_visible_for_category_with_prefetch_empty_categories(
        self, yoga_category: 'Category'
    ) -> None:
        """Test visibility check with prefetched empty categories (applies to all)."""
        group = TagGroup.objects.create(name='All Group')
        prefetched = TagGroup.objects.prefetch_related('categories').get(pk=group.pk)
        assert prefetched.is_visible_for_category(yoga_category) is True

    @pytest.mark.django_db
    def test_is_visible_for_category_with_prefetch_matching(
        self, yoga_category: 'Category'
    ) -> None:
        """Test visibility check with prefetched matching category."""
        group = TagGroup.objects.create(name='Yoga Group')
        group.categories.add(yoga_category)
        prefetched = TagGroup.objects.prefetch_related('categories').get(pk=group.pk)
        assert prefetched.is_visible_for_category(yoga_category) is True

    @pytest.mark.django_db
    def test_is_visible_for_category_with_prefetch_not_matching(
        self, yoga_category: 'Category', oils_category: 'Category'
    ) -> None:
        """Test visibility check with prefetched non-matching category."""
        group = TagGroup.objects.create(name='Oils Group')
        group.categories.add(oils_category)
        prefetched = TagGroup.objects.prefetch_related('categories').get(pk=group.pk)
        assert prefetched.is_visible_for_category(yoga_category) is False

    @pytest.mark.django_db
    def test_is_visible_for_category_with_prefetch_none_category(
        self, oils_category: 'Category'
    ) -> None:
        """Test visibility check with prefetched data and None category."""
        group = TagGroup.objects.create(name='Specific Group')
        group.categories.add(oils_category)
        prefetched = TagGroup.objects.prefetch_related('categories').get(pk=group.pk)
        assert prefetched.is_visible_for_category(None) is False

    @pytest.mark.django_db
    def test_is_visible_for_category_without_prefetch_not_matching(
        self, yoga_category: 'Category', oils_category: 'Category'
    ) -> None:
        """Test visibility check without prefetch - DB fallback path."""
        group = TagGroup.objects.create(name='Oils Only')
        group.categories.add(oils_category)
        fresh_group = TagGroup.objects.get(pk=group.pk)
        assert fresh_group.is_visible_for_category(yoga_category) is False

    @pytest.mark.django_db
    def test_is_visible_for_category_without_prefetch_none_category(
        self, oils_category: 'Category'
    ) -> None:
        """Test visibility check without prefetch and None category."""
        group = TagGroup.objects.create(name='Specific')
        group.categories.add(oils_category)
        fresh_group = TagGroup.objects.get(pk=group.pk)
        assert fresh_group.is_visible_for_category(None) is False

    @pytest.mark.django_db
    def test_is_visible_for_category_without_prefetch_empty_categories(
        self, yoga_category: 'Category'
    ) -> None:
        """Test visibility check without prefetch - empty categories (applies to all)."""
        group = TagGroup.objects.create(name='All Categories')
        fresh_group = TagGroup.objects.get(pk=group.pk)
        assert fresh_group.is_visible_for_category(yoga_category) is True


class TestTagModel:
    """Tests for Tag model."""

    @pytest.mark.django_db
    def test_create_tag(self) -> None:
        """Test creating a tag."""
        group = TagGroup.objects.create(name='Месяц')
        tag = Tag.objects.create(name='Первый месяц', group=group)
        assert tag.name == 'Первый месяц'
        assert tag.group == group

    @pytest.mark.django_db
    def test_tag_str(self) -> None:
        """Test tag string representation."""
        group = TagGroup.objects.create(name='Месяц')
        tag = Tag.objects.create(name='Первый', group=group)
        assert str(tag) == 'Месяц: Первый'

    @pytest.mark.django_db
    def test_tag_slug_auto_generated(self) -> None:
        """Test that slug is auto-generated from name."""
        group = TagGroup.objects.create(name='Test')
        tag = Tag.objects.create(name='Tag Name', group=group)
        assert tag.slug == 'tag-name'

    @pytest.mark.django_db
    def test_content_tags_relationship(self) -> None:
        """Test ManyToMany relationship between Content and Tag."""
        group = TagGroup.objects.create(name='Месяц')
        tag = Tag.objects.create(name='Первый', group=group)
        content = Content.objects.create(title='Test')
        content.tags.add(tag)
        assert tag in content.tags.all()
        assert content in tag.contents.all()


class TestTagGroupForm:
    """Tests for TagGroupForm."""

    @pytest.mark.django_db
    def test_form_has_required_fields(self) -> None:
        """Test that form has all required fields."""
        form = TagGroupForm()
        assert 'name' in form.fields
        assert 'select_all' in form.fields
        assert 'categories' in form.fields

    @pytest.mark.django_db
    def test_valid_form_creates_tag_group(self) -> None:
        """Test that valid form creates tag group."""
        form = TagGroupForm(data={'name': 'Новая группа'})
        assert form.is_valid()
        group = form.save()
        assert group.name == 'Новая группа'
        assert group.categories.count() == 0


class TestTagForm:
    """Tests for TagForm."""

    @pytest.mark.django_db
    def test_form_has_required_fields(self) -> None:
        """Test that form has required fields."""
        form = TagForm()
        assert 'name' in form.fields
        assert 'group' in form.fields

    @pytest.mark.django_db
    def test_valid_form_creates_tag(self) -> None:
        """Test that valid form creates tag."""
        group = TagGroup.objects.create(name='Группа')
        form = TagForm(data={'name': 'Новый тег', 'group': group.pk})
        assert form.is_valid()
        tag = form.save()
        assert tag.name == 'Новый тег'
        assert tag.group == group


class TagViewsTestCase(TestCase):
    """Tests for tag management views."""

    def setUp(self) -> None:
        self.client = Client()
        self.moderator = User.objects.create_user(
            username='moderator',
            password='testpass123',
        )
        moderators_group = get_or_create_moderators_group()
        self.moderator.groups.add(moderators_group)
        self.group = TagGroup.objects.create(name='Тестовая группа')
        self.tag = Tag.objects.create(name='Тестовый тег', group=self.group)

    def test_tag_list_requires_login(self) -> None:
        """Test that tag list requires authentication."""
        response = self.client.get(reverse('blog:tag_list'))
        self.assertEqual(response.status_code, 302)

    def test_tag_list_accessible_by_moderator(self) -> None:
        """Test that moderator can access tag list."""
        self.client.login(username='moderator', password='testpass123')
        response = self.client.get(reverse('blog:tag_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовая группа')

    def test_taggroup_create_view(self) -> None:
        """Test tag group creation view."""
        self.client.login(username='moderator', password='testpass123')
        response = self.client.get(reverse('blog:taggroup_create'))
        self.assertEqual(response.status_code, 200)

    def test_taggroup_create_post(self) -> None:
        """Test tag group creation via POST."""
        self.client.login(username='moderator', password='testpass123')
        response = self.client.post(
            reverse('blog:taggroup_create'),
            {'name': 'Новая группа'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(TagGroup.objects.filter(name='Новая группа').exists())

    def test_taggroup_update_view(self) -> None:
        """Test tag group update view."""
        self.client.login(username='moderator', password='testpass123')
        response = self.client.get(
            reverse('blog:taggroup_edit', kwargs={'pk': self.group.pk}),
        )
        self.assertEqual(response.status_code, 200)

    def test_taggroup_update_post(self) -> None:
        """Test tag group update via POST."""
        self.client.login(username='moderator', password='testpass123')
        response = self.client.post(
            reverse('blog:taggroup_edit', kwargs={'pk': self.group.pk}),
            {'name': 'Обновлённая группа'},
        )
        self.assertEqual(response.status_code, 302)
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, 'Обновлённая группа')

    def test_taggroup_delete_view(self) -> None:
        """Test tag group delete view."""
        self.client.login(username='moderator', password='testpass123')
        response = self.client.get(
            reverse('blog:taggroup_delete', kwargs={'pk': self.group.pk}),
        )
        self.assertEqual(response.status_code, 200)

    def test_taggroup_delete_post(self) -> None:
        """Test tag group deletion via POST."""
        self.client.login(username='moderator', password='testpass123')
        group_pk = self.group.pk
        response = self.client.post(
            reverse('blog:taggroup_delete', kwargs={'pk': group_pk}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(TagGroup.objects.filter(pk=group_pk).exists())

    def test_tag_create_view(self) -> None:
        """Test tag creation view."""
        self.client.login(username='moderator', password='testpass123')
        response = self.client.get(reverse('blog:tag_create'))
        self.assertEqual(response.status_code, 200)

    def test_tag_create_post(self) -> None:
        """Test tag creation via POST."""
        self.client.login(username='moderator', password='testpass123')
        response = self.client.post(
            reverse('blog:tag_create'),
            {'name': 'Новый тег', 'group': self.group.pk},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Tag.objects.filter(name='Новый тег').exists())

    def test_tag_update_view(self) -> None:
        """Test tag update view."""
        self.client.login(username='moderator', password='testpass123')
        response = self.client.get(
            reverse('blog:tag_edit', kwargs={'pk': self.tag.pk}),
        )
        self.assertEqual(response.status_code, 200)

    def test_tag_update_post(self) -> None:
        """Test tag update via POST."""
        self.client.login(username='moderator', password='testpass123')
        response = self.client.post(
            reverse('blog:tag_edit', kwargs={'pk': self.tag.pk}),
            {'name': 'Обновлённый тег', 'group': self.group.pk},
        )
        self.assertEqual(response.status_code, 302)
        self.tag.refresh_from_db()
        self.assertEqual(self.tag.name, 'Обновлённый тег')

    def test_tag_delete_view(self) -> None:
        """Test tag delete view."""
        self.client.login(username='moderator', password='testpass123')
        response = self.client.get(
            reverse('blog:tag_delete', kwargs={'pk': self.tag.pk}),
        )
        self.assertEqual(response.status_code, 200)

    def test_tag_delete_post(self) -> None:
        """Test tag deletion via POST."""
        self.client.login(username='moderator', password='testpass123')
        tag_pk = self.tag.pk
        response = self.client.post(
            reverse('blog:tag_delete', kwargs={'pk': tag_pk}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Tag.objects.filter(pk=tag_pk).exists())


class HomeViewTagsTestCase(TestCase):
    """Tests for tags on home page."""

    def test_home_page_shows_tag_groups(self) -> None:
        """Test that home page includes tag groups in context."""
        group = TagGroup.objects.create(name='Месяц')
        Tag.objects.create(name='Первый', group=group)
        response = self.client.get(reverse('blog:home'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('tag_groups', response.context)


class ContentListTagsTestCase(TestCase):
    """Tests for tags in content list view."""

    def setUp(self) -> None:
        self.client = Client()
        self.moderator = User.objects.create_user(
            username='moderator',
            password='testpass123',
        )
        moderators_group = get_or_create_moderators_group()
        self.moderator.groups.add(moderators_group)

    def test_content_list_shows_tag_groups(self) -> None:
        """Test that content list includes tag groups in context."""
        self.client.login(username='moderator', password='testpass123')
        group = TagGroup.objects.create(name='Месяц')
        Tag.objects.create(name='Первый', group=group)
        response = self.client.get(reverse('blog:content_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('tag_groups', response.context)
