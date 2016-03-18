import pytest
from datetime import datetime
from django.utils.text import slugify
from django.test import TestCase
from rest_framework.serializers import ValidationError

from accounts.tests.factories import UserFactory
from .. import serializers
from ..models import OrganizationRole, ProjectRole
from ..serializers import OrganizationSerializer, UserAdminSerializer
from .factories import OrganizationFactory, ProjectFactory


class OrganizationSerializerTest(TestCase):
    def test_slug_field_is_set(self):
        org_data = {
            'name': 'Test Organization',
        }
        serializer = serializers.OrganizationSerializer(data=org_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        org_instance = serializer.instance
        assert org_instance.slug == slugify(org_data['name'])

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
        assert serializer.data['roles']['admin'] is False

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
                assert u['roles']['admin'] is True
            else:
                assert u['roles']['admin'] is False

    def test_set_roles_for_existing_user(self):
        user = UserFactory.create()
        org = OrganizationFactory.create()

        data = {
            'username': user.username,
            'roles': {
                'admin': True,
            }
        }

        serializer = serializers.OrganizationUserSerializer(
            data=data,
            context={
                'organization': org
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        role = OrganizationRole.objects.get(user=user, organization=org)
        assert role.admin == data['roles']['admin']

    def test_set_roles_for_user_that_does_not_exist(self):
        org = OrganizationFactory.create()

        data = {
            'username': 'some-user',
            'roles': {
                'admin': True
            }
        }

        serializer = serializers.OrganizationUserSerializer(
            data=data,
            context={
                'organization': org
            }
        )

        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert 'User some-user does not exist' in serializer.errors['username']

    def test_update_roles_for_user(self):
        user = UserFactory.create()
        org = OrganizationFactory.create(add_users=[user])

        data = {
            'roles': {
                'admin': True,
            }
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
        assert role.admin == data['roles']['admin']


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
        assert serializer.data['roles']['manager'] is False
        assert serializer.data['roles']['collector'] is False

    def test_list_to_representation(self):
        users = UserFactory.create_batch(2)
        prj_admin = UserFactory.create()
        project = ProjectFactory.create(add_users=users)
        ProjectRole.objects.create(
            user=prj_admin,
            project=project,
            manager=True
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
                assert u['roles']['manager'] is True
            else:
                assert u['roles']['manager'] is False

    def test_set_roles_for_existing_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create()

        data = {
            'username': user.username,
            'roles': {
                'manager': False,
                'collector': True,
            }
        }

        serializer = serializers.ProjectUserSerializer(
            data=data,
            context={
                'project': project
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        role = ProjectRole.objects.get(user=user, project=project)
        assert role.manager == data['roles']['manager']
        assert role.collector == data['roles']['collector']

    def test_set_roles_for_user_that_does_not_exist(self):
        project = ProjectFactory.create()

        data = {
            'username': 'some-user',
            'roles': {
                'manager': False,
                'collector': True,
            }
        }

        serializer = serializers.ProjectUserSerializer(
            data=data,
            context={
                'project': project
            }
        )

        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)
        assert 'User some-user does not exist' in serializer.errors['username']

    def test_update_roles_for_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create(add_users=[user])

        data = {
            'roles': {
                'manager': True,
            }
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
        assert role.manager == data['roles']['manager']
        assert role.collector is False


class UserAdminSerializerTest(TestCase):
    def test_user_fields_are_set(self):
        user = UserFactory.create(last_login=datetime.now())
        serializer = UserAdminSerializer(user)

        assert 'username' in serializer.data
        assert 'last_login' in serializer.data
        assert 'is_active' in serializer.data

    def test_organizations_are_serialized(self):
        user = UserFactory.create()
        OrganizationFactory.create(add_users=[user])
        OrganizationFactory.create(add_users=[user])

        serializer = UserAdminSerializer(user)
        assert 'organizations' in serializer.data
