from django.contrib.auth.models import Group
from django.utils.functional import cached_property


class UserRole(object):

    @cached_property
    def permissions(self):
        if hasattr(self, '_group'):
            return self._group.permissions.values_list('codename', flat=True)
        else:
            return []


class PublicUserRole(UserRole):

    def __init__(self):
        try:
            self._group = Group.objects.get(name='PublicUser')
        except Group.DoesNotExist:
            pass


class AnonymousUserRole(UserRole):

    def __init__(self):
        try:
            self._group = Group.objects.get(name='AnonymousUser')
        except Group.DoesNotExist:
            pass
