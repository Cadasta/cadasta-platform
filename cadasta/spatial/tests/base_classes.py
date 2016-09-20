import json

from django.utils.translation import gettext as _
from django.contrib.auth.models import AnonymousUser
from rest_framework import status as status_code
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.exceptions import PermissionDenied

from core.tests.base_test_case import UserTestCase
from organization.models import OrganizationRole
from accounts.tests.factories import UserFactory
from organization.tests.factories import (OrganizationFactory,
                                          clause)
from tutelary.models import Policy


class RecordBaseTestCase(UserTestCase):

    def setUp(self):
        """Set up some policies and users having those policies."""

        super().setUp()

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
        self.user = UserFactory.create()
        self.user.assign_policies(policy)

        restricted_clauses = {
            'clause': [
                clause('allow', ['project.list'], ['organization/*']),
                clause('allow', ['project.view'], ['project/*/*'])
            ]
        }
        restricted_policy = Policy.objects.create(
            name='restricted',
            body=json.dumps(restricted_clauses))
        self.restricted_user = UserFactory.create()
        self.restricted_user.assign_policies(restricted_policy)


class RecordListBaseTestCase(RecordBaseTestCase):

    def _get(
        self, org_slug, prj_slug, user=None, query=None,
        status=None, length=None
    ):
        if user is None:
            user = self.user
        url = self.url.format(org=org_slug, prj=prj_slug)
        if query is not None:
            url += '?' + query
        request = APIRequestFactory().get(url)
        force_authenticate(request, user=user)
        response = self.view(
            request, organization=org_slug, project=prj_slug).render()
        content = json.loads(response.content.decode('utf-8'))
        if status is not None:
            print(response.status_code, status)
            assert response.status_code == status
        if status == status_code.HTTP_200_OK:
            assert length is not None
        if length is not None:
            assert len(content['features']) == length
        return content


class RecordListAPITest:

    # Hooks that need to be defined in the child class:
    # self._test_objs()
    # self.num_records

    def _test_list_private_record(
        self,
        status=None,              # Optional expected HTTP status status_code
        user=None,                # Optional user that does the update
        length=None,              # Expected number of records returned
        make_org_member=False,       # Flag to make the user an org member
        make_other_org_member=False  # Flag to make the user a member
                                     # of another org
    ):
        if user is None:
            user = self.user
        org, prj = self._test_objs(access='private')
        if make_org_member:
            OrganizationRole.objects.create(organization=org, user=user)
        if make_other_org_member:
            other_org = OrganizationFactory.create()
            OrganizationRole.objects.create(organization=other_org, user=user)
        if status == status_code.HTTP_200_OK and length is None:
            length = self.num_records
        content = self._get(
            org_slug=org.slug, prj_slug=prj.slug, user=user,
            status=status, length=length)
        if status == status_code.HTTP_403_FORBIDDEN:
            assert content['detail'] == PermissionDenied.default_detail

    def test_full_list_with_nonexistent_org(self):
        org, prj = self._test_objs()
        content = self._get(
            org_slug='evil-corp', prj_slug=prj.slug,
            status=status_code.HTTP_404_NOT_FOUND)
        assert content['detail'] == "Project not found."

    def test_full_list_with_nonexistent_project(self):
        org, prj = self._test_objs()
        content = self._get(
            org_slug=org.slug, prj_slug='world-domination',
            status=status_code.HTTP_404_NOT_FOUND)
        assert content['detail'] == "Project not found."

    def test_full_list_with_unauthorized_user(self):
        org, prj = self._test_objs()
        content = self._get(
            org_slug=org.slug, prj_slug=prj.slug, user=AnonymousUser(),
            status=status_code.HTTP_403_FORBIDDEN)
        assert content['detail'] == PermissionDenied.default_detail

    def test_list_private_record(self):
        self._test_list_private_record(status=status_code.HTTP_200_OK)

    def test_list_private_record_with_unauthorized_user(self):
        self._test_list_private_record(
            user=AnonymousUser(), status=status_code.HTTP_403_FORBIDDEN)

    def test_list_private_records_without_permission(self):
        self._test_list_private_record(
            user=self.restricted_user, status=status_code.HTTP_403_FORBIDDEN)

    def test_list_private_records_based_on_org_membership(self):
        self._test_list_private_record(
            user=UserFactory.create(), status=status_code.HTTP_200_OK,
            make_org_member=True)

    def test_list_private_records_with_other_org_membership(self):
        self._test_list_private_record(
            user=UserFactory.create(), status=status_code.HTTP_403_FORBIDDEN,
            make_other_org_member=True)


