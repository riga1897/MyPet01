from typing import Any

import blog.models
import django.db.models.deletion
from django.db import migrations, models


def create_content_types_and_migrate(apps: Any, schema_editor: Any) -> None:
    ContentType = apps.get_model('blog', 'ContentType')
    Content = apps.get_model('blog', 'Content')
    
    video_type, _ = ContentType.objects.get_or_create(
        code='video',
        defaults={
            'name': 'Видео',
            'slug': 'video',
            'upload_folder': 'videos',
        }
    )
    
    photo_type, _ = ContentType.objects.get_or_create(
        code='photo',
        defaults={
            'name': 'Фото',
            'slug': 'photo',
            'upload_folder': 'photos',
        }
    )
    
    Content.objects.filter(old_content_type='video').update(content_type_new=video_type)
    Content.objects.filter(old_content_type='photo').update(content_type_new=photo_type)


def reverse_migration(apps: Any, schema_editor: Any) -> None:
    ContentType = apps.get_model('blog', 'ContentType')
    Content = apps.get_model('blog', 'Content')
    
    for content in Content.objects.select_related('content_type_new').all():
        if content.content_type_new:
            content.old_content_type = content.content_type_new.code
            content.save(update_fields=['old_content_type'])
    
    ContentType.objects.filter(code__in=['video', 'photo']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0009_add_tag_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Название')),
                ('slug', models.SlugField(blank=True, max_length=100, unique=True, verbose_name='Слаг')),
                ('code', models.CharField(help_text='Уникальный код для использования в коде (например: video, photo, audio)', max_length=20, unique=True, verbose_name='Код')),
                ('upload_folder', models.CharField(default='content', help_text='Папка для сохранения файлов (например: videos, photos, audio)', max_length=100, verbose_name='Папка для файлов')),
            ],
            options={
                'verbose_name': 'Тип контента',
                'verbose_name_plural': 'Типы контента',
                'ordering': ['name'],
            },
        ),
        migrations.RenameField(
            model_name='content',
            old_name='content_type',
            new_name='old_content_type',
        ),
        migrations.AddField(
            model_name='content',
            name='content_type_new',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='contents', to='blog.contenttype', verbose_name='Тип'),
        ),
        migrations.AlterField(
            model_name='content',
            name='video_file',
            field=models.FileField(blank=True, upload_to=blog.models.content_file_upload_path, verbose_name='Файл контента'),
        ),
        migrations.RunPython(create_content_types_and_migrate, reverse_migration),
        migrations.RemoveField(
            model_name='content',
            name='old_content_type',
        ),
        migrations.RenameField(
            model_name='content',
            old_name='content_type_new',
            new_name='content_type',
        ),
    ]
