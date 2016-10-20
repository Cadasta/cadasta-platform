import json
from django.test import TestCase
from rest_framework.exceptions import PermissionDenied
from skivvy import APITestCase

from accounts.tests.factories import UserFactory
from core.tests.utils.cases import UserTestCase, FileStorageTestCase
from organization.tests.factories import ProjectFactory, clause
from organization.models import OrganizationRole
from resources.tests.factories import ResourceFactory
from resources.models import Resource
from spatial.tests.factories import SpatialUnitFactory
from party.tests.factories import PartyFactory, TenureRelationshipFactory
from party.models import TenureRelationship
from party.views import api
from tutelary.models import Policy, assign_user_policies


def assign_policies(user):
    clauses = {
        'clause': [
            {
                'effect': 'allow',
                'object': ['project/*/*',
                           'spatial/*/*/*',
                           'spatial_rel/*/*/*',
                           'party/*/*/*',
                           'party_rel/*/*/*',
                           'tenure_rel/*/*/*'],
                'action': ['project.*',
                           'project.*.*',
                           'spatial.*',
                           'spatial_rel.*',
                           'party.*',
                           'party_rel.*',
                           'tenure_rel.*', 'tenure_rel.resources.*']
            }
        ]
    }
    policy = Policy.objects.create(
        name='basic-test',
        body=json.dumps(clauses))
    user.assign_policies(policy)


class TenureRelationshipCreateTestCase(APITestCase, UserTestCase, TestCase):
    view_class = api.TenureRelationshipCreate
    record_model = TenureRelationship

    def setup_models(self):
        self.user = UserFactory.create()
        assign_policies(self.user)

        self.prj = ProjectFactory.create(slug='test-project', access='public')
        self.party1 = PartyFactory.create(project=self.prj, name='Landowner')
        self.su2 = SpatialUnitFactory.create(project=self.prj, type='PA')

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug
        }

    def setup_post_data(self):
        return {
            'party': self.party1.id,
            'spatial_unit': self.su2.id,
            'tenure_type': 'WR'
        }

    def test_create_valid_record(self):
        response = self.request(user=self.user, method='POST')
        assert response.status_code == 201
        assert TenureRelationship.objects.count() == 1

    def test_create_record_with_nonexistent_org(self):
        response = self.request(user=self.user,
                                method='POST',
                                url_kwargs={'organization': 'evil-corp'})
        assert response.status_code == 404
        assert TenureRelationship.objects.count() == 0
        assert response.content['detail'] == "Project not found."

    def test_create_record_with_nonexistent_project(self):
        response = self.request(user=self.user,
                                method='POST',
                                url_kwargs={'project': 'world-domination'})
        assert response.status_code == 404
        assert TenureRelationship.objects.count() == 0
        assert response.content['detail'] == "Project not found."

    def test_create_record_with_unauthorized_user(self):
        response = self.request(method='POST')
        assert response.status_code == 403
        assert TenureRelationship.objects.count() == 0
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_create_private_record(self):
        self.prj.access = 'private'
        self.prj.save()
        response = self.request(user=self.user, method='POST')
        assert response.status_code == 201
        assert TenureRelationship.objects.count() == 1

    def test_create_private_record_with_unauthorized_user(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request(method='POST')
        assert response.status_code == 403
        assert TenureRelationship.objects.count() == 0
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
        assert TenureRelationship.objects.count() == 0
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_create_private_record_based_on_org_membership(self):
        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.prj.organization,
                                        user=user)
        response = self.request(user=user, method='POST')
        assert response.status_code == 403
        assert TenureRelationship.objects.count() == 0
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_create_invalid_record_with_different_project(self):
        other_party = PartyFactory.create(name="Other")
        invalid_data = {
            'party': other_party.id,
            'spatial_unit': self.su2.id,
            'type': 'C'
        }
        response = self.request(user=self.user,
                                method='POST',
                                post_data=invalid_data)
        assert response.status_code == 400
        assert TenureRelationship.objects.count() == 0

        err_msg = ("'party' project ({}) should be equal to "
                   "'spatial_unit' project ({})")
        assert response.content['non_field_errors'][0] == (
            err_msg.format(other_party.project.slug, self.prj.slug))

    def test_create_valid_record_with_archived_project(self):
        self.prj.archived = True
        self.prj.save()

        response = self.request(user=self.user, method='POST')
        assert response.status_code == 403
        assert TenureRelationship.objects.count() == 0
        assert response.content['detail'] == PermissionDenied.default_detail


class TenureRelationshipDetailAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.TenureRelationshipDetail

    def setup_models(self):
        self.user = UserFactory.create()
        assign_policies(self.user)

        self.prj = ProjectFactory.create(slug='test-project', access='public')
        party = PartyFactory.create(project=self.prj, name='Landowner')
        spatial_unit = SpatialUnitFactory.create(project=self.prj, type='PA')
        self.rel = TenureRelationshipFactory.create(
            project=self.prj, party=party, spatial_unit=spatial_unit)

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'tenure_rel_id': self.rel.id
        }

    def test_get_public_record_with_valid_user(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['id'] == self.rel.id

    def test_get_public_nonexistent_record(self):
        response = self.request(user=self.user,
                                url_kwargs={'tenure_rel_id': 'notanid'})
        assert response.status_code == 404
        assert response.content['detail'] == "TenureRelationship not found."

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
        assert response.content['id'] == self.rel.id

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
        assert response.content['id'] == self.rel.id


class TenureRelationshipUpdateAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.TenureRelationshipDetail

    def setup_models(self):
        self.user = UserFactory.create()
        assign_policies(self.user)

        self.prj = ProjectFactory.create(slug='test-project', access='public')
        self.party = PartyFactory.create(project=self.prj)
        self.spatial_unit = SpatialUnitFactory.create(project=self.prj)
        self.rel = TenureRelationshipFactory.create(
            project=self.prj, party=self.party, spatial_unit=self.spatial_unit)
        self.party2 = PartyFactory.create(project=self.prj)
        self.spatial_unit2 = SpatialUnitFactory.create(project=self.prj)

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'tenure_rel_id': self.rel.id
        }

    def setup_post_data(self):
        return {
            'party': self.party2.id,
            'spatial_unit': self.spatial_unit2.id,
        }

    def test_update_with_valid_data(self):
        response = self.request(user=self.user, method='PATCH')
        assert response.status_code == 200
        self.rel.refresh_from_db()
        assert self.rel.party == self.party2
        assert self.rel.spatial_unit == self.spatial_unit2

    def test_update_with_nonexistent_org(self):
        response = self.request(user=self.user,
                                method='PATCH',
                                url_kwargs={'organization': 'evil-corp'})
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."
        self.rel.refresh_from_db()
        assert self.rel.party == self.party
        assert self.rel.spatial_unit == self.spatial_unit

    def test_update_with_nonexistent_project(self):
        response = self.request(user=self.user,
                                method='PATCH',
                                url_kwargs={'project': 'evil-corp'})
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."
        self.rel.refresh_from_db()
        assert self.rel.party == self.party
        assert self.rel.spatial_unit == self.spatial_unit

    def test_update_with_nonexistent_record(self):
        response = self.request(user=self.user,
                                method='PATCH',
                                url_kwargs={'tenure_rel_id': 'some-rel'})
        assert response.status_code == 404
        assert response.content['detail'] == "TenureRelationship not found."

    def test_update_with_unauthorized_user(self):
        response = self.request(method='PATCH')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

        self.rel.refresh_from_db()
        assert self.rel.party == self.party
        assert self.rel.spatial_unit == self.spatial_unit

    def test_update_private_record(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request(user=self.user, method='PATCH')
        assert response.status_code == 200

        self.rel.refresh_from_db()
        assert self.rel.party == self.party2
        assert self.rel.spatial_unit == self.spatial_unit2

    def test_update_private_record_with_unauthorized_user(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request(method='PATCH')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

        self.rel.refresh_from_db()
        assert self.rel.party == self.party
        assert self.rel.spatial_unit == self.spatial_unit

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

        self.rel.refresh_from_db()
        assert self.rel.party == self.party
        assert self.rel.spatial_unit == self.spatial_unit

    def test_update_private_record_based_on_org_membership(self):
        self.prj.access = 'private'
        self.prj.save()

        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.prj.organization,
                                        user=user)

        response = self.request(user=user, method='PATCH')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

        self.rel.refresh_from_db()
        assert self.rel.party == self.party
        assert self.rel.spatial_unit == self.spatial_unit

    def test_update_private_record_based_on_org_admin(self):
        self.prj.access = 'private'
        self.prj.save()

        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.prj.organization,
                                        user=user,
                                        admin=True)

        response = self.request(user=user, method='PATCH')
        assert response.status_code == 200

        self.rel.refresh_from_db()
        assert self.rel.party == self.party2
        assert self.rel.spatial_unit == self.spatial_unit2

    def test_update_invalid_record_with_different_project(self):
        other_party = PartyFactory.create()
        response = self.request(user=self.user,
                                method='PATCH',
                                post_data={'party': other_party.id})
        assert response.status_code == 400
        err_msg = (
            "'party' project ({}) should be equal to "
            "'spatial_unit' project ({})")
        assert response.content['non_field_errors'][0] == (
            err_msg.format(other_party.project.slug,
                           self.spatial_unit.project.slug))
        self.rel.refresh_from_db()
        assert self.rel.party == self.party
        assert self.rel.spatial_unit == self.spatial_unit

    def test_update_with_archived_project(self):
        self.prj.archived = True
        self.prj.save()

        response = self.request(user=self.user, method='PATCH')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

        self.rel.refresh_from_db()
        assert self.rel.party == self.party
        assert self.rel.spatial_unit == self.spatial_unit


class TenureRelationshipDeleteAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.TenureRelationshipDetail

    def setup_models(self):
        self.user = UserFactory.create()
        assign_policies(self.user)

        self.prj = ProjectFactory.create(slug='test-project', access='public')
        self.party = PartyFactory.create(project=self.prj)
        self.spatial_unit = SpatialUnitFactory.create(project=self.prj)
        self.rel = TenureRelationshipFactory.create(
            project=self.prj, party=self.party, spatial_unit=self.spatial_unit)
        self.party2 = PartyFactory.create(project=self.prj)
        self.spatial_unit2 = SpatialUnitFactory.create(project=self.prj)

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'tenure_rel_id': self.rel.id
        }

    def test_delete_record(self):
        response = self.request(method='DELETE', user=self.user)
        assert response.status_code == 204
        assert TenureRelationship.objects.count() == 0

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
                                url_kwargs={'tenure_rel_id': 'some-rel'})
        assert response.status_code == 404
        assert response.content['detail'] == "TenureRelationship not found."

    def test_delete_with_unauthorized_user(self):
        response = self.request(method='DELETE')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        assert TenureRelationship.objects.count() == 1

    def test_delete_private_record(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request(method='DELETE', user=self.user)
        assert response.status_code == 204
        assert TenureRelationship.objects.count() == 0

    def test_delete_private_record_with_unauthorized_user(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request(method='DELETE')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        assert TenureRelationship.objects.count() == 1

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
        assert TenureRelationship.objects.count() == 1

    def test_delete_private_record_based_on_org_membership(self):
        self.prj.access = 'private'
        self.prj.save()

        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.prj.organization,
                                        user=user)

        response = self.request(method='DELETE', user=user)
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        assert TenureRelationship.objects.count() == 1

    def test_delete_private_record_based_on_org_admin(self):
        self.prj.access = 'private'
        self.prj.save()

        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.prj.organization,
                                        user=user,
                                        admin=True)
        response = self.request(method='DELETE', user=user)
        assert response.status_code == 204
        assert TenureRelationship.objects.count() == 0

    def test_delete_record_with_archived_project(self):
        self.prj.archived = True
        self.prj.save()

        response = self.request(method='DELETE', user=self.user)
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        assert TenureRelationship.objects.count() == 1


