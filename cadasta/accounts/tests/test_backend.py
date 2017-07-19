from django.test import TestCase
from allauth.account.models import EmailAddress
from core.tests.utils.cases import UserTestCase
from ..backends import AuthenticationBackend, PhoneAuthenticationBackend
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

    def test_login_with_username(self):
        credentials = {'username': 'kindofblue',
                       'password': 'PlayTh3Trumpet!'}

        assert self.backend._authenticate_by_username(
            **credentials) == self.user

    def test_login_for_inactive_account(self):
        self.user.is_active = False
        self.user.save()
        credentials = {'username': 'kindofblue',
                       'password': 'PlayTh3Trumpet!'}

        assert self.backend._authenticate_by_username(**credentials) is None

    def test_login_with_non_existent_username(self):
        credentials = {'username': 'alwaysblue_alwaysblue',
                       'password': 'PlayTh3Trumpet!'}
        assert self.backend._authenticate_by_username(**credentials) is None


class PhoneAuthBackendTest(UserTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(
            phone='+912345678990', password='PlayTh3Trumpet!'
        )
        self.backend = PhoneAuthenticationBackend()

    def test_login_with_verified_phone(self):
        credentials = {'phone': '+912345678990',
                       'password': 'PlayTh3Trumpet!'}
        assert self.backend.authenticate(**credentials) == self.user

    def test_login_for_inactive_account(self):
        self.user.is_active = False
        self.user.save()
        credentials = {'phone': '+912345678990',
                       'password': 'PlayTh3Trumpet!'}
        assert self.backend.authenticate(**credentials) is None

    def test_login_with_non_existent_phone(self):
        credentials = {'phone': '+912345612345',
                       'password': 'PlayTh3Trumpet!'}
        assert self.backend.authenticate(**credentials) is None
