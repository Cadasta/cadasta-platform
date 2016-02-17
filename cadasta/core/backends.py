from tutelary.backends import Backend as TutelaryBackend
from django.contrib.auth.backends import ModelBackend


class Auth(TutelaryBackend, ModelBackend):
    pass