class TenureRelationshipResourceListAPITest(APITestCase, FileStorageTestCase,
                                            UserTestCase, TestCase):
    view_class = api.TenureRelationshipResourceList

    def setup_models(self):
        self.user = UserFactory.create()
        assign_policies(self.user)
        self.prj = ProjectFactory.create(slug='test-project', access='public')
        self.tenure = TenureRelationshipFactory.create(
                        project=self.prj)
        self.resources = ResourceFactory.create_batch(
            2, project=self.prj, content_object=self.tenure)
        ResourceFactory.create(project=self.prj)

        self.file = self.get_file(
            '/resources/tests/files/image.jpg', 'rb')
        self.file_name = self.storage.save('resources/image.jpg', self.file)

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'tenure_rel_id': self.tenure.id,
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
        tenure = TenureRelationshipFactory.create(
            project=self.prj)
        ResourceFactory.create_from_kwargs([
            {'content_object': tenure, 'project': self.prj, 'name': 'A'},
            {'content_object': tenure, 'project': self.prj, 'name': 'B'},
            {'content_object': tenure, 'project': self.prj, 'name': 'C'},
        ])

        response = self.request(
            user=self.user,
            url_kwargs={'tenure_rel_id': tenure.id},
            get_data={'ordering': 'name'})
        assert response.status_code == 200
        assert len(response.content) == 3
        names = [resource['name'] for resource in response.content]
        assert(names == sorted(names))

    def test_reverse_ordering(self):
        tenure = TenureRelationshipFactory.create(
            project=self.prj)
        ResourceFactory.create_from_kwargs([
            {'content_object': tenure, 'project': self.prj, 'name': 'A'},
            {'content_object': tenure, 'project': self.prj, 'name': 'B'},
            {'content_object': tenure, 'project': self.prj, 'name': 'C'},
        ])

        response = self.request(
            user=self.user,
            url_kwargs={'tenure_rel_id': tenure.id},
            get_data={'ordering': '-name'})
        assert response.status_code == 200
        assert len(response.content) == 3
        names = [resource['name'] for resource in response.content]
        assert(names == sorted(names, reverse=True))

    def test_search_filter(self):
        not_found = self.storage.save('resources/bild.jpg', self.file)
        tenure = TenureRelationshipFactory.create(
            project=self.prj)
        ResourceFactory.create_from_kwargs([
            {'content_object': tenure, 'project': self.prj,
                'file': self.file_name},
            {'content_object': tenure, 'project': self.prj,
                'file': self.file_name},
            {'content_object': tenure, 'project': self.prj,
                'file': not_found}
        ])

        response = self.request(
            user=self.user,
            url_kwargs={'organization': self.prj.organization.slug,
                        'project': self.prj.slug,
                        'tenure_rel_id': tenure.id},
            get_data={'search': 'image'})
        assert response.status_code == 200
        assert len(response.content) == 2

    def test_get_full_list_organization_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'organization': 'some-org'})
        assert response.status_code == 404
        assert response.content['detail'] == "TenureRelationship not found."

    def test_get_full_list_project_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'project': 'some-prj'})
        assert response.status_code == 404
        assert response.content['detail'] == "TenureRelationship not found."

    def test_get_full_list_spatial_unit_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'tenure_rel_id': 'some-tenure'})
        assert response.status_code == 404
        assert response.content['detail'] == "TenureRelationship not found."

    def test_archived_resources_not_listed(self):
        ResourceFactory.create(
            project=self.prj, content_object=self.tenure, archived=True)
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert len(response.content) == 2

        returned_ids = [r['id'] for r in response.content]
        assert all(res.id in returned_ids for res in self.resources)

    def test_add_resource(self):
        response = self.request(method='POST', user=self.user)
        assert response.status_code == 201
        assert self.tenure.resources.count() == 3

    def test_add_resource_with_unauthorized_user(self):
        response = self.request(method='POST', user=UserFactory.create())
        assert response.status_code == 403
        assert self.tenure.resources.count() == 2

    def test_add_existing_resource(self):
        new_resource = ResourceFactory.create()
        data = {'id': new_resource.id}
        response = self.request(method='POST', user=self.user, post_data=data)
        assert response.status_code == 201
        assert self.tenure.resources.count() == 3
        assert new_resource in self.tenure.resources

    def test_add_invalid_resource(self):
        data = {'name': ''}
        response = self.request(method='POST', user=self.user, post_data=data)
        assert response.status_code == 400
        assert self.tenure.resources.count() == 2
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
        assert self.tenure.resources.count() == 2


