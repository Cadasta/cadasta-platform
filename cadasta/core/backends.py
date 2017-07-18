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
