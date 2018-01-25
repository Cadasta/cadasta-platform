from tutelary.backends import Backend as TutelaryBackend
from django.contrib.auth.backends import ModelBackend
from django.core.cache.backends.memcached import PyLibMCCache
import pylibmc

from .types import HandledErrors


class Auth(TutelaryBackend, ModelBackend):
    pass


class MemorySafePyLibMCCache(PyLibMCCache, metaclass=HandledErrors):
    HANDLED_ERRORS = [
        ('add', pylibmc.TooBig),
        ('get_or_set', pylibmc.TooBig),
        ('incr', pylibmc.TooBig),
        ('incr_version', pylibmc.TooBig),
        ('set', pylibmc.TooBig),
        ('set_many', pylibmc.TooBig),
    ]

    def close(self):
        # The close method for the PyLibMCCache cache was overridden to be a
        # noop in Django 1.11+ (https://github.com/django/django/pull/7200) in
        # effort to prevent a performance issue from memcached connections
        # being closed after every connection. It is stated that libmemcached
        # manages connections on its own, making a need for Django to manage
        # connections obsolete. When we deployed the Django 1.11 upgrade
        # (release v1.14.1), connections to our cache instances began to swell
        # and eventually led to connection issues (the same issue that the
        # close() method originally intended to resolve,
        # https://code.djangoproject.com/ticket/5133). It is not known why our
        # system does not seem to be closing connections, hunches have pointed
        # to django-jsonattr and django-tutelary but nothing conclusive has
        # been determined.
        self._cache.disconnect_all()
