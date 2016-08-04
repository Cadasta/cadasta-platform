from datetime import datetime

from django.core import mail
from django.test import TestCase

from skivvy import APITestCase
from djoser.utils import encode_uid

from core.tests.utils.cases import UserTestCase
from ..models import User
from ..views import api as api_views
from ..token import cadastaTokenGenerator

from .factories import UserFactory


class AccountUserTest(APITestCase, UserTestCase, TestCase):
    view_class = api_views.AccountUser

    def setup_models(self):
        self.user = UserFactory.create(username='imagine71',
                                       email='john@beatles.uk')

    def test_update_email_address(self):
        """Service should send a verification email when the user updates their
           email."""
        data = {'email': 'boss@beatles.uk', 'username': 'imagine71'}
        response = self.request(method='PUT', post_data=data, user=self.user)
        assert response.status_code == 200
        assert len(mail.outbox) == 1

    def test_keep_email_address(self):
        """Service should not send a verification email when the user does not
           their email."""
        data = {'email': 'john@beatles.uk', 'username': 'imagine71'}
        response = self.request(method='PUT', post_data=data, user=self.user)
        assert response.status_code == 200
        assert len(mail.outbox) == 0

    def test_update_with_existing_email(self):
        UserFactory.create(email='boss@beatles.uk')
        data = {'email': 'boss@beatles.uk', 'username': self.user.username}
        response = self.request(method='PUT', post_data=data, user=self.user)
        self.user.refresh_from_db()
        assert response.status_code == 400
        assert self.user.email == 'john@beatles.uk'

    def test_update_username(self):
        data = {'email': self.user.email, 'username': 'john'}
        response = self.request(method='PUT', post_data=data, user=self.user)
        self.user.refresh_from_db()
        assert response.status_code == 200
        assert self.user.username == 'john'

    def test_update_with_existing_username(self):
        UserFactory.create(username='boss')
        data = {'email': self.user.email, 'username': 'boss'}
        response = self.request(method='PUT', post_data=data, user=self.user)
        self.user.refresh_from_db()
        assert response.status_code == 400
        assert self.user.username == 'imagine71'


class AccountSignupTest(APITestCase, UserTestCase, TestCase):
    view_class = api_views.AccountRegister

    def test_user_signs_up(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'iloveyoko79',
            'full_name': 'John Lennon',
        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 201
        assert User.objects.count() == 1

    def test_user_signs_up_with_invalid(self):
        """The server should respond with an 404 error code when a user tries
           to sign up with invalid data"""
        data = {
            'username': 'imagine71',
            'password': 'iloveyoko79',
            'full_name': 'John Lennon',
        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 400
        assert User.objects.count() == 0


class AccountLoginTest(APITestCase, UserTestCase, TestCase):
    view_class = api_views.AccountLogin

    def setup_models(self):
        self.user = UserFactory.create(username='imagine71',
                                       email='john@beatles.uk',
                                       password='iloveyoko79')

    def test_successful_login(self):
        """The view should return a token to authenticate API calls"""
        data = {'username': 'imagine71', 'password': 'iloveyoko79'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 200
        assert 'auth_token' in response.content

    def test_unsuccessful_login(self):
        """The view should return a token to authenticate API calls"""
        data = {'username': 'imagine71', 'password': 'iloveyoko78'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 400

    def test_login_with_unverified_email(self):
        """The view should return an error message if the User.verify_email_by
           is exceeded. An email with a verification link should be have been
           sent to the user."""
        self.user.verify_email_by = datetime.now()
        self.user.save()
        data = {'username': 'imagine71', 'password': 'iloveyoko79'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 400
        assert 'auth_token' not in response.content
        assert len(mail.outbox) == 1


class AccountVerifyTest(APITestCase, UserTestCase, TestCase):
    view_class = api_views.AccountVerify

    def test_activate_account(self):
        user = UserFactory.create()

        token = cadastaTokenGenerator.make_token(user)

        user.last_login = datetime.now()
        user.save()

        data = {'uid': encode_uid(user.pk), 'token': token}
        response = self.request(method='POST', post_data=data)

        user.refresh_from_db()
        assert response.status_code == 200
        assert user.email_verified is True
