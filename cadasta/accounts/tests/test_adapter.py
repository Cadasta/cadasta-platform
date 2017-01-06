import time
import pytest
from datetime import timedelta

from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.forms import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from allauth.account.adapter import DefaultAccountAdapter as all_auth

from config.settings.default import ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT
from core.tests.utils.cases import UserTestCase
from .factories import UserFactory
from ..adapter import DefaultAccountAdapter as a


class AccountAdapterTests(UserTestCase, TestCase):
    @override_settings(CACHES={
        'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}
        })
    def test_pre_authenticate(self):
        UserFactory.create(username='john_snow', password='Winteriscoming!')
        credentials = {'username': 'john_snow', 'password': 'knowsnothing'}
        request = self.client.get(
            reverse('account:login'),
            {'login': 'john_snow', 'password': 'knowsnothing'})
        a().pre_authenticate(request, **credentials)

    @override_settings(CACHES={
        'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}
        })
    def test_pre_authenticate_fails(self):
        UserFactory.create(username='john_snow', password='Winteriscoming!')
        credentials = {'username': 'john_snow', 'password': 'knowsnothing'}
        request = self.client.get(
            reverse('account:login'),
            {'login': 'john_snow', 'password': 'knowsnothing'})
        cache_key = all_auth()._get_login_attempts_cache_key(
            request, **credentials)

        data = []
        dt = timezone.now()

        data.append(time.mktime(dt.timetuple()))
        cache.set(cache_key, data, ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT)

        with pytest.raises(ValidationError):
            a().pre_authenticate(request, **credentials)

        # fake a user waiting 2 seconds
        dt = timezone.now() - timedelta(seconds=2)
        data.append(time.mktime(dt.timetuple()))
        cache.set(cache_key, data, ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT)

        a().pre_authenticate(request, **credentials)

    def test_pre_authenticate_maxes_out(self):
        UserFactory.create(username='john_snow', password='Winteriscoming!')
        credentials = {'username': 'john_snow', 'password': 'knowsnothing'}
        request = self.client.get(
            reverse('account:login'),
            {'login': 'john_snow', 'password': 'knowsnothing'})
        cache_key = all_auth()._get_login_attempts_cache_key(
            request, **credentials)

        data = [None]*1000
        dt = timezone.now()

        data.append(time.mktime(dt.timetuple()))
        cache.set(cache_key, data, ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT)

        with pytest.raises(ValidationError):
            a().pre_authenticate(request, **credentials)

        dt = timezone.now() - timedelta(seconds=ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT)
        data.append(time.mktime(dt.timetuple()))
        cache.set(cache_key, data, ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT)

        a().pre_authenticate(request, **credentials)
