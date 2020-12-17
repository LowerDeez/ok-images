from django.db import models
from django.utils.translation import ugettext_lazy as _

from versatileimagefield.fields import PPOIField

from .fields import OptimizedImageField

__all__ = (
    'ImageMixin',
)


class ImageMixin(models.Model):
    """
    Image mixin.
    Mixin to add image field with primary point of interest and alt text to models.

    Attrs:
        image (VersatileImageField): image
        ppoi (PPOIField): primary point of interest
        alt (CharField): alt text
    """
    image = OptimizedImageField(
        _('Изображение'),
        ppoi_field='ppoi',
        blank=True,
        null=True,
        db_index=True,
    )
    ppoi = PPOIField(
        verbose_name=_('PPOI')
    )
    image_alt = models.CharField(
        _('Image alt'),
        max_length=128,
        blank=True
    )

    class Meta:
        abstract = True

    def get_thumbnail_image(self, size=None):
        """
        Return url of thumbnailed image
        """
        try:
            if size:
                return self.image.thumbnail[size].url
            else:
                return self.image.url
        except Exception:
            return self.link if hasattr(self, 'link') else ''

    def get_crop_image(self, size=None):
        """
        Return url of cropped image
        """
        try:
            if size:
                return self.image.crop[size].url
            else:
                return self.image.url
        except Exception:
            return self.link if hasattr(self, 'link') else ''

    def delete(self, *args, **kwargs):
        self.image.delete(save=False)
        super().delete(*args, **kwargs)
