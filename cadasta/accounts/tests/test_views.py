from datetime import datetime

from django.test import TestCase
from django.core import mail

from rest_framework.test import APIRequestFactory, force_authenticate
from djoser.utils import encode_uid

from ..models import User
from ..views import AccountUser, AccountRegister, AccountLogin, AccountVerify
from ..token import cadastaTokenGenerator

from .factories import UserFactory


class AccountUserTest(TestCase):
    def test_update_email_address(self):
        """Service should send a verification email when the user updates their
           email."""
        user = UserFactory.create(**{
            'username': 'imagine71',
            'email': 'john@beatles.uk'
        })

        data = {
            'email': 'boss@beatles.uk',
            'username': 'imagine71'
        }

        request = APIRequestFactory().put('/account/', data)
        force_authenticate(request, user=user)
        response = AccountUser.as_view()(request).render()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

    def test_keep_email_address(self):
        """Service should not send a verification email when the user does not
           their email."""
        user = UserFactory.create(**{
            'username': 'imagine71',
            'email': 'john@beatles.uk',
        })

        data = {
            'email': 'john@beatles.uk',
            'username': 'imagine71'
        }

        request = APIRequestFactory().put('/account/', data)
        force_authenticate(request, user=user)
        response = AccountUser.as_view()(request).render()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_update_with_existing_email(self):
        UserFactory.create(**{
            'email': 'boss@beatles.uk'
        })

        user = UserFactory.create(**{
            'email': 'john@beatles.uk',
        })

        data = {
            'email': 'boss@beatles.uk',
            'username': user.username
        }

        request = APIRequestFactory().put('/account/', data)
        force_authenticate(request, user=user)
        response = AccountUser.as_view()(request).render()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

        user.refresh_from_db()
        self.assertEqual(user.email, 'john@beatles.uk')

    def test_update_username(self):
        user = UserFactory.create(**{
            'username': 'imagine71'
        })

        data = {
            'email': user.email,
            'username': 'john'
        }

        request = APIRequestFactory().put('/account/', data)
        force_authenticate(request, user=user)
        response = AccountUser.as_view()(request).render()
        self.assertEqual(response.status_code, 200)

        user.refresh_from_db()
        self.assertEqual(user.username, 'john')

    def test_update_with_existing_username(self):
        UserFactory.create(**{
            'username': 'boss'
        })

        user = UserFactory.create(**{
            'username': 'john'
        })

        data = {
            'email': user.email,
            'username': 'boss'
        }

        request = APIRequestFactory().put('/account/', data)
        force_authenticate(request, user=user)
        response = AccountUser.as_view()(request).render()
        self.assertEqual(response.status_code, 400)

        user.refresh_from_db()
        self.assertEqual(user.username, 'john')


class AccountSignupTest(TestCase):
    def test_user_signs_up(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'iloveyoko79',
            'first_name': 'John',
            'last_name': 'Lennon',
        }

        request = APIRequestFactory().post('/account/register/', data)
        response = AccountRegister.as_view()(request).render()
        self.assertEqual(response.status_code, 201)
        # self.assertIn('auth_token', response.content.decode("utf-8"))
        
        self.assertEqual(User.objects.count(), 1)
        # user = User.objects.first()
        # self.assertTrue(user.is_authenticated())

    def test_user_signs_up_with_invalid(self):
        """The server should respond with an 404 error code when a user tries
           to sign up with invalid data"""
        data = {
            'username': 'imagine71',
            'password': 'iloveyoko79',
            'first_name': 'John',
            'last_name': 'Lennon',
        }

        request = APIRequestFactory().post('/account/register/', data)
        response = AccountRegister.as_view()(request).render()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), 0)


class AccountLoginTest(TestCase):
    def setUp(self):
        self.user = UserFactory.create(**{
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'iloveyoko79'
        })

    def test_successful_login(self):
        """The view should return a token to authenticate API calls"""
        request = APIRequestFactory().post('/account/login/', {
            'username': 'imagine71',
            'password': 'iloveyoko79'
        })
        response = AccountLogin.as_view()(request).render()
        self.assertEqual(response.status_code, 200)
        self.assertIn('auth_token', response.content.decode("utf-8"))

    def test_unsuccessful_login(self):
        """The view should return a token to authenticate API calls"""
        request = APIRequestFactory().post('/account/login/', {
            'username': 'imagine71',
            'password': 'iloveyoko78'
        })
        response = AccountLogin.as_view()(request).render()
        self.assertEqual(response.status_code, 400)

    def test_login_with_unverified_email(self):
        """The view should return an error message if the User.verify_email_by
           is exceeded. An email with a verification link should be have been
           sent to the user."""
        self.user.verify_email_by = datetime.now()
        self.user.save()

        request = APIRequestFactory().post('/account/login/', {
            'username': 'imagine71',
            'password': 'iloveyoko79'
        })
        response = AccountLogin.as_view()(request).render()
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('auth_token', response.content.decode("utf-8"))
        self.assertEqual(len(mail.outbox), 1)


class AccountVerifyTest(TestCase):
    def test_activate_account(self):
        user = UserFactory.create()

        token = cadastaTokenGenerator.make_token(user)

        user.last_login = datetime.now()
        user.save()

        request = APIRequestFactory().post('/account/activate/', {
            'uid': encode_uid(user.pk),
            'token': token
        })
        response = AccountVerify.as_view()(request).render()
        self.assertEqual(response.status_code, 200)

        user.refresh_from_db()
        self.assertTrue(user.email_verified)
