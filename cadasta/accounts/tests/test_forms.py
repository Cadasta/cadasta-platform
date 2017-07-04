import random

from core.tests.utils.cases import UserTestCase
from core.messages import SANITIZE_ERROR
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.http import HttpRequest
from django.db import IntegrityError
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from django.test import TestCase
from django.utils.translation import gettext as _

from .. import forms
from ..models import User
from .factories import UserFactory


class RegisterFormTest(UserTestCase, TestCase):
    def test_valid_data(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password': 'iloveyoko79!',
            'full_name': 'John Lennon',
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
        assert (_("Another user with this email already exists")
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


class ProfileFormTest(UserTestCase, TestCase):
    def test_update_user(self):
        user = UserFactory.create(username='imagine71',
                                  email='john@beatles.uk',
                                  email_verified=True,
                                  password='sgt-pepper',
                                  language='en',
                                  measurement='metric')

        data = {
            'username': 'imagine71',
            'email': 'john2@beatles.uk',
            'full_name': 'John Lennon',
            'password': 'sgt-pepper',
            'language': 'en',
            'measurement': 'imperial'
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
                                  measurement='metric')
        assert user.get_display_name() == 'imagine71'

        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
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
                                  password='sgt-pepper')
        data = {
            'username': 'existing',
            'email': 'john@beatles.uk',
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
                                  measurement='metric')
        data = {
            'username': 'johnLennon',
            'email': 'john@beatles.uk',
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
            'full_name': 'John Lennon',
            'password': 'sgt-pepper',
            'language': 'en'
        }
        form = forms.ProfileForm(data, instance=user)
        assert form.is_valid() is False

    def test_signup_with_released_email(self):
        user = UserFactory.create(username='user1',
                                  email='user1@example.com',
                                  email_verified=True,
                                  password='sgt-pepper',
                                  measurement='metric')

        EmailAddress.objects.create(user=user, email=user.email,
                                    verified=True)
        data = {
            'username': 'user1',
            'email': 'user1_email_change@example.com',
            'password': 'sgt-pepper',
            'language': 'en',
            'measurement': 'metric'
        }

        request = HttpRequest()
        setattr(request, 'session', 'session')
        self.messages = FallbackStorage(request)
        setattr(request, '_messages', self.messages)
        request.META['SERVER_NAME'] = 'testserver'
        request.META['SERVER_PORT'] = '80'

        form = forms.ProfileForm(data, request=request, instance=user)
        form.save()

        user = UserFactory.create(username='user2',
                                  email='user1@example.com')
        try:
            send_email_confirmation(request, user)
        except IntegrityError:
            assert False
        else:
            assert True

    def test_update_email_with_incorrect_password(self):
        user = UserFactory.create(email='john@beatles.uk',
                                  password='imagine71')
        data = {
            'username': 'imagine71',
            'email': 'john2@beatles.uk',
            'full_name': 'John Lennon',
            'password': 'stg-pepper'
        }

        form = forms.ProfileForm(data, instance=user)
        assert form.is_valid() is False
        assert ("Please provide the correct password for your account." in
                form.errors['password'])

    def test_update_with_invalid_language(self):
        user = UserFactory.create(email='john@beatles.uk',
                                  password='imagine71',
                                  language='en')
        data = {
            'username': 'imagine71',
            'email': 'john2@beatles.uk',
            'full_name': 'John Lennon',
            'password': 'stg-pepper',
            'language': 'invalid'
        }
        form = forms.ProfileForm(data, instance=user)
        assert form.is_valid() is False
        assert user.language == 'en'
        assert ('Language invalid or not available'
                in form.errors.get('language'))

    def test_update_user_with_invalid_measurement(self):
        user = UserFactory.create(email='john@beatles.uk',
                                  password='imagine71',
                                  measurement='metric')
        data = {
            'username': 'imagine71',
            'email': 'john2@beatles.uk',
            'full_name': 'John Lennon',
            'password': 'stg-pepper',
            'measurement': 'invalid'
        }
        form = forms.ProfileForm(data, instance=user)
        assert form.is_valid() is False
        assert user.measurement == 'metric'
        assert ('Measurement system invalid or not available'
                in form.errors['measurement'])

    def test_sanitize(self):
        user = UserFactory.create(email='john@beatles.uk',
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
        user = UserFactory.create(password='beatles4Lyfe!', change_pw=False)
        data = {
            'oldpassword': 'beatles4Lyfe!',
            'password': 'iloveyoko79!',
        }
        form = forms.ChangePasswordForm(user, data)

        assert form.is_valid() is False
        assert (_("The password for this user can not be changed.") in
                form.errors.get('password'))


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
        user = UserFactory.create(password='beatles4Lyfe!', change_pw=False)
        data = {
            'password': 'iloveyoko79!',
        }
        form = forms.ResetPasswordKeyForm(data, user=user)

        assert form.is_valid() is False
        assert (_("The password for this user can not be changed.") in
                form.errors.get('password'))


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
