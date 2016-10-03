import pytest

from django.core.exceptions import ValidationError
from django.test import TestCase

from ..validators import validate_file_type


class ValidateFileTypeTest(TestCase):

    def test_valid_file(self):
        try:
            validate_file_type('image/png')
        except ValidationError:
            pytest.fail('ValidationError raised unexpectedly')

    def test_invalid_file(self):
        with pytest.raises(ValidationError) as e:
            validate_file_type('application/x-empty')
        assert e.value.message == (
            'Files of type application/x-empty are not accepted.')
