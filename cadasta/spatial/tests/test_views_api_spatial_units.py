import json
from django.test import TestCase
from rest_framework.exceptions import PermissionDenied
from tutelary.models import Policy, assign_user_policies
from skivvy import APITestCase

from accounts.tests.factories import UserFactory
from core.tests.utils.cases import UserTestCase
from organization.tests.factories import ProjectFactory, clause
from organization.models import OrganizationRole
from .factories import SpatialUnitFactory
from ..models import SpatialUnit
from ..views import api


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
                'action': ['spatial.*']
            }
        ]
    }
    policy = Policy.objects.create(
        name='test-policy',
        body=json.dumps(clauses))
    assign_user_policies(user, policy)


class SpatialUnitListAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.SpatialUnitList

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
        assert len(response.content) == 2
        assert extra_record.id not in (
            [u['properties']['id'] for u in response.content['features']])

    def test_full_list_with_unauthorized_user(self):
        SpatialUnitFactory.create_batch(2, project=self.prj)
        extra_record = SpatialUnitFactory.create()

        response = self.request()
        assert response.status_code == 200
        assert len(response.content) == 2
        assert extra_record.id not in (
            [u['properties']['id'] for u in response.content['features']])

    def test_ordering(self):
        SpatialUnitFactory.create(project=self.prj, type='AP')
        SpatialUnitFactory.create(project=self.prj, type='BU')
        SpatialUnitFactory.create(project=self.prj, type='RW')

        response = self.request(user=self.user, get_data={'ordering': 'type'})
        assert response.status_code == 200
        assert len(response.content['features']) == 3
        names = [su['properties']['type'] for su in
                 response.content['features']]
        assert names == sorted(names)

    def test_reverse_ordering(self):
        SpatialUnitFactory.create(project=self.prj, type='AP')
        SpatialUnitFactory.create(project=self.prj, type='BU')
        SpatialUnitFactory.create(project=self.prj, type='RW')

        response = self.request(user=self.user, get_data={'ordering': '-type'})
        assert response.status_code == 200
        assert len(response.content['features']) == 3
        names = [su['properties']['type'] for su in
                 response.content['features']]
        assert names == sorted(names, reverse=True)

    def test_type_filter(self):
        SpatialUnitFactory.create(project=self.prj, type='AP')
        SpatialUnitFactory.create(project=self.prj, type='BU')
        SpatialUnitFactory.create(project=self.prj, type='RW')
        response = self.request(user=self.user, get_data={'type': 'RW'})
        assert response.status_code == 200
        assert len(response.content['features']) == 1

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
        assert len(response.content) == 2
        assert extra_record.id not in (
            [u['properties']['id'] for u in response.content['features']])

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


class SpatialUnitCreateAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.SpatialUnitList

    def setup_models(self):
        self.user = UserFactory.create()
        assign_policies(self.user)
        self.prj = ProjectFactory.create(slug='test-project', access='public')

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug
        }

    def setup_post_data(self):
        return {
            'properties': {
                'type': "AP"
            },
            'geometry': {
                'type': 'Point',
                'coordinates': [100, 0]
            }
        }

    def test_create_valid_record(self):
        response = self.request(user=self.user, method='POST')
        assert response.status_code == 201
        assert SpatialUnit.objects.count() == 1

    def test_create_record_with_nonexistent_org(self):
        response = self.request(user=self.user,
                                method='POST',
                                url_kwargs={'organization': 'evil-corp'})
        assert response.status_code == 404
        assert SpatialUnit.objects.count() == 0
        assert response.content['detail'] == "Project not found."

    def test_create_record_with_nonexistent_project(self):
        response = self.request(user=self.user,
                                method='POST',
                                url_kwargs={'project': 'world-domination'})
        assert response.status_code == 404
        assert SpatialUnit.objects.count() == 0
        assert response.content['detail'] == "Project not found."

    def test_create_record_with_unauthorized_user(self):
        response = self.request(method='POST')
        assert response.status_code == 403
        assert SpatialUnit.objects.count() == 0
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_create_private_record(self):
        self.prj.access = 'private'
        self.prj.save()
        response = self.request(user=self.user, method='POST')
        assert response.status_code == 201
        assert SpatialUnit.objects.count() == 1

    def test_create_private_record_with_unauthorized_user(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request(method='POST')
        assert response.status_code == 403
        assert SpatialUnit.objects.count() == 0
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_create_private_record_without_permission(self):
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

        response = self.request(user=self.user, method='POST')
        assert response.status_code == 403
        assert SpatialUnit.objects.count() == 0
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_create_private_record_based_on_org_membership(self):
        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.prj.organization,
                                        user=user)
        response = self.request(user=user, method='POST')
        assert response.status_code == 403
        assert SpatialUnit.objects.count() == 0
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_create_invalid_spatial_unit(self):
        invalid_data = {
            'properties': {
                'type': ""
            },
            'geometry': {
                'type': 'Point',
                'coordinates': [100, 0]
            }
        }
        response = self.request(user=self.user,
                                method='POST',
                                post_data=invalid_data)
        print(response.content)
        assert response.status_code == 400
        assert response.content['type'][0] == '"" is not a valid choice.'

    def test_create_spatial_unit_with_invalid_geometry(self):
        invalid_data = {
            'type': "BU",
            'geometry': {
                'type': 'Cats',
                'coordinates': [100, 0]
            }
        }
        response = self.request(user=self.user,
                                method='POST',
                                post_data=invalid_data)
        assert response.status_code == 400
        assert response.content['geometry'][0] == (
            "Invalid format: string or unicode input"
            " unrecognized as GeoJSON, WKT EWKT or HEXEWKB.")


class SpatialUnitDetailAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.SpatialUnitDetail

    def setup_models(self):
        self.user = UserFactory.create()
        assign_policies(self.user)
        self.prj = ProjectFactory.create(slug='test-project', access='public')
        self.su = SpatialUnitFactory(project=self.prj)

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'spatial_id': self.su.id
        }

    def test_get_public_record_with_valid_user(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['properties']['id'] == self.su.id

    def test_get_public_nonexistent_record(self):
        response = self.request(user=self.user,
                                url_kwargs={'spatial_id': 'notanid'})
        assert response.status_code == 404
        assert response.content['detail'] == "SpatialUnit not found."

    def test_get_public_record_with_nonexistent_org(self):
        response = self.request(user=self.user,
                                url_kwargs={'organization': 'evil-corp'})
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."

    def test_get_public_record_with_nonexistent_project(self):
        response = self.request(user=self.user,
                                url_kwargs={'project': 'world-domination'})
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."

    def test_get_public_record_with_unauthorized_user(self):
        response = self.request()
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_get_private_record(self):
        self.prj.access = 'private'
        self.prj.save()
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['properties']['id'] == self.su.id

    def test_get_private_record_with_unauthorized_user(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request()
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_get_private_record_without_permission(self):
        self.prj.access = 'private'
        self.prj.save()

        restricted_clauses = {
            'clause': [
                clause('allow', ['project.list'], ['organization/*']),
                clause('allow', ['project.view'], ['project/*/*'])
            ]
        }
        restricted_policy = Policy.objects.create(
            name='restricted',
            body=json.dumps(restricted_clauses))
        self.user.assign_policies(restricted_policy)

        response = self.request(user=self.user)
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_get_private_record_based_on_org_membership(self):
        self.prj.access = 'private'
        self.prj.save()

        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.prj.organization,
                                        user=user)

        response = self.request(user=user)
        assert response.status_code == 200
        print(response.content)
        assert response.content['properties']['id'] == self.su.id


class SpatialUnitUpdateAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.SpatialUnitDetail

    def setup_models(self):
        self.user = UserFactory.create()
        assign_policies(self.user)
        self.prj = ProjectFactory.create(slug='test-project', access='public')
        self.su = SpatialUnitFactory(project=self.prj, type='PA')

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'spatial_id': self.su.id
        }

    def setup_post_data(self):
        return {'type': "BU"}

    def check_for_updated(self, content):
        data = self.get_valid_updated_data()
        assert content['properties']['type'] == data['type']

    def check_for_unchanged(self, content):
        assert content['properties']['type'] == self.su.type

    def test_update_with_valid_data(self):
        response = self.request(user=self.user, method='PATCH')
        assert response.status_code == 200
        self.su.refresh_from_db()
        assert self.su.type == 'BU'

    def test_update_with_nonexistent_org(self):
        response = self.request(user=self.user,
                                method='PATCH',
                                url_kwargs={'organization': 'evil-corp'})
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."
        self.su.refresh_from_db()
        assert self.su.type == 'PA'

    def test_update_with_nonexistent_project(self):
        response = self.request(user=self.user,
                                method='PATCH',
                                url_kwargs={'project': 'evil-corp'})
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."
        self.su.refresh_from_db()
        assert self.su.type == 'PA'

    def test_update_with_nonexistent_record(self):
        response = self.request(user=self.user,
                                method='PATCH',
                                url_kwargs={'spatial_id': 'some-su'})
        assert response.status_code == 404
        assert response.content['detail'] == "SpatialUnit not found."

    def test_update_with_unauthorized_user(self):
        response = self.request(method='PATCH')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

        self.su.refresh_from_db()
        assert self.su.type == 'PA'

    def test_update_private_record(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request(user=self.user, method='PATCH')
        assert response.status_code == 200
        self.su.refresh_from_db()
        assert self.su.type == 'BU'

    def test_update_private_record_with_unauthorized_user(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request(method='PATCH')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

        self.su.refresh_from_db()
        assert self.su.type == 'PA'

    def test_update_private_record_without_permission(self):
        self.prj.access = 'private'
        self.prj.save()

        restricted_clauses = {
            'clause': [
                clause('allow', ['project.list'], ['organization/*']),
                clause('allow', ['project.view'], ['project/*/*'])
            ]
        }
        restricted_policy = Policy.objects.create(
            name='restricted',
            body=json.dumps(restricted_clauses))
        self.user.assign_policies(restricted_policy)

        response = self.request(user=self.user, method='PATCH')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

        self.su.refresh_from_db()
        assert self.su.type == 'PA'

    def test_update_private_record_based_on_org_membership(self):
        self.prj.access = 'private'
        self.prj.save()

        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.prj.organization,
                                        user=user)

        response = self.request(user=user, method='PATCH')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

        self.su.refresh_from_db()
        assert self.su.type == 'PA'

    def test_update_private_record_based_on_org_admin(self):
        self.prj.access = 'private'
        self.prj.save()

        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.prj.organization,
                                        user=user,
                                        admin=True)

        response = self.request(user=self.user, method='PATCH')
        assert response.status_code == 200
        self.su.refresh_from_db()
        assert self.su.type == 'BU'

    def test_update_with_invalid_data(self):
        response = self.request(user=self.user,
                                method='PATCH',
                                post_data={'type': ''})

        assert response.status_code == 400
        self.su.refresh_from_db()
        assert self.su.type == 'PA'
        assert response.content['type'][0] == '"" is not a valid choice.'

    def test_update_with_invalid_geometry(self):
        invalid_data = {
                'geometry': {
                    'type': 'Cats',
                    'coordinates': [100, 0]
                }
            }

        response = self.request(user=self.user,
                                method='PATCH',
                                post_data=invalid_data)
        assert response.status_code == 400
        assert response.content['geometry'][0] == (
            "Invalid format: string or unicode input"
            " unrecognized as GeoJSON, WKT EWKT or HEXEWKB.")


class SpatialUnitDeleteAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.SpatialUnitDetail

    def setup_models(self):
        self.user = UserFactory.create()
        assign_policies(self.user)
        self.prj = ProjectFactory.create(slug='test-project', access='public')
        self.su = SpatialUnitFactory(project=self.prj, type='PA')

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'spatial_id': self.su.id
        }

    def test_delete_record(self):
        response = self.request(method='DELETE', user=self.user)
        assert response.status_code == 204
        assert SpatialUnit.objects.count() == 0

    def test_delete_with_nonexistent_org(self):
        response = self.request(method='DELETE',
                                user=self.user,
                                url_kwargs={'organization': 'evil-corp'})
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."

    def test_delete_with_nonexistent_project(self):
        response = self.request(method='DELETE',
                                user=self.user,
                                url_kwargs={'project': 'world-domination'})
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."

    def test_delete_with_nonexistent_record(self):
        response = self.request(method='DELETE',
                                user=self.user,
                                url_kwargs={'spatial_id': 'some-rel'})
        assert response.status_code == 404
        assert response.content['detail'] == "SpatialUnit not found."

    def test_delete_with_unauthorized_user(self):
        response = self.request(method='DELETE')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        assert SpatialUnit.objects.count() == 1

    def test_delete_private_record(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request(method='DELETE', user=self.user)
        assert response.status_code == 204
        assert SpatialUnit.objects.count() == 0

    def test_delete_private_record_with_unauthorized_user(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request(method='DELETE')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        assert SpatialUnit.objects.count() == 1

    def test_delete_private_record_without_permission(self):
        self.prj.access = 'private'
        self.prj.save()

        restricted_clauses = {
            'clause': [
                clause('allow', ['project.list'], ['organization/*']),
                clause('allow', ['project.view'], ['project/*/*'])
            ]
        }
        restricted_policy = Policy.objects.create(
            name='restricted',
            body=json.dumps(restricted_clauses))
        self.user.assign_policies(restricted_policy)

        response = self.request(method='DELETE', user=self.user)
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        assert SpatialUnit.objects.count() == 1

    def test_delete_private_record_based_on_org_membership(self):
        self.prj.access = 'private'
        self.prj.save()

        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.prj.organization,
                                        user=user)

        response = self.request(method='DELETE', user=user)
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        assert SpatialUnit.objects.count() == 1

    def test_delete_private_record_based_on_org_admin(self):
        self.prj.access = 'private'
        self.prj.save()

        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.prj.organization,
                                        user=user,
                                        admin=True)

        response = self.request(method='DELETE', user=user)
        assert response.status_code == 204
        assert SpatialUnit.objects.count() == 0
