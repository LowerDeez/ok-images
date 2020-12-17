from io import BytesIO
import logging
from PIL import Image

from django.apps import apps
from django.db.models import Model, QuerySet
from django.utils import timezone
from django.utils.module_loading import import_string
from django.utils.text import slugify

import tinify
from tinify import Error
from unidecode import unidecode
from versatileimagefield.image_warmer import VersatileImageFieldWarmer

from .consts import (
    IMAGE_DEFAULT_RENDITION_KEY_SET,
    IMAGE_RENDITION_KEY_SETS,
    IMAGE_OPTIMIZE_QUALITY,
    TINYPNG_ALLOWED_EXTENSIONS,
    TINYPNG_API_KEY_FUNCTION,
    TINYPNG_API_KEY
)

logger = logging.getLogger(__name__)

__all__ = (
    'get_tinypng_api_key',
    'image_optimizer',
    'image_upload_to',
    'get_model_image_fields',
    'delete_all_created_images',
    'warm_images',
)


def get_tinypng_api_key():
    api_key = TINYPNG_API_KEY

    if TINYPNG_API_KEY_FUNCTION:
        func = import_string(TINYPNG_API_KEY_FUNCTION)

        if callable(func):
            api_key = func()

    return api_key


def image_optimizer(data):
    """Optimize an image that has not been saved to a file."""
    if not data:
        return data

    extension = data.name.split('.')[-1]

    extension = extension.upper() if extension.lower() != 'jpg' else 'JPEG'

    optimized = False
    buffer = None

    tinypng_api_key = get_tinypng_api_key()

    if (
            tinypng_api_key
            and extension.lower() in TINYPNG_ALLOWED_EXTENSIONS
    ):
        tinify.key = tinypng_api_key

        try:
            buffer = tinify.from_buffer(data.file.read()).to_buffer()
            optimized = True
        except Error as e:
            logger.error(f"TinyPNG error: {e}")

    if not optimized:
        image = Image.open(data)
        bytes_io = BytesIO()

        if image.mode in ('RGBA', 'LA'):
            background = (
                Image.new(image.mode[:-1], image.size, '#FFFFFF')
            )
            background.paste(image, image.split()[-1])
            image = background

        # for PNG
        # if image.mode == 'P':
        #     image = image.convert('RGB')
        #
        # # image.save(bytes_io, format=extension.upper(), optimize=True)
        #
        # extension = extension.upper() if extension.lower() != 'png' else 'JPEG'

        image.save(
            bytes_io,
            format=extension,
            optimize=True,
            quality=IMAGE_OPTIMIZE_QUALITY
        )
        buffer = bytes_io.getvalue()

    if buffer:
        data.seek(0)
        data.file.write(buffer)
        data.file.truncate()

    return data


def image_upload_to(instance, filename):
    """
    Util to set upload_to path, based on model's class name and date of uploading,
    for image field in ImageMixin
    """
    name, ext = filename.rsplit('.', 1)
    filename = f'{slugify(unidecode(name).lower())}.{ext}'
    tz_now = timezone.now()

    if timezone.is_aware(tz_now):
        tz_now = timezone.localtime(tz_now)

    tz_now = tz_now.strftime('%Y/%m/%d')

    if hasattr(instance, 'content_object'):
        class_name = instance.content_object.__class__.__name__
    else:
        class_name = instance.__class__.__name__

    return (
        f"{instance._meta.app_label}/"
        f"{slugify(class_name)}/"
        f"{tz_now}/"
        f"{filename}".lower()
    )


def get_model_image_fields(model: 'Model'):
    from .fields import OptimizedImageField

    image_fields = [
        field
        for field
        in model._meta.fields
        if isinstance(field, OptimizedImageField)
    ]

    return image_fields


def delete_all_created_images(*all_models, delete_images: bool = True):
    """
    Delete all created images and clear cache
    """
    from .models import ImageMixin

    if not all_models:
        all_models = apps.get_models()

    for model in all_models:
        if issubclass(model, ImageMixin):
            image_fields = get_model_image_fields(model)
            image_sizes = model.image_sizes
            print(image_sizes)
            key_sets = IMAGE_RENDITION_KEY_SETS.get(image_sizes, [])
            print(key_sets)

            for obj in model.objects.all():
                for field in image_fields:
                    image_field = getattr(obj, field.name)

                    if delete_images and image_field:
                        image_field.delete_all_created_images()

                        for key_set in key_sets:
                            name, rendition_key = key_set

                            if '__' in rendition_key:
                                rendition_key_set = rendition_key.split('__')
                                print(rendition_key_set)

                                if rendition_key_set:
                                    if len(rendition_key_set) == 2:
                                        method, size = rendition_key_set

                                        getattr(image_field, method)[size].clear_cache()

                                    elif rendition_key_set[0] == 'filters':
                                        filters = getattr(image_field, 'filters')
                                        getattr(filters, rendition_key_set[1]).clear_cache()

                        image_field.thumbnail['300x300'].clear_cache()


def warm_images(instance_or_queryset, rendition_key_set: str = None):
    if isinstance(instance_or_queryset, QuerySet):
        model = instance_or_queryset.model
    else:
        model = instance_or_queryset.__class__

    image_fields = get_model_image_fields(model)

    for image_field in image_fields:
        if rendition_key_set is None:
            rendition_key_set = (
                image_field.image_sizes
                or getattr(model, 'image_sizes')
            )

        img_warmer = VersatileImageFieldWarmer(
            instance_or_queryset=instance_or_queryset,
            rendition_key_set=rendition_key_set or IMAGE_DEFAULT_RENDITION_KEY_SET,
            image_attr=image_field.name
        )
        img_warmer.warm()
