import json
from django.test import TestCase
from rest_framework.exceptions import PermissionDenied
from tutelary.models import Policy, assign_user_policies
from skivvy import APITestCase

from accounts.tests.factories import UserFactory
from organization.tests.factories import ProjectFactory, clause
from organization.models import OrganizationRole
from core.tests.utils.cases import UserTestCase
from .factories import SpatialUnitFactory, SpatialRelationshipFactory
from ..models import SpatialRelationship
from ..views import api


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


class SpatialRelationshipCreateAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.SpatialRelationshipCreate

    def setup_models(self, access='public'):
        self.user = UserFactory.create()
        assign_policies(self.user)

        self.prj = ProjectFactory.create(slug='test-project', access='public')
        self.su1 = SpatialUnitFactory.create(project=self.prj, type='AP')
        self.su2 = SpatialUnitFactory.create(project=self.prj, type='BU')

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug
        }

    def setup_post_data(self):
        return {
            'su1': self.su2.id,
            'su2': self.su1.id,
            'type': 'C'
        }

    def test_create_valid_record(self):
        response = self.request(user=self.user, method='POST')
        assert response.status_code == 201
        assert SpatialRelationship.objects.count() == 1

    def test_create_record_with_nonexistent_org(self):
        response = self.request(user=self.user,
                                method='POST',
                                url_kwargs={'organization': 'evil-corp'})
        assert response.status_code == 404
        assert SpatialRelationship.objects.count() == 0
        assert response.content['detail'] == "Project not found."

    def test_create_record_with_nonexistent_project(self):
        response = self.request(user=self.user,
                                method='POST',
                                url_kwargs={'project': 'world-domination'})
        assert response.status_code == 404
        assert SpatialRelationship.objects.count() == 0
        assert response.content['detail'] == "Project not found."

    def test_create_record_with_unauthorized_user(self):
        response = self.request(method='POST')
        assert response.status_code == 403
        assert SpatialRelationship.objects.count() == 0
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_create_private_record(self):
        self.prj.access = 'private'
        self.prj.save()
        response = self.request(user=self.user, method='POST')
        assert response.status_code == 201
        assert SpatialRelationship.objects.count() == 1

    def test_create_private_record_with_unauthorized_user(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request(method='POST')
        assert response.status_code == 403
        assert SpatialRelationship.objects.count() == 0
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
        assert SpatialRelationship.objects.count() == 0
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_create_private_record_based_on_org_membership(self):
        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.prj.organization,
                                        user=user)
        response = self.request(user=user, method='POST')
        assert response.status_code == 403
        assert SpatialRelationship.objects.count() == 0
        assert response.content['detail'] == PermissionDenied.default_detail

    def test_create_invalid_record_with_dupe_su(self):
        invalid_data = {
            'su1': self.su2.id,
            'su2': self.su2.id,
            'type': 'C'
        }
        response = self.request(user=self.user,
                                method='POST',
                                post_data=invalid_data)
        assert response.status_code == 400
        assert SpatialRelationship.objects.count() == 0
        assert (response.content['non_field_errors'][0] ==
                "The spatial units must be different")

    def test_create_invalid_record_with_different_project(self):
        other_su = SpatialUnitFactory.create()
        invalid_data = {
            'su1': self.su1.id,
            'su2': other_su.id,
            'type': 'C'
        }
        response = self.request(user=self.user,
                                method='POST',
                                post_data=invalid_data)
        err_msg = "'su1' project ({}) should be equal to 'su2' project ({})"
        assert response.content['non_field_errors'][0] == (
            err_msg.format(self.prj.slug, other_su.project.slug))


class SpatialRelationshipDetailAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.SpatialRelationshipDetail

    def setup_models(self, access='public'):
        self.user = UserFactory.create()
        assign_policies(self.user)

        self.prj = ProjectFactory.create(slug='test-project', access='public')
        self.su1 = SpatialUnitFactory.create(project=self.prj, type='AP')
        self.su2 = SpatialUnitFactory.create(project=self.prj, type='BU')
        self.rel = SpatialRelationshipFactory.create(
            project=self.prj, su1=self.su1, su2=self.su2)

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'spatial_rel_id': self.rel.id
        }

    def test_get_public_record_with_valid_user(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert response.content['id'] == self.rel.id

    def test_get_public_nonexistent_record(self):
        response = self.request(user=self.user,
                                url_kwargs={'spatial_rel_id': 'notanid'})
        assert response.status_code == 404
        assert response.content['detail'] == "SpatialRelationship not found."

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


class SpatialRelationshipUpdateAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.SpatialRelationshipDetail

    def setup_models(self, access='public'):
        self.user = UserFactory.create()
        assign_policies(self.user)

        self.prj = ProjectFactory.create(slug='test-project', access='public')
        self.su1 = SpatialUnitFactory.create(project=self.prj, type='AP')
        self.su2 = SpatialUnitFactory.create(project=self.prj, type='BU')
        self.rel = SpatialRelationshipFactory.create(
            project=self.prj, su1=self.su1, su2=self.su2)
        self.su3 = SpatialUnitFactory.create(project=self.prj, type='BU')

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'spatial_rel_id': self.rel.id
        }

    def setup_post_data(self):
        return {
            'su1': self.su2.id,
            'su2': self.su3.id,
        }

    def test_update_with_valid_data(self):
        response = self.request(user=self.user, method='PATCH')
        assert response.status_code == 200
        self.rel.refresh_from_db()
        assert self.rel.su1 == self.su2
        assert self.rel.su2 == self.su3

    def test_update_with_nonexistent_org(self):
        response = self.request(user=self.user,
                                method='PATCH',
                                url_kwargs={'organization': 'evil-corp'})
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."
        self.rel.refresh_from_db()
        assert self.rel.su1 == self.su1
        assert self.rel.su2 == self.su2

    def test_update_with_nonexistent_project(self):
        response = self.request(user=self.user,
                                method='PATCH',
                                url_kwargs={'project': 'evil-corp'})
        assert response.status_code == 404
        assert response.content['detail'] == "Project not found."
        self.rel.refresh_from_db()
        assert self.rel.su1 == self.su1
        assert self.rel.su2 == self.su2

    def test_update_with_nonexistent_record(self):
        response = self.request(user=self.user,
                                method='PATCH',
                                url_kwargs={'spatial_rel_id': 'some-rel'})
        assert response.status_code == 404
        assert response.content['detail'] == "SpatialRelationship not found."

    def test_update_with_unauthorized_user(self):
        response = self.request(method='PATCH')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

        self.rel.refresh_from_db()
        assert self.rel.su1 == self.su1
        assert self.rel.su2 == self.su2

    def test_update_private_record(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request(user=self.user, method='PATCH')
        assert response.status_code == 200
        self.rel.refresh_from_db()
        assert self.rel.su1 == self.su2
        assert self.rel.su2 == self.su3

    def test_update_private_record_with_unauthorized_user(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request(method='PATCH')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail

        self.rel.refresh_from_db()
        assert self.rel.su1 == self.su1
        assert self.rel.su2 == self.su2

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
        assert self.rel.su1 == self.su1
        assert self.rel.su2 == self.su2

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
        assert self.rel.su1 == self.su1
        assert self.rel.su2 == self.su2

    def test_update_private_record_based_on_org_admin(self):
        self.prj.access = 'private'
        self.prj.save()

        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.prj.organization,
                                        user=user,
                                        admin=True)

        response = self.request(user=self.user, method='PATCH')
        assert response.status_code == 200
        self.rel.refresh_from_db()
        assert self.rel.su1 == self.su2
        assert self.rel.su2 == self.su3

    def test_update_invalid_record_with_dupe_su(self):
        response = self.request(user=self.user,
                                method='PATCH',
                                post_data={'su2': self.su2.id})
        assert response.status_code == 400
        assert response.content['non_field_errors'][0] == (
            "The spatial units must be different")
        self.rel.refresh_from_db()
        assert self.rel.su1 == self.su1
        assert self.rel.su2 == self.su2

    def test_update_invalid_record_with_different_project(self):
        other_su = SpatialUnitFactory.create()
        response = self.request(user=self.user,
                                method='PATCH',
                                post_data={'su2': other_su.id})
        assert response.status_code == 400
        err_msg = "'su1' project ({}) should be equal to 'su2' project ({})"
        assert response.content['non_field_errors'][0] == (
            err_msg.format(self.su1.project.slug, other_su.project.slug))


class SpatialRelationshipDeleteAPITest(APITestCase, UserTestCase, TestCase):
    view_class = api.SpatialRelationshipDetail

    def setup_models(self, access='public'):
        self.user = UserFactory.create()
        assign_policies(self.user)

        self.prj = ProjectFactory.create(slug='test-project', access='public')
        self.su1 = SpatialUnitFactory.create(project=self.prj, type='AP')
        self.su2 = SpatialUnitFactory.create(project=self.prj, type='BU')
        self.rel = SpatialRelationshipFactory.create(
            project=self.prj, su1=self.su1, su2=self.su2)
        self.su3 = SpatialUnitFactory.create(project=self.prj, type='BU')

    def setup_url_kwargs(self):
        return {
            'organization': self.prj.organization.slug,
            'project': self.prj.slug,
            'spatial_rel_id': self.rel.id
        }

    def test_delete_record(self):
        response = self.request(method='DELETE', user=self.user)
        assert response.status_code == 204
        assert SpatialRelationship.objects.count() == 0

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
                                url_kwargs={'spatial_rel_id': 'some-rel'})
        assert response.status_code == 404
        assert response.content['detail'] == "SpatialRelationship not found."

    def test_delete_with_unauthorized_user(self):
        response = self.request(method='DELETE')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        assert SpatialRelationship.objects.count() == 1

    def test_delete_private_record(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request(method='DELETE', user=self.user)
        assert response.status_code == 204
        assert SpatialRelationship.objects.count() == 0

    def test_delete_private_record_with_unauthorized_user(self):
        self.prj.access = 'private'
        self.prj.save()

        response = self.request(method='DELETE')
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        assert SpatialRelationship.objects.count() == 1

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
        assert SpatialRelationship.objects.count() == 1

    def test_delete_private_record_based_on_org_membership(self):
        self.prj.access = 'private'
        self.prj.save()

        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.prj.organization,
                                        user=user)

        response = self.request(method='DELETE', user=user)
        assert response.status_code == 403
        assert response.content['detail'] == PermissionDenied.default_detail
        assert SpatialRelationship.objects.count() == 1

    def test_delete_private_record_based_on_org_admin(self):
        self.prj.access = 'private'
        self.prj.save()

        user = UserFactory.create()
        OrganizationRole.objects.create(organization=self.prj.organization,
                                        user=user,
                                        admin=True)

        response = self.request(method='DELETE', user=user)
        assert response.status_code == 204
        assert SpatialRelationship.objects.count() == 0
