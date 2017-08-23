import os
from unittest.mock import patch
from PIL import Image
from django.test import TestCase
from django.conf import settings
from ..utils import thumbnail
from accounts.tests.factories import UserFactory
from core.tests.utils.cases import UserTestCase

path = os.path.dirname(settings.BASE_DIR)


class ThumbnailTest(TestCase, UserTestCase):
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

    def test_make_rotated(self):
        image = path + '/resources/tests/files/rotated-image.jpg'
        thumb = thumbnail.make(image, (100, 100))
        assert thumb.size[0] == 100
        assert thumb.size[1] == 100

    @patch.object(thumbnail, 'make')
    def test_create_image_thumbnails_without_filefield_or_url(self, mock_make):
        user = UserFactory.build(username='MotherOfDragons',
                                 email='dragons@wester.os',
                                 password='G4me0fThr0ne5',
                                 )
        # user instance does not have attribute S3 field named 'picture'
        thumbnail.create_image_thumbnails(user, 'picture')

        # no avatar image is yet stored, so user.avatar.url = ''
        thumbnail.create_image_thumbnails(user, 'avatar')
        assert mock_make.call_count == 0
