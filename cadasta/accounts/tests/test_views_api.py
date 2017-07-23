from django.core import mail
from django.test import TestCase

from allauth.account.models import EmailAddress

from skivvy import APITestCase

from core.tests.utils.cases import UserTestCase
from ..models import User, VerificationDevice
from ..views import api as api_views

from .factories import UserFactory


class AccountUserTest(APITestCase, UserTestCase, TestCase):
    view_class = api_views.AccountUser

    def setup_models(self):
        self.user = UserFactory.create(username='imagine71',
                                       email='john@beatles.uk',
                                       phone='+12345678990',
                                       email_verified=True,
                                       phone_verified=True)

    def test_update_profile(self):
        data = {'email': 'boss@beatles.uk',
                'phone': '+919327768250',
                'username': 'imagine71'}
        response = self.request(method='PUT', post_data=data, user=self.user)
        assert response.status_code == 200

        assert len(mail.outbox) == 2
        assert VerificationDevice.objects.count() == 1
        assert VerificationDevice.objects.filter(
            unverified_phone='+12345678990').exists() is False
        assert 'boss@beatles.uk' in mail.outbox[0].to
        assert 'john@beatles.uk' in mail.outbox[1].to

        self.user.refresh_from_db()
        assert self.user.email_verified is True
        assert self.user.phone_verified is True
        assert self.user.email == 'john@beatles.uk'
        assert self.user.phone == '+12345678990'

    def test_update_email_address(self):
        """Service should send a verification email when the user updates their
           email."""
        data = {'email': 'boss@beatles.uk', 'username': 'imagine71'}
        response = self.request(method='PUT', post_data=data, user=self.user)
        assert response.status_code == 200

        assert len(mail.outbox) == 2
        assert 'boss@beatles.uk' in mail.outbox[0].to
        assert 'john@beatles.uk' in mail.outbox[1].to

        self.user.refresh_from_db()
        assert self.user.email_verified is True

    def test_keep_email_address(self):
        """Service should not send a verification email when the user does not
           their email."""
        data = {'email': 'john@beatles.uk', 'username': 'imagine71'}
        response = self.request(method='PUT', post_data=data, user=self.user)
        assert response.status_code == 200
        assert len(mail.outbox) == 0

        self.user.refresh_from_db()
        assert self.user.email_verified is True

    def test_update_with_existing_email(self):
        UserFactory.create(email='boss@beatles.uk')
        data = {'email': 'boss@beatles.uk', 'username': self.user.username}
        response = self.request(method='PUT', post_data=data, user=self.user)
        assert response.status_code == 400

        self.user.refresh_from_db()
        assert self.user.email == 'john@beatles.uk'
        assert self.user.email_verified is True

    def test_update_username(self):
        data = {'email': self.user.email, 'username': 'john'}
        response = self.request(method='PUT', post_data=data, user=self.user)
        assert response.status_code == 200

        self.user.refresh_from_db()
        assert self.user.username == 'john'
        assert self.user.email_verified is True

    def test_update_with_existing_username(self):
        UserFactory.create(username='boss')
        data = {'email': self.user.email, 'username': 'boss'}
        response = self.request(method='PUT', post_data=data, user=self.user)
        assert response.status_code == 400

        self.user.refresh_from_db()
        assert self.user.username == 'imagine71'
        assert self.user.email_verified is True

    def test_update_phone_number(self):
        VerificationDevice.objects.create(
            user=self.user, unverified_phone=self.user.phone)

        data = {'phone': '+919327768250', 'username': 'imagine71'}
        response = self.request(method='PUT', post_data=data, user=self.user)
        assert response.status_code == 200
        assert VerificationDevice.objects.filter(
            unverified_phone='+12345678990').exists() is False

        self.user.refresh_from_db()
        assert self.user.phone == '+12345678990'
        assert self.user.phone_verified is True

    def test_keep_phone_number(self):
        data = {'phone': self.user.phone, 'username': 'imagine71'}
        response = self.request(method='PUT', post_data=data, user=self.user)
        assert response.status_code == 200

        self.user.refresh_from_db()
        assert self.user.phone == '+12345678990'
        assert self.user.phone_verified is True
        assert VerificationDevice.objects.filter(
            user=self.user, unverified_phone=self.user.phone).exists() is False

    def test_update_with_existing_phone(self):
        VerificationDevice.objects.create(
            user=self.user, unverified_phone=self.user.phone)

        user2 = UserFactory.create(phone='+919327768250')
        data = {'phone': user2.phone, 'username': 'imagine71'}
        response = self.request(method='PUT', post_data=data, user=self.user)
        assert response.status_code == 400

        self.user.refresh_from_db()
        assert self.user.phone == '+12345678990'
        assert self.user.phone_verified is True

    def test_update_add_phone_and_remove_email(self):
        user1 = UserFactory.create(username='sherlock',
                                   phone=None,
                                   email='sherlock.holmes@bbc.uk',
                                   email_verified=True)
        EmailAddress.objects.create(user=user1, email=user1.email)

        data = {
            'phone': '+919327768250',
            'email': '',
            'username': 'sherlock'
        }
        response = self.request(method='PUT', post_data=data, user=user1)
        assert response.status_code == 200

        user1.refresh_from_db()
        assert user1.phone == '+919327768250'
        assert user1.phone_verified is False
        assert VerificationDevice.objects.count() == 1
        assert user1.email is None
        assert user1.email_verified is False
        assert VerificationDevice.objects.filter(
            unverified_phone=user1.phone).exists() is True

    def test_update_add_email_and_remove_phone(self):
        user1 = UserFactory.create(username='sherlock',
                                   phone='+919327768250',
                                   email=None,
                                   phone_verified=True)
        VerificationDevice.objects.create(user=user1,
                                          unverified_phone=user1.phone)
        data = {
            'phone': '',
            'email': 'sherlock.holmes@bbc.uk',
            'username': 'sherlock'
        }
        response = self.request(method='PUT', post_data=data, user=user1)
        assert response.status_code == 200

        user1.refresh_from_db()
        assert user1.phone is None
        assert user1.phone_verified is False
        assert user1.email == 'sherlock.holmes@bbc.uk'
        assert user1.email_verified is False
        assert VerificationDevice.objects.count() == 0
        assert len(mail.outbox) == 1
        assert 'sherlock.holmes@bbc.uk' in mail.outbox[0].to


