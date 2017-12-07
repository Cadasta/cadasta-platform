from functools import wraps
import logging


class HandledErrors(type):
    """
    Metaclass to suppress and log white-listed exceptions within the
    methods specified in the implementing class' HANDLED_ERRORS
    property. Rather than raising the error, an exception will be logged
    in the implementing class' module logger.

    HANDLED_ERRORS is expected to be a an iterable of tuples containing
    the method name to which the handling should be applied and an
    exception or tuple of exceptions that should caught and logged
    within the method.
    """

    def __init__(cls, name, bases, namespace, **kwargs):
        super(HandledErrors, cls).__init__(name, bases, namespace)

        METHOD_KEY = 'HANDLED_ERRORS'
        assert hasattr(cls, METHOD_KEY), (
            "Missing {!r} property, HandledErrors not correctly "
            "implemented".format(METHOD_KEY)
        )

        def safe_func(f, handled_exceptions):
            @wraps(f)
            def wrapper(*args, **kwds):
                try:
                    return f(*args, **kwds)
                except handled_exceptions:
                    logging.getLogger(cls.__module__).exception(
                        "Silenced cache failure at {}.{}.{}()"
                        "".format(cls.__module__, name, f.__name__))
            return wrapper

        try:
            for (method, errors) in getattr(cls, METHOD_KEY, []):
                setattr(cls, method, safe_func(getattr(cls, method), errors))
        except (ValueError, AttributeError):
            raise ValueError(
                "Failed to implement class {!r} with metaclass "
                "'HandledErrors'".format(name))
