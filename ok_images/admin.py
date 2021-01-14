__all__ = (
    'ImageMixinAdmin',
)


class ImageMixinAdmin:
    """
    Mixin.
    Sets created_at and updated_at timestamps as readonly fields
    """
    image_readonly_fields = [
        'image_width',
        'image_height'
    ]

    def get_readonly_fields(self, *args, **kwargs):
        """
        Add to list of readonly fields date created and date last updated model instance.

        Returns:
            tuple: List of model readonly fields with date created and date published.
        """
        fields = super().get_readonly_fields(*args, **kwargs)
        return tuple(fields) + tuple(self.image_readonly_fields)
