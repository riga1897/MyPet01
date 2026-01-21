from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib.auth.models import Group

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

    AnyUser = AbstractBaseUser | AnonymousUser


MODERATORS_GROUP_NAME = 'Модераторы'


def get_or_create_moderators_group() -> Group:
    group, _ = Group.objects.get_or_create(name=MODERATORS_GROUP_NAME)
    return group


def is_moderator(user: Any) -> bool:
    if not user.is_authenticated:
        return False
    return bool(user.is_superuser or user.groups.filter(name=MODERATORS_GROUP_NAME).exists())


def can_manage_moderators(user: Any) -> bool:
    return is_moderator(user)
