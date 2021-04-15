from django.core.validators import FileExtensionValidator

from versatileimagefield.fields import VersatileImageField
from versatileimagefield.placeholder import OnStoragePlaceholderImage
from versatileimagefield.serializers import VersatileImageFieldSerializer

from .consts import (
    IMAGE_ALLOWED_EXTENSIONS,
    IMAGE_MAX_FILE_SIZE,
    IMAGE_CREATE_ON_DEMAND,
    IMAGE_PLACEHOLDER_PATH
)
from .files import OptimizedVersatileImageFieldFile
from .utils import image_upload_to, image_optimizer
from .validators import FileSizeValidator

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
        self.validators.append(
            FileExtensionValidator(IMAGE_ALLOWED_EXTENSIONS)
        )

        if not any([isinstance(v, FileSizeValidator) for v in self.validators]):
            self.validators.append(FileSizeValidator(max_size=IMAGE_MAX_FILE_SIZE))

        if self.placeholder_image is None and IMAGE_PLACEHOLDER_PATH:
            self.placeholder_image = OnStoragePlaceholderImage(
                path=IMAGE_PLACEHOLDER_PATH
            )

    def save_form_data(self, instance, data):
        """Remove the OptimizedNotOptimized object on clearing the image."""
        real_data = data
        file = getattr(instance, self.name)

        if isinstance(data, tuple):
            real_data = data[0]

        # Are we updating an image?
        updating_image = (
            True if real_data and file != real_data else False
        )

        if updating_image:
            # to delete file on input clear
            if real_data is not None and file and file != real_data:
                file.delete(save=False)

            # optimize data
            if data:
                if isinstance(data, tuple):
                    optimized_data = image_optimizer(data[0])
                    data = optimized_data, data[1]
                else:
                    data = image_optimizer(data)

        super().save_form_data(instance, data)
