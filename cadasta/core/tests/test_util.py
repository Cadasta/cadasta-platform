from unittest import mock
from django.test import TestCase
from ..util import log_with_opbeat, settings


class OpbeatLogTest(TestCase):
    @mock.patch('opbeat.Client.capture_exception', return_value=None)
    def test_in_production(self, capture_exception):
        """In production, the error should be logged with Opbeat"""
        settings.DEBUG = False
        try:
            raise Exception
        except Exception:
            log_with_opbeat()

        capture_exception.assert_called_once_with()

    @mock.patch('opbeat.Client.capture_exception', return_value=None)
    def test_debug(self, capture_exception):
        """In all envs other than production, the error should not be logged
           with Opbeat"""
        settings.DEBUG = True
        try:
            raise Exception
        except Exception:
            log_with_opbeat()

        capture_exception.assert_not_called()
