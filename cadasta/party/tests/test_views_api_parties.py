"""Test cases for party api views."""

import json
from django.test import TestCase
from rest_framework.exceptions import PermissionDenied
from tutelary.models import Policy, assign_user_policies
from skivvy import APITestCase

from core.tests.utils.cases import UserTestCase, FileStorageTestCase
from organization.tests.factories import OrganizationFactory, ProjectFactory
from accounts.tests.factories import UserFactory
from resources.tests.factories import ResourceFactory
from resources.models import Resource
from ..tests.factories import PartyFactory

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
                'action': ['project.*', 'project.*.*', 'party.*']
            }, {
                'effect': 'allow',
                'object': ['party/*/*/*'],
                'action': ['party.*', 'party.resources.*']
            }
        ]
    }
    policy = Policy.objects.create(
        name='test-policy',
        body=json.dumps(clauses))
    assign_user_policies(user, policy)


class PartyListAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.PartyList

    def setup_models(self):
        self.user = UserFactory.create()
        assign_policies(self.user)
        self.org = OrganizationFactory.create()
        self.prj = ProjectFactory.create(
            organization=self.org, add_users=[self.user])

    def setup_url_kwargs(self):
        return {
            'organization': self.org.slug,
            'project': self.prj.slug
        }

    def test_full_list(self):
        """It should return all parties."""
        PartyFactory.create_batch(2, project=self.prj)
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert len(response.content['results']) == 2
        assert 'users' not in response.content['results'][0]

    def test_full_list_with_unauthorized_user(self):
        PartyFactory.create(project=self.prj)
        response = self.request()
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_search_filter(self):
        PartyFactory.create_from_kwargs([
            {'name': 'Test Party One', 'project': self.prj},
            {'name': 'Test Party Two', 'project': self.prj},
            {'name': 'Test Party Three', 'project': self.prj}
        ])
        response = self.request(user=self.user,
                                get_data={'name': 'Test Party One'})
        assert response.status_code == 200
        assert len(response.content['results']) == 1

    def test_type_filter(self):
        PartyFactory.create_from_kwargs([
            {'name': 'Test Party One', 'project': self.prj, 'type': 'IN'},
            {'name': 'Test Party Two', 'project': self.prj, 'type': 'IN'},
            {'name': 'Test Party Three', 'project': self.prj, 'type': 'GR'}
        ])
        response = self.request(user=self.user, get_data={'type': 'GR'})
        assert response.status_code == 200
        assert len(response.content['results']) == 1

    def test_ordering(self):
        PartyFactory.create_from_kwargs([
            {'name': 'Test Party One', 'project': self.prj},
            {'name': 'Test Party Two', 'project': self.prj},
            {'name': 'Test Party Three', 'project': self.prj}
        ])
        response = self.request(user=self.user, get_data={'ordering': 'name'})
        assert response.status_code == 200
        assert len(response.content['results']) == 3
        names = [party['name'] for party in response.content['results']]
        assert names == sorted(names)

    def test_reverse_ordering(self):
        PartyFactory.create_from_kwargs([
            {'name': 'Test Party One', 'project': self.prj},
            {'name': 'Test Party Two', 'project': self.prj},
            {'name': 'Test Party Three', 'project': self.prj}
        ])
        response = self.request(user=self.user, get_data={'ordering': '-name'})
        assert response.status_code == 200
        assert len(response.content['results']) == 3
        names = [party['name'] for party in response.content['results']]
        assert names == sorted(names, reverse=True)

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


class PartyCreateAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.PartyList

    def setup_models(self):
        self.user = UserFactory.create()
        assign_policies(self.user)
        self.org = OrganizationFactory.create()
        self.prj = ProjectFactory.create(
            organization=self.org, add_users=[self.user])

    def setup_url_kwargs(self):
        return {
            'organization': self.org.slug,
            'project': self.prj.slug
        }

    def test_add_party(self):
        data = {
            'name': 'TestParty',
            'description': 'Some description',
        }
        response = self.request(user=self.user, method='POST', post_data=data)
        assert response.status_code == 201
        assert self.prj.parties.count() == 1

    def test_add_party_to_archived_project(self):
        self.prj.archived = True
        self.prj.save()

        data = {
            'name': 'TestParty',
            'description': 'Some description',
            'project': self.prj.id
        }
        response = self.request(user=self.user, method='POST', post_data=data)
        assert response.status_code == 403
        assert self.prj.parties.count() == 0


class PartyDetailAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.PartyDetail

    def setup_models(self):
        self.user = UserFactory.create()
        assign_policies(self.user)
        self.org = OrganizationFactory.create()
        self.prj = ProjectFactory.create(
            organization=self.org, add_users=[self.user])
        self.party = PartyFactory.create(name="Test Party", project=self.prj)

    def setup_url_kwargs(self):
        return {
            'organization': self.org.slug,
            'project': self.prj.slug,
            'party': self.party.id
        }

    def test_party_detail(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['id'] == self.party.id

    def test_delete_party(self):
        response = self.request(user=self.user, method='DELETE')
        assert response.status_code == 204
        assert self.prj.parties.count() == 0

    def test_delete_party_in_archived_project(self):
        self.prj.archived = True
        self.prj.save()

        response = self.request(user=self.user, method='DELETE')
        assert response.status_code == 403
        assert self.prj.parties.count() == 1

    def test_update_party(self):
        data = {'name': 'Test Party Patched'}
        response = self.request(user=self.user, method='PATCH', post_data=data)
        assert response.status_code == 200
        self.party.refresh_from_db()
        assert self.party.name == response.content['name']

    def test_PATCH_party_with_anonymous_user(self):
        data = {'name': 'Test Party Patched'}
        response = self.request(method='PATCH', post_data=data)
        assert response.status_code == 403
        self.party.refresh_from_db()
        assert self.party.name != data['name']

    def test_PATCH_party_with_unauthorized_user(self):
        data = {'name': 'Test Party Patched'}
        user = UserFactory.create()
        response = self.request(method='PATCH', post_data=data, user=user)
        assert response.status_code == 403
        self.party.refresh_from_db()
        assert self.party.name != data['name']

    def test_PUT_party_with_anonymous_user(self):
        data = {'name': 'Test Party Patched'}
        response = self.request(method='PUT', post_data=data)
        assert response.status_code == 403
        self.party.refresh_from_db()
        assert self.party.name != data['name']

    def test_PUT_party_with_unauthorized_user(self):
        data = {'name': 'Test Party Patched'}
        user = UserFactory.create()
        response = self.request(method='PUT', post_data=data, user=user)
        assert response.status_code == 403
        self.party.refresh_from_db()
        assert self.party.name != data['name']

    def test_update_party_in_archived_project(self):
        self.prj.archived = True
        self.prj.save()

        data = {'name': 'Test Party Patched'}
        response = self.request(user=self.user, method='PATCH', post_data=data)
        assert response.status_code == 403
        self.party.refresh_from_db()
        assert self.party.name != 'Test Party Patched'


class PartyResourceListAPITest(APITestCase, UserTestCase, FileStorageTestCase,
                               TestCase):
    view_class = api.PartyResourceList

    def setup_models(self):
        self.user = UserFactory.create()
        assign_policies(self.user)
        self.prj = ProjectFactory.create(slug='test-project', access='public')
        self.party = PartyFactory.create(project=self.prj)
        self.resources = ResourceFactory.create_batch(
            2, project=self.prj, content_object=self.party)
        ResourceFactory.create(project=self.prj)

        self.file = self.get_file(
            '/resources/tests/files/image.jpg', 'rb')
        self.file_name = self.storage.save('resources/image.jpg',
                                           self.file.read())
        self.file.close()

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'party': self.party.id,
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
        assert len(response.content['results']) == 2

        returned_ids = [r['id'] for r in response.content['results']]
        assert all(res.id in returned_ids for res in self.resources)

    def test_full_list_with_unauthorized_user(self):
        response = self.request()
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_ordering(self):
        party = PartyFactory.create(project=self.prj)
        ResourceFactory.create_from_kwargs([
            {'content_object': party, 'project': self.prj, 'name': 'A'},
            {'content_object': party, 'project': self.prj, 'name': 'B'},
            {'content_object': party, 'project': self.prj, 'name': 'C'},
        ])

        response = self.request(
            user=self.user,
            url_kwargs={'party': party.id},
            get_data={'ordering': 'name'})
        assert response.status_code == 200
        assert len(response.content['results']) == 3
        names = [resource['name'] for resource in response.content['results']]
        assert(names == sorted(names))

    def test_reverse_ordering(self):
        party = PartyFactory.create(project=self.prj)
        ResourceFactory.create_from_kwargs([
            {'content_object': party, 'project': self.prj, 'name': 'A'},
            {'content_object': party, 'project': self.prj, 'name': 'B'},
            {'content_object': party, 'project': self.prj, 'name': 'C'},
        ])

        response = self.request(
            user=self.user,
            url_kwargs={'party': party.id},
            get_data={'ordering': '-name'})
        assert response.status_code == 200
        assert len(response.content['results']) == 3
        names = [resource['name'] for resource in response.content['results']]
        assert(names == sorted(names, reverse=True))

    def test_search_filter(self):
        file = self.get_file('/resources/tests/files/image.jpg', 'rb')
        not_found = self.storage.save('resources/bild.jpg', file.read())
        file.close()
        party = PartyFactory.create(project=self.prj)
        ResourceFactory.create_from_kwargs([
            {'content_object': party, 'project': self.prj,
                'file': self.file_name},
            {'content_object': party, 'project': self.prj,
                'file': self.file_name},
            {'content_object': party, 'project': self.prj,
                'file': not_found}
        ])

        response = self.request(
            user=self.user,
            url_kwargs={'organization': self.prj.organization.slug,
                        'project': self.prj.slug,
                        'party': party.id},
            get_data={'search': 'image'})
        assert response.status_code == 200
        assert len(response.content['results']) == 2

    def test_get_full_list_organization_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'organization': 'some-org'})
        assert response.status_code == 404
        assert response.content['detail'] == "Party not found."

    def test_get_full_list_project_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'project': 'some-prj'})
        assert response.status_code == 404
        assert response.content['detail'] == "Party not found."

    def test_get_full_list_spatial_unit_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'party': 'some-party'})
        assert response.status_code == 404
        assert response.content['detail'] == "Party not found."

    def test_archived_resources_not_listed(self):
        ResourceFactory.create(
            project=self.prj, content_object=self.party, archived=True)
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert len(response.content['results']) == 2

        returned_ids = [r['id'] for r in response.content['results']]
        assert all(res.id in returned_ids for res in self.resources)

    def test_add_resource(self):
        response = self.request(method='POST', user=self.user)
        assert response.status_code == 201
        assert self.party.resources.count() == 3

    def test_add_resource_with_unauthorized_user(self):
        response = self.request(method='POST', user=UserFactory.create())
        assert response.status_code == 403
        assert self.party.resources.count() == 2

    def test_add_existing_resource(self):
        new_resource = ResourceFactory.create()
        data = {'id': new_resource.id}
        response = self.request(method='POST', user=self.user, post_data=data)
        assert response.status_code == 201
        assert self.party.resources.count() == 3
        assert new_resource in self.party.resources

    def test_add_invalid_resource(self):
        data = {'name': ''}
        response = self.request(method='POST', user=self.user, post_data=data)
        assert response.status_code == 400
        assert self.party.resources.count() == 2
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
        assert self.party.resources.count() == 2


class PartyResourceDetailAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.PartyResourceDetail

    def setup_models(self):
        self.prj = ProjectFactory.create()
        self.party = PartyFactory.create(project=self.prj)
        self.resource = ResourceFactory.create(content_object=self.party,
                                               project=self.prj)
        self.user = UserFactory.create()
        assign_policies(self.user)

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'party': self.party.id,
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
        assert response.content['detail'] == "Party not found."

    def test_get_resource_from_spatial_unit_that_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'party': 'some-party'})
        assert response.status_code == 404
        assert response.content['detail'] == "Party not found."

    def test_get_resource_that_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'resource': 'abc123'})
        assert response.status_code == 404
        assert response.content['detail'] == "Not found."


class PartyResourceUpdateAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.PartyResourceDetail
    post_data = {'name': 'Updated'}

    def setup_models(self):
        self.prj = ProjectFactory.create()
        self.party = PartyFactory.create(project=self.prj)
        self.resource = ResourceFactory.create(content_object=self.party,
                                               project=self.prj)
        self.user = UserFactory.create()
        assign_policies(self.user)

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'party': self.party.id,
            'resource': self.resource.id,
        }

    def test_update_resource(self):
        response = self.request(method='PATCH', user=self.user)
        assert response.status_code == 200
        assert response.content['id'] == self.resource.id
        self.resource.refresh_from_db()
        assert self.resource.name == self.post_data['name']

    def test_PATCH_resource_with_unauthorized_user(self):
        response = self.request(method='PATCH', user=UserFactory.create())
        assert response.status_code == 403
        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']

    def test_PATCH_resource_with_anonymous_user(self):
        response = self.request(method='PATCH')
        assert response.status_code == 403
        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']

    def test_PUT_resource_with_unauthorized_user(self):
        response = self.request(method='PUT', user=UserFactory.create())
        assert response.status_code == 403
        self.resource.refresh_from_db()
        assert self.resource.name != self.post_data['name']

    def test_PUT_resource_with_anonymous_user(self):
        response = self.request(method='PUT')
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


class PartyResourceArchiveAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.PartyResourceDetail

    def setup_models(self):
        self.prj = ProjectFactory.create()
        self.party = PartyFactory.create(project=self.prj)
        self.resource = ResourceFactory.create(content_object=self.party,
                                               project=self.prj)
        self.user = UserFactory.create()
        assign_policies(self.user)

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'party': self.party.id,
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


class PartyResourceDetachAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.PartyResourceDetail

    def setup_models(self):
        self.prj = ProjectFactory.create()
        self.party = PartyFactory.create(project=self.prj)
        self.resource = ResourceFactory.create(content_object=self.party,
                                               project=self.prj)
        self.user = UserFactory.create()
        assign_policies(self.user)

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'party': self.party.id,
            'resource': self.resource.id,
        }

    def test_delete_resource(self):
        response = self.request(method='DELETE', user=self.user)
        assert response.status_code == 204
        assert len(self.party.resources) == 0
        assert Resource.objects.filter(
            id=self.resource.id, project=self.prj).exists()

    def test_delete_resource_with_unauthorized_user(self):
        response = self.request(method='DELETE', user=UserFactory.create())
        assert response.status_code == 403
        assert self.resource in self.party.resources
        assert Resource.objects.filter(
            id=self.resource.id, project=self.prj).exists()

    def test_delete_resource_with_archived_project(self):
        self.prj.archived = True
        self.prj.save()
        response = self.request(method='DELETE', user=self.user)
        assert response.status_code == 403
        assert self.resource in self.party.resources
        assert Resource.objects.filter(
            id=self.resource.id, project=self.prj).exists()

    def test_delete_resource_with_invalid_resource(self):
        new_resource = ResourceFactory.create(project=self.prj)
        response = self.request(method='DELETE', user=self.user, url_kwargs={
            'resource': new_resource.id
            })
        assert response.status_code == 404
        assert response.content['detail'] == "Not found."
        assert len(self.party.resources) == 1
        assert Resource.objects.filter(
            id=self.resource.id, project=self.prj).exists()
