from django.test import TestCase
from django.core.urlresolvers import reverse, resolve
from .. import views


class UserUrlsTest(TestCase):
    def test_account_register(self):
        self.assertEqual(reverse('accounts:register'), '/account/register/')

        resolved = resolve('/account/register/')
        self.assertEqual(resolved.func.__name__, views.AccountRegister.__name__)

    def test_account_login(self):
        self.assertEqual(reverse('accounts:login'), '/account/login/')

        resolved = resolve('/account/login/')
        self.assertEqual(resolved.func.__name__, views.AccountLogin.__name__)
