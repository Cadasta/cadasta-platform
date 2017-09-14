"""Party serializer test cases."""
import pytest
from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from rest_framework.serializers import ValidationError
from jsonattrs.models import Attribute, AttributeType, Schema

from core.tests.utils.cases import UserTestCase
from core.messages import SANITIZE_ERROR
from organization.tests.factories import ProjectFactory
from questionnaires.tests import factories as q_factories
from spatial.tests.factories import SpatialUnitFactory
from party import serializers

from .factories import PartyFactory


class PartySerializerTest(UserTestCase, TestCase):
    def test_serialize_party(self):
        party = PartyFactory.create()
        serializer = serializers.PartySerializer(party)
        serialized = serializer.data

        assert serialized['id'] == party.id
        assert serialized['name'] == party.name
        assert serialized['type'] == party.type
        assert 'attributes' in serialized

    def test_create_party(self):
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

    def test_validate_valid_attributes(self):
        project = ProjectFactory.create(name='Test Project')
        content_type = ContentType.objects.get(
            app_label='party', model='party')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, ))

        Attribute.objects.create(
            schema=schema,
            name='notes',
            long_name='Notes',
            attr_type=AttributeType.objects.get(name='text'),
            index=0
        )
        Attribute.objects.create(
            schema=schema,
            name='age',
            long_name='Homeowner Age',
            attr_type=AttributeType.objects.get(name='integer'),
            index=1, required=True, default=0
        )

        party_data = {
            'name': 'Tea Party',
            'type': 'IN',
            'attributes': {
                'notes': 'Blah',
                'age': 2
            }
        }
        serializer = serializers.PartySerializer(
            data=party_data,
            context={'project': project}
        )

        cleaned = serializer.validate_attributes(party_data['attributes'])
        assert cleaned == party_data['attributes']

    def test_validate_invalid_attributes(self):
        project = ProjectFactory.create(name='Test Project')
        content_type = ContentType.objects.get(
            app_label='party', model='party')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, ))

        Attribute.objects.create(
            schema=schema,
            name='notes',
            long_name='Notes',
            attr_type=AttributeType.objects.get(name='text'),
            index=0
        )
        Attribute.objects.create(
            schema=schema,
            name='age',
            long_name='Homeowner Age',
            attr_type=AttributeType.objects.get(name='integer'),
            index=1, required=True, default=0
        )

        party_data = {
            'name': 'Tea Party',
            'type': 'IN',
            'attributes': {
                'notes': 'Blah',
                'age': 'Blah'
            }
        }
        serializer = serializers.PartySerializer(
            data=party_data,
            context={'project': project}
        )

        with pytest.raises(ValidationError) as e:
            serializer.validate_attributes(party_data['attributes'])
        assert 'Validation failed for age: "Blah"' in e.value.detail

    def test_full_invalid(self):
        project = ProjectFactory.create(name='Test Project')
        content_type = ContentType.objects.get(
            app_label='party', model='party')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, ))

        Attribute.objects.create(
            schema=schema,
            name='notes',
            long_name='Notes',
            attr_type=AttributeType.objects.get(name='text'),
            index=0
        )
        Attribute.objects.create(
            schema=schema,
            name='age',
            long_name='Homeowner Age',
            attr_type=AttributeType.objects.get(name='integer'),
            index=1, required=True, default=0
        )

        party_data = {
            'name': 'Tea Party',
            'type': 'IN',
            'attributes': {
                'notes': 'Blah',
                'age': 'Blah'
            }
        }
        serializer = serializers.PartySerializer(
            data=party_data,
            context={'project': project}
        )

        with pytest.raises(ValidationError) as e:
            serializer.is_valid(raise_exception=True)
        assert ('Validation failed for age: "Blah"'
                in e.value.detail['attributes'])

    def test_sanitize_strings(self):
        project = ProjectFactory.create(name='Test Project')
        content_type = ContentType.objects.get(
            app_label='party', model='party')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, ))

        Attribute.objects.create(
            schema=schema,
            name='notes',
            long_name='Notes',
            attr_type=AttributeType.objects.get(name='text'),
            index=0
        )
        Attribute.objects.create(
            schema=schema,
            name='age',
            long_name='Homeowner Age',
            attr_type=AttributeType.objects.get(name='integer'),
            index=1, required=True, default=0
        )

        party_data = {
            'name': '<Tea Party>',
            'type': 'IN',
            'attributes': {
                'notes': '<Blah>',
                'age': 2
            }
        }
        serializer = serializers.PartySerializer(
            data=party_data,
            context={'project': project}
        )

        with pytest.raises(ValidationError) as e:
            serializer.is_valid(raise_exception=True)
        assert e.value.detail['name']
        assert e.value.detail['attributes']


