"""
Utils from versatileimagefield, modified to accept extensions
"""
import os

from versatileimagefield.utils import (
    QUAL,
    post_process_image_key,
    VERSATILEIMAGEFIELD_SIZED_DIRNAME,
    VERSATILEIMAGEFIELD_FILTERED_DIRNAME
)

__all__ = (
    'get_resized_filename',
    'get_resized_path',
    'get_filtered_filename',
    'get_filtered_path'
)


def get_resized_filename(filename, ext, width, height, filename_key):
    try:
        image_name, extension = filename.rsplit(".", 1)
    except ValueError:
        image_name = filename
        extension = 'jpg'

    if ext is None:
        ext = extension

    resized_template = "%(filename_key)s-%(width)dx%(height)d"

    if ext.lower() in ["jpg", "jpeg", "webp"]:
        resized_template = resized_template + "-%(quality)d"

    resized_key = resized_template % (
        {
            "filename_key": filename_key,
            "width": width,
            "height": height,
            "quality": QUAL,
        }
    )

    return "%(image_name)s-%(image_key)s.%(ext)s" % (
        {
            "image_name": image_name,
            "image_key": post_process_image_key(resized_key),
            "ext": ext,
        }
    )


def get_resized_path(path_to_image, ext, width, height, filename_key, storage):
    containing_folder, filename = os.path.split(path_to_image)

    resized_filename = get_resized_filename(
        filename,
        ext,
        width,
        height,
        filename_key
    )

    joined_path = os.path.join(*[
        VERSATILEIMAGEFIELD_SIZED_DIRNAME,
        containing_folder,
        resized_filename
    ]).replace(" ", "")  # Removing spaces so this path is memcached friendly

    return joined_path


def get_filtered_filename(filename, ext, filename_key):
    """
    Return the 'filtered filename' (according to `filename_key`)
    in the following format:
    `filename`__`filename_key`__.ext
    """
    try:
        image_name, extension = filename.rsplit('.', 1)
    except ValueError:
        image_name = filename
        extension = 'jpg'

    if ext is None:
        ext = extension

    return "%(image_name)s__%(filename_key)s__.%(ext)s" % ({
        'image_name': image_name,
        'filename_key': filename_key,
        'ext': ext
    })


def get_filtered_path(path_to_image, ext, filename_key, storage):
    """
    Return the 'filtered path'
    """
    containing_folder, filename = os.path.split(path_to_image)

    filtered_filename = get_filtered_filename(filename, ext, filename_key)
    path_to_return = os.path.join(*[
        containing_folder,
        VERSATILEIMAGEFIELD_FILTERED_DIRNAME,
        filtered_filename
    ])
    # Removing spaces so this path is memcached key friendly
    path_to_return = path_to_return.replace(' ', '')
    return path_to_return
