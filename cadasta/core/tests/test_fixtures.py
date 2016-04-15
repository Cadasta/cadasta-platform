from django.test import TestCase

from ..fixtures import FixturesData
from tutelary.models import Policy
from accounts.models import User
from organization.models import Organization, Project


class FixturesTest(TestCase):
    def test_fixture_setup(self):
        data = FixturesData()
        data.delete_test_users()
        data.delete_test_organizations()
        data.delete_test_projects()
        data.add_test_organizations()
        data.add_test_users_and_roles()
        data.add_test_projects()

        assert User.objects.count() == 20
        assert Policy.objects.count() == 6
        assert Organization.objects.count() == 2
        assert Project.objects.count() == 6

        data.delete_test_users()
        data.delete_test_organizations()
        data.delete_test_projects()

        assert User.objects.count() == 0
        assert Organization.objects.count() == 0
        assert Project.objects.count() == 0
