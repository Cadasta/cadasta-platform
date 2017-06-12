from ..permissions import load as load_permissions
from django.test import TestCase
from django.contrib.auth.models import Group, Permission


class LoadPermissionsTest(TestCase):
    def setUp(self):
        super().setUp()
        load_permissions()

    def test_permissions(self):
        permissions = Permission.objects.all()
        assert permissions.count() == 29

    def test_groups(self):
        groups = Group.objects.all()
        assert groups.count() == 5
