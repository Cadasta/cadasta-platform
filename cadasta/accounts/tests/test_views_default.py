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
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage


class RegisterTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.AccountRegister
    template = 'accounts/signup.html'

    def test_user_signs_up(self):
        data = {
            'username': 'sherlock',
            'email': 'sherlock.holmes@bbc.uk',
            'phone': '+919327768250',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert User.objects.count() == 1
        assert VerificationDevice.objects.count() == 1
        assert len(mail.outbox) == 1
        user = User.objects.first()
        assert user.check_password('221B@bakerstreet') is True
        assert '/account/verificationpage/' in response.location

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
            'full_name': 'Sherlock Holmes'
        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert User.objects.count() == 1
        assert VerificationDevice.objects.count() == 1
        assert len(mail.outbox) == 0
        assert 'account/verificationpage/' in response.location

    def test_signs_up_with_email_only(self):
        data = {
            'username': 'sherlock',
            'email': 'sherlock.holmes@bbc.uk',
            'phone': '',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert User.objects.count() == 1
        assert VerificationDevice.objects.count() == 0
        assert len(mail.outbox) == 1
        assert 'account/verificationpage/' in response.location


class ProfileTest(ViewTestCase, UserTestCase, TestCase):
    view_class = default.AccountProfile
    template = 'accounts/profile.html'

    def setup_template_context(self):
        return {
            'form': ProfileForm(instance=self.user),
            'emails_to_verify': False
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
            'full_name': 'John Lennon',
            'password': 'sgt-pepper',
            'language': 'en',
            'measurement': 'metric'
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
            'full_name': 'Bill Bloggs',
        }

        response = self.request(method='POST', user=user2, post_data=post_data)
        assert 'Failed to update profile information' in response.messages


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
        self.user.save()

        data = {'login': 'imagine71', 'password': 'iloveyoko79'}
        response = self.request(method='POST', post_data=data)
        assert response.status_code == 302
        assert 'account/inactive' in response.location
        assert len(mail.outbox) == 1
        self.user.refresh_from_db()
        assert self.user.is_active is False


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
        self.user = UserFactory.create(email='john@example.com')

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


class ConfirmPhoneViewTest(UserTestCase, TestCase):
    def setUp(self):
        super().setUp()

        self.user = UserFactory.create()
        EmailAddress.objects.create(
            user=self.user, email=self.user.email)
        self.factory = RequestFactory()

    def test_successful_phone_verification(self):
        self.device = self.user.verificationdevice_set.create(
            unverified_phone=self.user.phone)

        token = self.device.generate_challenge()
        data = {'token': token}

        request = self.factory.post('/account/verificationpage/', data=data)
        request.session = {"unverified_phone": self.user.phone}
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        response = default.ConfirmPhone.as_view()(request)

        self.user.refresh_from_db()

        assert response.status_code == 302
        assert self.user.phone_verified is True

    def test_unsuccessful_phone_verification(self):
        self.device = self.user.verificationdevice_set.create(
            unverified_phone=self.user.phone)

        token = self.device.generate_challenge()
        token = str(int(token) - 1)
        data = {'token': token}

        request = self.factory.post('/account/verificationpage/', data=data)
        request.session = {"unverified_phone": self.user.phone}
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        response = default.ConfirmPhone.as_view()(request)

        self.user.refresh_from_db()

        assert response.status_code == 200
        assert self.user.phone_verified is False

    def test_successful_phone_verification_new_phone(self):
        self.device = self.user.verificationdevice_set.create(
            unverified_phone='+919327768250')

        token = self.device.generate_challenge()
        data = {'token': token}

        request = self.factory.post('/account/verificationpage/', data=data)
        request.session = {"unverified_phone": '+919327768250'}
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        response = default.ConfirmPhone.as_view()(request)

        self.user.refresh_from_db()

        assert response.status_code == 302
        assert self.user.phone == '+919327768250'
        assert self.user.phone_verified is True
