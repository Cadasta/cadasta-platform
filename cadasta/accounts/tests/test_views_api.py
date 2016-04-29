from datetime import datetime

from django.test import TestCase
from django.core import mail

from rest_framework.test import APIRequestFactory, force_authenticate
from djoser.utils import encode_uid

from ..models import User
from ..views.api import (
    AccountUser, AccountRegister, AccountLogin, AccountVerify
)
from ..token import cadastaTokenGenerator

from .factories import UserFactory


class AccountUserTest(TestCase):
    def _put(self, user, data, versioned=True, status=None, mails=None):
        if versioned:
            url = '/v1/account/'
        else:
            url = '/account/'
        request = APIRequestFactory().put(url, data)
        force_authenticate(request, user=user)
        response = AccountUser.as_view()(request).render()
        if status is not None:
            assert response.status_code == status
        if mails is not None:
            assert len(mail.outbox) == mails

    def test_update_email_address(self):
        """Service should send a verification email when the user updates their
           email."""
        user = UserFactory.create(username='imagine71',
                                  email='john@beatles.uk')
        data = {'email': 'boss@beatles.uk', 'username': 'imagine71'}
        self._put(user, data, versioned=False, status=200, mails=1)

    def test_keep_email_address(self):
        """Service should not send a verification email when the user does not
           their email."""
        user = UserFactory.create(username='imagine71',
                                  email='john@beatles.uk')
        data = {'email': 'john@beatles.uk', 'username': 'imagine71'}
        self._put(user, data, status=200, mails=0)

    def test_update_with_existing_email(self):
        UserFactory.create(email='boss@beatles.uk')
        user = UserFactory.create(email='john@beatles.uk')
        data = {'email': 'boss@beatles.uk', 'username': user.username}
        self._put(user, data, status=400, mails=0)
        user.refresh_from_db()
        assert user.email == 'john@beatles.uk'

    def test_update_username(self):
        user = UserFactory.create(username='imagine71')
        data = {'email': user.email, 'username': 'john'}
        self._put(user, data, status=200)
        user.refresh_from_db()
        assert user.username == 'john'

    def test_update_with_existing_username(self):
        UserFactory.create(username='boss')
        user = UserFactory.create(username='john')
        data = {'email': user.email, 'username': 'boss'}
        self._put(user, data, status=400)
        user.refresh_from_db()
        assert user.username == 'john'


class AccountSignupTest(TestCase):
    def _post(self, data, status=None, count=None):
        url = '/v1/account/register/'
        request = APIRequestFactory().post(url, data)
        response = AccountRegister.as_view()(request).render()
        if status is not None:
            assert response.status_code == status
        if count is not None:
            assert User.objects.count() == count

    def test_user_signs_up(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'iloveyoko79',
            'full_name': 'John Lennon',
        }
        self._post(data, status=201, count=1)

    def test_user_signs_up_with_invalid(self):
        """The server should respond with an 404 error code when a user tries
           to sign up with invalid data"""
        data = {
            'username': 'imagine71',
            'password': 'iloveyoko79',
            'full_name': 'John Lennon',
        }
        self._post(data, status=400, count=0)


class AccountLoginTest(TestCase):
    def setUp(self):
        self.user = UserFactory.create(username='imagine71',
                                       email='john@beatles.uk',
                                       password='iloveyoko79')

    def _post(self, data, status=None, token=None):
        url = '/v1/account/login/'
        request = APIRequestFactory().post(url, data)
        response = AccountLogin.as_view()(request).render()
        content = None
        if len(response.content) > 0:
            content = response.content.decode("utf-8")
        if status is not None:
            assert response.status_code == status
        if token is not None:
            if token:
                assert 'auth_token' in content
            else:
                assert 'auth_token' not in content

    def test_successful_login(self):
        """The view should return a token to authenticate API calls"""
        self._post({'username': 'imagine71', 'password': 'iloveyoko79'},
                   status=200, token=True)

    def test_unsuccessful_login(self):
        """The view should return a token to authenticate API calls"""
        self._post({'username': 'imagine71', 'password': 'iloveyoko78'},
                   status=400)

    def test_login_with_unverified_email(self):
        """The view should return an error message if the User.verify_email_by
           is exceeded. An email with a verification link should be have been
           sent to the user."""
        self.user.verify_email_by = datetime.now()
        self.user.save()
        self._post({'username': 'imagine71', 'password': 'iloveyoko79'},
                   status=400, token=False)
        assert len(mail.outbox) == 1


class AccountVerifyTest(TestCase):
    def test_activate_account(self):
        user = UserFactory.create()

        token = cadastaTokenGenerator.make_token(user)

        user.last_login = datetime.now()
        user.save()

        request = APIRequestFactory().post('/v1/account/activate/', {
            'uid': encode_uid(user.pk),
            'token': token
        })
        response = AccountVerify.as_view()(request).render()
        assert response.status_code == 200

        user.refresh_from_db()
        assert user.email_verified
