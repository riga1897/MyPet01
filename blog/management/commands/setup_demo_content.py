"""Management command to load demo content from fixtures."""

from typing import Any

from django.core.management import call_command
from django.core.management.base import BaseCommand

from blog.models import Content


class Command(BaseCommand):
    """Load demo content from fixtures. Use only for preprod/testing."""

    help = 'Load demo content from fixtures (preprod/testing only)'

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reload even if content exists',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        force = options['force']

        if Content.objects.exists() and not force:
            self.stdout.write(
                self.style.WARNING(
                    'Content already exists. Use --force to reload demo data.'
                )
            )
            return

        self.stdout.write('Loading demo content...')

        call_command(
            'loaddata',
            'demo_content',
            verbosity=options.get('verbosity', 1),
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Loaded {Content.objects.count()} demo content items.'
            )
        )
