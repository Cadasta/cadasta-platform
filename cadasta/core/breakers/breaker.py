import pybreaker

from .storages import CircuitBreakerCacheStorage as CacheStorage
from .listeners import LogListener


class CircuitBreaker(pybreaker.CircuitBreaker):
    def __init__(self, name, expected_errors=(), **kwargs):
        # Set defaults
        kwargs['state_storage'] = (
            kwargs.get('state_storage') or CacheStorage(name))
        kwargs['listeners'] = (
            kwargs.get('listeners') or [LogListener()])
        kwargs['exclude'] = (
            kwargs.get('exclude') or [KeyboardInterrupt])

        self.name = name
        # Convenience attribute to allow codebase to easily catch and
        # handle expected errors
        self.expected_errors = tuple(
            (pybreaker.CircuitBreakerError,) + tuple(expected_errors))
        super(CircuitBreaker, self).__init__(**kwargs)

    @property
    def is_open(self):
        return self.current_state == pybreaker.STATE_OPEN

    def __repr__(self):
        return "<{0.__class__.__name__}: {0.name}>".format(self)
