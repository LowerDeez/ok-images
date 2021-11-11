===============================
django-ok-images |PyPI version|
===============================

|Build Status| |Code Health| |Python Versions| |PyPI downloads| |license| |Project Status|

WebP sizers and filters for `django-versatileimagefield`_. Custom image field with direct access to created images through readable names and model mixin to inherit. Helper utils to delete created images, clear cache and warm images.

Installation
============

Install with pip:

.. code:: shell

    $ pip install django-ok-images django-versatileimagefield

Update INSTALLED_APPS:

.. code:: python

    INSTALLED_APPS = [
        ...
        'versatileimagefield',
        ...
    ]



Available settings
==================

``IMAGE_ALLOWED_EXTENSIONS`` - Extensions for `OptimizedImageField`'s `FileExtensionValidator`.

``IMAGE_MAX_FILE_SIZE`` - Max file size of uploaded images in megabytes. Default to `10`.

``IMAGE_OPTIMIZE_QUALITY`` - Quality to optimize an uploaded image.

``IMAGE_CREATE_ON_DEMAND`` - Custom value for `django-versatileimagefield`_ `create_images_on_demand` setting.

``IMAGE_PLACEHOLDER_PATH`` - Default placeholder path for `django-versatileimagefield`_.

``IMAGE_RGBA_CHANGE_BACKGROUND`` - Changes background of RGBA images to white color.

``IMAGE_LOSSLESS`` - Image lossless configuration. Default to `False`.

How to enable image optimization through TinyPNG:
-------------------------------------------------

``TINYPNG_API_KEY_FUNCTION`` - Path to function, which returns TinyPNG api key.

``TINYPNG_API_KEY`` - TinyPNG api key.


How to use
==========

WebP sizers and filter:
-----------------------

Add next file in any app to register sizers and filters (`more about sizers and filters <https://django-versatileimagefield.readthedocs.io/en/latest/writing_custom_sizers_and_filters.html#registering-sizers-and-filters>`_):

.. code:: python

    # versatileimagefield.py

    from ok_images.contrib.versatileimagefield.versatileimagefield import *


Fields:
-------

There is an ``OptimizedImageField``, inherited from `VersatileImageField <https://django-versatileimagefield.readthedocs.io/en/latest/model_integration.html#model-integration>`_.

Example of usage:

Add next settings (`more about rendition key sets <https://django-versatileimagefield.readthedocs.io/en/latest/drf_integration.html#reusing-rendition-key-sets>`_):

.. code:: python

    # settings.py

    VERSATILEIMAGEFIELD_RENDITION_KEY_SETS = {
        'product': [
            ('full_size', 'url'),
            ('desktop', 'crop__460x430'),
            ('catalog_preview', 'crop__180x180'),

            # webp
            ('desktop_webp', 'crop_webp__460x430'),
            ('catalog_preview_webp', 'crop_webp__180x180'),
        ],
    }

Define a model like this:

.. code:: python

    # models.py
    from ok_images.fields import OptimizedImageField
    

    class Product(models.Model):
        image_sizes = 'product'  # could be set as a global rendition key set for an each image field

        image = OptimizedImageField(
            _('Image'),
            ppoi_field='ppoi',
            blank=True,
            null=True,
            # Optional keyword arguments with default values
            image_sizes_serializer=VersatileImageFieldSerializer,  # from versatileimagefield.serializers import VersatileImageFieldSerializer
            image_sizes='product',  # some of keys, defined in VERSATILEIMAGEFIELD_RENDITION_KEY_SETS setting
            create_on_demand=True,  # enables or disables on-demand image creation
        )
        ppoi = PPOIField(
            verbose_name=_('PPOI')
        )

If ``image_sizes`` is not defined, uses next default rendition key set:

.. code:: python

    IMAGE_DEFAULT_RENDITION_KEY_SET = [
        ('full_size', 'url'),
    ]

How to access generated previews:

.. code:: python

    product.image.full_size
    product.image.catalog_preview
    product.image.desktop_webp


Utils:
------

``delete_all_created_images`` - delete all created images (can be skipped with ``delete_images`` argument) and clear cache for passed models.

``warm_images`` - creates all sized images for a given instance or queryset with passed rendition key set.

.. code:: python
    
    # anywhere.py
    from ok_images.utils import delete_all_created_images, warm_images
		
    	
    delete_all_created_images(Product, delete_images = False)
    warm_images(product, 'product')

    # `rendition_key_set` could be taken from field's or model's attrbiute `image_sizes`, otherwise uses default key set
    warm_images(Product.objects.all())


Async image warming:
--------------------

`tasks.py`:

.. code:: python

    from ok_images.utils import warm_images

    @app.task
    def images_warmer_task(product_pk: int):
        from store.models import Product
        product = Product.objects.get(pk=product_pk)
        warm_images(
            instance_or_queryset=product,
            image_attr='image'
        )


`models.py`:

.. code:: python
   
    from .tasks import images_warmer_task
    	
    	
    def images_warmer(product):
        images_warmer_task.delay(product.pk)
	
		
    class Product(models.Model):
        image_sizes = 'product'

        image = OptimizedImageField(
            _('Image'),
            ppoi_field='ppoi',
            blank=True,
            null=True,
            images_warmer=images_warmer
        )


.. |PyPI version| image:: https://badge.fury.io/py/django-ok-images.svg
   :target: https://badge.fury.io/py/django-ok-images
.. |Build Status| image:: https://github.com/LowerDeez/ok-images/workflows/Upload%20Python%20Package/badge.svg
   :target: https://github.com/LowerDeez/ok-images/
   :alt: Build status
.. |Code Health| image:: https://api.codacy.com/project/badge/Grade/e5078569e40d428283d17efa0ebf9d19
   :target: https://www.codacy.com/app/LowerDeez/ok-images
   :alt: Code health
.. |Python Versions| image:: https://img.shields.io/pypi/pyversions/django-ok-images.svg
   :target: https://pypi.org/project/django-ok-images/
   :alt: Python versions
.. |license| image:: https://img.shields.io/pypi/l/django-ok-images.svg
   :alt: Software license
   :target: https://github.com/LowerDeez/ok-images/blob/master/LICENSE
.. |PyPI downloads| image:: https://img.shields.io/pypi/dm/django-ok-images.svg
   :alt: PyPI downloads
.. |Project Status| image:: https://img.shields.io/pypi/status/django-ok-images.svg
   :target: https://pypi.org/project/django-ok-images/
   :alt: Project Status

.. _django-versatileimagefield: https://github.com/respondcreate/django-versatileimagefield
