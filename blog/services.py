"""Video and image processing services for content management."""
import hashlib
import logging
import subprocess
import tempfile
import time
from io import BytesIO
from pathlib import Path
from typing import Any

from django.core.files.base import ContentFile
from PIL import Image

logger = logging.getLogger(__name__)

MAX_VIDEO_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB
FFMPEG_TIMEOUT_SECONDS = 60


def generate_unique_thumbnail_name(prefix: str = 'thumb') -> str:
    """Generate unique thumbnail filename with hash.
    
    Uses timestamp and random bytes to create unique hash suffix.
    """
    timestamp = str(time.time()).encode()
    unique_hash = hashlib.md5(timestamp).hexdigest()[:8]
    return f'{prefix}_{unique_hash}.jpg'


THUMBNAIL_MAX_SIZE = (800, 600)
THUMBNAIL_QUALITY = 85


def generate_thumbnail_from_video(video_file: Any) -> 'ContentFile[bytes] | None':
    """Generate thumbnail from first frame of video using ffmpeg.
    
    Args:
        video_file: Django file field with video content.
    
    Returns:
        ContentFile with JPEG thumbnail, or None if generation fails.
        Returns None if video file exceeds MAX_VIDEO_SIZE_BYTES (500 MB).
    """
    if not video_file or not hasattr(video_file, 'path'):
        return None
    
    try:
        file_size = Path(video_file.path).stat().st_size
        if file_size > MAX_VIDEO_SIZE_BYTES:
            logger.warning(
                'Video file too large for thumbnail generation: %d bytes (max: %d)',
                file_size,
                MAX_VIDEO_SIZE_BYTES,
            )
            return None
    except OSError as e:
        logger.warning('Failed to check video file size: %s', e)
        return None
    
    tmp_path = ''
    try:
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp_path = tmp.name
        
        result = subprocess.run(
            [
                'ffmpeg',
                '-y',
                '-i', str(video_file.path),
                '-ss', '00:00:01',
                '-vframes', '1',
                '-q:v', '2',
                tmp_path,
            ],
            capture_output=True,
            timeout=FFMPEG_TIMEOUT_SECONDS,
        )
        
        if result.returncode == 0:
            tmp_file = Path(tmp_path)
            if tmp_file.exists() and tmp_file.stat().st_size > 0:
                thumbnail_data = tmp_file.read_bytes()
                tmp_file.unlink()
                
                pil_img = Image.open(BytesIO(thumbnail_data))
                if pil_img.mode in ('RGBA', 'P'):
                    pil_img = pil_img.convert('RGB')  # type: ignore[assignment]
                pil_img.thumbnail(THUMBNAIL_MAX_SIZE, Image.Resampling.LANCZOS)
                
                output = BytesIO()
                pil_img.save(output, format='JPEG', quality=THUMBNAIL_QUALITY, optimize=True)
                output.seek(0)
                
                return ContentFile(output.read(), name=generate_unique_thumbnail_name('video'))
            
            if tmp_file.exists():  # pragma: no cover
                tmp_file.unlink()
    except (subprocess.TimeoutExpired, OSError) as e:
        logger.warning('Failed to generate thumbnail from video: %s', e)
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
    
    return None


def generate_thumbnail_from_image(image_file: Any) -> 'ContentFile[bytes] | None':
    """Generate thumbnail from uploaded image (resize and compress).
    
    Args:
        image_file: Django file field with image content.
    
    Returns:
        ContentFile with JPEG thumbnail, or None if generation fails.
    """
    if not image_file:
        return None
    
    try:
        pil_img = Image.open(image_file)
        if pil_img.mode in ('RGBA', 'P'):
            pil_img = pil_img.convert('RGB')  # type: ignore[assignment]
        pil_img.thumbnail(THUMBNAIL_MAX_SIZE, Image.Resampling.LANCZOS)
        
        output = BytesIO()
        pil_img.save(output, format='JPEG', quality=THUMBNAIL_QUALITY, optimize=True)
        output.seek(0)
        
        return ContentFile(output.read(), name=generate_unique_thumbnail_name('photo'))
    except (OSError, ValueError) as e:
        logger.warning('Failed to generate thumbnail from image: %s', e)
    
    return None


def generate_hashed_filename(uploaded_file: Any) -> tuple[str, str]:
    """Generate filename with MD5 hash from file content.
    
    Args:
        uploaded_file: Django UploadedFile with content.
    
    Returns:
        Tuple of (hashed_filename, content_hash).
        Example: ('photo_a1b2c3d4.jpg', 'a1b2c3d4')
    """
    import os as os_module
    md5_hash = hashlib.md5()
    
    uploaded_file.seek(0)
    for chunk in uploaded_file.chunks():
        md5_hash.update(chunk)
    uploaded_file.seek(0)
    
    content_hash = md5_hash.hexdigest()[:8]
    original_name = uploaded_file.name or 'file'
    
    name_part, ext = os_module.path.splitext(original_name)
    hashed_filename = f'{name_part}_{content_hash}{ext}'
    
    return hashed_filename, content_hash
