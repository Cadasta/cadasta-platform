import random

from django.utils.translation import gettext as _
from django.test import TestCase

from ..models import User
from ..forms import RegisterForm, ProfileForm
from core.tests.utils.cases import UserTestCase

from .factories import UserFactory


class RegisterFormTest(UserTestCase, TestCase):
    def test_valid_data(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password1': 'iloveyoko79',
            'password2': 'iloveyoko79',
            'full_name': 'John Lennon',
        }
        form = RegisterForm(data)
        form.save()

        assert form.is_valid() is True
        assert User.objects.count() == 1

        user = User.objects.first()
        assert user.check_password('iloveyoko79') is True

    def test_passwords_do_not_match(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password1': 'iloveyoko79',
            'password2': 'iloveyoko68',
            'full_name': 'John Lennon',
        }
        form = RegisterForm(data)

        assert form.is_valid() is False
        assert _("Passwords do not match") in form.errors.get('password1')
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
        form = RegisterForm(data)

        assert form.is_valid() is False
        assert (_("Another user with this email already exists")
                in form.errors.get('email'))
        assert User.objects.count() == 1

    def test_signup_with_restricted_username(self):
        invalid_usernames = ('add', 'ADD', 'Add', 'new', 'NEW', 'New')
        data = {
            'username': random.choice(invalid_usernames),
            'email': 'john@beatles.uk',
            'password1': 'iloveyoko79',
            'password2': 'iloveyoko68',
            'full_name': 'John Lennon',
        }
        form = RegisterForm(data)

        assert form.is_valid() is False
        assert (_("Username cannot be “add” or “new”.")
                in form.errors.get('username'))
        assert User.objects.count() == 0


class ProfileFormTest(UserTestCase, TestCase):
    def test_update_user(self):
        user = UserFactory.create(username='imagine71',
                                  email='john@beatles.uk')
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'full_name': 'John Lennon',
        }
        form = ProfileForm(data, instance=user)
        form.save()

        user.refresh_from_db()
        assert user.full_name == 'John Lennon'

    def test_update_user_with_existing_username(self):
        UserFactory.create(username='existing')
        user = UserFactory.create(username='imagine71',
                                  email='john@beatles.uk')
        data = {
            'username': 'existing',
            'email': 'john@beatles.uk',
            'full_name': 'John Lennon',
        }
        form = ProfileForm(data, instance=user)
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
        form = ProfileForm(data, instance=user)
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
        form = ProfileForm(data, instance=user)
        assert form.is_valid() is False
