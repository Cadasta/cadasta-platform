"""Party serializer test cases."""

from rest_framework.test import APIRequestFactory

from core.tests.base_test_case import UserTestCase
from accounts.tests.factories import UserFactory
from organization.tests.factories import ProjectFactory
from party import serializers


class PartySerializerTest(UserTestCase):
    def test_create_party(self,):
        request = APIRequestFactory().post('/')
        user = UserFactory.create()
        project = ProjectFactory.create(name='Test Project')

        setattr(request, 'user', user)
        party_data = {'name': 'Tea Party', 'project': project.id}
        serializer = serializers.PartySerializer(
            data=party_data,
            context={'request', request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        party_instance = serializer.instance
        assert party_instance.name == 'Tea Party'
        assert party_instance.project_id == project.id
