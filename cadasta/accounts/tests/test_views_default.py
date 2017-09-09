import datetime
from django.core.urlresolvers import reverse_lazy
from django.test import TestCase
from django.core import mail
from skivvy import ViewTestCase

from accounts.tests.factories import UserFactory
from core.tests.utils.cases import UserTestCase

from allauth.account.models import EmailConfirmation, EmailAddress
from allauth.account.forms import ChangePasswordForm

from accounts.models import User, VerificationDevice
from ..views import default
from ..forms import ProfileForm
from ..messages import account_inactive, unverified_identifier


class RegisterTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.AccountRegister
    template = 'accounts/signup.html'

    def test_user_signs_up(self):
        data = {
            'username': 'sherlock',
            'email': 'sherlock.holmes@bbc.uk',
            'phone': '+919327768250',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes',
            'language': 'fr'

        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert User.objects.count() == 1
        assert VerificationDevice.objects.count() == 1
        assert len(mail.outbox) == 1
        user = User.objects.first()
        assert user.check_password('221B@bakerstreet') is True
        assert '/account/accountverification/' in response.location

    def test_signs_up_with_invalid(self):
        data = {
            'username': 'sherlock',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 200
        assert User.objects.count() == 0
        assert VerificationDevice.objects.count() == 0
        assert len(mail.outbox) == 0

    def test_signs_up_with_phone_only(self):
        data = {
            'username': 'sherlock',
            'email': '',
            'phone': '+919327768250',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes',
            'language': 'fr'
        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert User.objects.count() == 1
        assert VerificationDevice.objects.count() == 1
        assert len(mail.outbox) == 0
        assert 'account/accountverification/' in response.location

    def test_signs_up_with_email_only(self):
        data = {
            'username': 'sherlock',
            'email': 'sherlock.holmes@bbc.uk',
            'phone': '',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes',
            'language': 'fr'
        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert User.objects.count() == 1
        assert VerificationDevice.objects.count() == 0
        assert len(mail.outbox) == 1
        assert 'account/accountverification/' in response.location


class ProfileTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.AccountProfile
    template = 'accounts/profile.html'

    def setup_template_context(self):
        return {
            'form': ProfileForm(instance=self.user),
            'emails_to_verify': False,
            'phones_to_verify': False
        }

    def test_get_profile(self):
        self.user = UserFactory.create()
        response = self.request(user=self.user)

        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_profile_with_unverified_email(self):
        self.user = UserFactory.create()
        EmailAddress.objects.create(
            user=self.user,
            email='miles2@davis.co',
            verified=False,
            primary=True
        )
        response = self.request(user=self.user)

        assert response.status_code == 200
        assert response.content == self.render_content(emails_to_verify=True)

    def test_get_profile_with_verified_email(self):
        self.user = UserFactory.create()
        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            verified=True,
            primary=True
        )
        response = self.request(user=self.user)

        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_update_profile(self):
        user = UserFactory.create(username='John',
                                  password='sgt-pepper')
        post_data = {
            'username': 'John',
            'email': user.email,
            'phone': user.phone,
            'language': 'en',
            'measurement': 'metric',
            'full_name': 'John Lennon',
            'password': 'sgt-pepper',
        }
        response = self.request(method='POST', post_data=post_data, user=user)
        response.status_code == 200

        user.refresh_from_db()
        assert user.full_name == 'John Lennon'

    def test_get_profile_when_no_user_is_signed_in(self):
        response = self.request()
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_update_profile_when_no_user_is_signed_in(self):
        response = self.request(method='POST', post_data={})
        assert response.status_code == 302
        assert '/account/login/' in response.location

    def test_update_profile_duplicate_email(self):
        user1 = UserFactory.create(username='John',
                                   full_name='John Lennon')
        user2 = UserFactory.create(username='Bill')
        post_data = {
            'username': 'Bill',
            'email': user1.email,
            'phone': user2.phone,
            'language': 'en',
            'measurement': 'metric',
            'full_name': 'Bill Bloggs',
        }

        response = self.request(method='POST', user=user2, post_data=post_data)
        assert 'Failed to update profile information' in response.messages

    def test_get_profile_with_verified_phone(self):
        self.user = UserFactory.create(phone_verified=True,
                                       email_verified=True)
        response = self.request(user=self.user)

        assert response.status_code == 200
        assert response.content == self.expected_content

    def test_get_profile_with_unverified_phone(self):
        self.user = UserFactory.create()
        VerificationDevice.objects.create(
            user=self.user, unverified_phone=self.user.phone)

        response = self.request(user=self.user)

        assert response.status_code == 200
        assert response.content == self.render_content(phones_to_verify=True)

    def test_update_profile_with_duplicate_phone(self):
        user1 = UserFactory.create(phone='+919327768250')
        user2 = UserFactory.create(password='221B@bakerstreet')
        post_data = {
            'username': user2.username,
            'email': user2.email,
            'phone': user1.phone,
            'language': 'en',
            'measurement': 'metric',
            'full_name': 'Sherlock Holmes',
            'password': '221B@bakerstreet'
        }
        response = self.request(method='POST', post_data=post_data, user=user2)

        assert response.status_code == 200
        assert 'Failed to update profile information' in response.messages

    def test_update_profile_with_phone(self):
        user = UserFactory.create(password='221B@bakerstreet')
        post_data = {
            'username': user.username,
            'email': user.email,
            'phone': '+919327768250',
            'language': 'en',
            'measurement': 'metric',
            'full_name': 'Sherlock Holmes',
            'password': '221B@bakerstreet'
        }
        response = self.request(method='POST', post_data=post_data, user=user)
        assert response.status_code == 302
        assert '/account/accountverification/' in response.location

    def test_update_keep_phone(self):
        user = UserFactory.create(
            password='221B@bakerstreet')
        post_data = {
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'language': 'en',
            'measurement': 'metric',
            'full_name': 'Sherlock Holmes',
            'password': '221B@bakerstreet'
        }
        response = self.request(method='POST', post_data=post_data, user=user)
        assert response.status_code == 302
        assert '/account/profile' in response.location


class PasswordChangeTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PasswordChangeView
    success_url = reverse_lazy('account:profile')

    def setup_template_context(self):
        return {
            'form': ChangePasswordForm(instance=self.user)
        }

    def test_password_change(self):
        self.user = UserFactory.create(password='Noonewillguess!')
        data = {'oldpassword': 'Noonewillguess!',
                'password': 'Someonemightguess?'}
        response = self.request(method='POST', post_data=data, user=self.user)

        assert response.status_code == 302
        assert response.location == self.expected_success_url
        assert self.user.check_password('Someonemightguess?') is True


class LoginTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.AccountLogin

    def setup_models(self):
        self.user = UserFactory.create(username='imagine71',
                                       email='john@beatles.uk',
                                       phone='+919327768250',
                                       password='iloveyoko79')

    def test_successful_login(self):
        self.user.email_verified = True
        self.user.save()

        data = {'login': 'imagine71', 'password': 'iloveyoko79'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert 'dashboard' in response.location

    def test_successful_login_with_unverified_user(self):
        self.user.email_verified = False
        self.user.phone_verified = False
        self.user.save()

        data = {'login': 'imagine71', 'password': 'iloveyoko79'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert '/account/resendtokenpage/' in response.location
        assert account_inactive in response.messages

        self.user.refresh_from_db()
        assert self.user.is_active is False

    def test_unsuccessful_login_with_email(self):

        data = {'login': 'john@beatles.uk', 'password': 'iloveyoko79'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert '/account/resendtokenpage/' in response.location
        assert unverified_identifier in response.messages

    def test_unsuccessful_login_with_phone(self):
        data = {'login': '+919327768250', 'password': 'iloveyoko79'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert '/account/resendtokenpage/' in response.location
        assert unverified_identifier in response.messages

    def test_successful_login_with_username_both_verified(self):
        self.user.email_verified = True
        self.user.phone_verified = True
        self.user.save()

        data = {'login': 'imagine71', 'password': 'iloveyoko79'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert 'dashboard' in response.location

    def test_successful_login_with_username_only_phone_verified(self):
        self.user.phone_verified = True
        self.user.save()

        data = {'login': 'imagine71', 'password': 'iloveyoko79'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert 'dashboard' in response.location

    def test_successful_login_with_email(self):
        self.user.email_verified = True
        self.user.save()

        data = {'login': 'john@beatles.uk', 'password': 'iloveyoko79'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert 'dashboard' in response.location

    def test_successful_login_with_phone(self):
        self.user.phone_verified = True
        self.user.save()

        data = {'login': '+919327768250', 'password': 'iloveyoko79'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert 'dashboard' in response.location


class ConfirmEmailTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.ConfirmEmail
    url_kwargs = {'key': '123'}

    def setup_models(self):
        self.user = UserFactory.create(email='john@example.com')
        self.email_address = EmailAddress.objects.create(
            user=self.user,
            email='john@example.com',
            verified=False,
            primary=True
        )
        self.confirmation = EmailConfirmation.objects.create(
            email_address=self.email_address,
            sent=datetime.datetime.now(),
            key='123'
        )

    def test_activate(self):
        response = self.request(user=self.user)
        assert response.status_code == 302
        assert 'dashboard' in response.location

        self.user.refresh_from_db()
        assert self.user.email_verified is True
        assert self.user.is_active is True

        self.email_address.refresh_from_db()
        assert self.email_address.verified is True

    def test_activate_changed_email(self):
        self.email_address.email = 'john2@example.com'
        self.email_address.save()

        EmailConfirmation.objects.create(
            email_address=self.email_address,
            sent=datetime.datetime.now(),
            key='456'
        )
        response = self.request(user=self.user, url_kwargs={'key': '456'})
        assert response.status_code == 302
        assert 'dashboard' in response.location

        self.user.refresh_from_db()
        assert self.user.email_verified is True
        assert self.user.is_active is True
        assert self.user.email == 'john2@example.com'

        self.email_address.refresh_from_db()
        assert self.email_address.verified is True

    def test_activate_with_invalid_token(self):
        response = self.request(user=self.user, url_kwargs={'key': 'abc'})
        assert response.status_code == 200

        self.user.refresh_from_db()
        assert self.user.email_verified is False
        assert self.user.is_active is True

        self.email_address.refresh_from_db()
        assert self.email_address.verified is False


class PasswordResetViewTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PasswordResetView

    def setup_models(self):
        self.user = UserFactory.create(email='john@example.com',
                                       phone='+919327762850')
        self.user.verificationdevice_set.create(
            unverified_phone=self.user.phone,
            label='password_reset')

    def test_mail_sent(self):
        data = {'email': 'john@example.com'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert len(mail.outbox) == 1

    def test_mail_not_sent(self):
        data = {'email': 'abcd@example.com'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert len(mail.outbox) == 0

    def test_text_msg_sent(self):
        data = {'phone': '+919327768250'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302

    def test_text_msg_not_sent(self):
        data = {'phone': '+12345678990'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302


class PasswordResetDoneViewTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PasswordResetDoneView

    def setup_models(self):
        self.user = UserFactory.create(phone='+919327768250',
                                       email='sherlock.holmes@bbc.uk',
                                       phone_verified=True,
                                       email_verified=True)
        self.device = VerificationDevice.objects.create(
            user=self.user,
            unverified_phone=self.user.phone,
            label='password_reset')

    def test_successful_token_verification(self):
        token = self.device.generate_challenge()
        data = {'token': token}
        response = self.request(
            method='POST',
            post_data=data,
            session_data={"phone": self.user.phone})

        assert response.status_code == 302
        assert '/account/password/reset/phone/' in response.location
        assert VerificationDevice.objects.filter(
            user=self.user, label='password_reset').exists() is False

    def test_without_phone(self):
        token = self.device.generate_challenge()
        data = {'token': token}
        response = self.request(
            method='POST',
            post_data=data,
            session_data={})
        assert response.status_code == 200

    def test_with_unknown_phone(self):
        token = self.device.generate_challenge()
        data = {'token': token}
        response = self.request(
            method='POST',
            post_data=data,
            session_data={"phone": '+12345678990'})

        assert response.status_code == 200


class PasswordResetFromPhoneViewTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.PasswordResetFromPhoneView

    def setup_models(self):
        self.user = UserFactory.create(password='221B@bakerstreet')

    def test_password_successfully_set(self):
        data = {'password': 'i@msher!0cked'}
        response = self.request(
            method='POST',
            post_data=data,
            session_data={"password_reset_id": self.user.id})
        assert response.status_code == 302
        self.user.refresh_from_db()
        assert self.user.check_password('i@msher!0cked') is True
        assert len(mail.outbox) == 1
        assert self.user.email in mail.outbox[0].to

    def test_password_set_without_password_reset_id(self):
        data = {'password': 'i@msher!0cked'}
        response = self.request(
            method='POST',
            post_data=data,
            session_data={})
        assert response.status_code == 200
        self.user.refresh_from_db()
        assert self.user.check_password('i@msher!0cked') is False


class ConfirmPhoneViewTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.ConfirmPhone

    def setup_models(self):
        self.user = UserFactory.create(phone='+919327768250')
        EmailAddress.objects.create(user=self.user, email=self.user.email)

    def test_successful_phone_verification(self):
        device = VerificationDevice.objects.create(
            user=self.user, unverified_phone=self.user.phone)
        token = device.generate_challenge()

        data = {'token': token}
        response = self.request(
            method='POST',
            post_data=data,
            session_data={'phone_verify_id': self.user.id})
        assert response.status_code == 302

        self.user.refresh_from_db()
        assert self.user.phone_verified is True
        assert VerificationDevice.objects.filter(
            user=self.user,
            unverified_phone=self.user.phone,
            label='phone_verify').exists() is False

    def test_successful_new_phone_verification(self):
        device = VerificationDevice.objects.create(
            user=self.user, unverified_phone='+12345678990')
        token = device.generate_challenge()

        data = {'token': token}
        response = self.request(
            method='POST',
            post_data=data,
            session_data={'phone_verify_id': self.user.id})
        assert response.status_code == 302

        self.user.refresh_from_db()
        assert self.user.phone == '+12345678990'
        assert self.user.phone_verified is True
        assert VerificationDevice.objects.filter(
            user=self.user,
            unverified_phone='+12345678990',
            label='phone_verify').exists() is False

    def test_phone_verification_without_phone_verify_id(self):
        device = VerificationDevice.objects.create(
            user=self.user, unverified_phone=self.user.phone)
        token = device.generate_challenge()

        data = {'token': token}
        response = self.request(
            method='POST',
            post_data=data,
            session_data={})
        assert response.status_code == 200


class ResendTokenViewTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.ResendTokenView

    def setup_models(self):
        self.user = UserFactory.create(username='sherlock',
                                       email='sherlock.holmes@bbc.uk',
                                       phone='+919327768250',
                                       password='221B@bakerstreet',
                                       )

    def test_phone_send_token(self):
        VerificationDevice.objects.create(user=self.user,
                                          unverified_phone=self.user.phone)
        data = {
            'phone': '+919327768250',
        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert '/account/accountverification/' in response.location

    def test_email_send_link(self):
        EmailAddress.objects.create(user=self.user, email=self.user.email)
        data = {
            'email': 'sherlock.holmes@bbc.uk',
        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert '/account/accountverification/' in response.location
        assert len(mail.outbox) == 1
        assert 'sherlock.holmes@bbc.uk' in mail.outbox[0].to

    def test_updated_email_send_link(self):
        EmailAddress.objects.create(user=self.user, email='john.watson@bbc.uk')
        data = {
            'email': 'john.watson@bbc.uk',
        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert '/account/accountverification/' in response.location
        assert len(mail.outbox) == 1
        assert 'john.watson@bbc.uk' in mail.outbox[0].to

    def test_already_verified_email(self):
        EmailAddress.objects.create(
            user=self.user, verified=True, email=self.user.email)
        data = {
            'email': 'john.watson@bbc.uk',
        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert '/account/accountverification/' in response.location
        assert len(mail.outbox) == 0

    def test_already_verified_phone(self):
        data = {
            'phone': '+919327768250',
        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert '/account/accountverification/' in response.location
        assert VerificationDevice.objects.filter(
            user=self.user,
            unverified_phone=self.user.phone,
            label='phone_verify').exists() is False
