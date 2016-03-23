from django.test import TestCase
from django.http import HttpRequest
from django.contrib.auth.models import AnonymousUser

from accounts.tests.factories import UserFactory

from ..views.default import IndexPage, Dashboard


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
