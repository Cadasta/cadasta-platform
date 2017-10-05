from unittest.mock import patch, MagicMock

from django.test import TestCase
import pybreaker

from core.breakers import breaker, listeners, storages


class BreakersTest(TestCase):

    def test_expected_errors(self):
        cb = breaker.CircuitBreaker(
            'test', expected_errors=(AttributeError,), state_storage=None)
        assert cb.expected_errors == (
            pybreaker.CircuitBreakerError, AttributeError)

    def test_repr(self):
        cb = breaker.CircuitBreaker('test', state_storage=None)
        assert str(cb) == '<CircuitBreaker: test>'

    def test_is_open(self):
        cb = breaker.CircuitBreaker(
            'test',
            state_storage=pybreaker.CircuitMemoryStorage('open'))
        assert cb.is_open is True
        cb = breaker.CircuitBreaker(
            'test',
            state_storage=pybreaker.CircuitMemoryStorage('closed'))
        assert cb.is_open is False
        cb = breaker.CircuitBreaker(
            'test',
            state_storage=pybreaker.CircuitMemoryStorage('half-open'))
        assert cb.is_open is False


class ListenersTest(TestCase):
    @staticmethod
    def _get_breaker(state):
        return breaker.CircuitBreaker(
            'test',
            state_storage=pybreaker.CircuitMemoryStorage(state),
            listeners=(listeners.LogListener(),)
        )

    @patch('core.breakers.listeners.logger')
    def test_log_state_change_closed(self, mock_logger):
        cb = self._get_breaker('open')
        cb.state = 'closed'
        mock_logger.info.assert_called_once_with(
            "Changed %r breaker state from %r to %r",
            cb._state_storage.name, 'open', 'closed')
        for level in ('debug', 'warning', 'error', 'exception'):
            assert not getattr(mock_logger, level).called

    @patch('core.breakers.listeners.logger')
    def test_log_state_change_open(self, mock_logger):
        cb = self._get_breaker('closed')
        cb.state = 'open'
        mock_logger.error.assert_called_once_with(
            "Changed %r breaker state from %r to %r",
            cb._state_storage.name, 'closed', 'open')
        for level in ('debug', 'info', 'warning', 'exception'):
            assert not getattr(mock_logger, level).called

    @patch('core.breakers.listeners.logger')
    def test_log_state_change_half_open(self, mock_logger):
        cb = self._get_breaker('open')
        cb.state = 'half-open'
        mock_logger.info.assert_called_once_with(
            "Changed %r breaker state from %r to %r",
            cb._state_storage.name, 'open', 'half-open')
        for level in ('debug', 'warning', 'error', 'exception'):
            assert not getattr(mock_logger, level).called

    @patch('core.breakers.listeners.logger')
    def test_success(self, mock_logger):
        cb = self._get_breaker('closed')

        @cb
        def test():
            assert True

        test()
        mock_logger.debug.assert_called_once_with(
            "Successful call on circuit breaker %r", cb._state_storage.name)
        for level in ('info', 'warning', 'error', 'exception'):
            assert not getattr(mock_logger, level).called

    @patch('core.breakers.listeners.logger')
    def test_failure(self, mock_logger):
        cb = self._get_breaker('closed')

        @cb
        def test():
            assert False

        with self.assertRaises(AssertionError):
            test()

        mock_logger.exception.assert_called_once_with(
            "Failed call on circuit breaker %r", cb._state_storage.name)
        for level in ('debug', 'info', 'error', 'warning'):
            assert not getattr(mock_logger, level).called


class StorageTest(TestCase):
    @staticmethod
    def _get_storage():
        return storages.CircuitBreakerCacheStorage("testStorage")

    def test_namespace(self):
        assert self._get_storage().namespace == 'pybreaker:testStorage'

    def test_duplicate_namespace(self):
        x = self._get_storage()  # NOQA
        with self.assertRaises(AssertionError):
            self._get_storage()

    def test_state_namespace(self):
        assert self._get_storage()._state_namespace == (
            'pybreaker:testStorage:state')

    def test_counter_namespace(self):
        assert self._get_storage()._counter_namespace == (
            'pybreaker:testStorage:counter')

    def test_opened_at_namespace(self):
        assert self._get_storage()._opened_at_namespace == (
            'pybreaker:testStorage:opened_at')

    @patch('core.breakers.storages.get_offline_cache_errors',
           MagicMock(return_value=(ValueError,)))
    @patch('core.breakers.storages.cache.set',
           MagicMock(side_effect=ValueError, __name__='fooBar'))
    @patch('core.decorators.logger')
    def test_safe_cache_set(self, logger):
        store = self._get_storage()
        store._safe_cache_set('foo')
        assert logger.exception.called

    @patch('core.breakers.storages.get_offline_cache_errors',
           MagicMock(return_value=(ValueError,)))
    @patch('core.breakers.storages.cache.get',
           MagicMock(side_effect=ValueError, __name__='fooBar'))
    @patch('core.decorators.logger')
    def test_safe_cache_get(self, logger):
        store = self._get_storage()
        store._safe_cache_get()
        assert logger.exception.called

    @patch('core.breakers.storages.get_offline_cache_errors',
           MagicMock(return_value=(ValueError,)))
    @patch('core.breakers.storages.cache.incr',
           MagicMock(side_effect=ValueError, __name__='fooBar'))
    @patch('core.decorators.logger')
    def test_safe_cache_incr(self, logger):
        store = self._get_storage()
        store._safe_cache_incr()
        assert logger.exception.called

    @patch('core.breakers.storages.cache.set')
    @patch('core.decorators.logger')
    def test_set_state(self, logger, cache_set):
        store = self._get_storage()
        store.state = 'open'
        cache_set.assert_called_once_with(store._state_namespace, 'open')

    @patch('core.breakers.storages.cache.incr')
    @patch('core.decorators.logger')
    def test_increment_counter(self, logger, cache_incr):
        store = self._get_storage()
        store.increment_counter()
        cache_incr.assert_called_once_with(store._counter_namespace)

    @patch('core.breakers.storages.cache.set')
    @patch('core.breakers.storages.cache.incr')
    def test_increment_counter_missing(self, cache_incr, cache_set):
        cache_incr.side_effect = ValueError
        cache_incr.__name__ = 'foo'
        store = self._get_storage()

        store.increment_counter()

        cache_incr.assert_called_once_with(store._counter_namespace)
        cache_set.assert_called_once_with(store._counter_namespace, 1)

    @patch('core.breakers.storages.cache.get')
    def test_increment_counter_error(self, cache_get):
        cache_get.return_value = 1234
        store = self._get_storage()
        assert store.counter == 1234
        cache_get.assert_called_once_with(store._counter_namespace, 0)

    @patch('core.breakers.storages.cache.get')
    def test_opened_at(self, cache_get):
        cache_get.return_value = 1234
        store = self._get_storage()
        assert store.opened_at == 1234
        cache_get.assert_called_once_with(store._opened_at_namespace)

    @patch('core.breakers.storages.cache.set')
    def test_opened_at_setter(self, cache_set):
        cache_set.return_value = 1234
        store = self._get_storage()
        store.opened_at = 1234
        cache_set.assert_called_once_with(store._opened_at_namespace, 1234)
