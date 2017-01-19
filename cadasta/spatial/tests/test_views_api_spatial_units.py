import json

from django.test import TestCase
from rest_framework.exceptions import PermissionDenied
from tutelary.models import Policy, assign_user_policies
from skivvy import APITestCase

from accounts.tests.factories import UserFactory
from core.tests.utils.cases import UserTestCase, FileStorageTestCase
from organization.tests.factories import ProjectFactory, clause
from organization.models import OrganizationRole
from resources.tests.factories import ResourceFactory
from resources.models import Resource
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
                'action': ['spatial.*', 'spatial.resources.*']
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

    def test_create_archived_project(self):
        self.prj.archived = True
        self.prj.save()
        response = self.request(user=self.user, method='POST')
        assert response.status_code == 403
        assert SpatialUnit.objects.count() == 0
        assert response.content['detail'] == PermissionDenied.default_detail


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
            'location': self.su.id
        }

    def test_get_public_record_with_valid_user(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['properties']['id'] == self.su.id

    def test_get_public_nonexistent_record(self):
        response = self.request(user=self.user,
                                url_kwargs={'location': 'notanid'})
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
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail


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
            'location': self.su.id
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
                                url_kwargs={'location': 'some-su'})
        assert response.status_code == 404
        assert response.content['detail'] == "SpatialUnit not found."

    def test_PATCH_with_anonymous_user(self):
        response = self.request(method='PATCH')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

        self.su.refresh_from_db()
        assert self.su.type == 'PA'

    def test_PATCH_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='PATCH', user=user)
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

        self.su.refresh_from_db()
        assert self.su.type == 'PA'

    def test_PUT_with_anonymous_user(self):
        response = self.request(method='PUT')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

        self.su.refresh_from_db()
        assert self.su.type == 'PA'

    def test_PUT_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='PUT', user=user)
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

    def test_update_with_archived_project(self):
        self.su.project.archived = True
        self.su.project.save()

        response = self.request(user=self.user, method='PATCH')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail


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
            'location': self.su.id
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
                                url_kwargs={'location': 'some-rel'})
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

    def test_delete_with_archived_project(self):
        self.prj.archived = True
        self.prj.save()
        response = self.request(method='DELETE', user=self.user)
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        assert SpatialUnit.objects.count() == 1


