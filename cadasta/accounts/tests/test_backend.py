from django.test import TestCase
from allauth.account.models import EmailAddress
from core.tests.utils.cases import UserTestCase
from ..backends import AuthenticationBackend
from .factories import UserFactory


class AuthBackendTest(UserTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(
            username='kindofblue',
            email='miles@davis.co',
            password='PlayTh3Trumpet!'
        )
        self.backend = AuthenticationBackend()

    def test_login_with_email(self):
        credentials = {'email': 'miles@davis.co',
                       'password': 'PlayTh3Trumpet!'}
        assert self.backend._authenticate_by_email(**credentials) == self.user

    def test_login_with_unapproved_email(self):
        EmailAddress.objects.create(
            user=self.user,
            email='miles2@davis.co',
            verified=False,
            primary=True
        )
        credentials = {'email': 'miles2@davis.co',
                       'password': 'PlayTh3Trumpet!'}
        assert self.backend._authenticate_by_email(**credentials) is None

    def test_auth_in_username_field(self):
        credentials = {'username': 'miles@davis.co',
                       'password': 'PlayTh3Trumpet!'}
        assert self.backend._authenticate_by_email(**credentials) == self.user
