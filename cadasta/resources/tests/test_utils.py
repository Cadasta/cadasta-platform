import os
from PIL import Image
from django.test import TestCase
from django.conf import settings
from ..utils import thumbnail

path = os.path.dirname(settings.BASE_DIR)


class ThumbnailTest(TestCase):
    def test_is_landscape(self):
        assert thumbnail.is_landscape(200, 100) is True
        assert thumbnail.is_landscape(100, 200) is False

    def test_box_params_center(self):
        box = (50, 0, 150, 100)
        assert thumbnail.box_params_center(200, 100) == box

        box = (0, 50, 100, 150)
        assert thumbnail.box_params_center(100, 200) == box

    def test_crop(self):
        image = Image.open(path + '/resources/tests/files/image.jpg')
        cropped = thumbnail.crop(image.copy())
        assert cropped.size[0] == cropped.size[1]

    def test_make(self):
        image = path + '/resources/tests/files/image.jpg'
        thumb = thumbnail.make(image, (100, 100))
        assert thumb.size[0] == 100
        assert thumb.size[1] == 100

    def test_make_no_crop(self):
        image = path + '/resources/tests/files/image.jpg'
        thumb = thumbnail.make(image, (100, 100), cropped=False)
        assert thumb.size[0] == 100
        assert thumb.size[1] == 74

    def test_make_rotated(self):
        image = path + '/resources/tests/files/rotated-image.jpg'
        thumb = thumbnail.make(image, (100, 100))
        assert thumb.size[0] == 100
        assert thumb.size[1] == 100
