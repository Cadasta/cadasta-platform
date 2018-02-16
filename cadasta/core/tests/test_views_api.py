from django.test import TestCase
from django.http import Http404
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework.exceptions import NotFound
from rest_framework.exceptions import ValidationError as DRFValidationError

from ..views.api import set_exception, eval_json


class ExceptionHandleTest(TestCase):
    def test_set_exception_with_404(self):
        exception = Http404("No Organization matches the given query.")

        e = set_exception(exception, 'http://testserver.com')
        assert type(e) == NotFound
        assert str(e) == "Organization not found."

    def test_set_exception_with_404_and_different_error(self):
        exception = Http404("Error Message")

        e = set_exception(exception, 'http://testserver.com')
        assert type(e) == Http404
        assert str(e) == "Error Message"

    def test_set_exception_with_NotFound(self):
        exception = NotFound("Error Message")

        e = set_exception(exception, 'http://testserver.com')
        assert type(e) == NotFound
        assert str(e) == "Error Message"

    def test_set_exception_with_validation_error(self):
        # message case
        exception = DjangoValidationError(message="Error Message")
        e = set_exception(exception, 'http://testserver.com')
        assert type(e) == DRFValidationError
        assert "Error Message" in e.detail['detail']

        # messages case
        exception = DjangoValidationError(message=["Error 1", "Error 2"])
        e = set_exception(exception, 'http://testserver.com')
        assert type(e) == DRFValidationError
        assert "Error 1" in e.detail['detail']
        assert "Error 2" in e.detail['detail']

        # message_dict case
        exception = DjangoValidationError(
            message={'error1': 'Error 1', 'error2': 'Error 2'})
        e = set_exception(exception, 'http://testserver.com')
        assert type(e) == DRFValidationError
        assert "Error 1" in e.detail['error1']
        assert "Error 2" in e.detail['error2']

    def test_evaluate_json(self):
        response_data = {
            'contacts': [
                '{"name": "This field is required.", '
                '"url": "\'blah\' is not a \'uri\'"}',
                '{"name": "This field is required."}',
            ],
            'field': "Something went wrong"
        }

        actual = eval_json(response_data)

        expected = {
            'contacts': [
                {'name': "This field is required.",
                 'url': "\'blah\' is not a \'uri\'"},
                {'name': "This field is required."},
            ],
            'field': "Something went wrong"
        }

        assert actual == expected

        # test with list
        response_data = ['Error 1', 'Error 2']
        actual = eval_json(response_data)
        expected = response_data
        assert actual == expected
