from django.conf import settings

from versatileimagefield.settings import VERSATILEIMAGEFIELD_CREATE_ON_DEMAND

__all__ = (
    'IMAGE_ALLOWED_EXTENSIONS',
    'IMAGE_RENDITION_KEY_SETS',
    'IMAGE_DEFAULT_RENDITION_KEY_SET',
    'IMAGE_OPTIMIZE_QUALITY',
    'IMAGE_CREATE_ON_DEMAND',
    'TINYPNG_ALLOWED_EXTENSIONS',
    'TINYPNG_API_KEY_FUNCTION',
    'TINYPNG_API_KEY'
)


IMAGE_ALLOWED_EXTENSIONS = getattr(
    settings,
    'IMAGE_ALLOWED_EXTENSIONS',
    ['jpeg', 'jpg', 'png', 'ico']
)


IMAGE_RENDITION_KEY_SETS = getattr(
    settings,
    'VERSATILEIMAGEFIELD_RENDITION_KEY_SETS',
    {}
)

IMAGE_DEFAULT_RENDITION_KEY_SET = [
    ('full_size', 'url'),
]

IMAGE_OPTIMIZE_QUALITY = getattr(
    settings,
    'IMAGE_OPTIMIZE_QUALITY',
    75
)

IMAGE_CREATE_ON_DEMAND = getattr(
    settings,
    'IMAGE_CREATE_ON_DEMAND',
    VERSATILEIMAGEFIELD_CREATE_ON_DEMAND
)

TINYPNG_ALLOWED_EXTENSIONS = ['jpeg', 'jpg', 'png']

TINYPNG_API_KEY_FUNCTION = getattr(settings, 'TINYPNG_API_KEY_FUNCTION', None)

TINYPNG_API_KEY = getattr(settings, 'TINYPNG_API_KEY', None)