class RecordCreateBaseTestCase(RecordBaseTestCase):

    # Hooks that need to be defined in the child class:
    # self.record_model
    # self.num_records

    def _post(self, org_slug, prj_slug, data, status, user=None):
        if user is None:
            user = self.user
        url = self.url.format(org=org_slug, prj=prj_slug)
        request = APIRequestFactory().post(url, data=data, format='json')
        force_authenticate(request, user=user)
        response = self.view(
            request, organization=org_slug, project=prj_slug).render()
        content = json.loads(response.content.decode('utf-8'))
        print(response.status_code, status)
        assert response.status_code == status
        assert self.record_model.objects.count() == (
            self.num_records +
            (1 if status == status_code.HTTP_201_CREATED else 0))
        return content


class RecordCreateAPITest:

    # Hooks that need to be defined in the child class:
    # self.default_create_data
    # self._test_objs()

    def _test_create_private_record(
        self,
        status,                   # Expected HTTP status status_code
        user=None,                # Optional user that does the update
        count=None,               # Expected number of records in DB
        make_org_member=False,       # Flag to make the user an org member
        make_other_org_member=False  # Flag to make the user a member
                                     # of another org
    ):
        if user is None:
            user = self.user
        org, prj = self._test_objs(access='private')
        if make_org_member:
            OrganizationRole.objects.create(organization=org, user=user)
        if make_other_org_member:
            other_org = OrganizationFactory.create()
            OrganizationRole.objects.create(organization=other_org, user=user)
        content = self._post(
            org_slug=org.slug, prj_slug=prj.slug, user=user,
            status=status, data=self.default_create_data)
        if status == status_code.HTTP_403_FORBIDDEN:
            assert content['detail'] == PermissionDenied.default_detail

    def test_create_valid_record(self):
        org, prj = self._test_objs()
        self._post(
            org_slug=org.slug, prj_slug=prj.slug,
            data=self.default_create_data, status=status_code.HTTP_201_CREATED)

    def test_create_record_with_nonexistent_org(self):
        org, prj = self._test_objs()
        content = self._post(
            org_slug='evil-corp', prj_slug=prj.slug,
            data=self.default_create_data,
            status=status_code.HTTP_404_NOT_FOUND)
        assert content['detail'] == "Project not found."

    def test_create_record_with_nonexistent_project(self):
        org, prj = self._test_objs()
        content = self._post(
            org_slug=org.slug, prj_slug='world-domination',
            data=self.default_create_data,
            status=status_code.HTTP_404_NOT_FOUND)
        assert content['detail'] == "Project not found."

    def test_create_record_with_unauthorized_user(self):
        org, prj = self._test_objs()
        content = self._post(
            org_slug=org.slug, prj_slug=prj.slug, user=AnonymousUser(),
            data=self.default_create_data,
            status=status_code.HTTP_403_FORBIDDEN)
        assert content['detail'] == PermissionDenied.default_detail

    def test_create_private_record(self):
        self._test_create_private_record(status=status_code.HTTP_201_CREATED)

    def test_create_private_record_with_unauthorized_user(self):
        self._test_create_private_record(
            user=AnonymousUser(), status=status_code.HTTP_403_FORBIDDEN)

    def test_create_private_record_without_permission(self):
        self._test_create_private_record(
            user=self.restricted_user, status=status_code.HTTP_403_FORBIDDEN)

    def test_create_private_record_based_on_org_membership(self):
        self._test_create_private_record(
            user=UserFactory.create(), status=status_code.HTTP_403_FORBIDDEN,
            make_org_member=True)

    def test_create_private_record_with_other_org_membership(self):
        self._test_create_private_record(
            user=UserFactory.create(), status=status_code.HTTP_403_FORBIDDEN,
            make_other_org_member=True)


