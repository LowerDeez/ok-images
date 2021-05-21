from django.core.validators import FileExtensionValidator
from django.db.models import signals

from versatileimagefield.fields import VersatileImageField
from versatileimagefield.placeholder import OnStoragePlaceholderImage
from versatileimagefield.serializers import VersatileImageFieldSerializer

from .consts import (
    IMAGE_ALLOWED_EXTENSIONS,
    IMAGE_MAX_FILE_SIZE,
    IMAGE_CREATE_ON_DEMAND,
    IMAGE_PLACEHOLDER_PATH,
)
from .files import OptimizedVersatileImageFieldFile, OptimizedVersatileImageFileDescriptor
from .utils import image_upload_to, image_optimizer
from .validators import FileSizeValidator

__all__ = (
    'OptimizedImageField',
)


class OptimizedImageField(VersatileImageField):
    """An ImageField that gets optimized on save() using tinyPNG."""
    descriptor_class = OptimizedVersatileImageFileDescriptor
    attr_class = OptimizedVersatileImageFieldFile

    def __init__(self, *args, **kwargs):
        self.image_sizes_serializer = (
            kwargs.pop(
                'image_sizes_serializer',
                VersatileImageFieldSerializer
            )
        )
        self.image_sizes = kwargs.pop(
            'image_sizes',
            None
        )
        self.create_on_demand = (
            kwargs.pop('create_on_demand', IMAGE_CREATE_ON_DEMAND)
        )
        self.images_warmer = kwargs.pop('images_warmer', None)

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

    def set_variations(self, instance=None, **kwargs):
        is_deferred_field = self.name in instance.get_deferred_fields()

        if is_deferred_field:
            return

        field = getattr(instance, self.name, None)

        image_sizes = self.attr_class.get_validated_image_sizes(
            instance=instance,
            image_sizes=self.image_sizes
        )

        if field and field._committed:
            sizes = (
                self.image_sizes_serializer(
                    sizes=image_sizes
                )
                .to_representation(
                    field
                )
            )
        else:
            sizes = {
                key: self.placeholder_image_name
                for key, _ in image_sizes
            }

        for size, url in sizes.items():
            # variation_field = ImageFieldFile(instance, self, url)
            # setattr(field, size, variation_field)
            setattr(field, size, url)

    def post_delete_callback(self, sender, instance, **kwargs):
        # force delete file and orphans
        field = getattr(instance, self.name)

        if field:
            getattr(instance, self.name).delete(False)

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        signals.post_init.connect(self.set_variations, sender=cls)
        signals.post_delete.connect(self.post_delete_callback, sender=cls)

    def save_form_data(self, instance, data):
        """Remove the OptimizedNotOptimized object on clearing the image."""
        data_ = data
        file = getattr(instance, self.name)

        if isinstance(data, tuple):
            data_ = data[0]

        # Are we updating an image?
        updating_image = (
            True if data_ and file != data_ else False
        )

        if updating_image:
            # optimize data
            if isinstance(data, tuple):
                optimized_data = image_optimizer(data_)
                data = optimized_data, data[1]
            else:
                data = image_optimizer(data)

        # delete orphans files on file clear or change
        if data_ is False or data_ is not None:
            if file and file._committed and file != data_:
                file.delete(save=False)

        super().save_form_data(instance, data)
