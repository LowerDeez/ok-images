"""
You need to import this file in any app in versatileimagefield.py file
to make it visible for versatileimagefield
"""
from PIL import Image

from django.utils.six import BytesIO

from versatileimagefield.datastructures.sizedimage import (
    MalformedSizedImageKey,
    settings,
    cache,
    VERSATILEIMAGEFIELD_CACHE_LENGTH,
    SizedImageInstance
)
from versatileimagefield.registry import versatileimagefield_registry
from versatileimagefield.utils import QUAL
from versatileimagefield.versatileimagefield import (
    FilteredImage,
    CroppedImage,
    ThumbnailImage
)

from .utils import (
    get_resized_path,
    get_filtered_path
)

__all__ = (
    'WebPMixin',
    'ToWebPImage',
    'WebPThumbnailImage'
)


class WebPMixin:
    ext = "webp"

    def __getitem__(self, key):
        """
        Return a URL to an image sized according to key.

        Arguments:
            * `key`: A string in the following format
                     '[width-in-pixels]x[height-in-pixels]'
                     Example: '400x400'
        """
        try:
            width, height = [int(i) for i in key.split('x')]
        except (KeyError, ValueError):
            raise MalformedSizedImageKey(
                "%s keys must be in the following format: "
                "'`width`x`height`' where both `width` and `height` are "
                "integers." % self.__class__.__name__
            )

        if not self.path_to_image and getattr(
            settings, 'VERSATILEIMAGEFIELD_USE_PLACEHOLDIT', False
        ):
            resized_url = "http://placehold.it/%dx%d" % (width, height)
            resized_storage_path = resized_url
        else:
            resized_storage_path = get_resized_path(
                path_to_image=self.path_to_image,
                ext=self.ext,
                width=width,
                height=height,
                filename_key=self.get_filename_key(),
                storage=self.storage
            )

            try:
                resized_url = self.storage.url(resized_storage_path)
            except Exception:
                resized_url = None

            if self.create_on_demand is True:
                if cache.get(resized_url) and resized_url is not None:
                    # The sized path exists in the cache so the image already
                    # exists. So we `pass` to skip directly to the return
                    # statement
                    pass
                else:
                    if resized_storage_path and not self.storage.exists(
                        resized_storage_path
                    ):
                        self.create_resized_image(
                            path_to_image=self.path_to_image,
                            save_path_on_storage=resized_storage_path,
                            width=width,
                            height=height
                        )

                        resized_url = self.storage.url(resized_storage_path)

                    # Setting a super-long cache for a resized image (30 Days)
                    cache.set(resized_url, 1, VERSATILEIMAGEFIELD_CACHE_LENGTH)

        return SizedImageInstance(
            name=resized_storage_path,
            url=resized_url,
            storage=self.storage
        )

    def retrieve_image(self, path_to_image):
        image = self.storage.open(path_to_image, "rb")
        file_ext = self.ext
        image_format, mime_type = "WEBP", "image/webp"
        return Image.open(image), file_ext, image_format, mime_type

    def save_image(self, imagefile, save_path, file_ext, mime_type):
        path, ext = save_path.rsplit('.')
        save_path = f'{path}.{self.ext}'
        return super().save_image(imagefile, save_path, file_ext, mime_type)

    def preprocess_WEBP(self, image, **kwargs):
        return image, {"quality": QUAL, "lossless": False, "icc_profile": ""}


class ToWebPImage(WebPMixin, FilteredImage):
    """
    object.image.filters.to_webp.url
    """
    def __init__(self, path_to_image, storage, create_on_demand, filename_key):
        super().__init__(
            path_to_image, storage, create_on_demand, filename_key
        )
        self.name = get_filtered_path(
            path_to_image=self.path_to_image,
            ext=self.ext,
            filename_key=filename_key,
            storage=storage
        )

        self.url = storage.url(self.name)

    def process_image(self, image, image_format, save_kwargs):
        imagefile = BytesIO()
        image, save_kwargs = self.preprocess(image, "WEBP")
        image.save(imagefile, **save_kwargs)
        return imagefile


class WebPThumbnailImage(WebPMixin, ThumbnailImage):
    """
    object.image.thumbnail_webp['512x511'].url
    """
    filename_key = "thumbnail_webp"

    def process_image(self, image, image_format, save_kwargs, width, height):
        imagefile = BytesIO()
        image.thumbnail(
            (width, height),
            Image.ANTIALIAS
        )

        image, save_kwargs = self.preprocess(image, "WEBP")

        image.save(
            imagefile,
            **save_kwargs
        )
        return imagefile


class WebPCroppedImage(WebPMixin, CroppedImage):
    """
    object.image.crop_webp['512x511'].url
    """
    filename_key = "crop_webp"
    filename_key_regex = r'crop_webp-c[0-9-]+__[0-9-]+'

    def process_image(self, image, image_format, save_kwargs,
                      width, height):
        imagefile = BytesIO()
        palette = image.getpalette()
        cropped_image = self.crop_on_centerpoint(
            image,
            width,
            height,
            self.ppoi
        )

        # Using ImageOps.fit on GIFs can introduce issues with their palette
        # Solution derived from: http://stackoverflow.com/a/4905209/1149774
        if image_format == 'GIF':
            cropped_image.putpalette(palette)

        cropped_image, save_kwargs = self.preprocess(cropped_image, "WEBP")

        cropped_image.save(
            imagefile,
            **save_kwargs
        )

        return imagefile


versatileimagefield_registry.register_filter('to_webp', ToWebPImage)
versatileimagefield_registry.register_sizer("thumbnail_webp", WebPThumbnailImage)
versatileimagefield_registry.register_sizer("crop_webp", WebPCroppedImage)
