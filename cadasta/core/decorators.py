from functools import wraps
import inspect
import logging


logger = logging.getLogger(__name__)


def handle_exc(*exceptions, fallback=None):
    """
    Decorator to catch, log, and suppress whitelisted exceptions. Optionally,
    will return fallback value if exception is caught.
    """
    msg = "{!r} not an instance of BaseException"
    for e in exceptions:
        try:
            assert inspect.isclass(e)
            assert issubclass(e, BaseException)
        except AssertionError:
            raise TypeError(msg.format(e))

    def wrapper(f):
        @wraps(f)
        def func(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except exceptions:
                logger.exception("Handling failure for %r", f.__name__)
                return fallback
        return func
    return wrapper
