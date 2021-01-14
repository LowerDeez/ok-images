import os

from django.core.cache import cache

from versatileimagefield.files import VersatileImageFieldFile
from versatileimagefield.utils import (
    validate_versatileimagefield_sizekey_list,
    get_rendition_key_set
)

from .consts import IMAGE_DEFAULT_RENDITION_KEY_SET

__all__ = (
    'OptimizedVersatileImageFieldFile',
)


class OptimizedVersatileImageFieldFile(VersatileImageFieldFile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image_sizes_serializer = self.field.image_sizes_serializer
        image_sizes = (
                self.field.image_sizes
                or getattr(self.instance, 'image_sizes', None)
                or IMAGE_DEFAULT_RENDITION_KEY_SET
        )

        if isinstance(image_sizes, str):
            image_sizes = get_rendition_key_set(image_sizes)

        self.image_sizes = validate_versatileimagefield_sizekey_list(image_sizes)
        self._create_on_demand = self.field.create_on_demand

        if self.name and self.storage.exists(self.name):
            self._sizes = (
                self.image_sizes_serializer(
                    sizes=self.image_sizes
                )
                .to_representation(
                    self
                )
            )
        else:
            self._sizes = {
                key: self.field.placeholder_image_name
                for key, _ in self.image_sizes
            }

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
