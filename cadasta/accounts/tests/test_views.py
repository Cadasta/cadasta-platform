from datetime import datetime

from django.test import TestCase
from django.core import mail
from django.contrib.auth.tokens import default_token_generator

from rest_framework.test import APIRequestFactory
from djoser.utils import encode_uid

from ..models import User
from ..views import AccountRegister, AccountLogin, AccountVerify


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
        self.assertEqual(User.objects.count(), 1)

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
        self.user = User(**{
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'first_name': 'John',
            'last_name': 'Lennon',
        })
        self.user.set_password('iloveyoko79')
        self.user.save()

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
        user = User(**{
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'first_name': 'John',
            'last_name': 'Lennon',
        })
        user.set_password('iloveyoko79')
        user.save()

        request = APIRequestFactory().post('/account/activate/', {
            'uid': encode_uid(user.pk),
            'token': default_token_generator.make_token(user)
        })
        response = AccountVerify.as_view()(request).render()
        self.assertEqual(response.status_code, 200)

        user.refresh_from_db()
        self.assertTrue(user.email_verified)
