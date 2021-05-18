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
    image_sizes = None
    image_preview_size = '300x300'

    image = OptimizedImageField(
        _('Image'),
        blank=True,
        null=True,
        db_index=True,
        ppoi_field='image_ppoi',
        width_field="image_width",
        height_field="image_height",
    )
    image_width = models.PositiveIntegerField(
        _("image width"),
        blank=True,
        null=True,
        editable=False
    )
    image_height = models.PositiveIntegerField(
        _("image height"),
        blank=True,
        null=True,
        editable=False
    )
    image_ppoi = PPOIField(
        verbose_name=_('primary point of interest')
    )
    image_alt = models.CharField(
        _('Image alt'),
        max_length=255,
        blank=True
    )

    class Meta:
        abstract = True
        verbose_name = _("image")
        verbose_name_plural = _("images")

    def __str__(self):
        return self.image_alt

    def get_image_preview(self, size=None):
        """
        Return url of thumbnailed image
        """
        try:
            if not size:
                size = self.image_preview_size

            if size:
                return self.image.crop[size].url
            else:
                return self.image.url
        except Exception:
            return ''