class SpatialUnitResourceListAPITest(APITestCase, UserTestCase,
                                     FileStorageTestCase, TestCase):
    view_class = api.SpatialUnitResourceList

    def setup_models(self):
        self.user = UserFactory.create()
        assign_policies(self.user)
        self.prj = ProjectFactory.create(slug='test-project', access='public')
        self.su = SpatialUnitFactory.create(project=self.prj)
        self.resources = ResourceFactory.create_batch(
            2, project=self.prj, content_object=self.su)
        ResourceFactory.create(project=self.prj)

        self.file = self.get_file('/resources/tests/files/image.jpg', 'rb')
        self.file_name = self.storage.save('resources/image.jpg', self.file)

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'location': self.su.id,
        }

    def setup_post_data(self):
        return {
            'name': 'New resource',
            'description': '',
            'file': self.file_name,
            'original_file': 'image.png',
        }

    def test_full_list(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert len(response.content) == 2

        returned_ids = [r['id'] for r in response.content]
        assert all(res.id in returned_ids for res in self.resources)

    def test_full_list_with_unauthorized_user(self):
        response = self.request()
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_ordering(self):
        su = SpatialUnitFactory.create(project=self.prj)
        ResourceFactory.create_from_kwargs([
            {'content_object': su, 'project': self.prj, 'name': 'A'},
            {'content_object': su, 'project': self.prj, 'name': 'B'},
            {'content_object': su, 'project': self.prj, 'name': 'C'},
        ])

        response = self.request(
            user=self.user,
            url_kwargs={'location': su.id},
            get_data={'ordering': 'name'})
        assert response.status_code == 200
        assert len(response.content) == 3
        names = [resource['name'] for resource in response.content]
        assert(names == sorted(names))

    def test_reverse_ordering(self):
        su = SpatialUnitFactory.create(project=self.prj)
        ResourceFactory.create_from_kwargs([
            {'content_object': su, 'project': self.prj, 'name': 'A'},
            {'content_object': su, 'project': self.prj, 'name': 'B'},
            {'content_object': su, 'project': self.prj, 'name': 'C'},
        ])

        response = self.request(
            user=self.user,
            url_kwargs={'location': su.id},
            get_data={'ordering': '-name'})
        assert response.status_code == 200
        assert len(response.content) == 3
        names = [resource['name'] for resource in response.content]
        assert(names == sorted(names, reverse=True))

    def test_search_filter(self):
        not_found = self.storage.save('resources/bild.jpg', self.file)
        su = SpatialUnitFactory.create(project=self.prj)
        ResourceFactory.create_from_kwargs([
            {'content_object': su, 'project': self.prj,
                'file': self.file_name},
            {'content_object': su, 'project': self.prj,
                'file': self.file_name},
            {'content_object': su, 'project': self.prj,
                'file': not_found}
        ])

        response = self.request(
            user=self.user,
            url_kwargs={'organization': self.prj.organization.slug,
                        'project': self.prj.slug,
                        'location': su.id},
            get_data={'search': 'image'})
        assert response.status_code == 200
        assert len(response.content) == 2

    def test_get_full_list_organization_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'organization': 'some-org'})
        assert response.status_code == 404
        assert response.content['detail'] == "SpatialUnit not found."

    def test_get_full_list_project_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'project': 'some-prj'})
        assert response.status_code == 404
        assert response.content['detail'] == "SpatialUnit not found."

    def test_get_full_list_spatial_unit_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'location': 'some-su'})
        assert response.status_code == 404
        assert response.content['detail'] == "SpatialUnit not found."

    def test_archived_resources_not_listed(self):
        ResourceFactory.create(
            project=self.prj, content_object=self.su, archived=True)
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert len(response.content) == 2

        returned_ids = [r['id'] for r in response.content]
        assert all(res.id in returned_ids for res in self.resources)

    def test_add_resource(self):
        response = self.request(method='POST', user=self.user)
        assert response.status_code == 201
        assert self.su.resources.count() == 3

    def test_add_resource_with_unauthorized_user(self):
        response = self.request(method='POST', user=UserFactory.create())
        assert response.status_code == 403
        assert self.su.resources.count() == 2

    def test_add_existing_resource(self):
        new_resource = ResourceFactory.create()
        data = {'id': new_resource.id}
        response = self.request(method='POST', user=self.user, post_data=data)
        assert response.status_code == 201
        assert self.su.resources.count() == 3
        assert new_resource in self.su.resources

    def test_add_invalid_resource(self):
        data = {'name': ''}
        response = self.request(method='POST', user=self.user, post_data=data)
        assert response.status_code == 400
        assert self.su.resources.count() == 2
        assert 'This field may not be blank.' in response.content['name']

    def test_add_with_archived_project(self):
        data = {
            'name': 'New resource',
            'description': '',
            'file': self.file_name
        }
        self.prj.archived = True
        self.prj.save()

        response = self.request(method='POST', user=self.user, post_data=data)
        assert response.status_code == 403
        assert self.su.resources.count() == 2


class SpatialUnitResourceDetailAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.SpatialUnitResourceDetail

    def setup_models(self):
        self.prj = ProjectFactory.create()
        self.su = SpatialUnitFactory.create(project=self.prj)
        self.resource = ResourceFactory.create(content_object=self.su,
                                               project=self.prj)
        self.user = UserFactory.create()
        assign_policies(self.user)

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'location': self.su.id,
            'resource': self.resource.id,
        }

    def test_get_resource(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['id'] == self.resource.id

    def test_get_resource_with_unauthorized_user(self):
        response = self.request(user=UserFactory.create())
        assert response.status_code == 403
        assert 'id' not in response.content

    def test_get_resource_from_org_that_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'organization': 'some-org'})
        assert response.status_code == 404
        assert response.content['detail'] == "SpatialUnit not found."

    def test_get_resource_from_project_that_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'project': 'some-prj'})
        assert response.status_code == 404
        assert response.content['detail'] == "SpatialUnit not found."

    def test_get_resource_from_spatial_unit_that_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'location': 'some-su'})
        assert response.status_code == 404
        assert response.content['detail'] == "SpatialUnit not found."

    def test_get_resource_that_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'resource': 'abc123'})
        assert response.status_code == 404
        assert response.content['detail'] == "Not found."


class SpatialUnitResourceUpdateAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.SpatialUnitResourceDetail
    post_data = {'name': 'Updated'}

    def setup_models(self):
        self.prj = ProjectFactory.create()
        self.su = SpatialUnitFactory.create(project=self.prj)
        self.resource = ResourceFactory.create(content_object=self.su,
                                               project=self.prj)
        self.user = UserFactory.create()
        assign_policies(self.user)

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'location': self.su.id,
            'resource': self.resource.id,
        }

    def test_update_resource(self):
        response = self.request(method='PATCH', user=self.user)
        assert response.status_code == 200
        assert response.content['id'] == self.resource.id
        self.resource.refresh_from_db()
        assert self.resource.name == self.post_data['name']

    def test_update_resource_with_unauthorized_user(self):
        response = self.request(method='PATCH', user=UserFactory.create())
        assert response.status_code == 403
        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']

    def test_update_invalid_resource(self):
        data = {'name': ''}
        response = self.request(method='PATCH', user=self.user, post_data=data)
        assert response.status_code == 400
        assert 'name' in response.content
        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']

    def test_update_with_archived_project(self):
        self.prj.archived = True
        self.prj.save()
        response = self.request(method='PATCH', user=UserFactory.create())
        assert response.status_code == 403
        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']

    def test_PATCH_with_anonymous_user(self):
        response = self.request(method='PATCH')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']

    def test_PATCH_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='PATCH', user=user)
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']

    def test_PUT_with_anonymous_user(self):
        response = self.request(method='PUT')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']

    def test_PUT_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(method='PUT', user=user)
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']


class SpatialUnitResourceArchiveAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.SpatialUnitResourceDetail

    def setup_models(self):
        self.prj = ProjectFactory.create()
        self.su = SpatialUnitFactory.create(project=self.prj)
        self.resource = ResourceFactory.create(content_object=self.su,
                                               project=self.prj)
        self.user = UserFactory.create()
        assign_policies(self.user)

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'location': self.su.id,
            'resource': self.resource.id,
        }

    def test_archive_resource(self):
        data = {'archived': True}
        response = self.request(method='PATCH', user=self.user, post_data=data)
        assert response.status_code == 200
        assert response.content['id'] == self.resource.id
        self.resource.refresh_from_db()
        assert self.resource.archived is True

    def test_archive_resource_with_unauthorized_user(self):
        data = {'archived': True}
        response = self.request(method='PATCH', user=UserFactory.create(),
                                post_data=data)
        assert response.status_code == 403
        assert 'id' not in response.content
        self.resource.refresh_from_db()
        assert self.resource.archived is False

    def test_unarchive_resource(self):
        # User should have to unarchive this from main project list?
        self.resource.archived = True
        self.resource.save()
        data = {'archived': False}
        assign_policies(self.user)

        response = self.request(method='PATCH', user=self.user, post_data=data)
        assert response.status_code == 404
        assert response.content['detail'] == "Not found."
        self.resource.refresh_from_db()
        assert self.resource.archived is True

    def test_unarchive_resource_with_unauthorized_user(self):
        self.resource.archived = True
        self.resource.save()
        data = {'archived': False}
        response = self.request(method='PATCH', user=self.user,
                                post_data=data)
        assert response.status_code == 404
        self.resource.refresh_from_db()
        assert self.resource.archived is True


class SpatialUnitResourceDetachAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.SpatialUnitResourceDetail

    def setup_models(self):
        self.prj = ProjectFactory.create()
        self.su = SpatialUnitFactory.create(project=self.prj)
        self.resource = ResourceFactory.create(content_object=self.su,
                                               project=self.prj)
        self.user = UserFactory.create()
        assign_policies(self.user)

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'location': self.su.id,
            'resource': self.resource.id,
        }

    def test_delete_resource(self):
        response = self.request(method='DELETE', user=self.user)
        assert response.status_code == 204
        assert len(self.su.resources) == 0
        assert Resource.objects.filter(
            id=self.resource.id, project=self.prj).exists()

    def test_delete_resource_with_unauthorized_user(self):
        response = self.request(method='DELETE', user=UserFactory.create())
        assert response.status_code == 403
        assert self.resource in self.su.resources
        assert Resource.objects.filter(
            id=self.resource.id, project=self.prj).exists()

    def test_delete_resource_with_archived_project(self):
        self.prj.archived = True
        self.prj.save()
        response = self.request(method='DELETE', user=self.user)
        assert response.status_code == 403
        assert self.resource in self.su.resources
        assert Resource.objects.filter(
            id=self.resource.id, project=self.prj).exists()

    def test_delete_resource_with_invalid_resource(self):
        new_resource = ResourceFactory.create(project=self.prj)
        response = self.request(method='DELETE', user=self.user, url_kwargs={
            'resource': new_resource.id
            })
        assert response.status_code == 404
        assert response.content['detail'] == "Not found."
        assert len(self.su.resources) == 1
        assert Resource.objects.filter(
            id=self.resource.id, project=self.prj).exists()
