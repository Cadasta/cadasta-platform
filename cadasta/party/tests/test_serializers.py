"""Party serializer test cases."""

from core.tests.base_test_case import UserTestCase
from organization.tests.factories import ProjectFactory
from party import serializers

from .factories import PartyFactory


class PartySerializerTest(UserTestCase):
    def test_serialize_party(self):
        party = PartyFactory.create()
        serializer = serializers.PartySerializer(party)
        serialized = serializer.data

        assert serialized['id'] == party.id
        assert serialized['name'] == party.name
        assert serialized['type'] == party.type
        assert 'attributes' in serialized
        assert 'contacts' in serialized

        assert serialized['project']['id'] == party.project.id
        assert (serialized['project']['organization']['id'] ==
                party.project.organization.id)

    def test_create_party(self,):
        project = ProjectFactory.create(name='Test Project')

        party_data = {'name': 'Tea Party'}
        serializer = serializers.PartySerializer(
            data=party_data,
            context={'project': project}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        party_instance = serializer.instance
        assert party_instance.name == 'Tea Party'
        assert party_instance.project_id == project.id
