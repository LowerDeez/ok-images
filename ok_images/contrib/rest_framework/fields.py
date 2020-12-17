from versatileimagefield.serializers import VersatileImageFieldSerializer

__all__ = (
    'WebPVersatileImageFieldSerializer',
)


class WebPVersatileImageFieldSerializer(VersatileImageFieldSerializer):
    def to_representation(self, value):
        data = super().to_representation(value)
        for key, image_url in data.items():
            if key.endswith('webp'):
                name, ext = image_url.rsplit('.', 1)
                data[key] = f'{name}.webp'
        return data
