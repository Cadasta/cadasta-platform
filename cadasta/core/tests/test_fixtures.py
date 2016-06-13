from django.test import TestCase

from core.tests.factories import PolicyFactory
from ..fixtures import FixturesData
from tutelary.models import Policy
from accounts.models import User
from organization.models import Organization, Project
from spatial.models import SpatialUnit, SpatialRelationship


class FixturesTest(TestCase):
    def test_fixture_setup(self):
        data = FixturesData()
        data.delete_test_users()
        data.delete_test_organizations()
        data.delete_test_projects()
        data.add_test_organizations()
        PolicyFactory.load_policies()
        data.add_test_users_and_roles()
        data.add_test_projects()
        data.add_test_spatial_units()

        assert User.objects.count() == 20
        assert Policy.objects.count() == 7
        assert Organization.objects.count() == 2
        assert Project.objects.count() == 9
        assert SpatialUnit.objects.count() == 7
        assert SpatialRelationship.objects.count() == 2

        data.delete_test_users()
        data.delete_test_organizations()
        data.delete_test_projects()

        assert User.objects.count() == 0
        assert Organization.objects.count() == 0
        assert Project.objects.count() == 0
        assert SpatialUnit.objects.count() == 0
        assert SpatialRelationship.objects.count() == 0
