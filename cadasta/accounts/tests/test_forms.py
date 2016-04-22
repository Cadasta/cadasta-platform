from django.test import TestCase
from django.utils.translation import gettext as _

from ..models import User
from ..forms import RegisterForm, ProfileForm

from .factories import UserFactory


class RegisterFormTest(TestCase):
    def test_valid_data(self):
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'password1': 'iloveyoko79',
            'password2': 'iloveyoko79',
            'first_name': 'John',
            'last_name': 'Lennon',
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
            'first_name': 'John',
            'last_name': 'Lennon',
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
            'first_name': 'John',
            'last_name': 'Lennon',
        }
        form = RegisterForm(data)

        assert form.is_valid() is False
        assert (_("Another user with this email already exists")
                in form.errors.get('email'))
        assert User.objects.count() == 1


class ProfileFormTest(TestCase):
    def test_update_user(self):
        user = UserFactory.create(username='imagine71',
                                  email='john@beatles.uk')
        data = {
            'username': 'imagine71',
            'email': 'john@beatles.uk',
            'first_name': 'John',
            'last_name': 'Lennon',
        }
        form = ProfileForm(data, instance=user)
        form.save()

        user.refresh_from_db()
        assert user.first_name == 'John'
        assert user.last_name == 'Lennon'

    def test_update_user_with_existing_username(self):
        UserFactory.create(username='existing')
        user = UserFactory.create(username='imagine71',
                                  email='john@beatles.uk')
        data = {
            'username': 'existing',
            'email': 'john@beatles.uk',
            'first_name': 'John',
            'last_name': 'Lennon',
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
            'first_name': 'John',
            'last_name': 'Lennon',
        }
        form = ProfileForm(data, instance=user)
        assert form.is_valid() is False
