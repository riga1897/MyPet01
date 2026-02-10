"""Management command to load demo content from fixtures."""

import shutil
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from blog.models import Category, Content

DEMO_MEDIA_DIR = Path(__file__).resolve().parent.parent.parent / 'fixtures' / 'demo_media'


class Command(BaseCommand):
    """Load demo content from fixtures. Use only for preprod/testing."""

    help = 'Load demo content from fixtures (preprod/testing only)'

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reload even if content exists',
        )

    def _copy_demo_media(self) -> int:
        """Copy demo media files to MEDIA_ROOT. Returns count of copied files."""
        if not DEMO_MEDIA_DIR.exists():
            self.stdout.write(
                self.style.WARNING(f'Demo media directory not found: {DEMO_MEDIA_DIR}')
            )
            return 0

        media_root = Path(settings.MEDIA_ROOT)
        copied = 0

        for src_file in DEMO_MEDIA_DIR.rglob('*'):
            if not src_file.is_file():
                continue

            relative = src_file.relative_to(DEMO_MEDIA_DIR)
            dst_file = media_root / relative
            dst_file.parent.mkdir(parents=True, exist_ok=True)

            if not dst_file.exists():
                shutil.copy2(src_file, dst_file)
                copied += 1

        return copied

    def handle(self, *args: Any, **options: Any) -> None:
        force = options['force']

        self.stdout.write('Copying demo media files...')
        copied = self._copy_demo_media()
        self.stdout.write(f'Copied {copied} media files.')

        if Content.objects.exists() and not force:
            self.stdout.write(
                self.style.WARNING(
                    'Content already exists. Use --force to reload demo data.'
                )
            )
            return

        if not Category.objects.exists():
            self.stdout.write('Loading initial structure first...')
            call_command(
                'setup_initial_structure',
                verbosity=options.get('verbosity', 1),
            )

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
