from datetime import datetime, timezone, timedelta
import os
from django.conf import settings
from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext as _
import django.contrib.auth.models as auth
import django.contrib.auth.base_user as auth_base
from tutelary.models import Policy
from tutelary.decorators import permissioned_model

from resources.utils import io, thumbnail
from buckets.fields import S3FileField
from simple_history.models import HistoricalRecords
from .manager import UserManager
from .validators import ACCEPTED_TYPES

PERMISSIONS_DIR = settings.BASE_DIR + '/permissions/'


def now_plus_48_hours():
    return datetime.now(tz=timezone.utc) + timedelta(hours=48)


def abstract_user_field(name):
    for f in auth.AbstractUser._meta.fields:
        if f.name == name:
            return f


def create_thumbnails(instance, created):
    if created or instance._original_url != instance.file.url:
        if instance.file.url.split('.')[-1] in ['jpg', 'jpeg', 'gif']:
            io.ensure_dirs()
            file_name = instance.file.url.split('/')[-1]
            name = file_name[:file_name.rfind('.')]
            ext = file_name.split('.')[-1]
            write_path = os.path.join(settings.MEDIA_ROOT,
                                      'temp',
                                      name + '-128x128.' + ext)

            size = 128, 128

            file = instance.file.open()
            thumb = thumbnail.make(file, size)
            thumb.save(write_path)
            if instance.file.field.upload_to:
                name = instance.file.field.upload_to + '/' + name
            instance.file.storage.save(name + '-128x128.' + ext,
                                       open(write_path, 'rb').read())


@permissioned_model
class User(auth_base.AbstractBaseUser, auth.PermissionsMixin):
    username = abstract_user_field('username')
    full_name = models.CharField(_('full name'), max_length=130, blank=True)
    email = abstract_user_field('email')
    is_staff = abstract_user_field('is_staff')
    is_active = abstract_user_field('is_active')
    date_joined = abstract_user_field('date_joined')
    email_verified = models.BooleanField(default=False)
    verify_email_by = models.DateTimeField(default=now_plus_48_hours)
    change_pw = models.BooleanField(default=True)
    file = S3FileField(blank=True, upload_to='users',
                       accepted_types=ACCEPTED_TYPES)

    objects = UserManager()

    history = HistoricalRecords()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'full_name']

    class Meta:
        ordering = ('username',)
        verbose_name = _('user')
        verbose_name_plural = _('users')

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_url = self.file.url

    def __repr__(self):
        repr_string = ('<User username={obj.username}'
                       ' full_name={obj.full_name}'
                       ' email={obj.email}'
                       ' file={obj.file.url}'
                       ' email_verified={obj.email_verified}'
                       ' verify_email_by={obj.verify_email_by}>')
        return repr_string.format(obj=self)

    @property
    def file_name(self):
        if not hasattr(self, '_file_name'):
            self._file_name = self.file.url.split('/')[-1]

        return self._file_name

    @property
    def file_type(self):
        return self.file_name.split('.')[-1]

    @property
    def thumbnail(self):
        if not hasattr(self, '_thumbnail'):
            if self.file_type in ['jpg', 'jpeg', 'gif']:
                ext = self.file_name.split('.')[-1]
                base_url = self.file.url[:self.file.url.rfind('.')]
                self._thumbnail = base_url + '-128x128.' + ext
            else:
                self._thumbnail = ''

        return self._thumbnail

    def get_display_name(self):
        """
        Returns the display name.
        If full name is present then return full name as display name
        else return username.
        """
        if self.full_name != '':
            return self.full_name
        else:
            return self.username

    def save(self, *args, **kwargs):
        create_thumbnails(self, (not self.id))
        super().save(*args, **kwargs)


@receiver(models.signals.post_save, sender=User)
def assign_default_policy(sender, instance, **kwargs):
    policy = Policy.objects.get(name='default')
    assigned_policies = instance.assigned_policies()
    if policy not in assigned_policies:
        assigned_policies.insert(0, policy)
    instance.assign_policies(*assigned_policies)