class TenureRelationshipResourceDetailAPITest(APITestCase, UserTestCase,
                                              TestCase):
    view_class = api.TenureRelationshipResourceDetail

    def setup_models(self):
        self.prj = ProjectFactory.create()
        self.tenure = TenureRelationshipFactory.create(
            project=self.prj)
        self.resource = ResourceFactory.create(content_object=self.tenure,
                                               project=self.prj)
        self.user = UserFactory.create()
        assign_policies(self.user)

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'tenure_rel_id': self.tenure.id,
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
        assert response.content['detail'] == "Project not found."

    def test_get_resource_from_project_that_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'project': 'some-prj'})
        assert response.status_code == 404
        assert response.content['detail'] == "TenureRelationship not found."

    def test_get_resource_from_spatial_unit_that_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'tenure_rel_id': 'some-party'})
        assert response.status_code == 404
        assert response.content['detail'] == "TenureRelationship not found."

    def test_get_resource_that_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'resource': 'abc123'})
        assert response.status_code == 404
        assert response.content['detail'] == "Not found."


class TenureRelationshipResourceUpdateAPITest(APITestCase, UserTestCase,
                                              TestCase):
    view_class = api.TenureRelationshipResourceDetail
    post_data = {'name': 'Updated'}

    def setup_models(self):
        self.prj = ProjectFactory.create()
        self.tenure = TenureRelationshipFactory.create(
            project=self.prj)
        self.resource = ResourceFactory.create(content_object=self.tenure,
                                               project=self.prj)
        self.user = UserFactory.create()
        assign_policies(self.user)

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'tenure_rel_id': self.tenure.id,
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


class TenureRelationshipResourceArchiveAPITest(APITestCase, UserTestCase,
                                               TestCase):
    view_class = api.TenureRelationshipResourceDetail

    def setup_models(self):
        self.prj = ProjectFactory.create()
        self.tenure = TenureRelationshipFactory.create(
            project=self.prj)
        self.resource = ResourceFactory.create(content_object=self.tenure,
                                               project=self.prj)
        self.user = UserFactory.create()
        assign_policies(self.user)

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'tenure_rel_id': self.tenure.id,
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
        response = self.request(method='PATCH', user=UserFactory.create(),
                                post_data=data)
        assert response.status_code == 404
        self.resource.refresh_from_db()
        assert self.resource.archived is True


class TenureRelationshipResourceDetachAPITest(APITestCase, UserTestCase,
                                              TestCase):
    view_class = api.TenureRelationshipResourceDetail

    def setup_models(self):
        self.prj = ProjectFactory.create()
        self.tenure = TenureRelationshipFactory.create(
            project=self.prj)
        self.resource = ResourceFactory.create(content_object=self.tenure,
                                               project=self.prj)
        self.user = UserFactory.create()
        assign_policies(self.user)

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'tenure_rel_id': self.tenure.id,
            'resource': self.resource.id,
        }

    def test_delete_resource(self):
        response = self.request(method='DELETE', user=self.user)
        assert response.status_code == 204
        assert len(self.tenure.resources) == 0
        assert Resource.objects.filter(
            id=self.resource.id, project=self.prj).exists()

    def test_delete_resource_with_unauthorized_user(self):
        response = self.request(method='DELETE', user=UserFactory.create())
        assert response.status_code == 403
        assert self.resource in self.tenure.resources
        assert Resource.objects.filter(
            id=self.resource.id, project=self.prj).exists()

    def test_delete_resource_with_archived_project(self):
        self.prj.archived = True
        self.prj.save()
        response = self.request(method='DELETE', user=self.user)
        assert response.status_code == 403
        assert self.resource in self.tenure.resources
        assert Resource.objects.filter(
            id=self.resource.id, project=self.prj).exists()

    def test_delete_resource_with_invalid_resource(self):
        new_resource = ResourceFactory.create(project=self.prj)
        response = self.request(method='DELETE', user=self.user, url_kwargs={
            'resource': new_resource.id
            })
        assert response.status_code == 404
        assert response.content['detail'] == "Not found."
        assert len(self.tenure.resources) == 1
        assert Resource.objects.filter(
            id=self.resource.id, project=self.prj).exists()
