import time

from django import forms
from django.utils import timezone
from django.core.cache import cache

from allauth.account import adapter


class DefaultAccountAdapter(adapter.DefaultAccountAdapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def pre_authenticate(self, request, **credentials):
        cache_key = super()._get_login_attempts_cache_key(
            request, **credentials)
        login_data = cache.get(cache_key, None)
        if login_data:
            dt = timezone.now()
            current_attempt_time = time.mktime(dt.timetuple())
            back_off = (1 << (len(login_data) - 1))

            # if back_off is more than a day, reset to a day
            back_off = back_off if back_off < 86400 else 86400
            if current_attempt_time < (login_data[-1] + back_off):
                raise forms.ValidationError(
                    self.error_messages['too_many_login_attempts'])
