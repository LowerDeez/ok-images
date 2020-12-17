import os

from django.core.cache import cache
from django.core.validators import FileExtensionValidator

from versatileimagefield.fields import VersatileImageField
from versatileimagefield.files import VersatileImageFieldFile
from versatileimagefield.serializers import VersatileImageFieldSerializer

from .consts import (
    IMAGE_ALLOWED_EXTENSIONS,
    IMAGE_DEFAULT_RENDITION_KEY_SET,
    IMAGE_CREATE_ON_DEMAND
)
from .utils import image_upload_to, image_optimizer

__all__ = (
    'OptimizedImageField',
)


class OptimizedVersatileImageFieldFile(VersatileImageFieldFile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image_sizes_serializer = self.field.image_sizes_serializer
        self.image_sizes = (
                self.field.image_sizes
                or getattr(self.instance, 'image_sizes', None)
                or IMAGE_DEFAULT_RENDITION_KEY_SET
        )
        self._create_on_demand = self.field.create_on_demand

        if self._file:
            self._sizes = (
                self.image_sizes_serializer(
                    sizes=self.image_sizes
                )
                .to_representation(
                    self
                )
            )
            for size, url in self._sizes.items():
                setattr(self, size, url)

    def delete_matching_files_from_storage(self, root_folder, regex):
        """
        Delete files in `root_folder` which match `regex` before file ext.

        Example values:
            * root_folder = 'foo/'
            * self.name = 'bar.jpg'
            * regex = re.compile('-baz')

            Result:
                * foo/bar-baz.jpg <- Deleted
                * foo/bar-biz.jpg <- Not deleted
        """
        if not self.name:   # pragma: no cover
            return

        try:
            directory_list, file_list = self.storage.listdir(root_folder)
        except OSError:   # pragma: no cover
            pass
        else:
            folder, filename = os.path.split(self.name)
            basename, ext = os.path.splitext(filename)

            for f in file_list:
                if not f.startswith(basename):   # pragma: no cover
                    continue

                tag = str(f[len(basename):-len(ext)]).rstrip('.')
                match = regex.match(tag)

                if match is not None:
                    file_location = os.path.join(root_folder, f)
                    self.storage.delete(file_location)

                    cache.delete(
                        self.storage.url(file_location)
                    )
                    print(
                        "Deleted {file} (created from: {original})".format(
                            file=os.path.join(root_folder, f),
                            original=self.name
                        )
                    )

    def delete(self, save=True):
        self.delete_all_created_images()
        super().delete(save=save)


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
