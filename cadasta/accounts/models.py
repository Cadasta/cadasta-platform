import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser
from tutelary.decorators import permissioned_model


def now_plus_48_hours():
    return datetime.datetime.now() + datetime.timedelta(hours=48)


@permissioned_model
class User(AbstractUser):
    email_verified = models.BooleanField(default=False)
    verify_email_by = models.DateTimeField(default=now_plus_48_hours)

    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    class TutelaryMeta:
        perm_type = 'user'
        path_fields = ('username',)
        actions = [('user.view', {'permissions_object': None}),
                   'user.update']
