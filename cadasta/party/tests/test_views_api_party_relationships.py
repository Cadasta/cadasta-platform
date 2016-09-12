import json
from django.test import TestCase

from rest_framework.exceptions import PermissionDenied
from tutelary.models import Policy, assign_user_policies
from skivvy import APITestCase

from accounts.tests.factories import UserFactory
from core.tests.utils.cases import UserTestCase
from organization.tests.factories import (ProjectFactory,
                                          OrganizationFactory,
                                          clause)
from organization.models import OrganizationRole
from party.tests.factories import PartyFactory, PartyRelationshipFactory
from party.models import PartyRelationship
from party.views import api


def assign_policies(user):
    clauses = {
        'clause': [
            {
                'effect': 'allow',
                'object': ['project/*',
                           'project/*/*',
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
                           'tenure_rel.*']
            }
        ]
    }
    policy = Policy.objects.create(
        name='basic-test',
        body=json.dumps(clauses))
    user.assign_policies(policy)


class PartyRelationshipCreateAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.PartyRelationshipCreate

    def setup_models(self):
        self.user = UserFactory.create()
        assign_policies(self.user)

        self.org = OrganizationFactory.create(slug='namati')
        self.prj = ProjectFactory.create(
            slug='test-project', organization=self.org, access='public')
        self.party1 = PartyFactory.create(project=self.prj, name='Landowner')
        self.party2 = PartyFactory.create(project=self.prj, name='Leaser')

    def setup_url_kwargs(self):
        return {
            'organization': self.org.slug,
            'project': self.prj.slug
        }

    def setup_post_data(self):
        return {
            'party1': self.party2.id,
            'party2': self.party1.id,
            'type': 'C'
        }

    def test_create_valid_record(self):
        response = self.request(user=self.user, method='POST')
        assert response.status_code == 201
        assert PartyRelationship.objects.count() == 1

    def test_create_record_with_nonexistent_org(self):
        response = self.request(user=self.user,
                                method='POST',
                                url_kwargs={'organization': 'evil-corp'})
        assert response.status_code == 404
        assert PartyRelationship.objects.count() == 0
        assert response.content['detail'] == "Project not found."

    def test_create_record_with_nonexistent_project(self):
        response = self.request(user=self.user,
                                method='POST',
                                url_kwargs={'project': 'world-domination'})
        assert response.status_code == 404
        assert PartyRelationship.objects.count() == 0
        assert response.content['detail'] == "Project not found."

    def test_create_record_with_unauthorized_user(self):
        response = self.request(method='POST')
        assert response.status_code == 403
        assert PartyRelationship.objects.count() == 0
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_create_private_record(self):
        self.prj.access = 'private'
        self.prj.save()
        response = self.request(user=self.user, method='POST')
        assert response.status_code == 201
        assert PartyRelationship.objects.count() == 1

    def test_create_private_record_with_unauthorized_user(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request(method='POST')
        assert response.status_code == 403
        assert PartyRelationship.objects.count() == 0
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
        assert PartyRelationship.objects.count() == 0
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_create_private_record_based_on_org_membership(self):
        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.org, user=user)
        response = self.request(user=user, method='POST')
        assert response.status_code == 403
        assert PartyRelationship.objects.count() == 0
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_create_invalid_record_with_same_party(self):
        invalid_data = {
            'party1': self.party2.id,
            'party2': self.party2.id,
            'type': 'C'
        }
        response = self.request(user=self.user,
                                method='POST',
                                post_data=invalid_data)
        assert response.status_code == 400
        assert PartyRelationship.objects.count() == 0
        assert (response.content['non_field_errors'][0] ==
                "The parties must be different")

    def test_create_invalid_record_with_different_project(self):
        other_party = PartyFactory.create(name="Other")
        invalid_data = {
            'party1': self.party1.id,
            'party2': other_party.id,
            'type': 'C'
        }
        response = self.request(user=self.user,
                                method='POST',
                                post_data=invalid_data)
        assert response.status_code == 400
        assert PartyRelationship.objects.count() == 0

        err_msg = ("'party1' project ({}) should be equal to 'party2' "
                   "project ({})")
        assert response.content['non_field_errors'][0] == (
            err_msg.format(self.prj.slug, other_party.project.slug))


class PartyRelationshipDetailAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.PartyRelationshipDetail

    def setup_models(self):
        self.user = UserFactory.create()
        assign_policies(self.user)

        self.org = OrganizationFactory.create(slug='namati')
        self.prj = ProjectFactory.create(
            slug='test-project', organization=self.org, access='public')
        self.party1 = PartyFactory.create(project=self.prj, name='Landowner')
        self.party2 = PartyFactory.create(project=self.prj, name='Leaser')
        self.rel = PartyRelationshipFactory.create(
            project=self.prj, party1=self.party1, party2=self.party2)

    def setup_url_kwargs(self):
        return {
            'organization': self.org.slug,
            'project': self.prj.slug,
            'party_rel_id': self.rel.id
        }

    def test_get_public_record_with_valid_user(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['id'] == self.rel.id

    def test_get_public_nonexistent_record(self):
        response = self.request(user=self.user,
                                url_kwargs={'party_rel_id': 'notanid'})
        assert response.status_code == 404
        assert response.content['detail'] == "PartyRelationship not found."

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
        OrganizationRole.objects.create(organization=self.org, user=user)

        response = self.request(user=user)
        assert response.status_code == 200
        assert response.content['id'] == self.rel.id


class PartyRelationshipUpdateAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.PartyRelationshipDetail

    def setup_models(self):
        self.user = UserFactory.create()
        assign_policies(self.user)

        self.org = OrganizationFactory.create(slug='namati')
        self.prj = ProjectFactory.create(
            slug='test-project', organization=self.org, access='public')
        self.party1 = PartyFactory.create(project=self.prj, name='Landowner')
        self.party2 = PartyFactory.create(project=self.prj, name='Leaser')
        self.rel = PartyRelationshipFactory.create(
            project=self.prj, party1=self.party1, party2=self.party2)
        self.party3 = PartyFactory.create(project=self.prj, name='Leaser')

    def setup_url_kwargs(self):
        return {
            'organization': self.org.slug,
            'project': self.prj.slug,
            'party_rel_id': self.rel.id
        }

    def setup_post_data(self):
        return {
            'party1': self.party3.id,
            'party2': self.party1.id,
        }

    def test_update_with_valid_data(self):
        response = self.request(user=self.user, method='PATCH')
        assert response.status_code == 200
        assert response.content['party1'] == self.party3.id
        assert response.content['party2'] == self.party1.id

    def test_update_with_nonexistent_org(self):
        response = self.request(user=self.user,
                                method='PATCH',
                                url_kwargs={'organization': 'evil-corp'})
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."
        self.rel.refresh_from_db()
        assert self.rel.party1 == self.party1
        assert self.rel.party2 == self.party2

    def test_update_with_nonexistent_project(self):
        response = self.request(user=self.user,
                                method='PATCH',
                                url_kwargs={'project': 'evil-corp'})
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."
        self.rel.refresh_from_db()
        assert self.rel.party1 == self.party1
        assert self.rel.party2 == self.party2

    def test_update_with_nonexistent_record(self):
        response = self.request(user=self.user,
                                method='PATCH',
                                url_kwargs={'party_rel_id': 'some-rel'})
        assert response.status_code == 404
        assert response.content['detail'] == "PartyRelationship not found."

    def test_update_with_unauthorized_user(self):
        response = self.request(method='PATCH')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

        self.rel.refresh_from_db()
        assert self.rel.party1 == self.party1
        assert self.rel.party2 == self.party2

    def test_update_private_record(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request(user=self.user, method='PATCH')
        assert response.status_code == 200
        assert response.content['party1'] == self.party3.id
        assert response.content['party2'] == self.party1.id

    def test_update_private_record_with_unauthorized_user(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request(method='PATCH')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

        self.rel.refresh_from_db()
        assert self.rel.party1 == self.party1
        assert self.rel.party2 == self.party2

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
        assert self.rel.party1 == self.party1
        assert self.rel.party2 == self.party2

    def test_update_private_record_based_on_org_membership(self):
        self.prj.access = 'private'
        self.prj.save()

        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.org, user=user)

        response = self.request(user=user, method='PATCH')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

        self.rel.refresh_from_db()
        assert self.rel.party1 == self.party1
        assert self.rel.party2 == self.party2

    def test_update_private_record_based_on_org_admin(self):
        self.prj.access = 'private'
        self.prj.save()

        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.org,
                                        user=user,
                                        admin=True)

        response = self.request(user=self.user, method='PATCH')
        assert response.status_code == 200
        assert response.content['party1'] == self.party3.id
        assert response.content['party2'] == self.party1.id

    def test_update_invalid_record_with_dupe_parties(self):
        response = self.request(user=self.user,
                                method='PATCH',
                                post_data={'party1': self.party1.id})
        assert response.status_code == 400
        assert response.content['non_field_errors'][0] == (
            "The parties must be different")
        self.rel.refresh_from_db()
        assert self.rel.party1 == self.party1
        assert self.rel.party2 == self.party2

    def test_update_invalid_record_with_different_project(self):
        other_party = PartyFactory.create(name="Other")
        response = self.request(user=self.user,
                                method='PATCH',
                                post_data={'party2': other_party.id})
        assert response.status_code == 400
        err_msg = (
            "'party1' project ({}) should be equal to 'party2' project ({})")
        assert response.content['non_field_errors'][0] == (
            err_msg.format(self.party1.project.slug, other_party.project.slug))


class PartyRelationshipDeleteAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.PartyRelationshipDetail

    def setup_models(self):
        self.user = UserFactory.create()
        assign_policies(self.user)

        self.org = OrganizationFactory.create(slug='namati')
        self.prj = ProjectFactory.create(
            slug='test-project', organization=self.org, access='public')
        self.party1 = PartyFactory.create(project=self.prj, name='Landowner')
        self.party2 = PartyFactory.create(project=self.prj, name='Leaser')
        self.rel = PartyRelationshipFactory.create(
            project=self.prj, party1=self.party1, party2=self.party2)

    def setup_url_kwargs(self):
        return {
            'organization': self.org.slug,
            'project': self.prj.slug,
            'party_rel_id': self.rel.id
        }

    def test_delete_record(self):
        response = self.request(method='DELETE', user=self.user)
        assert response.status_code == 204
        assert PartyRelationship.objects.count() == 0

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
                                url_kwargs={'party_rel_id': 'some-rel'})
        assert response.status_code == 404
        assert response.content['detail'] == "PartyRelationship not found."

    def test_delete_with_unauthorized_user(self):
        response = self.request(method='DELETE')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        assert PartyRelationship.objects.count() == 1

    def test_delete_private_record(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request(method='DELETE', user=self.user)
        assert response.status_code == 204
        assert PartyRelationship.objects.count() == 0

    def test_delete_private_record_with_unauthorized_user(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request(method='DELETE')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        assert PartyRelationship.objects.count() == 1

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
        assert PartyRelationship.objects.count() == 1

    def test_delete_private_record_based_on_org_membership(self):
        self.prj.access = 'private'
        self.prj.save()

        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.org, user=user)

        response = self.request(method='DELETE', user=user)
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        assert PartyRelationship.objects.count() == 1

    def test_delete_private_record_based_on_org_admin(self):
        self.prj.access = 'private'
        self.prj.save()

        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.org,
                                        user=user,
                                        admin=True)

        response = self.request(method='DELETE', user=user)
        assert response.status_code == 204
        assert PartyRelationship.objects.count() == 0
