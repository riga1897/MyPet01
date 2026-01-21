from typing import Any

from django.db import migrations


def create_moderators_group(apps: Any, schema_editor: Any) -> None:
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='Модераторы')


def remove_moderators_group(apps: Any, schema_editor: Any) -> None:
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='Модераторы').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_moderators_group, remove_moderators_group),
    ]
