import pytest
from django.forms import ValidationError, CharField, ChoiceField, BooleanField
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from jsonattrs.models import Attribute, AttributeType, Schema
from django.utils.translation import ugettext as _

from core.tests.utils.cases import UserTestCase
from organization.tests.factories import ProjectFactory
from party.tests.factories import PartyFactory
from party.models import TenureRelationship, Party, TENURE_RELATIONSHIP_TYPES
from .factories import SpatialUnitFactory
from ..models import SpatialUnit
from .. import forms
from ..widgets import SelectPartyWidget


class LocationFormTest(UserTestCase, TestCase):
    def test_create_location(self):
        data = {
            'geometry': '{"type": "Polygon","coordinates": [[[-0.1418137550354'
                        '004,51.55240622205599],[-0.14117002487182617,51.55167'
                        '905819532],[-0.1411914825439453,51.55181915488898],[-'
                        '0.1411271095275879,51.55254631651022],[-0.14181375503'
                        '54004,51.55240622205599]]]}',
            'type': 'CB'
        }
        project = ProjectFactory.create()
        form = forms.LocationForm(project_id=project.id,
                                  data=data,
                                  schema_selectors=())
        form.is_valid()
        form.save()

        assert SpatialUnit.objects.filter(project=project).count() == 1

    def test_create_location_with_attributes(self):
        data = {
            'geometry': '{"type": "Polygon","coordinates": [[[-0.1418137550354'
                        '004,51.55240622205599],[-0.14117002487182617,51.55167'
                        '905819532],[-0.1411914825439453,51.55181915488898],[-'
                        '0.1411271095275879,51.55254631651022],[-0.14181375503'
                        '54004,51.55240622205599]]]}',
            'type': 'CB',
            'attributes::fname': 'test'
        }

        project = ProjectFactory.create()
        content_type = ContentType.objects.get(
            app_label='spatial', model='spatialunit')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, ))
        attr_type = AttributeType.objects.get(name='text')
        Attribute.objects.create(
            schema=schema,
            name='fname', long_name='Test field',
            attr_type=attr_type, index=0,
            required=False, omit=False
        )

        form = forms.LocationForm(project_id=project.id,
                                  data=data,
                                  schema_selectors=(
                                    {'name': 'organization',
                                     'value': project.organization,
                                     'selector': project.organization.id},
                                    {'name': 'project',
                                     'value': project,
                                     'selector': project.id}
                                  ))
        form.is_valid()
        form.save()

        assert SpatialUnit.objects.filter(project=project).count() == 1
        unit = SpatialUnit.objects.filter(project=project).first()
        assert unit.attributes.get('fname') == 'test'


