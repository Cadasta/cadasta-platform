import json
from django.test import TestCase
from django.contrib.auth.models import Permission
from ..management.commands import loadpermissions

PERMISSIONS = []
for app in loadpermissions.PERMISSIONED_APPS:
    perm_file = open(loadpermissions.PERMISSIONS_DIR + app + '.json')

    models = json.loads(perm_file.read())
    PERMISSIONS += [p['codename'] for m in models for p in m['permissions']]

    perm_file.close()


class LoadpermissionsTest(TestCase):
    def test_create_permissions(self):
        loadpermissions.create_permissions()

        stored = Permission.objects.all().values_list('codename', flat=True)
        assert all(p in stored for p in PERMISSIONS)

    def test_update_permissions(self):
        loadpermissions.create_permissions()
        existing_perms = {p: Permission.objects.get(codename=p)
                          for p in PERMISSIONS}

        loadpermissions.create_permissions(force=False)

        stored = Permission.objects.all().values_list('codename', flat=True)
        assert all(p in stored for p in PERMISSIONS)
        assert all(Permission.objects.get(codename=p) == existing_perms[p]
                   for p in PERMISSIONS)

    def test_update_permissions_force(self):
        loadpermissions.create_permissions()
        existing_perms = {p: Permission.objects.get(codename=p)
                          for p in PERMISSIONS}

        loadpermissions.create_permissions(force=True)

        stored = Permission.objects.all().values_list('codename', flat=True)
        assert all(p in stored for p in PERMISSIONS)
        assert all(Permission.objects.get(codename=p) != existing_perms[p]
                   for p in PERMISSIONS)
