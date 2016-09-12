import json
from django.test import TestCase
from rest_framework.exceptions import PermissionDenied
from skivvy import APITestCase

from accounts.tests.factories import UserFactory
from core.tests.utils.cases import UserTestCase
from organization.tests.factories import ProjectFactory, clause
from organization.models import OrganizationRole
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
                           'tenure_rel.*']
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
