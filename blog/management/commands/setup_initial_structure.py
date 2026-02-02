"""Management command to load initial structure from fixtures."""

from typing import Any

from django.core.management import call_command
from django.core.management.base import BaseCommand

from blog.models import Category, ContentType, Tag, TagGroup


class Command(BaseCommand):
    """Load initial structure (categories, tags, content types) from fixtures."""

    help = 'Load initial structure from fixtures (idempotent)'

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reload even if data exists',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        force = options['force']

        has_data = (
            ContentType.objects.exists() or
            Category.objects.exists() or
            TagGroup.objects.exists() or
            Tag.objects.exists()
        )

        if has_data and not force:
            self.stdout.write(
                self.style.WARNING(
                    'Initial structure already exists. Use --force to reload.'
                )
            )
            return

        self.stdout.write('Loading initial structure...')

        call_command(
            'loaddata',
            'initial_structure',
            verbosity=options.get('verbosity', 1),
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Loaded: {ContentType.objects.count()} content types, '
                f'{Category.objects.count()} categories, '
                f'{TagGroup.objects.count()} tag groups, '
                f'{Tag.objects.count()} tags'
            )
        )
