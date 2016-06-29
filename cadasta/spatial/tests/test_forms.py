import pytest
from django.test import TestCase
from django.forms import ValidationError

from organization.tests.factories import ProjectFactory
from party.tests.factories import PartyFactory
from party.models import TenureRelationship, Party
from .factories import SpatialUnitFactory
from ..models import SpatialUnit
from .. import forms
from ..widgets import SelectPartyWidget


class LocationFormTest(TestCase):
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
        form = forms.LocationForm(project_id=project.id, data=data)
        form.is_valid()
        form.save()

        assert SpatialUnit.objects.filter(project=project).count() == 1


class TenureRelationshipFormTest(TestCase):
    def test_init(self):
        project = ProjectFactory.create()
        spatial_unit = SpatialUnitFactory.create(project=project)
        form = forms.TenureRelationshipForm(project=project,
                                            spatial_unit=spatial_unit)
        assert form.project == project
        assert form.spatial_unit == spatial_unit
        assert isinstance(form.fields['id'].widget, SelectPartyWidget)

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