class TenureRelationshipSerializer(UserTestCase, TestCase):
    def test_valid_attributes(self):
        project = ProjectFactory.create(name='Test Project')
        su = SpatialUnitFactory.create(project=project)
        party = PartyFactory.create(project=project)

        content_type = ContentType.objects.get(
            app_label='party', model='tenurerelationship')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, ))

        Attribute.objects.create(
            schema=schema,
            name='notes',
            long_name='Notes',
            attr_type=AttributeType.objects.get(name='text'),
            index=0
        )
        Attribute.objects.create(
            schema=schema,
            name='age',
            long_name='Homeowner Age',
            attr_type=AttributeType.objects.get(name='integer'),
            index=1, required=True, default=0
        )

        data = {
            'spatial_unit': su.id,
            'party': party.id,
            'tenure_type': 'WR',
            'attributes': {
                'notes': 'Blah',
                'age': 2
            }
        }
        serializer = serializers.TenureRelationshipSerializer(
            data=data,
            context={'project': project}
        )
        assert serializer.is_valid() is True

    def test_valid_tenure_type(self):
        project = ProjectFactory.create()
        su = SpatialUnitFactory.create(project=project)
        party = PartyFactory.create(project=project)
        data = {
            'tenure_type': 'FH',
            'spatial_unit': su.id,
            'party': party.id
        }

        serializer = serializers.TenureRelationshipSerializer(
            data=data,
            context={'project': project})
        assert serializer.is_valid() is True

    def test_invalid_tenure_type(self):
        project = ProjectFactory.create()
        su = SpatialUnitFactory.create(project=project)
        party = PartyFactory.create(project=project)
        data = {
            'tenure_type': 'BOO',
            'spatial_unit': su.id,
            'party': party.id
        }

        serializer = serializers.TenureRelationshipSerializer(
            data=data,
            context={'project': project})
        assert serializer.is_valid() is False
        assert ("'BOO' is not a valid choice for field 'tenure_type'." in
                serializer.errors['tenure_type'])

    def test_valid_custom_tenure_type(self):
        project = ProjectFactory.create()

        questionnaire = q_factories.QuestionnaireFactory.create(
            project=project)
        question = q_factories.QuestionFactory.create(
            type='S1',
            name='tenure_type',
            questionnaire=questionnaire)
        q_factories.QuestionOptionFactory.create(
            question=question,
            name='FU',
            label='FU Label')

        su = SpatialUnitFactory.create(project=project)
        party = PartyFactory.create(project=project)
        data = {
            'tenure_type': 'FU',
            'spatial_unit': su.id,
            'party': party.id
        }

        serializer = serializers.TenureRelationshipSerializer(
            data=data,
            context={'project': project})
        assert serializer.is_valid() is True

    def test_invalid_custom_tenure_type(self):
        project = ProjectFactory.create()

        questionnaire = q_factories.QuestionnaireFactory.create(
            project=project)
        question = q_factories.QuestionFactory.create(
            type='S1',
            name='tenure_type',
            questionnaire=questionnaire)
        q_factories.QuestionOptionFactory.create(
            question=question,
            name='FU',
            label='FU Label')

        su = SpatialUnitFactory.create(project=project)
        party = PartyFactory.create(project=project)
        data = {
            'tenure_type': 'FH',
            'spatial_unit': su.id,
            'party': party.id
        }

        serializer = serializers.TenureRelationshipSerializer(
            data=data,
            context={'project': project})
        assert serializer.is_valid() is False
        assert ("'FH' is not a valid choice for field 'tenure_type'." in
                serializer.errors['tenure_type'])

    def test_invalid_attributes(self):
        project = ProjectFactory.create(name='Test Project')
        su = SpatialUnitFactory.create(project=project)
        party = PartyFactory.create(project=project)

        content_type = ContentType.objects.get(
            app_label='party', model='tenurerelationship')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, ))

        Attribute.objects.create(
            schema=schema,
            name='notes',
            long_name='Notes',
            attr_type=AttributeType.objects.get(name='text'),
            index=0
        )
        Attribute.objects.create(
            schema=schema,
            name='age',
            long_name='Homeowner Age',
            attr_type=AttributeType.objects.get(name='integer'),
            index=1, required=True, default=0
        )

        data = {
            'spatial_unit': su.id,
            'party': party.id,
            'tenure_type': 'WR',
            'attributes': {
                'notes': 'Blah',
                'age': 'Blah'
            }
        }
        serializer = serializers.TenureRelationshipSerializer(
            data=data,
            context={'project': project}
        )
        assert serializer.is_valid() is False
        assert serializer.errors['attributes']

    def test_sanitise_string(self):
        project = ProjectFactory.create(name='Test Project')
        su = SpatialUnitFactory.create(project=project)
        party = PartyFactory.create(project=project)

        content_type = ContentType.objects.get(
            app_label='party', model='tenurerelationship')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, ))

        Attribute.objects.create(
            schema=schema,
            name='notes',
            long_name='Notes',
            attr_type=AttributeType.objects.get(name='text'),
            index=0
        )
        Attribute.objects.create(
            schema=schema,
            name='age',
            long_name='Homeowner Age',
            attr_type=AttributeType.objects.get(name='integer'),
            index=1, required=True, default=0
        )

        data = {
            'spatial_unit': su.id,
            'party': party.id,
            'tenure_type': 'WR',
            'attributes': {
                'notes': '<Blah>',
                'age': 2
            }
        }
        serializer = serializers.TenureRelationshipSerializer(
            data=data,
            context={'project': project}
        )
        assert serializer.is_valid() is False
        assert SANITIZE_ERROR in serializer.errors['attributes']
