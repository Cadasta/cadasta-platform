from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase

from core.tests.utils.cases import UserTestCase
from accounts.tests.factories import UserFactory
from geography import load as load_countries
from spatial.tests.factories import SpatialUnitFactory
from .factories import OrganizationFactory, ProjectFactory
from ..models import OrganizationRole, ProjectRole, ROLE_GROUPS


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
        self.user = UserFactory.create()
        self.org = OrganizationFactory.create(add_users=[self.user])
        self.no_user_org = OrganizationFactory.create()

    def test_repr(self):
        user = UserFactory.build(username='john')
        org = OrganizationFactory.build(slug='org')
        group = Group.objects.get(name='OrgAdmin')
        role = OrganizationRole(id='abc123', user=user, organization=org,
                                group=group)
        assert repr(role) == ('<OrganizationRole id=abc123 user=john'
                              ' organization=org group=OrgAdmin admin=True>')

    def _get_role(self):
        return OrganizationRole.objects.get(organization=self.org,
                                            user=self.user)

    def test_assign_new_admin(self):
        user = UserFactory.create(username='john')
        group = Group.objects.get(name='OrgAdmin')
        role = OrganizationRole.objects.create(
            organization=self.no_user_org, user=user,
            group=group)
        assert 'org.update' in role.permissions

    def test_add_org_member(self):
        user = UserFactory.create(username='john')
        group = Group.objects.get(name='OrgMember')
        role = OrganizationRole.objects.create(
            organization=self.no_user_org, user=user, group=group)
        assert 'org.update' not in role.permissions
        assert not role.admin

    def test_remove_admin_role(self):
        user = UserFactory.create(username='john')
        group = Group.objects.get(name='OrgAdmin')
        role = OrganizationRole.objects.create(
            organization=self.no_user_org, user=user,
            group=group)
        assert 'org.update' in role.permissions
        role.delete()
        assert user.organizationrole_set.count() == 0

    def test_delete_org_role(self):
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

    def test_get_absolute_url(self):
        project = ProjectFactory.create()
        assert project.get_absolute_url() == (
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
        group = Group.objects.get(name="ProjectMember")
        self.project_role = ProjectRole.objects.create(
            project=self.project, user=self.user, group=group, role='PU')

    def test_repr(self):
        group = Group.objects.get(name="DataCollector")
        user = UserFactory.build(username='john')
        project = ProjectFactory.build(slug='prj')
        role = ProjectRole(id='abc123', user=user, project=project,
                           group=group, role='DC')
        assert repr(role) == ('<ProjectRole id=abc123 user=john project=prj '
                              'group=DataCollector role=DC>')

    def _has(self, role, state=True):
        try:
            self.project_role.refresh_from_db()
        except ProjectRole.DoesNotExist:
            assert state is False
        else:
            assert (self.project_role.role == role) == state

    def _set_role(self, role):
        group = Group.objects.get(name=ROLE_GROUPS.get(role, 'ProjectMember'))
        self.project_role.group = group
        self.project_role.role = role
        self.project_role.save()
        self.project_role.refresh_from_db()

    def _change_role(self, before_role, after_role):
        self._set_role(before_role)
        self._has(before_role)
        self._set_role(after_role)
        self._has(after_role)
        if before_role != after_role:
            self._has(before_role, state=False)

    def test_assign_new_manager(self):
        self._set_role('PM')
        self._has('PM')

    def test_add_manager_role(self):
        self._has('PM', state=False)
        self._set_role('PM')
        self._has('PM', state=True)

    def test_keep_manager_role(self):
        self._change_role('PM', 'PM')

    def test_keep_non_manager_role(self):
        self._change_role('PU', 'PU')

    def test_remove_manager_role(self):
        self._change_role('PM', 'PU')

    def test_assign_new_collector(self):
        self._has('DC', state=False)
        self._set_role('DC')
        self._has('DC')

    def test_add_collector_role(self):
        self._has('DC', state=False)
        self._set_role('DC')
        self._has('DC')

    def test_keep_collector_role(self):
        self._change_role('DC', 'DC')

    def test_keep_non_collector_role(self):
        self._change_role('PU', 'PU')

    def test_remove_collector_role(self):
        self._change_role('DC', 'PU')

    def test_delete_manager_role(self):
        self._set_role('PM')
        self._has('PM', state=True)
        ProjectRole.objects.filter(
            project=self.project, user=self.user).delete()
        self._has('PM', state=False)

    def test_delete_collector_role(self):
        self._set_role('DC')
        self._has('DC', state=True)
        ProjectRole.objects.filter(
            project=self.project, user=self.user).delete()
        self._has('DC', state=False)

    def test_delete_user_role(self):
        self._set_role('PU')
        self._has('PU', state=True)
        ProjectRole.objects.filter(
            project=self.project, user=self.user).delete()
        self._has('PU', state=False)
