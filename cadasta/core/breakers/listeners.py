import logging

import pybreaker


logger = logging.getLogger(__name__)


class LogListener(pybreaker.CircuitBreakerListener):
    """ Listener used to log circuit breaker events. """

    def state_change(self, cb, old_state, new_state):
        was_closed = old_state.name == pybreaker.STATE_CLOSED
        now_open = new_state.name == pybreaker.STATE_OPEN
        level = "error" if was_closed and now_open else "info"
        getattr(logger, level)(
            "Changed %r breaker state from %r to %r",
            cb._state_storage.name, old_state.name, new_state.name)

    def failure(self, cb, exc):
        logger.exception("Failed call on circuit breaker %r",
                         cb._state_storage.name)

    def success(self, cb):
        logger.debug("Successful call on circuit breaker %r",
                     cb._state_storage.name)
