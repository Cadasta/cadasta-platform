import pytest
from datetime import datetime
from django.utils.text import slugify
from django.test import TestCase
from django.utils.translation import gettext as _
from django.core import mail
from django.core.urlresolvers import reverse
from rest_framework.serializers import ValidationError
from rest_framework.test import APIRequestFactory

from accounts.tests.factories import UserFactory
from .. import serializers
from ..models import OrganizationRole, ProjectRole
from .factories import OrganizationFactory, ProjectFactory


class OrganizationSerializerTest(TestCase):
    def test_slug_field_is_set(self):
        request = APIRequestFactory().post('/')
        user = UserFactory.create()
        setattr(request, 'user', user)

        org_data = {
            'name': 'Test Organization',
        }

        serializer = serializers.OrganizationSerializer(
            data=org_data,
            context={
                'request': request
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        org_instance = serializer.instance
        assert org_instance.slug == slugify(org_data['name'])
        assert OrganizationRole.objects.filter(
                    organization=org_instance).count() == 1

    def test_slug_field_is_unique(self):
        OrganizationFactory.create(**{
            'slug': 'org-slug'
        })

        org_data = {
            'name': 'Org Slug',
            'slug': 'org-slug'
        }
        serializer = serializers.OrganizationSerializer(data=org_data)
        assert not serializer.is_valid()

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


class ProjectSerializerTest(TestCase):
    def test_organization_is_set(self):
        organization = OrganizationFactory.create()
        project_data = {
            'name': 'Project',
            'organization': organization
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
        assert project_instance.organization == organization


class ProjectGeometrySerializerTest(TestCase):
    def test_method_fields_work(self):
        project = ProjectFactory.create()
        test_data = serializers.ProjectGeometrySerializer(project).data

        assert test_data['properties']['org'] == project.organization.name
        assert test_data['properties']['url'] == reverse(
            'organization:project-dashboard',
            kwargs={ 'organization': project.organization.slug,
                     'project': project.project_slug })


class OrganizationUserSerializerTest(TestCase):
    def test_to_represenation(self):
        user = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user])

        serializer = serializers.OrganizationUserSerializer(
            user,
            context={
                'organization': org
            }
        )
        assert serializer.data['username'] == user.username
        assert serializer.data['email'] == user.email
        assert serializer.data['role'] == 'User'

    def test_list_to_representation(self):
        users = UserFactory.create_batch(2)
        org_admin = UserFactory.create()
        org = OrganizationFactory.create(add_users=users)
        OrganizationRole.objects.create(
            user=org_admin,
            organization=org,
            admin=True
        )

        serializer = serializers.OrganizationUserSerializer(
            org.users.all(),
            many=True,
            context={
                'organization': org
            }
        )

        assert len(serializer.data) == 3

        for u in serializer.data:
            if u['username'] is org_admin.username:
                assert u['role'] == 'Admin'
            else:
                assert u['role'] == 'User'

    def test_set_roles_with_username(self):
        user = UserFactory.create()
        org = OrganizationFactory.create()

        data = {
            'username': user.username,
            'role': 'Admin'
        }

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
        assert len(mail.outbox) == 1

    def test_set_roles_with_email(self):
        user = UserFactory.create()
        org = OrganizationFactory.create()

        data = {
            'username': user.email,
            'role': 'Admin'
        }

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
        assert len(mail.outbox) == 1

    def test_set_roles_for_user_that_does_not_exist(self):
        org = OrganizationFactory.create()

        data = {
            'username': 'some-user',
            'role': 'Admin'
        }

        serializer = serializers.OrganizationUserSerializer(
            data=data,
            context={
                'organization': org
            }
        )

        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert (_('User with username or email {username} '
                  'does not exist').format(username='some-user')
                in serializer.errors['username'])

    def test_update_roles_for_user(self):
        user = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user])

        data = {
            'role': 'Admin'
        }

        serializer = serializers.OrganizationUserSerializer(
            user,
            data=data,
            partial=True,
            context={
                'organization': org
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        role = OrganizationRole.objects.get(user=user, organization=org)
        assert role.admin is True


class ProjectUserSerializerTest(TestCase):
    def test_to_represenation(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])

        serializer = serializers.ProjectUserSerializer(
            user,
            context={
                'project': project
            }
        )

        assert serializer.data['username'] == user.username
        assert serializer.data['email'] == user.email
        assert serializer.data['role'] == 'PU'

    def test_list_to_representation(self):
        users = UserFactory.create_batch(2)
        prj_admin = UserFactory.create()
        project = ProjectFactory.create(add_users=users)
        ProjectRole.objects.create(
            user=prj_admin,
            project=project,
            role='PM'
        )

        serializer = serializers.ProjectUserSerializer(
            project.users.all(),
            many=True,
            context={
                'project': project
            }
        )

        assert len(serializer.data) == 3

        for u in serializer.data:
            if u['username'] is prj_admin.username:
                assert u['role'] == 'PM'
            else:
                assert u['role'] == 'PU'

    def test_set_roles_for_existing_user(self):
        user = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user])
        project = ProjectFactory.create(**{'organization': org})

        data = {
            'username': user.username,
            'role': 'DC'
        }

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

        data = {
            'username': user.username,
            'role': 'DC'
        }

        serializer = serializers.ProjectUserSerializer(
            data=data,
            context={
                'project': project
            }
        )

        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert (_('User {username} is not member of the '
                  'project\'s organization').format(username=user.username)
                in serializer.errors['username'])

    def test_set_roles_for_user_that_does_not_exist(self):
        project = ProjectFactory.create()

        data = {
            'username': 'some-user',
            'role': 'DC'
        }

        serializer = serializers.ProjectUserSerializer(
            data=data,
            context={
                'project': project
            }
        )

        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert (_('User with username or email {username} '
                  'does not exist').format(username='some-user')
                in serializer.errors['username'])

    def test_update_roles_for_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])

        data = {
            'role': 'PM'
        }
        serializer = serializers.ProjectUserSerializer(
            user,
            partial=True,
            data=data,
            context={
                'project': project
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        role = ProjectRole.objects.get(user=user, project=project)
        assert role.role == data['role']


class UserAdminSerializerTest(TestCase):
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
