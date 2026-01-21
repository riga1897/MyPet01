import pytest
from django.contrib.auth.models import Group, User

from users.models import (
    MODERATORS_GROUP_NAME,
    can_manage_moderators,
    get_or_create_moderators_group,
    is_moderator,
)


@pytest.mark.django_db
class TestModeratorsGroup:
    def test_moderators_group_name_constant(self) -> None:
        assert MODERATORS_GROUP_NAME == 'Модераторы'

    def test_get_or_create_moderators_group_creates_group(self) -> None:
        Group.objects.filter(name=MODERATORS_GROUP_NAME).delete()
        group = get_or_create_moderators_group()
        assert group.name == MODERATORS_GROUP_NAME
        assert Group.objects.filter(name=MODERATORS_GROUP_NAME).exists()

    def test_get_or_create_moderators_group_returns_existing(self) -> None:
        group1 = get_or_create_moderators_group()
        group2 = get_or_create_moderators_group()
        assert group1.pk == group2.pk


@pytest.mark.django_db
class TestIsModerator:
    def test_anonymous_user_is_not_moderator(self) -> None:
        from django.contrib.auth.models import AnonymousUser
        user = AnonymousUser()
        assert is_moderator(user) is False

    def test_regular_user_is_not_moderator(self) -> None:
        user = User.objects.create_user(username='regular', password='test123')
        assert is_moderator(user) is False

    def test_superuser_is_moderator(self) -> None:
        user = User.objects.create_superuser(username='admin', password='test123')
        assert is_moderator(user) is True

    def test_user_in_moderators_group_is_moderator(self) -> None:
        user = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        user.groups.add(group)
        assert is_moderator(user) is True


@pytest.mark.django_db
class TestCanManageModerators:
    def test_anonymous_user_cannot_manage(self) -> None:
        from django.contrib.auth.models import AnonymousUser
        user = AnonymousUser()
        assert can_manage_moderators(user) is False

    def test_regular_user_cannot_manage(self) -> None:
        user = User.objects.create_user(username='regular', password='test123')
        assert can_manage_moderators(user) is False

    def test_moderator_can_manage(self) -> None:
        user = User.objects.create_user(username='mod', password='test123')
        group = get_or_create_moderators_group()
        user.groups.add(group)
        assert can_manage_moderators(user) is True

    def test_superuser_can_manage(self) -> None:
        user = User.objects.create_superuser(username='admin', password='test123')
        assert can_manage_moderators(user) is True
