from django.test import TestCase
from django.core.urlresolvers import reverse, resolve
import allauth.account.views as allauth_views
from ..views import default


class UserUrlsTest(TestCase):
    def test_profile(self):
        assert reverse('account:profile') == '/account/profile/'

        resolved = resolve('/account/profile/')
        assert resolved.func.__name__ == default.AccountProfile.__name__

    def test_login(self):
        assert reverse('account:login') == '/account/login/'

        resolved = resolve('/account/login/')
        assert resolved.func.__name__ == default.AccountLogin.__name__

    def test_verify_email(self):
        assert reverse('account:verify_email',
                       kwargs={'key': '123'}) == '/account/confirm-email/123/'

        resolved = resolve('/account/confirm-email/123/')
        assert resolved.func.__name__ == default.ConfirmEmail.__name__
        assert resolved.kwargs['key'] == '123'

    def test_signup(self):
        assert reverse('account:register') == '/account/signup/'

        resolved = resolve('/account/signup/')
        assert resolved.func.__name__ == default.AccountRegister.__name__

    def test_verify_phone(self):
        assert reverse(
            'account:verify_phone') == '/account/accountverification/'

        resolved = resolve('/account/accountverification/')
        assert resolved.func.__name__ == default.ConfirmPhone.__name__

    def test_resend_token(self):
        assert reverse('account:resend_token') == '/account/resendtokenpage/'
        resolved = resolve('/account/resendtokenpage/')
        assert resolved.func.__name__ == default.ResendTokenView.__name__

    def test_change_password(self):
        assert reverse(
            'account:account_change_password') == '/account/password/change/'

        resolved = resolve('/account/password/change/')
        assert resolved.func.__name__ == default.PasswordChangeView.__name__

    def test_reset_password(self):
        assert reverse(
            'account:account_reset_password') == '/account/password/reset/'

        resolved = resolve('/account/password/reset/')
        assert resolved.func.__name__ == default.PasswordResetView.__name__

    def test_reset_password_from_key(self):
        assert reverse(
            'account:account_reset_password_from_key',
            kwargs={'uidb36': 'ABC', 'key': '123'}) == (
            '/account/password/reset/key/ABC-123/')

        resolved = resolve('/account/password/reset/key/ABC-123/')
        assert (resolved.func.__name__ ==
                default.PasswordResetFromKeyView.__name__)
        assert resolved.kwargs['uidb36'] == 'ABC'
        assert resolved.kwargs['key'] == '123'

    def test_reset_password_from_phone(self):
        assert reverse(
            'account:account_reset_password_from_phone') == (
            '/account/password/reset/phone/')

        resolved = resolve('/account/password/reset/phone/')
        assert (resolved.func.__name__ ==
                default.PasswordResetFromPhoneView.__name__)

    def test_reset_password_done(self):
        assert reverse(
            'account:account_reset_password_done') == (
            '/account/password/reset/done/')

        resolved = resolve('/account/password/reset/done/')
        assert resolved.func.__name__ == default.PasswordResetDoneView.__name__

    def test_reset_password_from_key_done(self):
        assert reverse(
            'account:account_reset_password_from_key_done') == (
            '/account/password/reset/key/done/')

        resolved = resolve('/account/password/reset/key/done/')
        assert (resolved.func.__name__ ==
                allauth_views.PasswordResetFromKeyDoneView.__name__)
