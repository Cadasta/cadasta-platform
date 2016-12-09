import json
import pytest
from django.test import TestCase
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError

from ..validators import validate_contact


class ValidateContactTest(TestCase):
    def test_valid_contact(self):
        value = {
            'name': 'Nicole Smith',
            'email': 'n.smith@example.com'
        }

        assert validate_contact(value) is None

    def test_validate_single_error(self):
        value = {
            'email': 'n.smith@example.com'
        }

        with pytest.raises(ValidationError) as exc:
            validate_contact(value)

        assert len(exc.value.error_list) == 1
        assert exc.value.error_list[0].messages[0] == (
            '{"name": "' + _("This field is required.") + '"}')

    def test_validate_multiple_errors(self):
        value = {
            'email': "noemail"
        }

        with pytest.raises(ValidationError) as exc:
            validate_contact(value)

        assert len(exc.value.error_list) == 1

        actual = json.loads(exc.value.error_list[0].messages[0])
        expected = {
            'name': 'This field is required.',
            'email': '\'noemail\' is not a \'email\''
        }
        assert actual == expected

    def test_validate_multiple_contacts(self):
        value = [{
            'email': 'n.smith@exampl.com'
        }, {
            'name': "Nicole Smith",
            'email': "noemail"
        }]

        with pytest.raises(ValidationError) as exc:
            validate_contact(value)

        assert len(exc.value.error_list) == 2
        assert exc.value.error_list[0].messages[0] == (
            '{"name": "' + _("This field is required.") + '"}')
        assert exc.value.error_list[1].messages[0] == (
            '{"email": "\'noemail\' is not a \'email\'"}')
