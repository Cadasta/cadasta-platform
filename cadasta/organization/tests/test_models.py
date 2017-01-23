from django.conf import settings
from django.test import TestCase

from tutelary.models import Policy

from core.tests.utils.cases import UserTestCase
from accounts.tests.factories import UserFactory
from geography import load as load_countries
from spatial.tests.factories import SpatialUnitFactory
from .factories import OrganizationFactory, ProjectFactory
from ..models import OrganizationRole, ProjectRole

PERMISSIONS_DIR = settings.BASE_DIR + '/permissions/'


class OrganizationTest(TestCase):
    def test_str(self):
        org = OrganizationFactory.build(name='Org')
        assert str(org) == '<Organization: Org>'

    def test_repr(self):
        org = OrganizationFactory.build(id='abc123', name='Org', slug='slug',
                                        archived=True, access='public')
        assert repr(org) == ('<Organization id=abc123 name=Org'
                             ' slug=slug'
                             ' archived=True'
                             ' access=public>')

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

    def test_repr(self):
        user = UserFactory.build(username='john')
        org = OrganizationFactory.build(slug='org')
        role = OrganizationRole(id='abc123', user=user, organization=org,
                                admin=True)
        assert repr(role) == ('<OrganizationRole id=abc123 user=john'
                              ' organization=org admin=True>')

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

    def test_delete_org_role(self):
        ProjectFactory.create_batch(2, add_users=[self.user],
                                    organization=self.org)
        ProjectFactory.create_batch(2, add_users=[self.user])
        assert ProjectRole.objects.filter(user=self.user).count() == 4

        role = self._get_role()
        role.delete()
        assert ProjectRole.objects.filter(user=self.user).count() == 2

    def test_delete_admin_role(self):
        role = self._get_role()
        role.admin = True
        role.save()
        assert self.user.has_perm('org.update', self.org) is True

        role.delete()
        assert self.user.has_perm('org.update', self.org) is False


class ProjectTest(TestCase):
    def test_str(self):
        project = ProjectFactory.create(name='Project')
        assert str(project) == '<Project: Project>'

    def test_repr(self):
        prj = ProjectFactory.build(id='abc123', name='PRJ', slug='prj',
                                   archived=True, access='public')
        assert repr(prj) == ('<Project id=abc123 name=PRJ'
                             ' slug=prj'
                             ' organization={}'
                             ' archived=True'
                             ' access=public>').format(prj.organization.slug)

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

    def test_has_records(self):
        project = ProjectFactory.create()
        assert project.has_records is False

        project = ProjectFactory.create()
        SpatialUnitFactory.create(project=project)
        assert project.has_records is True


class ProjectRoleTest(UserTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.project = ProjectFactory.create()
        self.user = UserFactory.create()
        v = {
            'organization': self.project.organization.slug,
            'project': self.project.slug
        }
        self.roles = {
            'PM': (Policy.objects.get(name='project-manager'), v),
            'DC': (Policy.objects.get(name='data-collector'), v),
            'PU': (Policy.objects.get(name='project-user'), v)
        }

    def test_repr(self):
        user = UserFactory.build(username='john')
        project = ProjectFactory.build(slug='prj')
        role = ProjectRole(id='abc123', user=user, project=project, role='DC')
        assert repr(role) == ('<ProjectRole id=abc123 user=john project=prj '
                              'role=DC>')

    def _has(self, role, state=True):
        assert (self.roles[role] in self.user.assigned_policies()) is state

    def _add_role(self, role):
        return ProjectRole.objects.create(
            project=self.project, user=self.user, role=role)

    def _change_role(self, before_role, after_role):
        role = self._add_role(before_role)
        self._has(before_role)
        role.role = after_role
        role.save()
        self._has(after_role)
        if before_role != after_role:
            self._has(before_role, state=False)

    def test_assign_new_manager(self):
        self._add_role('PM')
        self._has('PM')

    def test_add_manager_role(self):
        self._has('PM', state=False)
        self._add_role('PM')
        self._has('PM', state=True)

    def test_keep_manager_role(self):
        self._change_role('PM', 'PM')

    def test_keep_non_manager_role(self):
        self._change_role('PU', 'PU')

    def test_remove_manager_role(self):
        self._change_role('PM', 'PU')

    def test_assign_new_collector(self):
        self._add_role('DC')
        self._has('DC')

    def test_add_collector_role(self):
        self._has('DC', state=False)
        self._add_role('DC')
        self._has('DC', state=True)

    def test_keep_collector_role(self):
        self._change_role('DC', 'DC')

    def test_keep_non_collector_role(self):
        self._change_role('PU', 'PU')

    def test_remove_collector_role(self):
        self._change_role('DC', 'PU')

    def test_delete_manager_role(self):
        self._add_role('PM')
        self._has('PM', state=True)
        ProjectRole.objects.get(project=self.project, user=self.user).delete()
        self._has('PM', state=False)

    def test_delete_collector_role(self):
        self._add_role('DC')
        self._has('DC', state=True)
        ProjectRole.objects.get(project=self.project, user=self.user).delete()
        self._has('DC', state=False)

    def test_delete_user_role(self):
        self._add_role('PU')
        self._has('PU', state=True)
        ProjectRole.objects.get(project=self.project, user=self.user).delete()
        self._has('PU', state=False)
