"""Add pg_trgm extension for fuzzy search."""

from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    """Enable pg_trgm extension for trigram similarity search."""

    dependencies = [
        ('blog', '0020_content_blog_conten_created_52a246_idx'),
    ]

    operations = [
        TrigramExtension(),
    ]
