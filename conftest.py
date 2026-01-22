import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture(scope='session', autouse=True)
def temp_media_root(request: Any) -> Generator[str, None, None]:
    """Create a temporary MEDIA_ROOT for tests that is cleaned up after all tests."""
    from django.conf import settings
    
    original_media_root = settings.MEDIA_ROOT
    temp_dir = tempfile.mkdtemp(prefix='test_media_')
    settings.MEDIA_ROOT = temp_dir
    
    yield temp_dir
    
    settings.MEDIA_ROOT = original_media_root
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)
