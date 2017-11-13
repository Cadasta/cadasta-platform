from django.core import mail
from django.test import TestCase
from django.conf import settings
from unittest import mock

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
        VerificationDevice.objects.create(
            user=self.user, unverified_phone=self.user.phone, verified=True)
        EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True)

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
        # email confirmation sent to new email address
        assert 'boss@beatles.uk' in mail.outbox[0].to
        # email update mail sent to old email address
        assert 'john@beatles.uk' in mail.outbox[1].to
        # verification token message sent to new phone number
        # phone update message sent to old phone number

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
        # email update message will be sent to the existing phone number
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

        data = {'phone': '+919327768250', 'username': 'imagine71'}
        response = self.request(method='PUT', post_data=data, user=self.user)
        assert response.status_code == 200
        assert VerificationDevice.objects.filter(
            unverified_phone='+12345678990').exists() is False

        self.user.refresh_from_db()
        assert self.user.phone == '+12345678990'
        assert self.user.phone_verified is True
        assert len(mail.outbox) == 1
        # phone update mail sent to the existing email address
        assert self.user.email in mail.outbox[0].to
        # verification token message sent to the new phone number
        # phone update message sent to the old phone number

    def test_keep_phone_number(self):
        data = {'phone': self.user.phone, 'username': 'imagine71'}
        response = self.request(method='PUT', post_data=data, user=self.user)
        assert response.status_code == 200

        self.user.refresh_from_db()
        assert self.user.phone == '+12345678990'
        assert self.user.phone_verified is True

    def test_update_with_existing_phone(self):
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
        EmailAddress.objects.create(
            user=user1, email=user1.email, verified=True)

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
        assert user1.email is None
        assert user1.email_verified is False
        assert VerificationDevice.objects.filter(
            user=user1, unverified_phone=user1.phone).exists() is True
        assert len(mail.outbox) == 1
        # email removed mail sent to the removed email address
        assert 'sherlock.holmes@bbc.uk' in mail.outbox[0].to
        # verification token message sent to the phone number

    def test_update_add_email_and_remove_phone(self):
        user1 = UserFactory.create(username='sherlock',
                                   phone='+919327768250',
                                   email=None,
                                   phone_verified=True)
        VerificationDevice.objects.create(
            user=user1, unverified_phone=user1.phone, verified=True)
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
        assert VerificationDevice.objects.filter(
            user=user1, unverified_phone=user1.phone).exists() is False
        assert len(mail.outbox) == 1
        # confirmation mail sent to the email address
        assert 'sherlock.holmes@bbc.uk' in mail.outbox[0].to
        # phone removed message sent to the removed phone number


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
        VerificationDevice.objects.create(
            user=self.user, unverified_phone=self.user.phone)

    def test_successful_login(self):
        """The view should return a token to authenticate API calls"""
        self.user.email_verified = True
        self.user.save()
        data = {'username': 'imagine71', 'password': 'iloveyoko79!'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 200
        assert 'auth_token' in response.content

    def test_unsuccessful_login_incorrect_password(self):
        """The view should not return a token to authenticate API calls"""
        data = {'username': 'imagine71', 'password': 'iloveyoko78!'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 401

    def test_login_with_unverified_email(self):
        """The view should return an error message if the User email
        has not been verified."""
        data = {'username': 'john@beatles.uk', 'password': 'iloveyoko79!'}
        response = self.request(method='POST', post_data=data, user=self.user)
        assert response.status_code == 401
        assert 'auth_token' not in response.content
        assert (
            response.content['detail'] == "The email has not been verified.")

    def test_unsuccessful_login_with_username_both_unverified(self):
        data = {'username': 'imagine71', 'password': 'iloveyoko79!'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 401
        assert (
            response.content['detail'] == "User account is disabled.")

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

    def test_successful_login_with_verified_phone(self):
        self.user.phone_verified = True
        self.user.save()

        data = {'username': '+919327768250', 'password': 'iloveyoko79!'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 200
        assert 'auth_token' in response.content

    def test_unsuccessful_login_with_unverified_phone(self):
        self.user.email_verified = True
        self.user.phone_verified = False
        self.user.save()
        data = {'username': '+919327768250', 'password': 'iloveyoko79!'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 401
        assert 'auth_token' not in response.content
        assert (
            response.content['detail'] == "The phone has not been verified.")


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


class ConfirmPhoneViewTest(APITestCase, UserTestCase, TestCase):
    view_class = api_views.ConfirmPhoneView

    def setup_models(self):
        self.user = UserFactory.create(phone='+919327762850',
                                       password='221B@bakerstreet')
        self.device = VerificationDevice.objects.create(
            user=self.user, unverified_phone=self.user.phone)

    def test_successful_phone_verification(self):
        token = self.device.generate_challenge()
        data = {
            'phone': self.user.phone,
            'token': token
        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 200
        assert 'Phone successfully verified.' in response.content['detail']
        self.user.refresh_from_db()
        assert self.user.phone_verified is True

    def test_successful_new_phone_verification(self):
        self.device.unverified_phone = '+12345678990'
        self.device.save()
        token = self.device.generate_challenge()
        data = {
            'phone': '+12345678990',
            'token': token
        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 200
        assert 'Phone successfully verified.' in response.content['detail']
        self.user.refresh_from_db()
        assert self.user.phone == '+12345678990'

    def test_unsuccessful_phone_verification_invalid_token(self):
        token = self.device.generate_challenge()
        token = str(int(token) - 1)
        data = {
            'phone': self.user.phone,
            'token': token
        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 400
        assert (
            "Invalid Token. Enter a valid token." in response.content['token'])

    def test_unsuccessful_phone_verification_expired_token(self):
        now = 1497657600
        with mock.patch('time.time', return_value=now):
            token = self.device.generate_challenge()
            data = {
                'phone': self.user.phone,
                'token': token
            }
        with mock.patch('time.time',
                        return_value=(now + settings.TOTP_TOKEN_VALIDITY + 1)):
            response = self.request(method='POST', post_data=data)
            assert response.status_code == 400
            assert (
                "The token has expired." in response.content['token'])

    def test_unsuccessful_phone_verification_non_existent_phone(self):
        token = self.device.generate_challenge()
        data = {
            'phone': '+12345678990',
            'token': token
        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 400
        assert (
            "Phone is already verified or not linked to any user account."
            in response.content['token'])
