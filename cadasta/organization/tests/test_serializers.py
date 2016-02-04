from django.utils.text import slugify
from django.test import TestCase

from ..serializers import OrganizationSerializer

from accounts.tests.factories import UserFactory
from .factories import OrganizationFactory


class OrganizationSerializerTest(TestCase):
    def test_slug_field_is_set(self):
        org_data = {
            'name': 'Test Organization',
        }
        serializer = OrganizationSerializer(data=org_data)
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
        serializer = OrganizationSerializer(data=org_data)
        assert not serializer.is_valid()

    def test_users_are_not_serialized(self):
        users = UserFactory.create_batch(2)
        org = OrganizationFactory.create(add_users=users)

        serializer = OrganizationSerializer([org], many=True)
        assert 'users' not in serializer.data[0]

    def test_users_are_serialized_detail_view(self):
        users = UserFactory.create_batch(2)
        org = OrganizationFactory.create(add_users=users)

        serializer = OrganizationSerializer(org, detail=True)
        assert 'users' in serializer.data
