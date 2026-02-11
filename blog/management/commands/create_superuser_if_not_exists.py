"""Management command to create superuser if not exists."""

import os
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Create superuser from environment variables if not exists."""

    help = 'Create superuser from environment variables if not exists'

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            '--username',
            default=os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin'),
            help='Superuser username (default: DJANGO_SUPERUSER_USERNAME or "admin")',
        )
        parser.add_argument(
            '--email',
            default=os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com'),
            help='Superuser email (default: DJANGO_SUPERUSER_EMAIL or "admin@example.com")',
        )
        parser.add_argument(
            '--password',
            default=os.environ.get('DJANGO_SUPERUSER_PASSWORD'),
            help='Superuser password (default: DJANGO_SUPERUSER_PASSWORD)',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        User = get_user_model()
        username = options['username']
        email = options['email']
        password = options['password']

        if not password:
            self.stderr.write(
                self.style.ERROR(
                    'Password is required. Set DJANGO_SUPERUSER_PASSWORD env var or use --password'
                )
            )
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Superuser "{username}" already exists, skipping.')
            )
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        self.stdout.write(
            self.style.SUCCESS(f'Superuser "{username}" created successfully.')
        )
