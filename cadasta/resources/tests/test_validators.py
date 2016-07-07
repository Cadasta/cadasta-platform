import pytest
import os
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.conf import settings
from buckets.fields import S3File, S3FileField
from buckets.test.utils import ensure_dirs
from buckets.test.storage import FakeS3Storage

from ..validators import validate_file_type

path = os.path.dirname(settings.BASE_DIR)


class ValidateFileTypeTest(TestCase):
    def test_valid_file(self):
        ensure_dirs()
        storage = FakeS3Storage()
        field = S3FileField(storage=storage)
        file = open(path + '/resources/tests/files/image.jpg', 'rb')
        file = storage.save('image.jpg', file)
        s3_file = S3File(file, field=field)

        try:
            validate_file_type(s3_file)
        except ValidationError:
            pytest.fail('ValidationError raised unexpectedly')

    def test_invalid_file(self):
        ensure_dirs()
        storage = FakeS3Storage()
        field = S3FileField(storage=storage)
        file = open(path + '/resources/tests/files/text.txt', 'rb')
        file = storage.save('text.txt', file)
        s3_file = S3File(file, field=field)

        with pytest.raises(ValidationError) as e:
            validate_file_type(s3_file)
        assert e.value.message == "Files of type text/plain are not accepted."
