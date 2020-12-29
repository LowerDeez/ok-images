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
    'get_file_extension',
    'image_optimizer',
    'image_upload_to',
    'get_model_image_fields',
    'delete_all_created_images',
    'warm_images',
    'optimize_existing_images'
)


def get_tinypng_api_key():
    api_key = TINYPNG_API_KEY

    if TINYPNG_API_KEY_FUNCTION:
        func = import_string(TINYPNG_API_KEY_FUNCTION)

        if callable(func):
            api_key = func()

    return api_key


def get_file_extension(file_name):
    # Get image file extension
    extension = file_name.split('.')[-1]

    extension = (
        extension.upper()
        if extension.lower() != 'jpg' else 'JPEG'
    )

    return extension


def image_optimizer(data):
    """Optimize an image that has not been saved to a file."""
    if not data:
        return data

    extension = get_file_extension(data.name)

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
            # image = image.convert('RGB')

        save_kwargs = {
            'format': extension,
            'optimize': True,
            'quality': IMAGE_OPTIMIZE_QUALITY,
        }

        if extension == 'WEBP':
            save_kwargs['lossless'] = True
        elif extension == 'JPEG':
            save_kwargs['progressive'] = True

        image.save(
            bytes_io,
            **save_kwargs
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
    if not all_models:
        all_models = apps.get_models()

    for model in all_models:
        image_fields = get_model_image_fields(model)

        if not image_fields:
            continue

        image_sizes = getattr(model, 'image_sizes', None)
        key_sets = IMAGE_RENDITION_KEY_SETS.get(image_sizes, [])

        for obj in model.objects.all():
            for field in image_fields:
                image_field = getattr(obj, field.name)

                if image_field:
                    if image_field.image_sizes:
                        image_sizes = image_field.image_sizes

                        # default key set
                        if isinstance(image_sizes, list):
                            key_sets = []
                        else:
                            key_sets = IMAGE_RENDITION_KEY_SETS.get(image_sizes, [])

                    if delete_images:
                        image_field.delete_all_created_images()

                    # clear cache
                    for key_set in key_sets:
                        name, rendition_key = key_set

                        if '__' in rendition_key:
                            rendition_key_set = rendition_key.split('__')
                            print(rendition_key_set)

                            if rendition_key_set:
                                if len(rendition_key_set) == 2:
                                    method, size = rendition_key_set

                                    getattr(image_field, method)[size].clear_cache()

                                # clear filters cache
                                elif rendition_key_set[0] == 'filters':
                                    filters = getattr(image_field, 'filters')
                                    getattr(filters, rendition_key_set[1]).clear_cache()

                    image_field.thumbnail['300x300'].clear_cache()


def warm_images(
        instance_or_queryset,
        rendition_key_set: str = None,
        image_attr: str = None
):
    if rendition_key_set and image_attr:
        img_warmer = VersatileImageFieldWarmer(
            instance_or_queryset=instance_or_queryset,
            rendition_key_set=rendition_key_set,
            image_attr=image_attr
        )
        return img_warmer.warm()

    if isinstance(instance_or_queryset, QuerySet):
        model = instance_or_queryset.model
    else:
        model = instance_or_queryset.__class__

    if image_attr:
        image_fields = [model._meta.get_field(image_attr)]
    else:
        image_fields = get_model_image_fields(model)

    for image_field in image_fields:
        if image_field.name == "":
            continue

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


def optimize_existing_images(*all_models):
    if not all_models:
        all_models = apps.get_models()

    for model in all_models:
        image_fields = get_model_image_fields(model)

        if not image_fields:
            continue

        for obj in model.objects.all():
            for field in image_fields:
                image_field = getattr(obj, field.name)

                if image_field:
                    extension = get_file_extension(image_field.name)
                    image = Image.open(image_field.path)
                    image.save(
                        image_field.path,
                        format=extension.upper(),
                        optimize=True,
                        quality=IMAGE_OPTIMIZE_QUALITY,
                    )
