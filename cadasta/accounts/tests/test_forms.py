import random

from django.utils.translation import gettext as _
from django.test import TestCase
from django.core import mail
from django.http import HttpRequest
from django.contrib.messages.storage.fallback import FallbackStorage

from ..models import User
from .. import forms
from core.tests.utils.cases import UserTestCase

from .factories import UserFactory


class RegisterFormTest(UserTestCase, TestCase):
    def test_valid_data(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password1': 'iloveyoko79!',
            'password2': 'iloveyoko79!',
            'full_name': 'John Lennon',
        }
        form = forms.RegisterForm(data)
        form.save()

        assert form.is_valid() is True
        assert User.objects.count() == 1

        user = User.objects.first()
        assert user.check_password('iloveyoko79!') is True

    def test_passwords_do_not_match(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password1': 'Iloveyoko79!',
            'password2': 'Iloveyoko68!',
            'full_name': 'John Lennon',
        }
        form = forms.RegisterForm(data)

        assert form.is_valid() is False
        assert _("Passwords do not match") in form.errors.get('password1')
        assert User.objects.count() == 0

    def test_password_contains_username(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password1': 'Letsimagine71things?',
            'password2': 'Letsimagine71things?',
            'full_name': 'John Lennon',
        }
        form = forms.RegisterForm(data)

        assert form.is_valid() is False
        assert (_("The password is too similar to the username.") in
                form.errors.get('password1'))
        assert User.objects.count() == 0

    def test_password_contains_email(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password1': 'Isjohnreallythebest34?',
            'password2': 'Isjohnreallythebest34?',
            'full_name': 'John Lennon',
        }
        form = forms.RegisterForm(data)

        assert form.is_valid() is False
        assert (_("Passwords cannot contain your email.") in
                form.errors.get('password1'))
        assert User.objects.count() == 0

    def test_password_contains_less_than_min_characters(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password1': '<3yoko',
            'password2': '<3yoko',
            'full_name': 'John Lennon',
        }
        form = forms.RegisterForm(data)

        assert form.is_valid() is False
        assert (_("This password is too short."
                  " It must contain at least 10 characters.") in
                form.errors.get('password1'))
        assert User.objects.count() == 0

    def test_password_does_not_meet_unique_character_requirements(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password1': 'yokoisjustthebest',
            'password2': 'yokoisjustthebest',
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
            'password1': 'YOKOISJUSTTHEBEST',
            'password2': 'YOKOISJUSTTHEBEST',
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
            'password1': 'iloveyoko79',
            'password2': 'iloveyoko79',
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
            'password1': 'Iloveyoko68!',
            'password2': 'Iloveyoko68!',
            'full_name': 'John Lennon',
        }
        form = forms.RegisterForm(data)

        assert form.is_valid() is False
        assert (_("Username cannot be “add” or “new”.")
                in form.errors.get('username'))
        assert User.objects.count() == 0

    def test_signup_with_existing_username(self):
        UserFactory.create(username='dee')
        data = {
            'username': 'DEE',
            'email': 'dee@firstpr.com',
            'password1': 'Iloveyoko68!',
            'password2': 'Iloveyoko68!',
            'full_name': 'Delight Mawoyo',
        }

        form = forms.RegisterForm(data)
        assert form.is_valid() is False
        assert User.objects.count() == 1
        assert (_("A user with that username already exists.")
                in form.errors.get('username'))


class ProfileFormTest(UserTestCase, TestCase):
    def test_update_user(self):
        user = UserFactory.create(username='imagine71',
                                  email='john@beatles.uk',
                                  email_verified=True)
        data = {
            'username': 'IMAGINE71',
            'email': 'john2@beatles.uk',
            'full_name': 'John Lennon',
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
        assert user.username == 'IMAGINE71'
        assert user.full_name == 'John Lennon'
        assert user.email_verified is False
        assert len(mail.outbox) == 1

    def test_display_name(self):
        user = UserFactory.create(username='imagine71',
                                  email='john@beatles.uk')
        assert user.get_display_name() == 'imagine71'

        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'full_name': 'John Lennon',
        }
        form = forms.ProfileForm(data, instance=user)
        form.save()

        user.refresh_from_db()
        assert user.get_display_name() == 'John Lennon'

    def test_update_user_with_existing_username(self):
        UserFactory.create(username='existing')
        user = UserFactory.create(username='imagine71',
                                  email='john@beatles.uk')
        data = {
            'username': 'existing',
            'email': 'john@beatles.uk',
            'full_name': 'John Lennon',
        }
        form = forms.ProfileForm(data, instance=user)
        assert form.is_valid() is False

    def test_update_user_with_existing_username_case_insensitive(self):
        UserFactory.create(username='existing')
        user = UserFactory.create(username='imagine71',
                                  email='john@beatles.uk')
        data = {
            'username': 'Existing',
            'email': 'john@beatles.uk',
            'full_name': 'John Lennon',
        }
        form = forms.ProfileForm(data, instance=user)
        assert form.is_valid() is False

    def test_update_user_with_existing_email(self):
        UserFactory.create(email='existing@example.com')
        user = UserFactory.create(username='imagine71',
                                  email='john@beatles.uk')
        data = {
            'username': 'imagine71',
            'email': 'existing@example.com',
            'full_name': 'John Lennon',
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
        }
        form = forms.ProfileForm(data, instance=user)
        assert form.is_valid() is False


