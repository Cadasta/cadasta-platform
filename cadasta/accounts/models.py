from datetime import datetime, timezone, timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser
from tutelary.decorators import permissioned_model

from .manager import UserManager


def now_plus_48_hours():
    return datetime.now(tz=timezone.utc) + timedelta(hours=48)


@permissioned_model
class User(AbstractUser):
    email_verified = models.BooleanField(default=False)
    verify_email_by = models.DateTimeField(default=now_plus_48_hours)

    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    objects = UserManager()

    class TutelaryMeta:
        perm_type = 'user'
        path_fields = ('username',)
        actions = [('user.list',
                    {'permissions_object': None,
                     'error_message':
                     "You don't have permission to view user details"}),
                   ('user.update',
                    {'error_message':
                     "You don't have permission to update user details"})]
