from io import BytesIO
import magic

from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator
from django.template.defaultfilters import filesizeformat
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from PIL import Image

__all__ = (
    'BaseSizeValidator',
    'MinSizeValidator',
    'MaxSizeValidator',
    'FileSizeValidator',
)


class BaseSizeValidator(BaseValidator):
    """Base validator that validates the size of an image."""

    def __init__(self, width, height):
        self.limit_value = width or float('inf'), height or float('inf')

    def __call__(self, value):
        cleaned = self.clean(value)

        if self.compare(cleaned, self.limit_value):
            params = {
                'width': self.limit_value[0],
                'height': self.limit_value[1],
            }

            raise ValidationError(
                self.message,
                code=self.code,
                params=params
            )

    def compare(self, a, b):
        return True

    def clean(self, value):
        value.seek(0)
        stream = BytesIO(value.read())
        size = Image.open(stream).size
        value.seek(0)
        return size


class MaxSizeValidator(BaseSizeValidator):
    """
    ImageField validator to validate the max width and height of an image.
    You may use None as an infinite boundary.

    image2 = StdImageField(validators=[MaxSizeValidator(1028, 768)])
    """
    code = 'max_resolution'
    message = _(
        'The image you uploaded is too large.'
        ' The required maximum resolution is:'
        ' %(width)sx%(height)s px.'
    )

    def compare(self, img_size, max_size):
        return img_size[0] > max_size[0] or img_size[1] > max_size[1]


class MinSizeValidator(BaseSizeValidator):
    """
    ImageField validator to validate the min width and height of an image.
    You may use None as an infinite boundary.

    image1 = StdImageField(validators=[MinSizeValidator(800, 600)])

    """
    message = _(
        'The image you uploaded is too small.'
        ' The required minimum resolution is:'
        ' %(width)sx%(height)s px.'
    )

    def compare(self, img_size, min_size):
        return img_size[0] < min_size[0] or img_size[1] < min_size[1]


def _to_mb(value: int):
    if value:
        value *= 1024 * 1024

    return value


@deconstructible
class FileSizeValidator:
    error_messages = {
        'max_size': _(
            "Ensure this file size is not greater than %(max_size)s."
            " Your file size is %(size)s."
        ),
        'min_size': _(
            "Ensure this file size is not less than %(min_size)s. "
            "Your file size is %(size)s."
        ),
        'content_type': _(
            "Files of type %(content_type)s are not supported."
        ),
    }

    def __init__(self, max_size=None, min_size=None, content_types=None):
        self.max_size = _to_mb(max_size)
        self.min_size = _to_mb(min_size)
        self.content_types = content_types

    def __call__(self, value):
        size = value.size

        if self.max_size is not None and size > self.max_size:
            params = {
                'max_size': filesizeformat(self.max_size),
                'size': filesizeformat(size),
            }
            raise ValidationError(
                self.error_messages['max_size'],
                'max_size',
                params
            )

        if self.min_size is not None and size < self.min_size:
            params = {
                'min_size': filesizeformat(self.min_size),
                'size': filesizeformat(size)
            }
            raise ValidationError(
                self.error_messages['min_size'],
                'min_size',
                params
            )

        if self.content_types:
            content_type = magic.from_buffer(value.read(), mime=True)
            value.seek(0)

            if content_type not in self.content_types:
                params = {'content_type': content_type}
                raise ValidationError(
                    self.error_messages['content_type'],
                    'content_type',
                    params
                )

    def __eq__(self, other):
        return (
            isinstance(other, FileSizeValidator) and
            self.max_size == other.max_size and
            self.min_size == other.min_size and
            self.content_types == other.content_types
        )
