from django.test import TestCase
from django.core.urlresolvers import reverse, resolve
from .. import views


class UserUrlsTest(TestCase):
    def test_account_user(self):
        self.assertEqual(reverse('accounts:user'), '/account/')

        resolved = resolve('/account/')
        self.assertEqual(resolved.func.__name__, views.AccountUser.__name__)

    def test_account_register(self):
        self.assertEqual(reverse('accounts:register'), '/account/register/')

        resolved = resolve('/account/register/')
        self.assertEqual(resolved.func.__name__, views.AccountRegister.__name__)

    def test_account_login(self):
        self.assertEqual(reverse('accounts:login'), '/account/login/')

        resolved = resolve('/account/login/')
        self.assertEqual(resolved.func.__name__, views.AccountLogin.__name__)

    def test_account_activate(self):
        self.assertEqual(reverse('accounts:activate'), '/account/activate/')

        resolved = resolve('/account/activate/')
        self.assertEqual(resolved.func.__name__, views.AccountVerify.__name__)

    def test_password_reset(self):
        self.assertEqual(reverse('accounts:password_reset'), '/account/password/reset/')

        resolved = resolve('/account/password/reset/')
        self.assertEqual(resolved.func.__name__, views.PasswordReset.__name__)
