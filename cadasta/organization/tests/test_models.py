from django.conf import settings
from django.test import TestCase

from tutelary.models import Policy, Role

from accounts.tests.factories import UserFactory
from .factories import OrganizationFactory, ProjectFactory
from ..models import OrganizationRole

PERMISSIONS_DIR = settings.BASE_DIR + '/permissions/'


class OrganizationTest(TestCase):
    def test_str(self):
        org = OrganizationFactory.create(**{'name': 'Org'})
        assert str(org) == '<Organization: Org>'

    def test_has_random_id(self):
        org = OrganizationFactory.create()
        assert type(org.id) is not int


class OrganizationRoleTest(TestCase):
    def test_assign_new_admin(self):
        org = OrganizationFactory.create()
        user = UserFactory.create()

        policy = Policy.objects.create(
            name='org-admin',
            body=open(PERMISSIONS_DIR + 'org-admin.json').read()
        )
        # org_admin = Role.objects.create(
        #     name='org-admin',
        #     policies=[policy],
        #     variables={'organization': org.slug}
        # )

        OrganizationRole.objects.create(
            organization=org, user=user, admin=True)
        assert user.has_perm('org.update', org) is True


class ProjectTest(TestCase):
    def test_str(self):
        project = ProjectFactory.create(**{'name': 'Project'})
        assert str(project) == '<Project: Project>'

    def test_has_random_id(self):
        project = ProjectFactory.create()
        assert type(project.id) is not int
