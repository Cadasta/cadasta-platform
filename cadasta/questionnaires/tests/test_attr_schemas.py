import os

import pytest

from buckets.test.storage import FakeS3Storage
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase
from jsonattrs.models import Attribute, Schema
from organization.tests.factories import ProjectFactory
from party.tests.factories import (PartyFactory, PartyRelationshipFactory,
                                   TenureRelationshipFactory)
from spatial.tests.factories import (SpatialUnitFactory,
                                     SpatialRelationshipFactory)

from .. import models
# from ..exceptions import InvalidXLSForm
from ..managers import create_attrs_schema
from .attr_schemas import (location_relationship_xform_group,
                           location_xform_group,
                           party_relationship_xform_group, party_xform_group,
                           tenure_relationship_xform_group)

path = os.path.dirname(settings.BASE_DIR)


class CreateAttributeSchemaTest(TestCase):

    def test_create_attribute_schemas(self):
        storage = FakeS3Storage()
        file = open(
            path + '/questionnaires/tests/files/xls-form-attrs.xlsx', 'rb')
        form = storage.save('xls-form-attrs.xlsx', file)
        project = ProjectFactory.create()
        models.Questionnaire.objects.create_from_form(
            xls_form=form,
            project=project
        )
        # test for expected schema and attribute creation
        assert 5 == Schema.objects.all().count()
        assert 8 == Attribute.objects.all().count()

    def test_party_attribute_schema(self):
        project = ProjectFactory.create(name='TestFactory')
        content_type = ContentType.objects.get(
            app_label='party', model='party')
        create_attrs_schema(
            project=project, dict=party_xform_group, errors=[])
        party = PartyFactory.create(
            name='TestParty', project=project,
            attributes={
                'homeowner': 'yes',
                'dob': '1980-01-01'
            }
        )
        assert 1 == Schema.objects.all().count()
        schema = Schema.objects.get(content_type=content_type)
        assert schema is not None
        assert schema.selectors == [project.organization.pk, project.pk]
        assert 'homeowner' in party.attributes.attributes
        assert 'dob' in party.attributes.attributes
        assert 'gender' in party.attributes.attributes
        assert 3 == Attribute.objects.filter(schema=schema).count()
        assert party.attributes['homeowner'] == 'yes'
        assert party.attributes['dob'] == '1980-01-01'

    def test_party_invalid_attribute(self):
        project = ProjectFactory.create(name='TestFactory')
        create_attrs_schema(
            project=project, dict=party_xform_group, errors=[])
        assert 1 == Schema.objects.all().count()
        with pytest.raises(KeyError):
            PartyFactory.create(
                name='TestParty', project=project,
                attributes={
                    'invalid_attribute': 'yes',
                    'dob': '1980-01-01'
                }
            )

    def test_spatial_unit_attribute_schema(self):
        project = ProjectFactory.create(name='TestFactory')
        content_type = ContentType.objects.get(
            app_label='spatial', model='spatialunit')
        create_attrs_schema(
            project=project, dict=location_xform_group, errors=[])
        spatial_unit = SpatialUnitFactory.create(
            name='Test', project=project,
            attributes={
                'quality': 'polygon_high'
            }
        )
        assert 1 == Schema.objects.all().count()
        schema = Schema.objects.get(content_type=content_type)
        assert schema is not None
        assert schema.selectors == [project.organization.pk, project.pk]
        assert 'quality' in spatial_unit.attributes.attributes
        assert 'polygon_high' == spatial_unit.attributes['quality']
        # notes field is omitted in xform
        assert 'notes' not in spatial_unit.attributes.attributes

    def test_spatial_unit_invalid_attribute(self):
        project = ProjectFactory.create(name='TestFactory')
        create_attrs_schema(
            project=project, dict=location_xform_group, errors=[])
        assert 1 == Schema.objects.all().count()
        with pytest.raises(KeyError):
            SpatialUnitFactory.create(
                name='TestLocation', project=project,
                attributes={
                    'invalid_attribute': 'yes',
                }
            )

    def test_spatial_relationship_schema(self):
        project = ProjectFactory.create(name='TestFactory')
        content_type = ContentType.objects.get(
            app_label='spatial', model='spatialrelationship')
        create_attrs_schema(
            project=project, dict=location_relationship_xform_group, errors=[])
        sur = SpatialRelationshipFactory.create(
            project=project, attributes={
                'notes': 'Some additional textual info'}
        )
        assert 1 == Schema.objects.all().count()
        schema = Schema.objects.get(content_type=content_type)
        assert schema is not None
        assert schema.selectors == [project.organization.pk, project.pk]
        assert 'notes' in sur.attributes.attributes

    def test_spatial_relationship_invalid_attribute(self):
        project = ProjectFactory.create(name='TestFactory')
        create_attrs_schema(
            project=project, dict=location_relationship_xform_group, errors=[])
        assert 1 == Schema.objects.all().count()
        with pytest.raises(KeyError):
            SpatialRelationshipFactory.create(
                project=project,
                attributes={
                    'invalid_attribute': 'yes',
                }
            )

    def test_party_relationship_schema(self):
        project = ProjectFactory.create(name='TestFactory')
        content_type = ContentType.objects.get(
            app_label='party', model='partyrelationship')
        create_attrs_schema(
            project=project, dict=party_relationship_xform_group, errors=[])
        pr = PartyRelationshipFactory.create(
            project=project, attributes={
                'notes': 'Some additional textual info'}
        )
        assert 1 == Schema.objects.all().count()
        schema = Schema.objects.get(content_type=content_type)
        assert schema is not None
        assert schema.selectors == [project.organization.pk, project.pk]
        assert 'notes' in pr.attributes.attributes

    def test_party_relationship_invalid_attribute(self):
        project = ProjectFactory.create(name='TestFactory')
        create_attrs_schema(
            project=project, dict=party_relationship_xform_group, errors=[])
        assert 1 == Schema.objects.all().count()
        with pytest.raises(KeyError):
            PartyRelationshipFactory.create(
                project=project,
                attributes={
                    'invalid_attribute': 'yes',
                }
            )

    def test_tenure_relationship_schema(self):
        project = ProjectFactory.create(name='TestFactory')
        content_type = ContentType.objects.get(
            app_label='party', model='tenurerelationship')
        create_attrs_schema(
            project=project, dict=tenure_relationship_xform_group, errors=[])
        tr = TenureRelationshipFactory.create(
            project=project, attributes={
                'notes': 'Some additional textual info'}
        )
        assert 1 == Schema.objects.all().count()
        schema = Schema.objects.get(content_type=content_type)
        assert schema is not None
        assert schema.selectors == [project.organization.pk, project.pk]
        assert 'notes' in tr.attributes.attributes

    def test_tenure_relationship_invalid_attribute(self):
        project = ProjectFactory.create(name='TestFactory')
        create_attrs_schema(
            project=project, dict=tenure_relationship_xform_group, errors=[])
        assert 1 == Schema.objects.all().count()
        with pytest.raises(KeyError):
            TenureRelationshipFactory.create(
                project=project,
                attributes={
                    'invalid_attribute': 'yes',
                }
            )

    def test_omit_attribute(self):
        project = ProjectFactory.create(name='TestFactory')
        create_attrs_schema(
            project=project, dict=location_xform_group, errors=[])
        with pytest.raises(KeyError):
            SpatialUnitFactory.create(
                project=project,
                attributes={
                    'notes': 'Some textual content',
                }
            )

    def test_required_attribute(self):
        project = ProjectFactory.create(name='TestFactory')
        content_type = ContentType.objects.get(
            app_label='party', model='party')
        create_attrs_schema(
            project=project, dict=party_xform_group, errors=[])
        # with pytest.raises(ValidationError):
        #     PartyFactory.create(
        #         project=project,
        #         attributes={}
        #     )

        # should raise validation error as dob value is required?
        PartyFactory.create(
            project=project,
            attributes={}
        )
        schema = Schema.objects.get(content_type=content_type)
        attr = Attribute.objects.get(schema=schema, name='dob')
        assert attr.required

    def test_invalid_choice_attribute(self):
        project = ProjectFactory.create(name='TestFactory')
        create_attrs_schema(
            project=project, dict=party_xform_group, errors=[])
        assert 1 == Schema.objects.all().count()
        with pytest.raises(ValidationError):
            PartyFactory.create(
                name='TestParty', project=project,
                attributes={
                    'homeowner': 'blah!',
                    'dob': '1980-01-01'
                }
            )
