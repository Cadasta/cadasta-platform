import time

from django import forms
from django.utils import timezone
from django.core.cache import cache

from config.settings.default import ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT
from allauth.account import adapter


class DefaultAccountAdapter(adapter.DefaultAccountAdapter):
    def pre_authenticate(self, request, **credentials):
        cache_key = self._get_login_attempts_cache_key(
            request, **credentials)
        login_data = cache.get(cache_key, None)
        if login_data:
            dt = timezone.now()
            current_attempt_time = time.mktime(dt.timetuple())
            back_off = (1 << (len(login_data) - 1))

            # ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT should be set to maximum amount of
            # time a user can be locked out.
            if back_off > ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT:
                back_off = ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT

            if current_attempt_time < (login_data[-1] + back_off):
                raise forms.ValidationError(
                    self.error_messages['too_many_login_attempts'])
