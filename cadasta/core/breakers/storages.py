from functools import partial
import weakref

from django.core.cache import cache
import pybreaker

from core.decorators import handle_exc


def get_offline_cache_errors():
    if getattr(cache, '_lib', None) and cache._lib.__name__ == 'pylibmc':
        import pylibmc  # pragma: no cover
        return (  # pragma: no cover
            pylibmc.ConnectionError, pylibmc.UnixSocketError,
            pylibmc.ServerDown, pylibmc.ServerDead, pylibmc.NoServers,
        )
    return ()


class CircuitBreakerCacheStorage(pybreaker.CircuitBreakerStorage):
    """
    A cache-based storage for pybreaker. If cache retrieval fails (in the event
    of an infrastructure failure) the storage defaults to its provided
    fallback_state.
    """
    BASE_NAMESPACE = 'pybreaker'
    __NAMESPACES = weakref.WeakValueDictionary()

    def __init__(self, namespace, fallback_state=pybreaker.STATE_CLOSED):
        """
        Creates a new instance with the given `namespace` and an optional
        `fallback_state` object. The namespace is used to identify the circuit
        breaker within the cache and therefore must be different from any other
        circuit breaker namespaces. If there are any connection issues with
        cache, the `fallback_circuit_state` is used to determine the state of
        the circuit.
        """
        assert namespace not in self.__NAMESPACES, (
            "Attempt to create circuit breaker for already-used namespace "
            "{!r}".format(namespace))
        self.__NAMESPACES[namespace] = self

        super(CircuitBreakerCacheStorage, self).__init__(namespace)
        self._namespace_name = namespace
        self._fallback_state = fallback_state

        # Helpers to handle down cache-backend
        self._handled_cache_errs = get_offline_cache_errors()
        self._down_cache_handler_partial = partial(
            handle_exc, *self._handled_cache_errs)

    @property
    def _safe_cache_set(self):
        """ cache.set that silently handles down cache """
        return self._down_cache_handler_partial()(cache.set)

    @property
    def _safe_cache_get(self):
        """ cache.get that silently handles down cache """
        return self._down_cache_handler_partial()(cache.get)

    @property
    def _safe_cache_incr(self):
        """ cache.incr that silently handles down cache """
        return self._down_cache_handler_partial()(cache.incr)

    @property
    def namespace(self):
        return '{}:{}'.format(self.BASE_NAMESPACE, self._namespace_name)

    @property
    def _state_namespace(self):
        return '{}:state'.format(self.namespace)

    @property
    def _counter_namespace(self):
        return '{}:counter'.format(self.namespace)

    @property
    def _opened_at_namespace(self):
        return '{}:opened_at'.format(self.namespace)

    @property
    def state(self):
        down_cache_handler = self._down_cache_handler_partial(
            fallback=self._fallback_state)
        safe_cache_get = down_cache_handler(cache.get)
        return safe_cache_get(self._state_namespace, self._fallback_state)

    @state.setter
    def state(self, state):
        self._safe_cache_set(self._state_namespace, state)

    def increment_counter(self):
        namespace = self._counter_namespace
        try:
            return self._safe_cache_incr(namespace)
        except ValueError:
            # No counter at specified namespace, make counter starting at 1
            return self._safe_cache_set(namespace, 1)

    def reset_counter(self):
        return self._safe_cache_set(self._counter_namespace, 0)

    @property
    def counter(self):
        return self._safe_cache_get(self._counter_namespace, 0)

    @property
    def opened_at(self):
        return self._safe_cache_get(self._opened_at_namespace)

    @opened_at.setter
    def opened_at(self, datetime):
        return self._safe_cache_set(self._opened_at_namespace, datetime)
