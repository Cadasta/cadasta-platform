import pybreaker

from .storages import CircuitBreakerCacheStorage as CacheStorage
from .listeners import LogListener


class CircuitBreaker(pybreaker.CircuitBreaker):
    def __init__(self, name, expected_errors=(), **kwargs):
        # Set defaults
        if 'state_storage' not in kwargs:
            kwargs['state_storage'] = CacheStorage(name)
        if 'listeners' not in kwargs:
            kwargs['listeners'] = [LogListener()]
        if 'exclude' not in kwargs:
            kwargs['exclude'] = [KeyboardInterrupt]

        # Convenience attribute to allow codebase to easily catch and
        # handle expected errors
        self.expected_errors = tuple(
            (pybreaker.CircuitBreakerError,) + tuple(expected_errors))
        super(CircuitBreaker, self).__init__(name=name, **kwargs)

    @property
    def is_open(self):
        return self.current_state == pybreaker.STATE_OPEN

    def __repr__(self):
        print(self.name)
        return "<{0.__class__.__name__}: {0.name}>".format(self)
