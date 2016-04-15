from django.conf import settings
from django.test import TestCase

from tutelary.models import Policy

from accounts.tests.factories import UserFactory
from .factories import OrganizationFactory, ProjectFactory
from ..models import OrganizationRole, ProjectRole

PERMISSIONS_DIR = settings.BASE_DIR + '/permissions/'


class OrganizationTest(TestCase):
    def test_str(self):
        org = OrganizationFactory.create(**{'name': 'Org'})
        assert str(org) == '<Organization: Org>'

    def test_has_random_id(self):
        org = OrganizationFactory.create()
        assert type(org.id) is not int


class OrganizationRoleTest(TestCase):
    def setUp(self):
        self.oa_policy = Policy.objects.create(
            name='org-admin',
            body=open(PERMISSIONS_DIR + 'org-admin.json').read()
        )
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
                                    **{'organization': self.org})
        ProjectFactory.create_batch(2, add_users=[self.user])
        assert ProjectRole.objects.filter(user=self.user).count() == 4

        role = self._get_role()
        role.delete()
        assert ProjectRole.objects.filter(user=self.user).count() == 2


class ProjectTest(TestCase):
    def test_str(self):
        project = ProjectFactory.create(**{'name': 'Project'})
        assert str(project) == '<Project: Project>'

    def test_has_random_id(self):
        project = ProjectFactory.create()
        assert type(project.id) is not int


class ProjectRoleTest(TestCase):
    def setUp(self):
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
        self._has('project.resources.add', True)

    def test_add_collector_role(self):
        self._has('project.resources.add', False)
        self._add_role('DC')
        self._has('project.resources.add', True)

    def test_keep_collector_role(self):
        self._change_role('project.resources.add', 'DC', True, 'DC', True)

    def test_keep_non_collector_role(self):
        self._change_role('project.resources.add', 'PU', False, 'PU', False)

    def test_remove_collector_role(self):
        self._change_role('project.resources.add', 'DC', True, 'PU', False)
