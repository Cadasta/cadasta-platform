"""Test cases for party api views."""

import json

from django.http import QueryDict
# from django.utils.translation import gettext as _

from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import PermissionDenied
from tutelary.models import Policy, assign_user_policies

from core.tests.base_test_case import UserTestCase
from organization.tests.factories import OrganizationFactory, ProjectFactory
from accounts.tests.factories import UserFactory
from ..tests.factories import PartyFactory

from ..views import api


class PartyListAPITest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.view = api.PartyList.as_view()
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
                }
            ]
        }
        policy = Policy.objects.create(
            name='test-policy',
            body=json.dumps(clauses))
        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)
        # self.user = UserFactory.create()
        self.org = OrganizationFactory.create()
        self.prj = ProjectFactory.create(
            organization=self.org, add_users=[self.user])
        self.url = '/v1/organizations/{org}/projects/{prj}/parties/'

    def _get(self, org, prj, user=None, query=None, status=None, length=None):
        if user is None:
            user = self.user
        url = self.url.format(org=org, prj=prj)
        if query is not None:
            url += '?' + query
        request = APIRequestFactory().get(url)
        if query is not None:
            setattr(request, 'GET', QueryDict(query))
        force_authenticate(request, user=user)
        response = self.view(request, organization=org,
                             project=prj).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        if length is not None:
            assert len(content) == length
        return content

    def test_full_list(self):
        """It should return all parties."""
        PartyFactory.create_batch(2, project=self.prj)
        content = self._get(self.org.slug, self.prj.slug, status=200, length=2)
        assert 'users' not in content[0]

    def test_full_list_with_unauthorized_user(self):
        PartyFactory.create(project=self.prj)
        content = self._get(self.org.slug, self.prj.slug,
                            user=AnonymousUser(), status=403)
        assert content['detail'] == PermissionDenied.default_detail

    def test_search_filter(self):
        PartyFactory.create_from_kwargs([
            {'name': 'Test Party One', 'project': self.prj},
            {'name': 'Test Party Two', 'project': self.prj},
            {'name': 'Test Party Three', 'project': self.prj}
        ])
        self._get(self.org.slug,
                  self.prj.slug, query='name=Test Party One',
                  status=200, length=1)

    def test_type_filter(self):
        PartyFactory.create_from_kwargs([
            {'name': 'Test Party One', 'project': self.prj, 'type': 'IN'},
            {'name': 'Test Party Two', 'project': self.prj, 'type': 'IN'},
            {'name': 'Test Party Three', 'project': self.prj, 'type': 'GR'}
        ])
        self._get(self.org.slug,
                  self.prj.slug, query='type=GR',
                  status=200, length=1)

    def test_ordering(self):
        PartyFactory.create_from_kwargs([
            {'name': 'Test Party One', 'project': self.prj},
            {'name': 'Test Party Two', 'project': self.prj},
            {'name': 'Test Party Three', 'project': self.prj}
        ])
        content = self._get(self.org.slug,
                            self.prj.slug, query='ordering=name',
                            status=200, length=3)
        names = [party['name'] for party in content]
        assert names == sorted(names)

    def test_reverse_ordering(self):
        PartyFactory.create_from_kwargs([
            {'name': 'Test Party One', 'project': self.prj},
            {'name': 'Test Party Two', 'project': self.prj},
            {'name': 'Test Party Three', 'project': self.prj}
        ])
        content = self._get(self.org.slug,
                            self.prj.slug, query='ordering=-name',
                            status=200, length=3)
        names = [party['name'] for party in content]
        assert names == sorted(names, reverse=True)

    def test_get_full_list_organization_does_not_exist(self):
        project = ProjectFactory.create()
        content = self._get('some-org', project, status=404)
        assert content['detail'] == "Project not found."

    def test_get_full_list_project_does_not_exist(self):
        organization = OrganizationFactory.create()
        content = self._get(organization, 'some-prj', status=404)
        assert content['detail'] == "Project not found."


class PartyCreateAPITest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.view = api.PartyList.as_view()
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
                }
            ]
        }
        policy = Policy.objects.create(
            name='test-policy',
            body=json.dumps(clauses))
        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)
        self.org = OrganizationFactory.create()
        self.prj = ProjectFactory.create(
            organization=self.org, add_users=[self.user])
        self.url = '/v1/organizations/{org}/projects/{prj}/parties/'

    def _post(self, org, prj, data, user=None, status=None, count=None):
        if user is None:
            user = self.user
        url = self.url.format(org=org, prj=prj)
        request = APIRequestFactory().post(
            url, data, format='json'
        )
        force_authenticate(request, user=user)
        response = self.view(request, organization=org,
                             project=prj).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        if count is not None:
            assert self.prj.parties.count() == count
        return content

    def test_add_party(self):
        PartyFactory.create_batch(2, project=self.prj)
        data = {
            'name': 'TestParty',
            'description': 'Some description',
            'project': self.prj.id
        }
        self._post(self.org.slug,
                   self.prj.slug,
                   data,
                   status=201,
                   count=3)


class PartyDetailAPITest(UserTestCase):
    def setUp(self):
        super().setUp()
        self.view = api.PartyDetail.as_view()
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
        self.user = UserFactory.create()
        assign_user_policies(self.user, policy)
        self.org = OrganizationFactory.create()
        self.prj = ProjectFactory.create(
            organization=self.org, add_users=[self.user])
        self.url = '/v1/organizations/{org}/projects/{prj}/parties/{id}/'

    def _get(self, org, prj, party_id, user=None, status=None):
        if user is None:
            user = self.user
        url = self.url.format(org=org, prj=prj.slug, id=party_id)
        request = APIRequestFactory().get(url)
        force_authenticate(request, user=user)
        response = self.view(request, organization=org,
                             project=prj.slug, party=party_id).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        return content

    def _patch(self, org, prj, party_id, data, user=None, status=None):
        if user is None:
            user = self.user
        url = self.url.format(org=org, prj=prj, id=party_id)
        request = APIRequestFactory().patch(url, data)
        force_authenticate(request, user=user)
        response = self.view(request, organization=org,
                             project=prj, party=party_id).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            assert response.status_code == status
        return content

    def _delete(self, org, prj, party_id, user=None, status=None):
        if user is None:
            user = self.user
        url = self.url.format(org=org, prj=prj, id=party_id)
        request = APIRequestFactory().delete(url)
        force_authenticate(request, user=user)
        response = self.view(request, organization=org, project=prj,
                             party=party_id).render()

        if status is not None:
            assert response.status_code == status

    def test_party_detail(self):
        party = PartyFactory.create(name="Test Party", project=self.prj)
        content = self._get(self.org.slug, self.prj, party.id, status=200)
        assert content['id'] == party.id

    def test_delete_party(self):
        party = PartyFactory.create(name='Test Party', project=self.prj)
        self._delete(
            self.org.slug, self.prj.slug, party.id, status=204)

    def test_update_party(self):
        party = PartyFactory.create(name='Test Party', project=self.prj)
        data = {
            'name': 'Test Party Patched'
        }
        content = self._patch(self.org.slug, self.prj.slug,
                              party.id, data, status=200)
        party.refresh_from_db()
        assert party.name == content['name']