class ChangePasswordFormTest(UserTestCase, TestCase):
    def test_valid_data(self):
        user = UserFactory.create(password='beatles4Lyfe!')

        data = {
            'oldpassword': 'beatles4Lyfe!',
            'password1': 'iloveyoko79!',
            'password2': 'iloveyoko79!',
        }

        form = forms.ChangePasswordForm(user, data)
        assert form.is_valid() is True
        form.save()

        assert User.objects.count() == 1

        assert user.check_password('iloveyoko79!') is True

    def test_passwords_do_not_match(self):
        user = UserFactory.create(password='beatles4Lyfe!')

        data = {
            'oldpassword': 'beatles4Lyfe!',
            'password1': 'Iloveyoko79!',
            'password2': 'Iloveyoko68!',
        }
        form = forms.ChangePasswordForm(user, data)

        assert form.is_valid() is False
        assert (_('You must type the same password each time.') in
                form.errors.get('password2'))

    def test_password_contains_username(self):
        user = UserFactory.create(
            password='beatles4Lyfe!', username='imagine71')

        data = {
            'oldpassword': 'beatles4Lyfe!',
            'password1': 'Letsimagine71?',
            'password2': 'Letsimagine71?',
        }
        form = forms.ChangePasswordForm(user, data)

        assert form.is_valid() is False
        assert (_("The password is too similar to the username.") in
                form.errors.get('password1'))

    def test_password_contains_email(self):
        user = UserFactory.create(
            password='beatles4Lyfe!', email='john@thebeatles.uk')

        data = {
            'oldpassword': 'beatles4Lyfe!',
            'password1': 'Isjohnreallythebest34?',
            'password2': 'Isjohnreallythebest34?',
        }
        form = forms.ChangePasswordForm(user, data)

        assert form.is_valid() is False
        assert (_("Passwords cannot contain your email.") in
                form.errors.get('password1'))

    def test_password_contains_less_than_min_characters(self):
        user = UserFactory.create(password='beatles4Lyfe!')

        data = {
            'oldpassword': 'beatles4Lyfe!',
            'password1': '<3yoko',
            'password2': '<3yoko',
        }
        form = forms.ChangePasswordForm(user, data)

        assert form.is_valid() is False
        assert (_("This password is too short."
                  " It must contain at least 10 characters.") in
                form.errors.get('password1'))

    def test_password_does_not_meet_unique_character_requirements(self):
        user = UserFactory.create(password='beatles4Lyfe!')

        data = {
            'oldpassword': 'beatles4Lyfe!',
            'password1': 'YOKOISJUSTTHEBEST',
            'password2': 'YOKOISJUSTTHEBEST',
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
            'password1': 'iloveyoko79!',
            'password2': 'iloveyoko79!',
        }
        form = forms.ChangePasswordForm(user, data)

        assert form.is_valid() is False
        assert (_("The password for this user can not be changed.") in
                form.errors.get('password1'))


class ResetPasswordFormTest(UserTestCase, TestCase):
    def test_valid_data(self):
        user = UserFactory.create(password='beatles4Lyfe!')

        data = {
            'password1': 'iloveyoko79!',
            'password2': 'iloveyoko79!',
        }

        form = forms.ResetPasswordKeyForm(data, user=user)

        assert form.is_valid() is True
        form.save()

        assert User.objects.count() == 1

        assert user.check_password('iloveyoko79!') is True

    def test_passwords_do_not_match(self):
        user = UserFactory.create(password='beatles4Lyfe!')

        data = {
            'password1': 'Iloveyoko79!',
            'password2': 'Iloveyoko68!',
        }
        form = forms.ResetPasswordKeyForm(data, user=user)

        assert form.is_valid() is False
        assert (_('You must type the same password each time.') in
                form.errors.get('password2'))

    def test_password_contains_username(self):
        user = UserFactory.create(
            password='beatles4Lyfe!', username='imagine71')

        data = {
            'password1': 'Letsimagine71?',
            'password2': 'Letsimagine71?',
        }
        form = forms.ResetPasswordKeyForm(data, user=user)

        assert form.is_valid() is False
        assert (_("The password is too similar to the username.") in
                form.errors.get('password1'))

    def test_password_contains_email(self):
        user = UserFactory.create(
            password='beatles4Lyfe!', email='john@thebeatles.uk')

        data = {
            'password1': 'Isjohnreallythebest34?',
            'password2': 'Isjohnreallythebest34?',
        }
        form = forms.ResetPasswordKeyForm(data, user=user)

        assert form.is_valid() is False
        assert (_("Passwords cannot contain your email.") in
                form.errors.get('password1'))

    def test_password_contains_less_than_min_characters(self):
        user = UserFactory.create(password='beatles4Lyfe!')

        data = {
            'password1': '<3yoko',
            'password2': '<3yoko',
        }
        form = forms.ResetPasswordKeyForm(data, user=user)

        assert form.is_valid() is False
        assert (_("This password is too short."
                  " It must contain at least 10 characters.") in
                form.errors.get('password1'))

    def test_password_does_not_meet_unique_character_requirements(self):
        user = UserFactory.create(password='beatles4Lyfe!')

        data = {
            'password1': 'YOKOISJUSTTHEBEST',
            'password2': 'YOKOISJUSTTHEBEST',
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
            'password1': 'iloveyoko79!',
            'password2': 'iloveyoko79!',
        }
        form = forms.ResetPasswordKeyForm(data, user=user)

        assert form.is_valid() is False
        assert (_("The password for this user can not be changed.") in
                form.errors.get('password1'))
