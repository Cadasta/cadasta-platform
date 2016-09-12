from django.test import TestCase
from django.core.urlresolvers import reverse, resolve

from core.tests.utils.urls import version_ns, version_url
from ..views import api


class UserUrlsTest(TestCase):
    def test_account_user(self):
        assert reverse(version_ns('accounts:user')) == version_url('/account/')

        resolved = resolve(version_url('/account/'))
        assert resolved.func.__name__ == api.AccountUser.__name__

    def test_account_register(self):
        assert (reverse(version_ns('accounts:register')) ==
                version_url('/account/register/'))

        resolved = resolve(version_url('/account/register/'))
        assert resolved.func.__name__ == api.AccountRegister.__name__

    def test_account_login(self):
        assert (reverse(version_ns('accounts:login')) ==
                version_url('/account/login/'))

        resolved = resolve(version_url('/account/login/'))
        assert resolved.func.__name__ == api.AccountLogin.__name__

    def test_account_activate(self):
        assert (reverse(version_ns('accounts:activate')) ==
                version_url('/account/activate/'))

        resolved = resolve(version_url('/account/activate/'))
        assert resolved.func.__name__ == api.AccountVerify.__name__

    def test_password_reset(self):
        self.assertEqual(
            reverse(version_ns('accounts:password_reset')),
            version_url('/account/password/reset/')
        )

        resolved = resolve(version_url('/account/password/reset/'))
        assert resolved.func.__name__ == api.PasswordReset.__name__
