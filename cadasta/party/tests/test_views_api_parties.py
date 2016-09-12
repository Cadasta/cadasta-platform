"""Test cases for party api views."""

import json

from django.test import TestCase
from rest_framework.exceptions import PermissionDenied
from tutelary.models import Policy, assign_user_policies
from skivvy import APITestCase

from core.tests.utils.cases import UserTestCase
from organization.tests.factories import OrganizationFactory, ProjectFactory
from accounts.tests.factories import UserFactory
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
                'action': ['party.*']
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
        assert len(response.content) == 2
        assert 'users' not in response.content[0]

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
        assert len(response.content) == 1

    def test_type_filter(self):
        PartyFactory.create_from_kwargs([
            {'name': 'Test Party One', 'project': self.prj, 'type': 'IN'},
            {'name': 'Test Party Two', 'project': self.prj, 'type': 'IN'},
            {'name': 'Test Party Three', 'project': self.prj, 'type': 'GR'}
        ])
        response = self.request(user=self.user, get_data={'type': 'GR'})
        assert response.status_code == 200
        assert len(response.content) == 1

    def test_ordering(self):
        PartyFactory.create_from_kwargs([
            {'name': 'Test Party One', 'project': self.prj},
            {'name': 'Test Party Two', 'project': self.prj},
            {'name': 'Test Party Three', 'project': self.prj}
        ])
        response = self.request(user=self.user, get_data={'ordering': 'name'})
        assert response.status_code == 200
        assert len(response.content) == 3
        names = [party['name'] for party in response.content]
        assert names == sorted(names)

    def test_reverse_ordering(self):
        PartyFactory.create_from_kwargs([
            {'name': 'Test Party One', 'project': self.prj},
            {'name': 'Test Party Two', 'project': self.prj},
            {'name': 'Test Party Three', 'project': self.prj}
        ])
        response = self.request(user=self.user, get_data={'ordering': '-name'})
        assert response.status_code == 200
        assert len(response.content) == 3
        names = [party['name'] for party in response.content]
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

    def test_update_party(self):
        data = {'name': 'Test Party Patched'}
        response = self.request(user=self.user, method='PATCH', post_data=data)
        assert response.status_code == 200
        self.party.refresh_from_db()
        assert self.party.name == response.content['name']