class RecordDetailBaseTestCase(RecordBaseTestCase):

    # Hooks that need to be defined in the child class:
    # self.record_id_url_var_name

    def _get(self, org_slug, prj_slug, record_id, user, status):
        url = self.url.format(org=org_slug, prj=prj_slug, record=record_id)
        request = APIRequestFactory().get(url)
        force_authenticate(request, user=user)
        kwargs = {self.record_id_url_var_name: record_id}
        response = self.view(
            request, organization=org_slug, project=prj_slug, **kwargs
        ).render()
        content = json.loads(response.content.decode('utf-8'))
        print(response.status_code, status)
        assert response.status_code == status
        return content

    def _patch(self, org_slug, prj_slug, record, data, user, status):
        url = self.url.format(org=org_slug, prj=prj_slug, record=record.id)
        request = APIRequestFactory().patch(url, data, format='json')
        force_authenticate(request, user=user)
        kwargs = {self.record_id_url_var_name: record.id}
        response = self.view(
            request, organization=org_slug, project=prj_slug, **kwargs
        ).render()
        content = json.loads(response.content.decode('utf-8'))
        print(response.status_code, status)
        assert response.status_code == status
        record.refresh_from_db()
        return content

    def _delete(self, org_slug, prj_slug, record_id, user, status):
        url = self.url.format(org=org_slug, prj=prj_slug, record=record_id)
        request = APIRequestFactory().delete(url)
        force_authenticate(request, user=user)
        kwargs = {self.record_id_url_var_name: record_id}
        response = self.view(
            request, organization=org_slug, project=prj_slug, **kwargs
        ).render()
        print(response.status_code, status)
        assert response.status_code == status
        if response.content:
            content = json.loads(response.content.decode('utf-8'))
            return content


class RecordDetailAPITest:

    # Hooks that need to be defined in the child class:
    # self.model_name
    # self._test_objs()
    # self.is_id_in_content()

    def _test_get_public_record(
        self,
        status,         # Expected HTTP status status_code
        user=None,      # Optional user that does the update
        org_slug=None,  # Optional org slug of record
        prj_slug=None   # Optional project slug of record
    ):
        # Set up request
        record = self._test_objs()[0]
        record_id = record.id
        if user is None:
            user = self.user
        if (
            status == status_code.HTTP_404_NOT_FOUND and
            prj_slug is None and org_slug is None
        ):
            record_id = 'notanid'
        if org_slug is None:
            org_slug = record.project.organization.slug
        if prj_slug is None:
            prj_slug = record.project.slug

        # Perform request
        content = self._get(
            org_slug=org_slug, prj_slug=prj_slug, record_id=record_id,
            user=user, status=status)

        # Perform post-checks
        if status == status_code.HTTP_200_OK:
            assert self.is_id_in_content(content, record.id)
        if status == status_code.HTTP_403_FORBIDDEN:
            assert content['detail'] == PermissionDenied.default_detail
        if status == status_code.HTTP_404_NOT_FOUND:
            if record_id == 'notanid':
                err_msg = _("{} not found.".format(self.model_name))
                assert content['detail'] == err_msg
            else:
                assert content['detail'] == _("Project not found.")

    def _test_get_private_record(
        self,
        status,                      # Expected HTTP status status_code
        user=None,                   # Optional user that does the update
        make_org_member=False,       # Flag to make the user an org member
        make_other_org_member=False  # Flag to make the user a member
                                     # of another org
    ):
        # Set up request
        record, org = self._test_objs(access='private')
        if user is None:
            user = self.user
        if make_org_member:
            OrganizationRole.objects.create(organization=org, user=user)
        if make_other_org_member:
            other_org = OrganizationFactory.create()
            OrganizationRole.objects.create(organization=other_org, user=user)

        # Perform request
        content = self._get(
            org_slug=org.slug, prj_slug=record.project.slug,
            record_id=record.id, user=user, status=status)

        # Perform post-checks
        if status == status_code.HTTP_200_OK:
            assert self.is_id_in_content(content, record.id)
        if status == status_code.HTTP_403_FORBIDDEN:
            assert content['detail'] == PermissionDenied.default_detail

    def test_get_public_record_with_valid_user(self):
        self._test_get_public_record(status_code.HTTP_200_OK)

    def test_get_public_nonexistent_record(self):
        self._test_get_public_record(status_code.HTTP_404_NOT_FOUND)

    def test_get_public_record_with_nonexistent_org(self):
        self._test_get_public_record(
            status_code.HTTP_404_NOT_FOUND, org_slug='evil-corp')

    def test_get_public_record_with_nonexistent_project(self):
        self._test_get_public_record(
            status_code.HTTP_404_NOT_FOUND, prj_slug='world-domination')

    def test_get_public_record_with_unauthorized_user(self):
        self._test_get_public_record(
            status_code.HTTP_403_FORBIDDEN, user=AnonymousUser())

    def test_get_private_record(self):
        self._test_get_private_record(status_code.HTTP_200_OK)

    def test_get_private_record_with_unauthorized_user(self):
        self._test_get_private_record(
            status_code.HTTP_403_FORBIDDEN, user=AnonymousUser())

    def test_get_private_record_without_permission(self):
        self._test_get_private_record(
            status_code.HTTP_403_FORBIDDEN, user=self.restricted_user)

    def test_get_private_record_based_on_org_membership(self):
        self._test_get_private_record(
            status_code.HTTP_200_OK, user=UserFactory.create(),
            make_org_member=True)

    def test_get_private_record_with_other_org_membership(self):
        self._test_get_private_record(
            status_code.HTTP_403_FORBIDDEN, user=UserFactory.create(),
            make_other_org_member=True)


