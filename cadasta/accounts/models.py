from datetime import datetime, timezone, timedelta
from django.conf import settings
from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext as _
from django.contrib.auth.models import AbstractUser
from tutelary.models import Policy
from tutelary.decorators import permissioned_model

from .manager import UserManager


PERMISSIONS_DIR = settings.BASE_DIR + '/permissions/'


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
                     _("You don't have permission to view user details")}),
                   ('user.update',
                    {'error_message':
                     _("You don't have permission to update user details")})]


@receiver(models.signals.post_save, sender=User)
def assign_default_policy(sender, instance, **kwargs):
    try:
        policy = Policy.objects.get(name='default')
    except Policy.DoesNotExist:
        policy = Policy.objects.create(
            name='default',
            body=open(PERMISSIONS_DIR + 'default.json').read()
        )
    assigned_policies = instance.assigned_policies()
    if policy not in assigned_policies:
        assigned_policies.insert(0, policy)
    instance.assign_policies(*assigned_policies)
