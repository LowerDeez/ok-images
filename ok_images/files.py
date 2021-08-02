import os

from django.core.cache import cache
from django.db import transaction

from versatileimagefield.fields import VersatileImageField
from versatileimagefield.files import VersatileImageFieldFile, VersatileImageFileDescriptor
from versatileimagefield.utils import (
    validate_versatileimagefield_sizekey_list,
    get_rendition_key_set
)

from .consts import IMAGE_DEFAULT_RENDITION_KEY_SET

__all__ = (
    'OptimizedVersatileImageFileDescriptor',
    'OptimizedVersatileImageFieldFile',
)


class OptimizedVersatileImageFileDescriptor(VersatileImageFileDescriptor):
    def __set__(self, instance, value):
        return super().__set__(instance, value)

    def __get__(self, instance=None, owner=None):
        return super().__get__(instance, owner)


class OptimizedVersatileImageFieldFile(VersatileImageFieldFile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image_sizes_serializer = self.field.image_sizes_serializer
        self.image_sizes = self.get_validated_image_sizes(self.instance, self.field.image_sizes)
        self._create_on_demand = self.field.create_on_demand

    @classmethod
    def get_validated_image_sizes(cls, instance, image_sizes=None):
        image_sizes = (
            image_sizes
            or getattr(instance, 'image_sizes', None)
            or IMAGE_DEFAULT_RENDITION_KEY_SET
        )

        if isinstance(image_sizes, str):
            image_sizes = get_rendition_key_set(image_sizes)

        image_sizes = validate_versatileimagefield_sizekey_list(image_sizes)

        return image_sizes

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

    def save(self, name, content, save=True):
        # delete old file on replace
        old_file = getattr(self.field, 'old_file', None)

        if old_file:
            old_file.delete(save=False)

        super().save(name, content, save)
        images_warmer = self.field.images_warmer

        if images_warmer:
            transaction.on_commit(lambda: images_warmer(self.instance))
        else:
            self.build_versatileimagefield_url_set()

    def build_versatileimagefield_url_set(self):
        file = VersatileImageFieldFile(self.instance, self.field, self.name)

        if self.name and self.storage.exists(self.name):
            self._sizes = (
                self.image_sizes_serializer(
                    sizes=self.image_sizes
                )
                .to_representation(
                    file
                )
            )
        else:
            self._sizes = {
                key: self.field.placeholder_image_name
                for key, _ in self.image_sizes
            }
