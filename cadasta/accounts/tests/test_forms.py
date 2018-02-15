import random
import pytest
from unittest.mock import Mock

from core.tests.utils.cases import UserTestCase, FileStorageTestCase
from core.messages import SANITIZE_ERROR
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.http import HttpRequest
from django.db import IntegrityError

from allauth.account.models import EmailAddress
from django.conf import settings

from django.test import TestCase
from django.utils.translation import gettext as _
from core.tests.utils.files import make_dirs  # noqa
from unittest import mock

from .. import forms
from ..models import User, VerificationDevice
from ..messages import phone_format
from .factories import UserFactory


class RegisterFormTest(UserTestCase, TestCase):

    def test_valid_data(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'iloveyoko79!',
            'full_name': 'John Lennon',
            'language': 'fr',
        }
        form = forms.RegisterForm(data)
        form.save()

        assert form.is_valid() is True
        assert User.objects.count() == 1

        user = User.objects.first()
        assert user.check_password('iloveyoko79!') is True

    def test_case_insensitive_username(self):
        chars = ['', 'İ', 'É', 'Ø', 'œ', 'ß', 'ss', 'Ξ', 'ф', '大家好']
        usernames = ['UsEr%s' % c for c in chars]
        users = [
            UserFactory.create(username=username) for username in usernames]
        for user in users:
            data = {
                'username': user.username.lower(),
                'email': '%s@beatles.uk' % user.username,
                'password': 'iloveyoko79!',
                'full_name': 'John Lennon',
            }
            form = forms.RegisterForm(data)
            assert form.is_valid() is False
            assert (_("A user with that username already exists") in
                    form.errors.get('username'))

        user = UserFactory.create(username='JohNlEnNoN')
        data = {
            'username': 'johnLennon',
            'email': 'john@beatles.uk',
            'password': 'iloveyoko79!',
            'full_name': 'John Lennon',
        }
        form = forms.RegisterForm(data)
        assert form.is_valid() is False
        assert (_("A user with that username already exists") in
                form.errors.get('username'))

    def test_password_contains_username(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'Letsimagine71things?',
            'full_name': 'John Lennon',
        }
        form = forms.RegisterForm(data)

        assert form.is_valid() is False
        assert (_("The password is too similar to the username.") in
                form.errors.get('password'))
        assert User.objects.count() == 0

    def test_password_contains_username_case_insensitive(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'LetsIMAGINE71things?',
            'full_name': 'John Lennon',
        }
        form = forms.RegisterForm(data)

        assert form.is_valid() is False
        assert (_("The password is too similar to the username.") in
                form.errors.get('password'))
        assert User.objects.count() == 0

    def test_password_contains_blank_username(self):
        data = {
            'username': '',
            'email': 'john@beatles.uk',
            'password': 'Letsimagine71things?',
            'full_name': 'John Lennon',
        }
        form = forms.RegisterForm(data)

        assert form.is_valid() is False
        assert (form.errors.get('password') is None)
        assert User.objects.count() == 0

    def test_password_contains_email(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'IsJOHNreallythebest34?',
            'full_name': 'John Lennon',
        }
        form = forms.RegisterForm(data)

        assert form.is_valid() is False
        assert (_("Passwords cannot contain your email.") in
                form.errors.get('password'))
        assert User.objects.count() == 0

    def test_password_contains_blank_email(self):
        data = {
            'username': 'imagine71',
            'email': '',
            'password': 'Isjohnreallythebest34?',
            'full_name': 'John Lennon',
        }
        form = forms.RegisterForm(data)

        assert form.is_valid() is False
        assert (form.errors.get('password') is None)
        assert User.objects.count() == 0

    def test_password_contains_less_than_min_characters(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': '<3yoko',
            'full_name': 'John Lennon',
        }
        form = forms.RegisterForm(data)

        assert form.is_valid() is False
        assert (_("This password is too short."
                  " It must contain at least 10 characters.") in
                form.errors.get('password'))
        assert User.objects.count() == 0

    def test_password_does_not_meet_unique_character_requirements(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'yokoisjustthebest',
            'full_name': 'John Lennon',
        }
        form = forms.RegisterForm(data)

        assert form.is_valid() is False
        assert (_("Passwords must contain at least 3"
                  " of the following 4 character types:\n"
                  "lowercase characters, uppercase characters,"
                  " special characters, and/or numerical character.\n"
                  ))
        assert User.objects.count() == 0

        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'YOKOISJUSTTHEBEST',
            'full_name': 'John Lennon',
        }
        form = forms.RegisterForm(data)

        assert form.is_valid() is False
        assert (_("Passwords must contain at least 3"
                  " of the following 4 character types:\n"
                  "lowercase characters, uppercase characters,"
                  " special characters, and/or numerical character.\n"
                  ))
        assert User.objects.count() == 0

    def test_signup_with_existing_email(self):
        UserFactory.create(email='john@beatles.uk')
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'iloveyoko79',
            'full_name': 'John Lennon',
        }
        form = forms.RegisterForm(data)

        assert form.is_valid() is False
        assert (_("User with this Email address already exists.")
                in form.errors.get('email'))
        assert User.objects.count() == 1

    def test_signup_with_restricted_username(self):
        invalid_usernames = ('add', 'ADD', 'Add', 'new', 'NEW', 'New')
        data = {
            'username': random.choice(invalid_usernames),
            'email': 'john@beatles.uk',
            'password': 'Iloveyoko68!',
            'full_name': 'John Lennon'
        }
        form = forms.RegisterForm(data)

        assert form.is_valid() is False
        assert (_("Username cannot be “add” or “new”.")
                in form.errors.get('username'))
        assert User.objects.count() == 0

    def test_sanitize(self):
        data = {
            'username': '😛😛😛😛',
            'email': 'john@beatles.uk',
            'password': 'Iloveyoko68!',
            'full_name': 'John Lennon'
        }
        form = forms.RegisterForm(data)

        assert form.is_valid() is False
        assert SANITIZE_ERROR in form.errors.get('username')
        assert User.objects.count() == 0

    def test_password_contains_blank_phone(self):
        data = {
            'username': 'sherlock',
            'email': 'sherlock.holmes@bbc.uk',
            'phone': '',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes',
            'language': 'fr'
        }
        form = forms.RegisterForm(data)
        assert form.is_valid() is True
        assert (form.errors.get('password') is None)

    def test_password_contains_phone(self):
        data = {
            'username': 'sherlock',
            'phone': '+919327768250',
            'password': 'holmes@9327768250',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.RegisterForm(data)
        assert form.is_valid() is False
        assert (_("Passwords cannot contain your phone.")
                in form.errors.get('password'))
        assert User.objects.count() == 0

    def test_signup_with_existing_phone(self):
        UserFactory.create(phone='+919327768250')

        data = {
            'username': 'sherlock',
            'phone': '+919327768250',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.RegisterForm(data)
        assert form.is_valid() is False
        assert (_("User with this Phone number already exists.")
                in form.errors.get('phone'))
        assert User.objects.count() == 1

    def test_signup_with_invalid_phone(self):
        data = {
            'username': 'sherlock',
            'phone': 'Invalid Number',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.RegisterForm(data)
        assert form.is_valid() is False
        assert phone_format in form.errors.get('phone')

        assert User.objects.count() == 0

        data = {
            'username': 'sherlock',
            'phone': '+91-9067439937',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.RegisterForm(data)
        assert form.is_valid() is False
        assert phone_format in form.errors.get('phone')

        assert User.objects.count() == 0

        data = {
            'username': 'sherlock',
            'phone': '9327768250',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.RegisterForm(data)
        assert form.is_valid() is False
        assert phone_format in form.errors.get('phone')

        assert User.objects.count() == 0

        data = {
            'username': 'sherlock',
            'phone': ' +91 9327768250 ',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.RegisterForm(data)
        assert form.is_valid() is False
        assert phone_format in form.errors.get('phone')

        assert User.objects.count() == 0

        data = {
            'username': 'sherlock',
            'phone': '+919327768250137284721',
            'password': '221B@bakertstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.RegisterForm(data)
        assert form.is_valid() is False
        assert phone_format in form.errors.get('phone')

        assert User.objects.count() == 0

        data = {
            'username': 'sherlock',
            'phone': '+1234',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.RegisterForm(data)
        assert form.is_valid() is False
        assert phone_format in form.errors.get('phone')

        assert User.objects.count() == 0

        data = {
            'username': 'sherlock',
            'phone': '+8018225332',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.RegisterForm(data)
        assert form.is_valid() is False
        assert (_("Please enter a valid country code.")
                in form.errors.get('phone'))

    def test_signup_with_blank_phone_and_email(self):
        data = {
            'username': 'sherlock',
            'email': '',
            'phone': '',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.RegisterForm(data)
        assert form.is_valid() is False
        assert (_("You cannot leave both phone and email empty."
                  " Signup with either phone or email or both.")
                in form.errors.get('__all__'))

        assert User.objects.count() == 0

    def test_signup_with_phone_only(self):
        data = {
            'username': 'sherlock',
            'phone': '+919327768250',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes',
            'language': 'fr'
        }
        form = forms.RegisterForm(data)
        form.save()
        assert form.is_valid() is True
        assert User.objects.count() == 1

        user = User.objects.first()
        assert user.email is None
        assert user.check_password('221B@bakerstreet') is True

    def test_case_insensitive_email_check(self):
        UserFactory.create(email='sherlock.holmes@bbc.uk')
        data = {
            'username': 'sherlock',
            'email': 'SHERLOCK.HOLMES@BBC.UK',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.RegisterForm(data)
        assert form.is_valid() is False
        assert (_("User with this Email address already exists.")
                in form.errors.get('email'))

        assert User.objects.count() == 1

    def test_signup_with_existing_email_in_EmailAddress(self):
        user = UserFactory.create()
        EmailAddress.objects.create(email='sherlock.holmes@bbc.uk', user=user)
        data = {
            'username': 'sherlock',
            'email': 'sherlock.holmes@bbc.uk',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.RegisterForm(data)
        assert form.is_valid() is False
        assert (_("User with this Email address already exists.")
                in form.errors.get('email'))

    def test_signup_with_existing_phone_in_VerificationDevice(self):
        user = UserFactory.create()
        VerificationDevice.objects.create(unverified_phone='+919327768250',
                                          user=user)
        data = {
            'username': 'sherlock',
            'phone': '+919327768250',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.RegisterForm(data)
        assert form.is_valid() is False
        assert (_("User with this Phone number already exists.")
                in form.errors.get('phone'))


@pytest.mark.usefixtures('make_dirs')
class ProfileFormTest(UserTestCase, FileStorageTestCase, TestCase):

    def test_init_with_email(self):
        user = UserFactory.build(email='john@beatles.uk',
                                 email_verified=True,
                                 phone=None,
                                 phone_verified=False)
        form = forms.ProfileForm({}, request=Mock(), instance=user)
        assert form.fields['email'].required is True
        assert form.fields['phone'].required is False

    def test_init_with_phone(self):
        user = UserFactory.build(email=None,
                                 email_verified=False,
                                 phone='+4915712111111111',
                                 phone_verified=True)
        form = forms.ProfileForm({}, request=Mock(), instance=user)
        assert form.fields['phone'].required is True
        assert form.fields['email'].required is False

    def test_update_user(self):
        test_file_path = '/accounts/tests/files/avatar.png'
        with self.get_file(test_file_path, 'rb') as test_file:
            image = self.storage.save('avatars/avatar.png', test_file.read())

        user = UserFactory.create(username='imagine71',
                                  email='john@beatles.uk',
                                  email_verified=True,
                                  password='sgt-pepper',
                                  language='en',
                                  measurement='metric',
                                  phone=None,
                                  phone_verified=False)
        data = {
            'username': 'imagine71',
            'email': 'john2@beatles.uk',
            'full_name': 'John Lennon',
            'password': 'sgt-pepper',
            'language': 'en',
            'measurement': 'imperial',
            'avatar': image,
        }

        request = HttpRequest()
        setattr(request, 'session', 'session')
        self.messages = FallbackStorage(request)
        setattr(request, '_messages', self.messages)
        request.META['SERVER_NAME'] = 'testserver'
        request.META['SERVER_PORT'] = '80'

        form = forms.ProfileForm(data, request=request, instance=user)
        form.save()
        user.refresh_from_db()

        assert user.full_name == 'John Lennon'
        assert user.email == 'john@beatles.uk'
        assert user.language == 'en'
        assert user.measurement == 'imperial'
        assert user.email_verified is True
        assert len(mail.outbox) == 2
        assert 'john2@beatles.uk' in mail.outbox[0].to
        assert 'john@beatles.uk' in mail.outbox[1].to

    def test_display_name(self):
        user = UserFactory.create(username='imagine71',
                                  email='john@beatles.uk',
                                  password='sgt-pepper',
                                  measurement='metric',
                                  phone='+919327768250')
        assert user.get_display_name() == 'imagine71'

        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'phone': '+919327768250',
            'full_name': 'John Lennon',
            'password': 'sgt-pepper',
            'language': 'en',
            'measurement': 'metric'
        }
        form = forms.ProfileForm(data, instance=user)
        form.save()

        user.refresh_from_db()
        assert user.get_display_name() == 'John Lennon'

    def test_update_user_with_existing_username(self):
        UserFactory.create(username='existing')
        user = UserFactory.create(username='imagine71',
                                  email='john@beatles.uk',
                                  phone='+919327768250',
                                  password='sgt-pepper')
        data = {
            'username': 'existing',
            'email': 'john@beatles.uk',
            'phone': '+919327768250',
            'full_name': 'John Lennon',
            'password': 'sgt-pepper',
            'language': 'en'
        }
        form = forms.ProfileForm(data, instance=user)
        assert form.is_valid() is False

    def test_case_insensitive_username(self):
        existing_user = UserFactory.create(username='TestUser')
        chars = ['', 'İ', 'É', 'Ø', 'œ', 'ß', 'ss', 'Ξ', 'ф', '大家好']
        usernames = ['UsEr%s' % c for c in chars]
        users = [
            UserFactory.create(username=username) for username in usernames]
        for user in users:
            data = {
                'username': user.username.lower(),
                'email': '%s@beatles.uk' % user.username,
                'phone': '+919327768250',
                'full_name': 'John Lennon',
                'language': 'en'
            }
            form = forms.ProfileForm(data, instance=existing_user)
            assert form.is_valid() is False
            assert (_("A user with that username already exists") in
                    form.errors.get('username'))
        existing_user.refresh_from_db()
        assert existing_user.username == 'TestUser'

        user = UserFactory.create(username='JohNlEnNoN',
                                  email='john@beatles.uk',
                                  password='sgt-pepper',
                                  measurement='metric',
                                  phone='+919327768250')
        data = {
            'username': 'johnLennon',
            'email': 'john@beatles.uk',
            'phone': '+919327768250',
            'full_name': 'John Lennon',
            'password': 'sgt-pepper',
            'language': 'en',
            'measurement': 'metric'
        }
        form = forms.ProfileForm(data, instance=user)
        assert form.is_valid() is True
        form.save()

        user.refresh_from_db()
        assert user.username == 'johnLennon'

    def test_update_user_with_existing_email(self):
        UserFactory.create(email='existing@example.com')
        user = UserFactory.create(username='imagine71',
                                  email='john@beatles.uk',
                                  phone=None,
                                  password='sgt-pepper')
        data = {
            'username': 'imagine71',
            'email': 'existing@example.com',
            'full_name': 'John Lennon',
            'password': 'sgt-pepper',
            'language': 'en'
        }
        form = forms.ProfileForm(data, instance=user)
        assert form.is_valid() is False

    def test_update_user_with_restricted_username(self):
        user = UserFactory.create(username='imagine71',
                                  email='john@beatles.uk')
        invalid_usernames = ('add', 'ADD', 'Add', 'new', 'NEW', 'New')
        data = {
            'username': random.choice(invalid_usernames),
            'email': 'john@beatles.uk',
            'phone': '+919327768250',
            'full_name': 'John Lennon',
            'password': 'sgt-pepper',
            'language': 'en'
        }
        form = forms.ProfileForm(data, instance=user)
        assert form.is_valid() is False

    def test_signup_with_released_email(self):
        user = UserFactory.create(username='user1',
                                  email='user1@example.com',
                                  phone=None,
                                  email_verified=True,
                                  password='sgt-pepper',
                                  measurement='metric')

        EmailAddress.objects.create(user=user, email=user.email,
                                    verified=True)
        data = {
            'username': 'user1',
            'email': 'user1_email_change@example.com',
            'language': 'en',
            'measurement': 'metric',
            'password': 'sgt-pepper'
        }

        request = HttpRequest()
        setattr(request, 'session', 'session')
        self.messages = FallbackStorage(request)
        setattr(request, '_messages', self.messages)
        request.META['SERVER_NAME'] = 'testserver'
        request.META['SERVER_PORT'] = '80'

        form = forms.ProfileForm(data, request=request, instance=user)
        form.save()
        assert EmailAddress.objects.filter(
            email="user1@example.com").exists() is False

        with pytest.raises(IntegrityError):
            user = UserFactory.create(username='user2',
                                      email='user1@example.com')

    def test_update_email_with_incorrect_password(self):
        user = UserFactory.create(email='john@beatles.uk',
                                  phone=None,
                                  password='imagine71')
        data = {
            'username': 'imagine71',
            'email': 'john2@beatles.uk',
            'language': 'en',
            'measurement': 'metric',
            'full_name': 'John Lennon',
            'password': 'stg-pepper'
        }

        form = forms.ProfileForm(data, instance=user)
        assert form.is_valid() is False
        assert ("Please provide the correct password for your account." in
                form.errors['password'])

    def test_sanitize(self):
        user = UserFactory.create(email='john@beatles.uk',
                                  phone=None,
                                  password='imagine71')
        data = {
            'username': '😛😛😛😛',
            'email': 'john@beatles.uk',
            'password': 'Iloveyoko68!',
            'full_name': 'John Lennon'
        }
        form = forms.ProfileForm(data, instance=user)

        assert form.is_valid() is False
        assert SANITIZE_ERROR in form.errors.get('username')

    def test_update_phone(self):
        user = UserFactory.create(username='sherlock',
                                  email=None,
                                  phone='+919327768250',
                                  email_verified=False,
                                  phone_verified=True,
                                  password='221B@bakerstreet',
                                  full_name='Sherlock Holmes')
        VerificationDevice.objects.create(user=user,
                                          unverified_phone=user.phone)
        data = {
            'username': 'sherlock',
            'phone': '+12345678990',
            'language': 'en',
            'measurement': 'metric',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes',
        }
        form = forms.ProfileForm(data, instance=user)
        form.save()

        user.refresh_from_db()
        assert form.is_valid() is True
        assert user.phone == '+919327768250'
        assert user.phone_verified is True
        assert VerificationDevice.objects.filter(
            unverified_phone='+919327768250').exists() is False

    def test_update_email(self):
        user = UserFactory.create(username='sherlock',
                                  email='sherlock.holmes@bbc.uk',
                                  phone=None,
                                  email_verified=True,
                                  phone_verified=False,
                                  password='221B@bakerstreet',
                                  full_name='Sherlock Holmes')
        EmailAddress.objects.create(user=user, email=user.email, verified=True)

        data = {
            'username': 'sherlock',
            'email': 'john.watson@bbc.uk',
            'language': 'en',
            'measurement': 'metric',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes',
        }

        request = HttpRequest()
        setattr(request, 'session', 'session')
        self.messages = FallbackStorage(request)
        setattr(request, '_messages', self.messages)
        request.META['SERVER_NAME'] = 'testserver'
        request.META['SERVER_PORT'] = '80'

        form = forms.ProfileForm(data, request=request, instance=user)
        form.save()

        user.refresh_from_db()
        assert user.email == 'sherlock.holmes@bbc.uk'
        assert user.email_verified is True
        assert len(mail.outbox) == 2
        assert 'john.watson@bbc.uk' in mail.outbox[0].to
        assert 'sherlock.holmes@bbc.uk' in mail.outbox[1].to
        assert EmailAddress.objects.filter(
            email="sherlock.holmes@bbc.uk").exists() is False
        # sms must be sent about email change to phone '+919327768250'

    def test_update_with_duplicate_phone(self):
        UserFactory.create(phone='+12345678990')
        user = UserFactory.create(username='sherlock',
                                  email=None,
                                  email_verified=False,
                                  phone_verified=True,
                                  phone='+919327768250',
                                  password='221B@bakerstreet',
                                  full_name='Sherlock Holmes')

        data = {
            'username': 'sherlock',
            'phone': '+12345678990',
            'language': 'en',
            'measurement': 'metric',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes',
        }
        form = forms.ProfileForm(data, instance=user)
        assert form.is_valid() is False
        assert (_("User with this Phone number already exists.")
                in form.errors.get('phone'))

    def test_udpate_with_invalid_phone(self):
        user = UserFactory.create(username='sherlock',
                                  email=None,
                                  phone='+919327768250',
                                  email_verified=False,
                                  phone_verified=True,
                                  password='221B@bakerstreet',
                                  full_name='Sherlock Holmes')
        data = {
            'username': 'sherlock',
            'phone': 'Test Number',
            'password': '221B@bakerstreet',
            'language': 'en',
            'measurement': 'metric',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.ProfileForm(data=data, instance=user)
        assert form.is_valid() is False
        assert (phone_format in form.errors.get('phone'))

        data = {
            'username': 'sherlock',
            'phone': '9327768250',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.ProfileForm(data=data, instance=user)
        assert form.is_valid() is False
        assert (phone_format in form.errors.get('phone'))

        data = {
            'username': 'sherlock',
            'phone': '+91-9067439937',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.ProfileForm(data=data, instance=user)
        assert form.is_valid() is False
        assert (phone_format in form.errors.get('phone'))

        data = {
            'username': 'sherlock',
            'phone': ' +91 9327768250 ',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.ProfileForm(data=data, instance=user)
        assert form.is_valid() is False
        assert (phone_format in form.errors.get('phone'))

        data = {
            'username': 'sherlock',
            'phone': '+919327768250137284721',
            'password': '221B@bakertstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.ProfileForm(data=data, instance=user)
        assert form.is_valid() is False
        assert (phone_format in form.errors.get('phone'))

        data = {
            'username': 'sherlock',
            'phone': '+1234',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.ProfileForm(data=data, instance=user)
        assert form.is_valid() is False
        assert (phone_format in form.errors.get('phone'))

        data = {
            'username': 'sherlock',
            'phone': '+8018225332',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.ProfileForm(data=data, instance=user)
        assert form.is_valid() is False
        assert (_("Please enter a valid country code.")
                in form.errors.get('phone'))

    def test_update_remove_phone(self):
        user = UserFactory.create(username='sherlock',
                                  email=None,
                                  phone='+919327768250',
                                  email_verified=False,
                                  phone_verified=True,
                                  password='221B@bakerstreet',
                                  full_name='Sherlock Holmes')
        VerificationDevice.objects.create(user=user,
                                          unverified_phone=user.phone)
        data = {
            'username': 'sherlock',
            'phone': '',
            'language': 'en',
            'measurement': 'metric',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.ProfileForm(data=data, instance=user)
        assert form.is_valid() is False

    def test_update_remove_email(self):
        user = UserFactory.create(username='sherlock',
                                  email='sherlock.holmes@bbc.uk',
                                  phone=None,
                                  email_verified=True,
                                  phone_verified=False,
                                  password='221B@bakerstreet',
                                  full_name='Sherlock Holmes')
        EmailAddress.objects.create(user=user,
                                    email=user.email)
        data = {
            'username': 'sherlock',
            'email': '',
            'language': 'en',
            'measurement': 'metric',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.ProfileForm(data=data, instance=user)
        assert form.is_valid() is False

    def test_update_add_phone_and_remove_email(self):
        user = UserFactory.create(username='sherlock',
                                  email='sherlock.holmes@bbc.uk',
                                  phone=None,
                                  email_verified=True,
                                  password='221B@bakerstreet',
                                  full_name='Sherlock Holmes')

        EmailAddress.objects.create(user=user, email=user.email)

        data = {
            'username': 'sherlock',
            'email': '',
            'phone': '+919327768250',
            'language': 'en',
            'measurement': 'metric',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.ProfileForm(data=data, instance=user)
        assert form.is_valid() is False
        assert ('This field is required.' in form.errors['email'])

    def test_update_add_email_and_remove_phone(self):
        user = UserFactory.create(username='sherlock',
                                  email=None,
                                  phone='+919327768250',
                                  phone_verified=True,
                                  password='221B@bakerstreet',
                                  full_name='Sherlock Holmes')

        VerificationDevice.objects.create(user=user,
                                          unverified_phone=user.phone)

        data = {
            'username': 'sherlock',
            'email': 'sherlock.holmes@bbc.uk',
            'phone': '',
            'language': 'en',
            'measurement': 'metric',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }

        form = forms.ProfileForm(data, instance=user)
        assert form.is_valid() is False
        assert ('This field is required.' in form.errors['phone'])

    def test_update_with_existing_email_in_EmailAddress(self):
        user = UserFactory.create()
        EmailAddress.objects.create(email='sherlock.holmes@bbc.uk', user=user)
        user1 = UserFactory.create(username='sherlock',
                                   email='john.watson@bbc.uk',
                                   phone=None,
                                   phone_verified=False,
                                   email_verified=True,
                                   password='221B@bakerstreet',
                                   full_name='Sherlock Holmes')
        data = {
            'username': 'sherlock',
            'email': 'sherlock.holmes@bbc.uk',
            'language': 'en',
            'measurement': 'metric',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.ProfileForm(data=data, instance=user1)
        assert form.is_valid() is False
        assert (_("User with this Email address already exists.")
                in form.errors.get('email'))

    def test_update_with_existing_phone_in_VerificationDevice(self):
        user = UserFactory.create()
        VerificationDevice.objects.create(unverified_phone='+919327768250',
                                          user=user)
        user1 = UserFactory.create(username='sherlock',
                                   email=None,
                                   phone='+12345678990',
                                   phone_verified=True,
                                   email_verified=False,
                                   password='221B@bakerstreet',
                                   full_name='Sherlock Holmes')

        data = {
            'username': 'sherlock',
            'phone': '+919327768250',
            'language': 'en',
            'measurement': 'metric',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.ProfileForm(data=data, instance=user1)
        assert form.is_valid() is False
        assert (_("User with this Phone number already exists.")
                in form.errors.get('phone'))


class ChangePasswordFormTest(UserTestCase, TestCase):

    def test_valid_data(self):
        user = UserFactory.create(password='beatles4Lyfe!')

        data = {
            'oldpassword': 'beatles4Lyfe!',
            'password': 'iloveyoko79!',
        }

        form = forms.ChangePasswordForm(user, data)
        assert form.is_valid() is True
        form.save()

        assert User.objects.count() == 1

        assert user.check_password('iloveyoko79!') is True

    def test_password_incorrect(self):
        user = UserFactory.create(
            password='beatles4Lyfe!', username='imagine71')

        data = {
            'oldpassword': 'th3m0nkeesRule!!',
            'password': 'l3titb3333!',
        }
        form = forms.ChangePasswordForm(user, data)

        assert form.is_valid() is False
        assert (_("Please type your current password.") in
                form.errors.get('oldpassword'))

    def test_password_contains_username(self):
        user = UserFactory.create(
            password='beatles4Lyfe!', username='imagine71')

        data = {
            'oldpassword': 'beatles4Lyfe!',
            'password': 'Letsimagine71?1234567890',
        }
        form = forms.ChangePasswordForm(user, data)

        assert form.is_valid() is False
        assert (_("The password is too similar to the username.") in
                form.errors.get('password'))

    def test_password_contains_username_case_insensitive(self):
        user = UserFactory.create(
            password='beatles4Lyfe!', username='imagine71')

        data = {
            'oldpassword': 'beatles4Lyfe!',
            'password': 'LetsIMAGINE71?1234567890',
        }
        form = forms.ChangePasswordForm(user, data)

        assert form.is_valid() is False
        assert (_("The password is too similar to the username.") in
                form.errors.get('password'))

    def test_password_contains_email(self):
        user = UserFactory.create(
            password='beatles4Lyfe!', email='john@thebeatles.uk')

        data = {
            'oldpassword': 'beatles4Lyfe!',
            'password': 'IsJOHNreallythebest34?',
        }
        form = forms.ChangePasswordForm(user, data)

        assert form.is_valid() is False
        assert (_("Passwords cannot contain your email.") in
                form.errors.get('password'))

    def test_password_contains_less_than_min_characters(self):
        user = UserFactory.create(password='beatles4Lyfe!')

        data = {
            'oldpassword': 'beatles4Lyfe!',
            'password': '<3yoko',
        }
        form = forms.ChangePasswordForm(user, data)

        assert form.is_valid() is False
        assert (_("This password is too short."
                  " It must contain at least 10 characters.") in
                form.errors.get('password'))

    def test_password_does_not_meet_unique_character_requirements(self):
        user = UserFactory.create(password='beatles4Lyfe!')

        data = {
            'oldpassword': 'beatles4Lyfe!',
            'password': 'YOKOISJUSTTHEBEST',
        }
        form = forms.ChangePasswordForm(user, data)

        assert form.is_valid() is False
        assert (_("Passwords must contain at least 3"
                  " of the following 4 character types:\n"
                  "lowercase characters, uppercase characters,"
                  " special characters, and/or numerical character.\n"
                  ))

    def test_user_not_allowed_change_password(self):
        user = UserFactory.create(password='beatles4Lyfe!',
                                  update_profile=False)
        data = {
            'oldpassword': 'beatles4Lyfe!',
            'password': 'iloveyoko79!',
        }
        form = forms.ChangePasswordForm(user, data)

        assert form.is_valid() is False
        assert (_("The password for this user can not be changed.") in
                form.errors.get('password'))

    def test_password_contains_phone(self):
        user = UserFactory.create(password='221B@bakerstreet',
                                  phone='+919327768250')
        data = {
            'oldpassword': '221B@bakerstreet',
            'password': '9327768250@bakerstreet'
        }

        form = forms.ChangePasswordForm(user, data)
        assert form.is_valid() is False
        assert (_("Passwords cannot contain your phone.")
                in form.errors.get('password'))


class ResetPasswordKeyFormTest(UserTestCase, TestCase):

    def test_valid_data(self):
        user = UserFactory.create(password='beatles4Lyfe!')

        data = {
            'password': 'iloveyoko79!',
        }

        form = forms.ResetPasswordKeyForm(data, user=user)

        assert form.is_valid() is True
        form.save()

        assert User.objects.count() == 1

        assert user.check_password('iloveyoko79!') is True

    def test_password_contains_username(self):
        user = UserFactory.create(
            password='beatles4Lyfe!', username='imagine71')

        data = {
            'password': 'Letsimagine71?1234567890',
        }
        form = forms.ResetPasswordKeyForm(data, user=user)

        assert form.is_valid() is False
        assert (_("The password is too similar to the username.") in
                form.errors.get('password'))

    def test_password_contains_username_case_insensitive(self):
        user = UserFactory.create(
            password='beatles4Lyfe!', username='imagine71')

        data = {
            'password': 'LetsIMAGINE71?1234567890',
        }
        form = forms.ResetPasswordKeyForm(data, user=user)

        assert form.is_valid() is False
        assert (_("The password is too similar to the username.") in
                form.errors.get('password'))

    def test_password_contains_email(self):
        user = UserFactory.create(
            password='beatles4Lyfe!', email='john@thebeatles.uk')

        data = {
            'password': 'IsJOHNreallythebest34?',
        }
        form = forms.ResetPasswordKeyForm(data, user=user)

        assert form.is_valid() is False
        assert (_("Passwords cannot contain your email.") in
                form.errors.get('password'))

    def test_password_contains_less_than_min_characters(self):
        user = UserFactory.create(password='beatles4Lyfe!')

        data = {
            'password': '<3yoko',
        }
        form = forms.ResetPasswordKeyForm(data, user=user)

        assert form.is_valid() is False
        assert (_("This password is too short."
                  " It must contain at least 10 characters.") in
                form.errors.get('password'))

    def test_password_does_not_meet_unique_character_requirements(self):
        user = UserFactory.create(password='beatles4Lyfe!')

        data = {
            'password': 'YOKOISJUSTTHEBEST',
        }
        form = forms.ResetPasswordKeyForm(data, user=user)

        assert form.is_valid() is False
        assert (_("Passwords must contain at least 3"
                  " of the following 4 character types:\n"
                  "lowercase characters, uppercase characters,"
                  " special characters, and/or numerical character.\n"
                  ))

    def test_user_not_allowed_change_password(self):
        user = UserFactory.create(password='beatles4Lyfe!',
                                  update_profile=False)
        data = {
            'password': 'iloveyoko79!',
        }
        form = forms.ResetPasswordKeyForm(data, user=user)

        assert form.is_valid() is False
        assert (_("The password for this user can not be changed.") in
                form.errors.get('password'))

    def test_password_contains_phone(self):
        user = UserFactory.create(password='221B@bakerstreet',
                                  phone='+919327768250')
        data = {
            'password': '9327768250@bakerstreet'
        }

        form = forms.ResetPasswordKeyForm(data, user=user)
        assert form.is_valid() is False
        assert (_("Passwords cannot contain your phone.")
                in form.errors.get('password'))

    def test_password_change_without_user(self):
        data = {'password': 'iloveyoko79!'}
        form = forms.ResetPasswordKeyForm(data)
        assert form.is_valid() is False
        assert (_(
            "The password for this user can not be changed.")
            in form.errors.get('password'))


class ResetPasswordFormTest(UserTestCase, TestCase):

    def test_email_not_sent_reset(self):
        data = {
            'email': 'john@thebeatles.uk'
        }

        form = forms.ResetPasswordForm(data)
        assert form.is_valid() is True

    def test_email_sent_reset(self):
        UserFactory.create(
            password='beatles4Lyfe!', email='john@thebeatles.uk')

        data = {
            'email': 'john@thebeatles.uk'
        }

        form = forms.ResetPasswordForm(data)
        assert form.is_valid() is True

    def test_msg_sent_reset_with_phone(self):
        UserFactory.create(
            password='221B@bakerstreet', phone='+919327768250')

        data = {
            'phone': '+919327768250'
        }
        form = forms.ResetPasswordForm(data)
        request = HttpRequest()
        setattr(request, 'session', {})
        form.save(request)

        assert form.is_valid() is True
        assert VerificationDevice.objects.filter(
            unverified_phone='+919327768250',
            label='password_reset').exists() is True

    def test_msg_not_sent_reset_with_phone(self):
        data = {
            'phone': '+919327768250'
        }

        form = forms.ResetPasswordForm(data)
        assert form.is_valid() is True
        request = HttpRequest()
        setattr(request, 'session', {})
        form.save(request)
        assert VerificationDevice.objects.filter(
            unverified_phone='+919327768250',
            label='password_reset').exists() is False

    def test_empty_submit(self):
        data = {
            'phone': '',
        }

        form = forms.ResetPasswordForm(data)
        assert form.is_valid() is False
        assert (_("You cannot leave both phone and email empty.")
                in form.errors.get('__all__'))

        data = {
            'email': '',
        }

        form = forms.ResetPasswordForm(data)
        assert form.is_valid() is False
        assert (_("You cannot leave both phone and email empty.")
                in form.errors.get('__all__'))


class TokenVerificationFormTest(UserTestCase, TestCase):

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.device = VerificationDevice.objects.create(
            user=self.user, unverified_phone=self.user.phone)

    def test_valid_token(self):
        token = self.device.generate_challenge()
        data = {'token': token}
        form = forms.TokenVerificationForm(data=data, device=self.device)
        assert form.is_valid() is True

    def test_invalid_token(self):
        token = self.device.generate_challenge()
        token = str(int(token) - 1)
        data = {'token': token}
        form = forms.TokenVerificationForm(data=data, device=self.device)
        assert form.is_valid() is False
        assert (_("Invalid Token. Enter a valid token.")
                in form.errors.get('token'))

    def test_expired_token(self):
        now = 1497657600
        with mock.patch('time.time', return_value=now):
            token = self.device.generate_challenge()
            data = {'token': token}
        with mock.patch('time.time', return_value=(
                now + settings.TOTP_TOKEN_VALIDITY + 1)):
            form = forms.TokenVerificationForm(data=data, device=self.device)
            assert form.is_valid() is False
            assert (_("The token has expired."
                      " Please click on 'here' to receive the new token.")
                    in form.errors.get('token'))

    def test_invalid_token_format(self):
        data = {'token': 'TOKEN'}
        form = forms.TokenVerificationForm(data=data, device=self.device)
        assert form.is_valid() is False
        assert (_("Token must be a number.") in form.errors.get('token'))

    def test_token_without_device(self):
        data = {'token': '123456'}
        form = forms.TokenVerificationForm(data=data, device=None)
        assert form.is_valid() is False
        assert (_("The token could not be verified."
                  " Please click on 'here' to try again.")
                in form.errors.get('token'))


class ResendTokenFormTest(UserTestCase, TestCase):

    def test_invalid_phone(self):
        data = {'phone': '12345678990'}
        form = forms.ResendTokenForm(data)
        assert form.is_valid() is False
        assert phone_format in form.errors.get('phone')

        data = {'phone': 'Test Number'}
        form = forms.ResendTokenForm(data)
        assert form.is_valid() is False
        assert phone_format in form.errors.get('phone')

        data = {'phone': ' +1 2345678990 '}
        form = forms.ResendTokenForm(data)
        assert form.is_valid() is False
        assert phone_format in form.errors.get('phone')

        data = {'phone': '+12345678790123456890'}
        form = forms.ResendTokenForm(data)
        assert form.is_valid() is False
        assert phone_format in form.errors.get('phone')

        data = {
            'username': 'sherlock',
            'phone': '+1234',
            'password': '221B@bakerstreet',
            'full_name': 'Sherlock Holmes'
        }
        form = forms.ResendTokenForm(data)
        assert form.is_valid() is False
        assert phone_format in form.errors.get('phone')

    def test_submit_empty(self):
        data = {'email': ''}
        form = forms.ResendTokenForm(data)
        assert form.is_valid() is False
        assert (
            _("You cannot leave both phone and email empty.")
            in form.errors.get('__all__'))

        data = {'phone': ''}
        form = forms.ResendTokenForm(data)
        assert form.is_valid() is False
        assert (
            _("You cannot leave both phone and email empty.")
            in form.errors.get('__all__'))
