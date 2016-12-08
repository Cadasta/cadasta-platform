from core.tests.factories import PolicyFactory
from tutelary.models import PermissionSet, Role, Policy
from django.test import TestCase
from .. import load

policies = ['default', 'superuser', 'org-admin', 'org-member',
            'project-manager', 'data-collector', 'project-user']


class LoadTest(TestCase):
    def test_load_create(self):
        assert PermissionSet.objects.exists() is False
        assert Role.objects.exists() is False
        assert Policy.objects.exists() is False

        load.run()

        for pol in policies:
            assert Policy.objects.get(name=pol)

    def test_load(self):
        PolicyFactory.load_policies()
        existing_pols = {p: Policy.objects.get(name=p) for p in policies}

        load.run()

        for pol in policies:
            assert Policy.objects.get(name=pol) == existing_pols[pol]

    def test_load_force(self):
        PolicyFactory.load_policies()
        existing_pols = {p: Policy.objects.get(name=p) for p in policies}

        load.run(force=True)

        for pol in policies:
            assert Policy.objects.get(name=pol) != existing_pols[pol]
