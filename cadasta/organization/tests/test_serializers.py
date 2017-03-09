import json
import random
import pytest
from datetime import datetime
from tutelary.models import Role
from core.util import slugify
from django.test import TestCase
from django.utils.translation import gettext as _
from django.core.urlresolvers import reverse
from rest_framework.serializers import ValidationError
from rest_framework.test import APIRequestFactory

from core.tests.utils.cases import UserTestCase
from core.messages import SANITIZE_ERROR
from accounts.tests.factories import UserFactory
from .. import serializers
from ..models import OrganizationRole, ProjectRole, Project
from .factories import OrganizationFactory, ProjectFactory


class OrganizationSerializerTest(UserTestCase, TestCase):
    def test_slug_field_is_set(self):
        request = APIRequestFactory().post('/')
        user = UserFactory.create()
        setattr(request, 'user', user)

        org_data = {'name': "Test Organization"}

        serializer = serializers.OrganizationSerializer(
            data=org_data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        org_instance = serializer.instance
        assert org_instance.slug == slugify(
            org_data['name'], allow_unicode=True)
        assert OrganizationRole.objects.filter(
            organization=org_instance).count() == 1

    def test_unicode_slug_field_is_set(self):
        request = APIRequestFactory().post('/')
        user = UserFactory.create()
        setattr(request, 'user', user)

        org_data = {'name': "東京プロジェクト"}

        serializer = serializers.OrganizationSerializer(
            data=org_data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        org_instance = serializer.instance
        assert org_instance.slug == '東京プロジェクト'
        assert OrganizationRole.objects.filter(
            organization=org_instance).count() == 1

    def test_users_are_not_serialized(self):
        users = UserFactory.create_batch(2)
        org = OrganizationFactory.create(add_users=users)

        serializer = serializers.OrganizationSerializer([org], many=True)
        assert 'users' not in serializer.data[0]

    def test_users_are_serialized_detail_view(self):
        users = UserFactory.create_batch(2)
        org = OrganizationFactory.create(add_users=users)

        serializer = serializers.OrganizationSerializer(org, detail=True)
        assert 'users' in serializer.data

    def test_restricted_organization_name(self):
        request = APIRequestFactory().post('/')
        user = UserFactory.create()
        setattr(request, 'user', user)

        invalid_names = ('add', 'ADD', 'Add', 'new', 'NEW', 'New')
        data = {'name': random.choice(invalid_names)}
        serializer = serializers.OrganizationSerializer(
            data=data,
            context={'request': request}
        )
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert serializer.errors == {
            'name': ["Organization name cannot be “Add” or “New”."]
        }

    def test_update_with_restricted_organization_name(self):
        request = APIRequestFactory().post('/')
        user = UserFactory.create()
        setattr(request, 'user', user)
        org = OrganizationFactory.create(add_users=[user])

        invalid_names = ('add', 'ADD', 'Add', 'new', 'NEW', 'New')
        data = {'name': random.choice(invalid_names)}
        serializer = serializers.OrganizationSerializer(
            org,
            data=data,
            partial=True,
            context={'request': request}
        )
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert serializer.errors == {
            'name': ["Organization name cannot be “Add” or “New”."]
        }

    def test_duplicate_organization_name(self):
        existing_org = OrganizationFactory.create()

        request = APIRequestFactory().post('/')
        user = UserFactory.create()
        setattr(request, 'user', user)

        data = {'name': existing_org.name}
        serializer = serializers.OrganizationSerializer(
            data=data,
            context={'request': request}
        )
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert serializer.errors == {
            'name': ["Organization with this name already exists."]
        }

    def test_update_with_duplicate_organization_name(self):
        org_1 = OrganizationFactory.create()
        org_2 = OrganizationFactory.create()

        request = APIRequestFactory().post('/')
        user = UserFactory.create()
        setattr(request, 'user', user)

        data = {'name': org_1.name}
        serializer = serializers.OrganizationSerializer(
            org_2,
            data=data,
            partial=True,
            context={'request': request}
        )
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert serializer.errors == {
            'name': ["Organization with this name already exists."]
        }

    def test_sanitize_stings(self):
        request = APIRequestFactory().post('/')
        user = UserFactory.create()
        setattr(request, 'user', user)

        org_data = {'name': "<Test Organization>"}

        serializer = serializers.OrganizationSerializer(
            data=org_data,
            context={'request': request}
        )
        assert serializer.is_valid() is False
        assert SANITIZE_ERROR in serializer.errors['name']


class ProjectSerializerTest(TestCase):
    def test_project_is_set(self):
        organization = OrganizationFactory.create()
        project_data = {
            'name': "Project",
            'organization': organization,
            'extent': {
                'coordinates': [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0],
                                 [0., 1.0], [0.0, 0.0]]],
                'type': 'Polygon'
            }
        }
        serializer = serializers.ProjectSerializer(
            data=project_data,
            context={'organization': organization}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        project_instance = serializer.instance
        assert project_instance.organization == organization
        assert (json.loads(project_instance.extent.json) ==
                project_data['extent'])

    def test_project_public_visibility(self):
        organization = OrganizationFactory.create()
        project_data = {
            'name': "Project",
            'organization': organization,
            'access': 'public'
        }
        context = {
            'organization': organization
        }
        serializer = serializers.ProjectSerializer(
            data=project_data,
            context=context
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        project_instance = serializer.instance
        assert project_instance.access == 'public'

    def test_project_private_visibility(self):
        organization = OrganizationFactory.create()
        project_data = {
            'name': "Project",
            'organization': organization,
            'access': 'private'
        }
        context = {
            'organization': organization
        }
        serializer = serializers.ProjectSerializer(
            data=project_data,
            context=context
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        project_instance = serializer.instance
        assert project_instance.access == 'private'

    def test_restricted_project_name(self):
        org = OrganizationFactory.create()
        invalid_names = ('add', 'ADD', 'Add', 'new', 'NEW', 'New')
        data = {
            'name': random.choice(invalid_names),
            'organization': org,
            'access': 'private'
        }
        serializer = serializers.ProjectSerializer(
            data=data,
            context={'organization': org}
        )
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert serializer.errors == {
            'name': ["Project name cannot be “Add” or “New”."]
        }

    def test_update_with_restricted_project_name(self):
        org = OrganizationFactory.create()
        project = ProjectFactory.create(organization=org)
        invalid_names = ('add', 'ADD', 'Add', 'new', 'NEW', 'New')
        data = {'name': random.choice(invalid_names)}
        serializer = serializers.ProjectSerializer(
            project,
            data=data,
            partial=True,
            context={'organization': org}
        )
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert serializer.errors == {
            'name': ["Project name cannot be “Add” or “New”."]
        }

    def test_duplicate_project_name(self):
        existing_project = ProjectFactory.create()
        org = existing_project.organization
        data = {
            'name': existing_project.name,
            'organization': org,
        }
        serializer = serializers.ProjectSerializer(
            data=data,
            context={'organization': org}
        )
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert serializer.errors == {
            'name': [
                "Project with this name already exists in this organization."]
        }

    def test_duplicate_project_name_in_another_org(self):
        existing_project = ProjectFactory.create()
        another_org = OrganizationFactory.create()
        data = {
            'name': existing_project.name,
            'organization': another_org,
        }
        serializer = serializers.ProjectSerializer(
            data=data,
            context={'organization': another_org}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        project_instance = serializer.instance
        assert project_instance.name == existing_project.name
        assert Project.objects.count() == 2

    def test_update_with_duplicate_project_name(self):
        project_1 = ProjectFactory.create()
        org = project_1.organization
        project_2 = ProjectFactory.create(organization=org)
        data = {'name': project_1.name}
        serializer = serializers.ProjectSerializer(
            project_2,
            data=data,
            partial=True,
            context={'organization': org}
        )
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert serializer.errors == {
            'name': [
                "Project with this name already exists in this organization."]
        }

    def test_unicode_slug(self):
        org = OrganizationFactory.create()
        data = {
            'name': "東京プロジェクト 2016",
            'organization': org,
            'access': 'private'
        }
        serializer = serializers.ProjectSerializer(
            data=data,
            context={'organization': org}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        project_instance = serializer.instance
        assert project_instance.slug == '東京プロジェクト-2016'

    def test_sanitize_stings(self):
        org = OrganizationFactory.create()
        data = {
            'name': "<Name>"
        }
        serializer = serializers.ProjectSerializer(
            data=data,
            context={'organization': org}
        )
        assert serializer.is_valid() is False
        assert SANITIZE_ERROR in serializer.errors['name']


class ProjectGeometrySerializerTest(TestCase):
    def test_method_fields_work(self):
        project = ProjectFactory.create()
        test_data = serializers.ProjectGeometrySerializer(project).data

        assert test_data['properties']['org'] == project.organization.name
        assert test_data['properties']['url'] == reverse(
            'organization:project-dashboard',
            kwargs={'organization': project.organization.slug,
                    'project': project.slug})


class OrganizationUserSerializerTest(UserTestCase, TestCase):
    def test_to_represenation(self):
        user = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user])
        serializer = serializers.OrganizationUserSerializer(
            user,
            context={'organization': org}
        )

        assert serializer.data['username'] == user.username
        assert serializer.data['email'] == user.email
        assert serializer.data['admin'] is False

    def test_list_to_representation(self):
        users = UserFactory.create_batch(2)
        org_admin = UserFactory.create()
        org = OrganizationFactory.create(add_users=users)
        OrganizationRole.objects.create(
            user=org_admin, organization=org, admin=True
        )
        serializer = serializers.OrganizationUserSerializer(
            org.users.all(), many=True, context={'organization': org}
        )

        assert len(serializer.data) == 3

        for u in serializer.data:
            if u['username'] == org_admin.username:
                assert u['admin'] is True
            else:
                assert u['admin'] is False

    def test_set_roles_with_username(self):
        user = UserFactory.create()
        org = OrganizationFactory.create()
        data = {'username': user.username, 'admin': True}
        serializer = serializers.OrganizationUserSerializer(
            data=data,
            context={
                'organization': org,
                'domain': 'https://example.com',
                'sitename': 'Cadasta'
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        role = OrganizationRole.objects.get(user=user, organization=org)
        assert role.admin is True

    def test_set_roles_with_email(self):
        user = UserFactory.create()
        org = OrganizationFactory.create()
        data = {'username': user.email, 'admin': True}
        serializer = serializers.OrganizationUserSerializer(
            data=data,
            context={
                'organization': org,
                'domain': 'https://example.com',
                'sitename': 'Cadasta'
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        role = OrganizationRole.objects.get(user=user, organization=org)
        assert role.admin is True

    def test_set_roles_for_user_that_does_not_exist(self):
        org = OrganizationFactory.create()
        data = {'username': 'some-user', 'admin': True}
        serializer = serializers.OrganizationUserSerializer(
            data=data, context={'organization': org}
        )

        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert (_('User with username or email {username} '
                  'does not exist').format(username='some-user')
                in serializer.errors['username'])

    def test_set_roles_for_duplicate_username(self):
        org = OrganizationFactory.create()
        user1 = UserFactory.create(email='some-user@some.com')
        UserFactory.create(email='some-user@some.com')
        data = {'username': user1.email, 'admin': 'true'}
        serializer = serializers.OrganizationUserSerializer(
            data=data, context={'organization': org}
        )

        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert (_('More than one user found for username or email '
                  '{email}').format(email='some-user@some.com')
                in serializer.errors['username'])

    def test_set_role_when_role_exists(self):
        user = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user])
        serializer = serializers.OrganizationUserSerializer(
            data={'username': user.email, 'admin': 'True'},
            partial=True,
            context={'organization': org}
        )
        assert serializer.is_valid() is False
        assert ("Not able to add member. The role already exists." in
                serializer.errors['username'])

    def test_update_roles_for_user(self):
        user = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user])
        serializer = serializers.OrganizationUserSerializer(
            user,
            data={'admin': 'True'},
            partial=True,
            context={'organization': org}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        role = OrganizationRole.objects.get(user=user, organization=org)
        assert role.admin is True


class ProjectUserSerializerTest(UserTestCase, TestCase):
    def test_to_represenation(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])
        serializer = serializers.ProjectUserSerializer(
            user, context={'project': project}
        )

        assert serializer.data['username'] == user.username
        assert serializer.data['email'] == user.email
        assert serializer.data['role'] == 'PU'

    def test_list_to_representation(self):
        users = UserFactory.create_batch(2)
        prj_admin = UserFactory.create()
        org_admin = UserFactory.create()
        public_user = UserFactory.create()

        superuser = UserFactory.create()
        superuser_role = Role.objects.get(name='superuser')
        superuser.assign_policies(superuser_role)

        org = OrganizationFactory.create(
            add_users=[superuser, prj_admin, public_user])
        project = ProjectFactory.create(add_users=users, organization=org)

        OrganizationRole.objects.create(
            organization=org, user=org_admin, admin=True)
        ProjectRole.objects.create(
            project=project, user=prj_admin, role='PM')

        serializer = serializers.ProjectUserSerializer(
            org.users.all(),
            many=True,
            context={'project': project}
        )

        assert len(serializer.data) == 6

        for u in serializer.data:
            if u['username'] == superuser.username:
                assert u['role'] == 'A'
            elif u['username'] == org_admin.username:
                assert u['role'] == 'A'
            elif u['username'] == prj_admin.username:
                assert u['role'] == 'PM'
            elif u['username'] == public_user.username:
                assert u['role'] == 'Pb'
            else:
                assert u['role'] == 'PU'

    def test_set_roles_for_existing_user(self):
        user = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user])
        project = ProjectFactory.create(organization=org)
        data = {'username': user.username, 'role': 'DC'}
        serializer = serializers.ProjectUserSerializer(
            data=data,
            context={'project': project}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        role = ProjectRole.objects.get(user=user, project=project)
        assert role.role == data['role']

    def test_set_roles_for_user_who_is_not_an_org_member(self):
        user = UserFactory.create()
        project = ProjectFactory.create()
        data = {'username': user.username, 'role': 'DC'}
        serializer = serializers.ProjectUserSerializer(
            data=data,
            context={'project': project}
        )

        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert (_('User {username} is not member of the '
                  'project\'s organization').format(username=user.username)
                in serializer.errors['username'])

    def test_set_roles_for_user_that_does_not_exist(self):
        project = ProjectFactory.create()
        data = {'username': 'some-user', 'role': 'DC'}
        serializer = serializers.ProjectUserSerializer(
            data=data,
            context={'project': project}
        )

        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert (_('User with username or email {username} '
                  'does not exist').format(username='some-user')
                in serializer.errors['username'])

    def test_set_role_when_role_exists(self):
        user = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user])
        project = ProjectFactory.create(organization=org)
        ProjectRole.objects.create(user=user, project=project)
        serializer = serializers.ProjectUserSerializer(
            data={'username': user.username, 'role': 'DC'},
            partial=True,
            context={'project': project}
        )
        assert serializer.is_valid() is False
        assert ("Not able to add member. The role already exists." in
                serializer.errors['username'])

    def test_update_roles_for_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])
        data = {'role': 'PM'}
        serializer = serializers.ProjectUserSerializer(
            user,
            partial=True,
            data=data,
            context={'project': project}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        role = ProjectRole.objects.get(user=user, project=project)
        assert role.role == data['role']

    def test_update_roles_for_user_with_additional_payload(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])
        data = {'username': user.username, 'role': 'PM'}
        serializer = serializers.ProjectUserSerializer(
            user,
            partial=True,
            data=data,
            context={'project': project}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        role = ProjectRole.objects.get(user=user, project=project)
        assert role.role == data['role']

    def test_update_roles_for_organization_user(self):
        user = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user])
        project = ProjectFactory.create(organization=org)
        data = {'role': 'PM'}
        serializer = serializers.ProjectUserSerializer(
            user,
            partial=True,
            data=data,
            context={'project': project}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        role = ProjectRole.objects.get(user=user, project=project)
        assert role.role == data['role']

    def test_update_roles_for_org_admin(self):
        user = UserFactory.create(username='some-user')
        project = ProjectFactory.create()
        OrganizationRole.objects.create(organization=project.organization,
                                        user=user,
                                        admin=True)
        data = {'role': 'DC'}
        serializer = serializers.ProjectUserSerializer(
            user,
            partial=True,
            data=data,
            context={'project': project}
        )

        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert (('User some-user is an organization admin, the role cannot be'
                 ' updated.') in serializer.errors['non_field_errors'])

    def test_update_roles_for_superuser(self):
        user = UserFactory.create(username='some-user')
        superuser_role = Role.objects.get(name='superuser')
        user.assign_policies(superuser_role)

        project = ProjectFactory.create()
        OrganizationRole.objects.create(organization=project.organization,
                                        user=user,
                                        admin=True)
        data = {'role': 'DC'}
        serializer = serializers.ProjectUserSerializer(
            user,
            partial=True,
            data=data,
            context={'project': project}
        )

        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert (('User some-user is an organization admin, the role cannot be'
                 ' updated.') in serializer.errors['non_field_errors'])

    def test_update_roles_to_public_user(self):
        user = UserFactory.create(username='some-user')
        project = ProjectFactory.create(add_users=[user])
        assert (ProjectRole.objects.filter(project=project, user=user).exists()
                is True)
        data = {'role': 'Pb'}
        serializer = serializers.ProjectUserSerializer(
            user,
            partial=True,
            data=data,
            context={'project': project}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        assert (ProjectRole.objects.filter(project=project, user=user).exists()
                is False)


class UserAdminSerializerTest(UserTestCase, TestCase):
    def test_user_fields_are_set(self):
        user = UserFactory.create(last_login=datetime.now())
        serializer = serializers.UserAdminSerializer(user)

        assert 'username' in serializer.data
        assert 'last_login' in serializer.data
        assert 'is_active' in serializer.data

    def test_organizations_are_serialized(self):
        user = UserFactory.create()
        OrganizationFactory.create(add_users=[user])
        OrganizationFactory.create(add_users=[user])

        serializer = serializers.UserAdminSerializer(user)
        assert 'organizations' in serializer.data
