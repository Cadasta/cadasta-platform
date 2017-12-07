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

    def test_account_password(self):
        assert (reverse(version_ns('accounts:password')) ==
                version_url('/account/password/'))

        resolved = resolve(version_url('/account/password/'))
        assert resolved.func.__name__ == api.SetPasswordView.__name__

    def test_account_verify_phone(self):
        assert (reverse(version_ns('accounts:verify_phone')) ==
                version_url('/account/verify/phone/'))

        resolved = resolve(version_url('/account/verify/phone/'))
        assert resolved.func.__name__ == api.ConfirmPhoneView.__name__
