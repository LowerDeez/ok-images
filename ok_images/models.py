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

    image = OptimizedImageField(
        _('Изображение'),
        ppoi_field='ppoi',
        blank=True,
        null=True,
        db_index=True,
        image_sizes=image_sizes
    )
    ppoi = PPOIField(
        verbose_name=_('PPOI')
    )
    image_alt = models.CharField(
        _('Image alt'),
        max_length=255,
        blank=True
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.image_alt

    def delete(self, *args, **kwargs):
        self.image.delete(save=False)
        super().delete(*args, **kwargs)
