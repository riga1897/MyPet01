from typing import Any

from django.db import migrations, models


def migrate_content_type_to_m2m(apps: Any, schema_editor: Any) -> None:
    Content = apps.get_model('blog', 'Content')
    for content in Content.objects.filter(content_type__isnull=False):
        content.content_types.add(content.content_type)


def reverse_m2m_to_content_type(apps: Any, schema_editor: Any) -> None:
    Content = apps.get_model('blog', 'Content')
    for content in Content.objects.all():
        first_type = content.content_types.first()
        if first_type:
            content.content_type = first_type
            content.save(update_fields=['content_type'])


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0010_add_content_type_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='content',
            name='content_types',
            field=models.ManyToManyField(blank=True, related_name='contents', to='blog.contenttype', verbose_name='Типы контента'),
        ),
        migrations.RunPython(migrate_content_type_to_m2m, reverse_m2m_to_content_type),
        migrations.RemoveField(
            model_name='content',
            name='content_type',
        ),
    ]
