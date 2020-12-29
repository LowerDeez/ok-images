from django.core.validators import FileExtensionValidator

from versatileimagefield.fields import VersatileImageField
from versatileimagefield.placeholder import OnStoragePlaceholderImage
from versatileimagefield.serializers import VersatileImageFieldSerializer

from .consts import (
    IMAGE_ALLOWED_EXTENSIONS,
    IMAGE_CREATE_ON_DEMAND,
    IMAGE_PLACEHOLDER_PATH
)
from .files import OptimizedVersatileImageFieldFile
from .utils import image_upload_to, image_optimizer

__all__ = (
    'OptimizedImageField',
)


class OptimizedImageField(VersatileImageField):
    """An ImageField that gets optimized on save() using tinyPNG."""
    attr_class = OptimizedVersatileImageFieldFile

    def __init__(self, *args, **kwargs):
        self.image_sizes_serializer = (
            kwargs.pop(
                'image_sizes_serializer',
                VersatileImageFieldSerializer
            )
        )
        self.image_sizes = kwargs.pop('image_sizes', None)
        self.create_on_demand = (
            kwargs.pop('create_on_demand', IMAGE_CREATE_ON_DEMAND)
        )

        super().__init__(*args, **kwargs)
        
        self.upload_to = image_upload_to
        self.validators.append(FileExtensionValidator(IMAGE_ALLOWED_EXTENSIONS))

        if self.placeholder_image is None and IMAGE_PLACEHOLDER_PATH:
            self.placeholder_image = OnStoragePlaceholderImage(
                path=IMAGE_PLACEHOLDER_PATH
            )

    def save_form_data(self, instance, data):
        """Remove the OptimizedNotOptimized object on clearing the image."""
        # Are we updating an image?
        updating_image = (
            True if data and getattr(instance, self.name) != data else False
        )

        if updating_image:
            # to delete file on input clear
            to_check = data

            if to_check is not None:
                if isinstance(data, tuple):
                    to_check = data[0]

                file = getattr(instance, self.attname)

                if file and file != to_check:
                    file.delete(save=False)

            # optimize data
            if data:
                if isinstance(data, tuple):
                    optimized_data = image_optimizer(data[0])
                    data = optimized_data, data[1]
                else:
                    data = image_optimizer(data)

        super().save_form_data(instance, data)
