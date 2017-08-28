from django.test import TestCase
from django.core.urlresolvers import reverse, resolve

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
