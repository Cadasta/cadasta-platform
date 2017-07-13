import importlib
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.core.cache.backends.memcached import PyLibMCCache
import pylibmc

from core import backends


class MemorySafePyLibMCCacheTest(TestCase):

    @override_settings(CACHES={
        'default': {
            'BACKEND': 'core.backends.MemorySafePyLibMCCache',
            'LOCATION': ['localhost'],
        }
    })
    @patch('core.types.logging')
    def _test_method(self, method, logging):
        mock_logger = MagicMock()
        logging.getLogger.return_value = mock_logger

        # Patch the parent class of MemorySafePyLibMCCache, then reimport
        with patch.object(PyLibMCCache, method) as mock_method:
            importlib.reload(backends)
            from core.backends import MemorySafePyLibMCCache

            mock_method.__name__ = method
            mock_method.side_effect = pylibmc.TooBig()
            with patch('django.core.cache.cache', MemorySafePyLibMCCache):
                from django.core.cache import cache

                getattr(cache, method)('key', 1)

                logging.getLogger.assert_called_once_with('core.backends')
                mock_logger.exception.assert_called_once_with(
                    "Silenced cache failure at core.backends."
                    "MemorySafePyLibMCCache.{}()".format(method)
                )

                logging.getLogger.reset_mock()
                mock_logger.exception.reset_mock()

    def test_add(self):
        return self._test_method('add')

    def test_get_or_set(self):
        return self._test_method('get_or_set')

    def test_incr(self):
        return self._test_method('incr')

    def test_incr_version(self):
        return self._test_method('incr_version')

    def test_set(self):
        return self._test_method('set')

    def test_set_many(self):
        return self._test_method('set_many')
