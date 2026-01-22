"""Root-level pytest configuration for the project."""
import shutil
from pathlib import Path
from typing import Generator

import pytest
from django.conf import settings


@pytest.fixture(scope='session', autouse=True)
def setup_test_media() -> Generator[None, None, None]:
    """Set up and clean up test media directory.
    
    Creates a separate media_test/ directory for tests to prevent
    test files from polluting the main media/ folder.
    Automatically cleans up after all tests complete.
    """
    test_media_root = Path(settings.BASE_DIR) / 'media_test'
    
    if test_media_root.exists():
        shutil.rmtree(test_media_root)
    test_media_root.mkdir(parents=True, exist_ok=True)
    
    original_media_root = settings.MEDIA_ROOT
    settings.MEDIA_ROOT = str(test_media_root)
    
    yield
    
    settings.MEDIA_ROOT = original_media_root
    
    if test_media_root.exists():
        shutil.rmtree(test_media_root)