class RecordUpdateAPITest:

    # Hooks that need to be defined in the child class:
    # self.model_name
    # self.record_factory
    # self._test_objs()
    # self.get_valid_updated_data()
    # self.check_for_unchanged()

    def _test_patch_public_record(
        self,
        get_new_data,       # Callback to return partially updated record
        status,             # Expected HTTP status status_code
        user=None,          # Optional user that does the update
        org_slug=None,      # Optional org slug of record
        prj_slug=None,      # Optional project slug of record
        record=None         # Optional existing record
    ):
        # Set up request
        existing_record, org = self._test_objs()
        record = record or existing_record
        if user is None:
            user = self.user
        if org_slug is None:
            org_slug = existing_record.project.organization.slug
        if prj_slug is None:
            prj_slug = existing_record.project.slug

        print(org_slug, prj_slug)
        # Perform request
        content = self._patch(
            org_slug=org_slug, prj_slug=prj_slug, record=record, user=user,
            status=status, data=get_new_data())

        # Perform post-checks
        if status == status_code.HTTP_403_FORBIDDEN:
            assert content['detail'] == PermissionDenied.default_detail
        if status == status_code.HTTP_404_NOT_FOUND:
            if record != existing_record:
                err_msg = _("{} not found.".format(self.model_name))
                assert content['detail'] == err_msg
            else:
                assert content['detail'] == _("Project not found.")
        if status != status_code.HTTP_200_OK:
            existing_content = self._get(
                org_slug=org.slug, prj_slug=existing_record.project.slug,
                record_id=existing_record.id, user=self.user,
                status=status_code.HTTP_200_OK)
            self.check_for_unchanged(existing_content)
        return content

    def _test_patch_private_record(
        self,
        get_new_data,           # Callback to return partially updated record
        status,                 # Expected HTTP status status_code
        user=None,              # Optional user that does the update
        make_org_member=False,       # Flag to make the user an org member
        make_org_admin=False,        # Flag to make the user an org admin
        make_other_org_member=False  # Flag to make the user a member
                                     # of another org
    ):
        # Set up request
        existing_record, org = self._test_objs(access='private')
        if user is None:
            user = self.user
        if make_org_member:
            OrganizationRole.objects.create(organization=org, user=user)
        if make_org_admin:
            OrganizationRole.objects.create(
                organization=org, user=user, admin=True)
        if make_other_org_member:
            other_org = OrganizationFactory.create()
            OrganizationRole.objects.create(organization=other_org, user=user)

        # Perform request
        content = self._patch(
            org_slug=org.slug, prj_slug=existing_record.project.slug,
            record=existing_record, user=user, data=get_new_data(),
            status=status)

        # Perform post-checks
        if status == status_code.HTTP_403_FORBIDDEN:
            assert content['detail'] == PermissionDenied.default_detail
        if status != status_code.HTTP_200_OK:
            existing_content = self._get(
                org_slug=org.slug, prj_slug=existing_record.project.slug,
                record_id=existing_record.id, user=self.user,
                status=status_code.HTTP_200_OK)
            self.check_for_unchanged(existing_content)
        return content

    def test_update_with_valid_data(self):
        content = self._test_patch_public_record(
            self.get_valid_updated_data, status_code.HTTP_200_OK)
        self.check_for_updated(content)

    def test_update_with_nonexistent_org(self):
        self._test_patch_public_record(
            self.get_valid_updated_data, status_code.HTTP_404_NOT_FOUND,
            org_slug='evil-corp')

    def test_update_with_nonexistent_project(self):
        self._test_patch_public_record(
            self.get_valid_updated_data, status_code.HTTP_404_NOT_FOUND,
            prj_slug='world-domination')

    def test_update_with_nonexistent_record(self):
        self._test_patch_public_record(
            self.get_valid_updated_data, status_code.HTTP_404_NOT_FOUND,
            record=self.record_factory.create())

    def test_update_with_unauthorized_user(self):
        self._test_patch_public_record(
            self.get_valid_updated_data, status_code.HTTP_403_FORBIDDEN,
            user=AnonymousUser())

    def test_update_private_record(self):
        content = self._test_patch_private_record(
            self.get_valid_updated_data, status_code.HTTP_200_OK)
        self.check_for_updated(content)

    def test_update_private_record_with_unauthorized_user(self):
        self._test_patch_private_record(
            self.get_valid_updated_data, status_code.HTTP_403_FORBIDDEN,
            user=AnonymousUser())

    def test_update_private_record_without_permission(self):
        self._test_patch_private_record(
            self.get_valid_updated_data, status_code.HTTP_403_FORBIDDEN,
            user=self.restricted_user)

    def test_update_private_record_based_on_org_membership(self):
        self._test_patch_private_record(
            self.get_valid_updated_data, status_code.HTTP_403_FORBIDDEN,
            user=UserFactory.create(), make_org_member=True)

    def test_update_private_record_based_on_org_admin(self):
        content = self._test_patch_private_record(
            self.get_valid_updated_data, status_code.HTTP_200_OK,
            user=UserFactory.create(), make_org_admin=True)
        self.check_for_updated(content)

    def test_update_private_record_with_other_org_membership(self):
        self._test_patch_private_record(
            self.get_valid_updated_data, status_code.HTTP_403_FORBIDDEN,
            user=UserFactory.create(), make_other_org_member=True)


