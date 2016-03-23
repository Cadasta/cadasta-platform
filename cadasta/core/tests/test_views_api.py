from django.test import TestCase
from django.http import Http404

from rest_framework.exceptions import NotFound

from ..views.api import set_exception, eval_json


class ExceptionHandleTest(TestCase):
    def test_set_exception_with_404(self):
        exception = Http404("No Organization matches the given query.")

        e = set_exception(exception)
        assert type(e) == NotFound
        assert str(e) == "Organization not found."

    def test_set_exception_with_404_and_different_error(self):
        exception = Http404("Error Message")

        e = set_exception(exception)
        assert type(e) == Http404
        assert str(e) == "Error Message"

    def test_set_exception_with_NotFound(self):
        exception = NotFound("Error Message")

        e = set_exception(exception)
        assert type(e) == NotFound
        assert str(e) == "Error Message"

    def test_evaluate_json(self):
        response_data = {
            'contacts': [
                '{"name": "This field is required.", "url": "\'blah\' is not a \'uri\'"}',
                '{"name": "This field is required."}',
            ],
            'field': "Something went wrong"
        }

        actual = eval_json(response_data)

        expected = {
            'contacts': [
                {'name': "This field is required.", 'url': "\'blah\' is not a \'uri\'"},
                {'name': "This field is required."},
            ],
            'field': "Something went wrong"
        }

        assert actual == expected
