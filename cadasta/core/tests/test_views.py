from django.test import TestCase
from django.http import Http404, HttpRequest
from django.contrib.auth.models import AnonymousUser

from rest_framework.exceptions import NotFound

from accounts.tests.factories import UserFactory

from ..views import set_exception, eval_json, IndexPage, Dashboard


class IndexPageTest(TestCase):
    def setUp(self):
        self.view = IndexPage.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        setattr(self.request, 'user', AnonymousUser())

    def test_redirects_when_user_is_signed_in(self):
        user = UserFactory.create()
        setattr(self.request, 'user', user)
        response = self.view(self.request)
        assert response.status_code == 302
        assert '/dashboard/' in response['location']

    def test_page_is_rendered_when_user_is_not_signed_in(self):
        response = self.view(self.request)
        assert response.status_code == 200


class DashboardTest(TestCase):
    def setUp(self):
        self.view = Dashboard.as_view()
        self.request = HttpRequest()
        setattr(self.request, 'method', 'GET')
        setattr(self.request, 'user', AnonymousUser())

    def test_redirects_when_user_is_not_signed_in(self):
        response = self.view(self.request)
        assert response.status_code == 302
        assert '/account/login/' in response['location']

    def test_page_is_rendered_when_user_is_signed_in(self):
        user = UserFactory.create()
        setattr(self.request, 'user', user)
        response = self.view(self.request)
        assert response.status_code == 200


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