class RecordDeleteAPITest:

    # Hooks that need to be defined in the child class:
    # self.model_name
    # self.record_factory
    # self._test_objs()

    def _test_delete_public_record(
        self,
        status,         # Expected HTTP status status_code
        user=None,      # Optional user that does the update
        org_slug=None,  # Optional org slug of record
        prj_slug=None,  # Optional project slug of record
        record=None     # Optional existing record
    ):
        # Set up request
        existing_record = self._test_objs()[0]
        record = record or existing_record
        if user is None:
            user = self.user
        if org_slug is None:
            org_slug = existing_record.project.organization.slug
        if prj_slug is None:
            prj_slug = existing_record.project.slug
        kwargs = {
            'org_slug': org_slug,
            'prj_slug': prj_slug,
            'record_id': record.id,
            'user': user,
        }

        # Perform request
        content = self._delete(status=status, **kwargs)

        # Perform post-checks
        kwargs['user'] = self.user
        kwargs['record_id'] = existing_record.id
        if status == status_code.HTTP_204_NO_CONTENT:
            self._get(status=status_code.HTTP_404_NOT_FOUND, **kwargs)
        if status == status_code.HTTP_403_FORBIDDEN:
            assert content['detail'] == PermissionDenied.default_detail
            self._get(status=status_code.HTTP_200_OK, **kwargs)
        if status == status_code.HTTP_404_NOT_FOUND:
            if record != existing_record:
                err_msg = _("{} not found.".format(self.model_name))
                assert content['detail'] == err_msg
            else:
                assert content['detail'] == _("Project not found.")

    def _test_delete_private_record(
        self,
        status,                      # Expected HTTP status status_code
        user=None,                   # Optional user that does the update
        make_org_member=False,       # Flag to make the user an org member
        make_org_admin=False,        # Flag to make the user an org admin
        make_other_org_member=False  # Flag to make the user a member
                                     # of another org
    ):
        # Set up request
        existing_record, org = self._test_objs(access='private')
        if user is None:
            user = self.user
        if make_org_member:
            OrganizationRole.objects.create(organization=org, user=user)
        if make_org_admin:
            OrganizationRole.objects.create(
                organization=org, user=user, admin=True)
        if make_other_org_member:
            other_org = OrganizationFactory.create()
            OrganizationRole.objects.create(organization=other_org, user=user)

        kwargs = {
            'org_slug': org.slug,
            'prj_slug': existing_record.project.slug,
            'record_id': existing_record.id,
            'user': user,
        }

        # Perform request
        content = self._delete(status=status, **kwargs)

        # Perform post-checks
        kwargs['user'] = self.user
        if status == status_code.HTTP_204_NO_CONTENT:
            self._get(status=status_code.HTTP_404_NOT_FOUND, **kwargs)
        if status == status_code.HTTP_403_FORBIDDEN:
            assert content['detail'] == PermissionDenied.default_detail
            self._get(status=status_code.HTTP_200_OK, **kwargs)

    def test_delete_record(self):
        self._test_delete_public_record(status_code.HTTP_204_NO_CONTENT)

    def test_delete_with_nonexistent_org(self):
        self._test_delete_public_record(
            status_code.HTTP_404_NOT_FOUND, org_slug='evil-corp')

    def test_delete_with_nonexistent_project(self):
        self._test_delete_public_record(
            status_code.HTTP_404_NOT_FOUND, prj_slug='world-domination')

    def test_delete_with_nonexistent_record(self):
        self._test_delete_public_record(
            status_code.HTTP_404_NOT_FOUND,
            record=self.record_factory.create())

    def test_delete_with_unauthorized_user(self):
        self._test_delete_public_record(
            status_code.HTTP_403_FORBIDDEN, user=AnonymousUser())

    def test_delete_private_record(self):
        self._test_delete_private_record(status_code.HTTP_204_NO_CONTENT)

    def test_delete_private_record_with_unauthorized_user(self):
        self._test_delete_private_record(
            status_code.HTTP_403_FORBIDDEN, user=AnonymousUser())

    def test_delete_private_record_without_permission(self):
        self._test_delete_private_record(
            status_code.HTTP_403_FORBIDDEN, user=self.restricted_user)

    def test_delete_private_record_based_on_org_membership(self):
        self._test_delete_private_record(
            status_code.HTTP_403_FORBIDDEN, user=UserFactory.create(),
            make_org_member=True)

    def test_delete_private_record_based_on_org_admin(self):
        self._test_delete_private_record(
            status_code.HTTP_204_NO_CONTENT, user=UserFactory.create(),
            make_org_admin=True)

    def test_delete_private_record_with_other_org_membership(self):
        self._test_delete_private_record(
            status_code.HTTP_403_FORBIDDEN, user=UserFactory.create(),
            make_other_org_member=True)
