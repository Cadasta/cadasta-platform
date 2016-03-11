import json

from django.utils.text import slugify
from django.test import TestCase

from tutelary.models import Role, Policy

from .. import serializers

from accounts.tests.factories import UserFactory
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


class ProjectUserSerializerTest(TestCase):
    def test_to_internal_value_with_instance(self):
        user = UserFactory.create()
        serializer = serializers.ProjectUserSerializer(user)
        internal = serializer.to_internal_value(None)
        assert not internal

    def test_to_internal_value_no_roles_set(self):
        data = {}
        serializer = serializers.ProjectUserSerializer()
        internal = serializer.to_internal_value(data)
        assert not internal.get('roles')

    def test_to_internal_value(self):
        data = {
            'roles': {
                'manager': False,
                'collector': True,
            }
        }
        serializer = serializers.ProjectUserSerializer()
        internal = serializer.to_internal_value(data)
        assert not internal['roles']['manager']
        assert internal['roles']['collector']

    def test_to_representation(self):
        user = UserFactory.create()
        project = ProjectFactory.create()
        data = {
            'username': user.username,
            'roles': {
                'manager': True,
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

        assert serializer.data['username'] == user.username
        assert serializer.data['email'] == user.email
        assert serializer.data['roles']
        assert serializer.data['roles']['manager']
        assert serializer.data['roles']['collector']

    def test_set_roles_for_existing_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create()

        collector_pol = Policy.objects.create(
            name='default',
            body=json.dumps({
                "effect": "allow",
                "action": ["project.collect_data"],
                "object": ["project/*/*"]
            })
        )
        project_role = Role.objects.create(
            name='Data Collector',
            policies=[collector_pol],
            variables={
                'organization': project.organization.slug,
                'project': project.id}
        )

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
        # assert False, 'Fix this test when permissions work properly'
        # user.has_perm()

    def test_update_roles_for_user(self):
        user = UserFactory.create()
        project = ProjectFactory.create()

        manager_pol = Policy.objects.create(
            name='default',
            body=json.dumps({
                "effect": "allow",
                "action": ["project.*"],
                "object": ["project/*/*"]
            })
        )
        user.assign_policies(
            (manager_pol,
             {'organization': project.organization.slug,
              'project': project.id})
        )

        data = {
            'roles': {
                'manager': False,
                'collector': True,
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
        # assert False, 'Fix this test when permissions work properly'