class TenureRelationshipFormTest(UserTestCase, TestCase):
    def test_init(self):
        project = ProjectFactory.create()
        spatial_unit = SpatialUnitFactory.create(project=project)
        form = forms.TenureRelationshipForm(project=project,
                                            spatial_unit=spatial_unit)
        content_type = ContentType.objects.get(
            app_label='party', model='tenurerelationship')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, ))
        attr_type = AttributeType.objects.get(name='text')
        Attribute.objects.create(
            schema=schema,
            name='r_name', long_name='Relationship field',
            attr_type=attr_type, index=0,
            required=False, omit=False
        )

        content_type = ContentType.objects.get(
            app_label='party', model='party')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, ))

        Attribute.objects.create(
            schema=schema, name='p_name', long_name='Party field',
            attr_type=AttributeType.objects.get(name='text'),
            index=0, required=True, default='John'
        )
        Attribute.objects.create(
            schema=schema, name='p_choice', long_name='Party field',
            attr_type=AttributeType.objects.get(name='select_one'),
            index=1, choices=['1', '2']
        )
        Attribute.objects.create(
            schema=schema, name='p_bool', long_name='Party field',
            attr_type=AttributeType.objects.get(name='boolean'),
            index=2, default='False'
        )

        form = forms.TenureRelationshipForm(
            data={'new_item': 'on'},
            project=project,
            spatial_unit=spatial_unit,
            schema_selectors=(
                {'name': 'organization',
                 'value': project.organization,
                 'selector': project.organization.id},
                {'name': 'project',
                 'value': project,
                 'selector': project.id}
            ))

        assert form.project == project
        assert form.spatial_unit == spatial_unit
        assert isinstance(form.fields['id'].widget, SelectPartyWidget)
        assert isinstance(form.fields['party::p_name'], CharField)
        assert form.fields['party::p_name'].initial == 'John'
        assert form.fields['party::p_name'].required is True
        assert isinstance(form.fields['party::p_choice'], ChoiceField)
        assert isinstance(form.fields['party::p_bool'], BooleanField)
        assert form.fields['party::p_bool'].initial is False
        assert isinstance(form.fields['relationship::r_name'], CharField)
        assert isinstance(form.fields['tenure_type'], ChoiceField)
        assert form.fields['tenure_type'].choices == (
            [('', _('Please select a relationship type'))] +
            sorted(list(TENURE_RELATIONSHIP_TYPES))
        )
        assert ("All Types" not in
                dict(form.fields['tenure_type'].choices).values())

    def test_clean_invalid_id(self):
        project = ProjectFactory.create()
        spatial_unit = SpatialUnitFactory.create(project=project)
        form = forms.TenureRelationshipForm(project=project,
                                            spatial_unit=spatial_unit,
                                            data={'new_entity': '', 'id': ''})
        form.is_valid()
        with pytest.raises(ValidationError):
            form.clean_id()

    def test_clean_valid_id(self):
        project = ProjectFactory.create()
        spatial_unit = SpatialUnitFactory.create(project=project)
        form = forms.TenureRelationshipForm(project=project,
                                            spatial_unit=spatial_unit,
                                            data={'new_entity': '',
                                                  'id': 'abc'})
        form.is_valid()
        assert form.clean_id() == 'abc'

    def test_clean_invalid_name(self):
        project = ProjectFactory.create()
        spatial_unit = SpatialUnitFactory.create(project=project)
        form = forms.TenureRelationshipForm(project=project,
                                            spatial_unit=spatial_unit,
                                            data={'new_entity': 'on',
                                                  'name': ''})
        form.is_valid()
        with pytest.raises(ValidationError):
            form.clean_name()

    def test_clean_valid_name(self):
        project = ProjectFactory.create()
        spatial_unit = SpatialUnitFactory.create(project=project)
        form = forms.TenureRelationshipForm(project=project,
                                            spatial_unit=spatial_unit,
                                            data={'new_entity': 'on',
                                                  'name': 'A'})
        form.is_valid()
        assert form.clean_name() == 'A'

    def test_save_exisiting_party(self):
        project = ProjectFactory.create()
        party = PartyFactory.create(project=project)
        spatial_unit = SpatialUnitFactory.create(project=project)

        form = forms.TenureRelationshipForm(project=project,
                                            spatial_unit=spatial_unit,
                                            data={'new_entity': '',
                                                  'id': party.id,
                                                  'tenure_type': 'CU'})
        form.is_valid()
        form.save()
        assert TenureRelationship.objects.count() == 1
        rel = TenureRelationship.objects.first()
        assert rel.party == party
        assert rel.spatial_unit == spatial_unit
        assert rel.tenure_type_id == 'CU'

    def test_save_new_party(self):
        project = ProjectFactory.create()
        spatial_unit = SpatialUnitFactory.create(project=project)
        form = forms.TenureRelationshipForm(project=project,
                                            spatial_unit=spatial_unit,
                                            data={'new_entity': 'on',
                                                  'id': '',
                                                  'name': 'The Beatles',
                                                  'party_type': 'GR',
                                                  'tenure_type': 'CU'})

        form.is_valid()
        form.save()

        assert Party.objects.count() == 1
        party = Party.objects.first()
        assert party.name == 'The Beatles'
        assert party.type == 'GR'

        assert TenureRelationship.objects.count() == 1
        rel = TenureRelationship.objects.first()
        assert rel.party == party
        assert rel.spatial_unit == spatial_unit
        assert rel.tenure_type_id == 'CU'

    def test_save_new_party_with_attributes(self):
        project = ProjectFactory.create()
        spatial_unit = SpatialUnitFactory.create(project=project)

        content_type = ContentType.objects.get(
            app_label='party', model='tenurerelationship')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, ))
        attr_type = AttributeType.objects.get(name='text')
        Attribute.objects.create(
            schema=schema,
            name='r_name', long_name='Relationship field',
            attr_type=attr_type, index=0,
            required=False, omit=False
        )

        content_type = ContentType.objects.get(
            app_label='party', model='party')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, ))
        attr_type = AttributeType.objects.get(name='text')
        Attribute.objects.create(
            schema=schema,
            name='p_name', long_name='Party field',
            attr_type=attr_type, index=0,
            required=False, omit=False
        )

        form = forms.TenureRelationshipForm(
            project=project,
            spatial_unit=spatial_unit,
            data={'new_entity': 'on',
                  'id': '',
                  'name': 'The Beatles',
                  'party::p_name': 'Party Name',
                  'party_type': 'GR',
                  'tenure_type': 'CU',
                  'relationship::r_name': 'Rel Name'},
            schema_selectors=(
                {'name': 'organization',
                 'value': project.organization,
                 'selector': project.organization.id},
                {'name': 'project',
                 'value': project,
                 'selector': project.id}
            ))

        form.is_valid()
        form.save()

        assert Party.objects.count() == 1
        party = Party.objects.first()
        assert party.name == 'The Beatles'
        assert party.type == 'GR'
        assert party.attributes.get('p_name') == 'Party Name'

        assert TenureRelationship.objects.count() == 1
        rel = TenureRelationship.objects.first()
        assert rel.party == party
        assert rel.spatial_unit == spatial_unit
        assert rel.tenure_type_id == 'CU'
        assert rel.attributes.get('r_name') == 'Rel Name'
