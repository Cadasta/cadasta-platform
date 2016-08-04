from django.conf import settings
from django.test import TestCase

from tutelary.models import Policy

from core.tests.utils.cases import UserTestCase
from accounts.tests.factories import UserFactory
from geography import load as load_countries
from .factories import OrganizationFactory, ProjectFactory
from ..models import OrganizationRole, ProjectRole

PERMISSIONS_DIR = settings.BASE_DIR + '/permissions/'


class OrganizationTest(TestCase):
    def test_str(self):
        org = OrganizationFactory.create(name='Org')
        assert str(org) == '<Organization: Org>'

    def test_repr(self):
        org = OrganizationFactory.create(name='Org')
        assert repr(org) == '<Organization: Org>'

    def test_has_random_id(self):
        org = OrganizationFactory.create()
        assert type(org.id) is not int


class OrganizationRoleTest(UserTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.oa_policy = Policy.objects.get(name='org-admin')
        self.user = UserFactory.create()
        self.org = OrganizationFactory.create(add_users=[self.user])
        self.no_user_org = OrganizationFactory.create()

    def _get_role(self):
        return OrganizationRole.objects.get(organization=self.org,
                                            user=self.user)

    def _admin_role(self, before, assign, after):
        assert self.user.has_perm('org.update', self.org) is before
        role = self._get_role()
        role.admin = assign
        role.save()
        assert self.user.has_perm('org.update', self.org) is after

    def test_assign_new_admin(self):
        OrganizationRole.objects.create(
            organization=self.no_user_org, user=self.user, admin=True)
        assert self.user.has_perm('org.update', self.no_user_org) is True

    def test_keep_admin_role(self):
        self.user.assign_policies((self.oa_policy,
                                   {'organization': self.org.slug}))
        self._admin_role(True, True, True)

    def test_keep_non_admin_role(self):
        self._admin_role(False, False, False)

    def test_add_admin_role(self):
        self._admin_role(False, True, True)

    def test_remove_admin_role(self):
        self.user.assign_policies((self.oa_policy,
                                   {'organization': self.org.slug}))
        self._admin_role(True, False, False)

    def test_delete_project_roles(self):
        ProjectFactory.create_batch(2, add_users=[self.user],
                                    organization=self.org)
        ProjectFactory.create_batch(2, add_users=[self.user])
        assert ProjectRole.objects.filter(user=self.user).count() == 4

        role = self._get_role()
        role.delete()
        assert ProjectRole.objects.filter(user=self.user).count() == 2


class ProjectTest(TestCase):
    def test_str(self):
        project = ProjectFactory.create(name='Project')
        assert str(project) == '<Project: Project>'

    def test_repr(self):
        project = ProjectFactory.create(name='Project')
        assert repr(project) == '<Project: Project>'

    def test_has_random_id(self):
        project = ProjectFactory.create()
        assert type(project.id) is not int

    def test_country_assignment(self):
        load_countries.run()
        project = ProjectFactory.create(
            extent='SRID=4326;POLYGON(('
            '11.36667 47.25000, '
            '11.41667 47.25000, '
            '11.41667 47.28333, '
            '11.36667 47.28333, '
            '11.36667 47.25000))'
        )
        assert project.country == 'AT'

    def test_country_assignment_for_invalid_geometry(self):
        load_countries.run()
        project = ProjectFactory.create(
            extent='SRID=4326;POLYGON(('
            '0.00000 0.00000, '
            '0.00001 0.00000, '
            '0.00001 0.00001, '
            '0.00000 0.00001, '
            '0.00000 0.00000))'
        )
        assert project.country == ''

    def test_reassign_extent(self):
        project = ProjectFactory.create(
            extent='SRID=4326;POLYGON(('
            '211.36667 47.25000, '
            '211.41667 47.25000, '
            '211.41667 47.28333, '
            '211.36667 47.28333, '
            '211.36667 47.25000))'
        )
        assert project.extent.boundary.coords == (
            (-148.63333, 47.25), (-148.58333, 47.25), (-148.58333, 47.28333),
            (-148.63333, 47.28333), (-148.63333, 47.25))

    def test_defaults_to_public(self):
        project = ProjectFactory.create()
        assert project.public()

    def test_can_create_private(self):
        project = ProjectFactory.create(access='private')
        assert not project.public()

    def test_ui_class_name(self):
        project = ProjectFactory.create()
        assert project.ui_class_name == "Project"

    def test_ui_detail_url(self):
        project = ProjectFactory.create()
        assert project.ui_detail_url == (
            '/organizations/{org}/projects/{prj}/'.format(
                org=project.organization.slug,
                prj=project.slug))


class ProjectRoleTest(UserTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.project = ProjectFactory.create()
        self.user = UserFactory.create()

    def _has(self, action, state):
        assert self.user.has_perm(action, self.project) is state

    def _add_role(self, role):
        return ProjectRole.objects.create(
            project=self.project, user=self.user, role=role)

    def _change_role(self, action, before_role, before, after_role, after):
        role = self._add_role(before_role)
        self._has(action, before)
        role.role = after_role
        role.save()
        self._has(action, after)

    def _change_manager(self, action, role, before, manager, after):
        role = self._add_role(role)
        self._has(action, before)
        role.manager = manager
        role.save()
        self._has(action, after)

    def test_assign_new_manager(self):
        self._add_role('PM')
        self._has('project.edit', True)

    def test_add_manager_role(self):
        self._has('project.edit', False)
        self._add_role('PM')
        self._has('project.edit', True)

    def test_keep_manager_role(self):
        self._change_manager('project.edit', 'PM', True, True, True)

    def test_keep_non_manager_role(self):
        self._change_manager('project.edit', 'PU', False, False, False)

    def test_remove_manager_role(self):
        self._change_role('project.edit', 'PM', True, 'PU', False)

    def test_assign_new_collector(self):
        self._add_role('DC')
        self._has('resource.add', True)

    def test_add_collector_role(self):
        self._has('resource.add', False)
        self._add_role('DC')
        self._has('resource.add', True)

    def test_keep_collector_role(self):
        self._change_role('resource.add', 'DC', True, 'DC', True)

    def test_keep_non_collector_role(self):
        self._change_role('resource.add', 'PU', False, 'PU', False)

    def test_remove_collector_role(self):
        self._change_role('resource.add', 'DC', True, 'PU', False)
