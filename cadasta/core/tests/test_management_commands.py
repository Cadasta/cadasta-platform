from django.test import TestCase
from django.contrib.sites.models import Site

from core.tests.factories import PolicyFactory
from ..fixtures import FixturesData
from tutelary.models import Policy
from accounts.models import User
from organization.models import Organization, Project
from spatial.models import SpatialUnit, SpatialRelationship
from core.management.commands import loadsite
from jsonattrs.models import create_attribute_types
from party.models import load_tenure_relationship_types


class FixturesTest(TestCase):
    def test_fixture_setup(self):
        data = FixturesData()
        data.delete_test_users()
        data.delete_test_organizations()
        data.delete_test_projects()
        data.add_test_organizations()
        PolicyFactory.load_policies()
        create_attribute_types()
        load_tenure_relationship_types()
        data.add_test_users_and_roles()
        data.add_test_projects()
        data.add_test_spatial_units()
        data.add_huge_project()

        assert User.objects.count() == 20
        assert Policy.objects.count() == 7
        assert Organization.objects.count() == 2
        assert Project.objects.count() == 9
        assert SpatialUnit.objects.count() == 4007
        assert SpatialRelationship.objects.count() == 2

        data.delete_test_users()
        data.delete_test_organizations()
        data.delete_test_projects()

        assert User.objects.count() == 0
        assert Organization.objects.count() == 0
        assert Project.objects.count() == 0
        assert SpatialUnit.objects.count() == 0
        assert SpatialRelationship.objects.count() == 0


class LoadSiteTest(TestCase):
    def test_default_site_replacement(self):
        assert Site.objects.filter(name='example.com').exists()
        loadsite.Command().handle()
        assert len(Site.objects.all()) == 1
        assert Site.objects.filter(name='Cadasta').exists()
        loadsite.Command().handle()
        assert len(Site.objects.all()) == 1
