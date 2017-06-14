from django.contrib.auth.models import Group


class AnonymousUserRole(object):

    def __init__(self):
        try:
            self._group = Group.objects.get(name='AnonymousUser')
        except Group.DoesNotExist:
            pass

    @property
    def permissions(self):
        if hasattr(self, '_group'):
            return [perm.codename for perm in self._group.permissions.all()]
        else:
            return []


class SuperUserRole(object):

    def __init__(self):
        try:
            self._group = Group.objects.get(name='SuperUser')
        except Group.DoesNotExist:
            pass

    @property
    def permissions(self):
        if hasattr(self, '_group'):
            return [perm.codename for perm in self._group.permissions.all()]
        else:
            return []