class AccountSignupTest(APITestCase, UserTestCase, TestCase):
    view_class = api_views.AccountRegister

    def test_user_signs_up(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'phone': '+919327768250',
            'password': 'iloveyoko79!',
            'full_name': 'John Lennon',
        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 201
        assert User.objects.count() == 1
        assert len(mail.outbox) == 1

    def test_user_signs_up_with_invalid(self):
        """The server should respond with an 404 error code when a user tries
           to sign up with invalid data"""
        data = {
            'username': 'imagine71',
            'password': 'iloveyoko79!',
            'full_name': 'John Lennon',
        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 400
        assert User.objects.count() == 0
        assert len(mail.outbox) == 0
        assert VerificationDevice.objects.count() == 0

    def test_user_signs_up_with_phone_only(self):
        data = {
            'username': 'sherlock',
            'email': '',
            'phone': '+919327768250',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 201
        assert User.objects.count() == 1
        assert VerificationDevice.objects.count() == 1

    def test_user_signs_up_with_email_only(self):
        data = {
            'username': 'sherlock',
            'email': 'sherlock.holmes@bbc.uk',
            'phone': '',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 201
        assert User.objects.count() == 1
        assert len(mail.outbox) == 1


class AccountLoginTest(APITestCase, UserTestCase, TestCase):
    view_class = api_views.AccountLogin

    def setup_models(self):
        self.user = UserFactory.create(username='imagine71',
                                       email='john@beatles.uk',
                                       phone='+919327768250',
                                       password='iloveyoko79!')

    def test_successful_login(self):
        """The view should return a token to authenticate API calls"""
        self.user.email_verified = True
        self.user.save()
        data = {'username': 'imagine71', 'password': 'iloveyoko79!'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 200
        assert 'auth_token' in response.content

    def test_unsuccessful_login(self):
        """The view should not return a token to authenticate API calls"""
        data = {'username': 'imagine71', 'password': 'iloveyoko78!'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 401

    def test_login_with_unverified_email(self):
        """The view should return an error message if the User email
        has not been verified."""
        data = {'username': 'imagine71', 'password': 'iloveyoko79!'}
        response = self.request(method='POST', post_data=data, user=self.user)
        assert response.status_code == 401
        assert 'auth_token' not in response.content

    def test_successful_login_with_email_both_unverified(self):
        data = {'username': 'john@beatles.uk', 'password': 'iloveyoko79!'}
        response = self.request(method='POST', post_data=data, user=self.user)
        assert response.status_code == 401
        assert 'auth_token' not in response.content

    def test_successful_login_with_phone_both_unverified(self):
        data = {'username': '+919327768250', 'password': 'iloveyoko79!'}
        response = self.request(method='POST', post_data=data, user=self.user)
        assert response.status_code == 401
        assert 'auth_token' not in response.content

    def test_successful_login_with_username_both_verified(self):
        self.user.email_verified = True
        self.user.phone_verified = True
        self.user.save()
        data = {'username': 'imagine71', 'password': 'iloveyoko79!'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 200
        assert 'auth_token' in response.content

    def test_successful_login_with_username_only_phone_verified(self):
        self.user.phone_verified = True
        self.user.save()

        data = {'username': 'imagine71', 'password': 'iloveyoko79!'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 200
        assert 'auth_token' in response.content

    def test_successful_login_with_verified_email(self):
        self.user.email_verified = True
        self.user.save()

        data = {'username': 'john@beatles.uk', 'password': 'iloveyoko79!'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 200
        assert 'auth_token' in response.content

    def test_successful_login_with_unverified_email_verified_phone(self):
        self.user.email_verified = False
        self.user.phone_verified = True
        self.user.save()
        data = {'username': 'john@beatles.uk', 'password': 'iloveyoko79!'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 401
        assert 'auth_token' not in response.content

    def test_successful_login_with_phone_verified(self):
        self.user.phone_verified = True
        self.user.save()

        data = {'username': '+919327768250', 'password': 'iloveyoko79!'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 200
        assert 'auth_token' in response.content

    def test_successful_login_with_unverified_phone_verified_email(self):
        self.user.email_verified = True
        self.user.phone_verified = False
        self.user.save()
        data = {'username': '+919327768250', 'password': 'iloveyoko79!'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 401
        assert 'auth_token' not in response.content


class AccountSetPasswordViewTest(APITestCase, UserTestCase, TestCase):
    view_class = api_views.SetPasswordView

    def setup_models(self):
        self.user = UserFactory.create(username='imagine71',
                                       email='john@beatles.uk',
                                       password='iloveyoko79!')

    def test_change_password(self):
        data = {
            'new_password': 'iloveyoko80!',
            're_new_password': 'iloveyoko80!',
            'current_password': 'iloveyoko79!',
        }
        response = self.request(method='POST', post_data=data, user=self.user)
        assert response.status_code == 204
        assert len(mail.outbox) == 1
        assert (mail.outbox[0].subject ==
                'Change of password at Cadasta Platform')
        assert 'john@beatles.uk' in mail.outbox[0].to
        self.user.refresh_from_db()
        assert self.user.check_password('iloveyoko80!') is True
