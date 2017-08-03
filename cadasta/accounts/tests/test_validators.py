from ..validators import phone_validator
from unittest import TestCase


class PhoneValidatorTest(TestCase):
    def test_valid_phone(self):
        phone = '+91937768250'
        assert phone_validator(phone) is True

    def test_invalid_phone(self):
        phone = 'Test Number'
        assert phone_validator(phone) is False

    def test_invalid_phone_without_country_code(self):
        phone = '9327768250'
        assert phone_validator(phone) is False

    def test_invalid_phone_with_white_spaces(self):
        phone = '+91 9327768250'
        assert phone_validator(phone) is False
