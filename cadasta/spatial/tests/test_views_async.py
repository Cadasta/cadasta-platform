import json

from django.test import TestCase

from tutelary.models import Policy, assign_user_policies
from rest_framework.exceptions import PermissionDenied
from skivvy import APITestCase

from core.tests.utils.cases import UserTestCase
from accounts.tests.factories import UserFactory
from organization.tests.factories import ProjectFactory
from organization.models import OrganizationRole
from ..views import async
from .factories import SpatialUnitFactory


def assign_policies(user):
    clauses = {
        'clause': [
            {
                "effect": "allow",
                "object": ["*"],
                "action": ["org.*"]
            }, {
                'effect': 'allow',
                'object': ['organization/*'],
                'action': ['org.*', "org.*.*"]
            }, {
                'effect': 'allow',
                'object': ['project/*/*'],
                'action': ['project.*', 'project.*.*', 'spatial.*']
            }, {
                'effect': 'allow',
                'object': ['spatial/*/*/*'],
                'action': ['spatial.*', 'spatial.resources.*']
            }
        ]
    }
    policy = Policy.objects.create(
        name='test-policy',
        body=json.dumps(clauses))
    assign_user_policies(user, policy)


class SpatialUnitListAPITest(APITestCase, UserTestCase, TestCase):
    view_class = async.SpatialUnitList

    def setup_models(self):
        self.user = UserFactory.create()
        assign_policies(self.user)
        self.prj = ProjectFactory.create(slug='test-project', access='public')

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug
        }

    def test_full_list(self):
        SpatialUnitFactory.create_batch(2, project=self.prj)
        extra_record = SpatialUnitFactory.create()
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert len(response.content['features']) == 2
        assert extra_record.id not in (
            [u['id'] for u in response.content['features']])

    def test_exclude(self):
        SpatialUnitFactory.create_batch(2, project=self.prj)
        excluded = SpatialUnitFactory.create(project=self.prj)

        response = self.request(user=self.user,
                                get_data={'exclude': excluded.id})
        assert response.status_code == 200
        assert len(response.content['features']) == 2
        assert excluded.id not in (
            [u['id'] for u in response.content['features']])

    def test_pagination_page_1(self):
        SpatialUnitFactory.create_batch(1010, project=self.prj)

        response = self.request(user=self.user, get_data={'page': '1'})
        assert response.status_code == 200
        assert response.content['count'] == 1010
        assert '?page=2' in response.content['next']
        assert response.content['previous'] is None
        assert len(response.content['features']) == 1000

    def test_pagination_page_2(self):
        SpatialUnitFactory.create_batch(1010, project=self.prj)

        response = self.request(user=self.user, get_data={'page': '2'})
        assert response.status_code == 200
        assert len(response.content['features']) == 10
        assert response.content['count'] == 1010
        assert response.content['next'] is None

    def test_full_list_with_unauthorized_user(self):
        SpatialUnitFactory.create_batch(2, project=self.prj)
        extra_record = SpatialUnitFactory.create()

        response = self.request()
        assert response.status_code == 200
        assert len(response.content['features']) == 2
        assert extra_record.id not in (
            [u['id'] for u in response.content['features']])

    def test_get_full_list_organization_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'organization': 'some-org'})
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."

    def test_get_full_list_project_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'project': 'some-prj'})
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."

    def test_list_private_record(self):
        self.prj.access = 'private'
        self.prj.save()

        SpatialUnitFactory.create_batch(2, project=self.prj)
        extra_record = SpatialUnitFactory.create()
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert len(response.content['features']) == 2
        assert extra_record.id not in (
            [u['id'] for u in response.content['features']])

    def test_list_private_record_with_unauthorized_user(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request()
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_list_private_records_without_permission(self):
        self.prj.access = 'private'
        self.prj.save()

        restricted_clauses = {
            'clause': [
                {
                    'effect': 'allow',
                    'object': ['project.list'],
                    'action': ['organization/*']
                },
                {
                    'effect': 'allow',
                    'object': ['project.view'],
                    'action': ['project/*/*']
                }
            ]
        }
        restricted_policy = Policy.objects.create(
            name='restricted',
            body=json.dumps(restricted_clauses))
        assign_user_policies(self.user, restricted_policy)

        response = self.request(user=self.user)
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_list_private_records_based_on_org_membership(self):
        SpatialUnitFactory.create(project=self.prj)
        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.prj.organization,
                                        user=user)
        response = self.request(user=user)
        assert response.status_code == 200

    def test_archived_filter_with_unauthorized_user(self):
        SpatialUnitFactory.create(project=self.prj, type='AP')
        SpatialUnitFactory.create(project=self.prj, type='BU')
        SpatialUnitFactory.create(project=self.prj, type='RW')
        self.prj.archived = True
        self.prj.save()

        response = self.request()
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_archived_filter_with_org_admin(self):
        SpatialUnitFactory.create(project=self.prj, type='AP')
        SpatialUnitFactory.create(project=self.prj, type='BU')
        SpatialUnitFactory.create(project=self.prj, type='RW')
        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.prj.organization,
                                        user=user, admin=True)

        self.prj.archived = True
        self.prj.save()
        response = self.request(user=user)
        assert response.status_code == 200
