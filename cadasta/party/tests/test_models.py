"""TestCases for Party models."""

from datetime import date

from django.test import TestCase
from organization.tests.factories import ProjectFactory
from party.models import Party, TenureRelationshipType
from party.tests.factories import (PartyFactory, PartyRelationshipFactory,
                                   TenureRelationshipFactory)
from spatial.tests.factories import SpatialUnitFactory


class PartyTest(TestCase):

    def test_str(self):
        party = PartyFactory.create(name='TeaParty')
        assert str(party) == '<Party: TeaParty>'

    def test_repr(self):
        party = PartyFactory.create(name='TeaParty')
        assert repr(party) == '<Party: TeaParty>'

    def test_has_random_id(self):
        party = PartyFactory.create(name='TeaParty')
        assert type(party.id) is not int

    def test_has_project_id(self):
        party = PartyFactory.create(name='TeaParty')
        assert type(party.project_id) is not None
        assert type(party.project_id) is not int

    def test_setting_type(self):
        party = PartyFactory.create(
            type=Party.GROUP)
        assert party.type == 'GR'
        assert party.get_type_display() == 'Group'

    def test_adding_attributes(self):
        party = PartyFactory.create(
            attributes={
                'description': 'Mad Hatters Tea Party'
            })
        assert party.attributes['description'] == 'Mad Hatters Tea Party'


class PartyRelationshipTest(TestCase):

    def test_relationships_creation(self):
        relationship = PartyRelationshipFactory(
            party1__name='Mad Hatter',
            party2__name='Mad Hatters Tea Party')
        party2_name = str(relationship.party1.relationships.all()[0])
        assert party2_name == '<Party: Mad Hatters Tea Party>'

    def test_reverse_relationship(self):
        relationship = PartyRelationshipFactory(
            party1__name='Mad Hatter',
            party2__name='Mad Hatters Tea Party')
        party1_name = str(relationship.party2.relationships_set.all()[0])
        assert party1_name == '<Party: Mad Hatter>'

    def test_relationship_type(self):
        relationship = PartyRelationshipFactory(type='M')
        assert relationship.type == 'M'
        assert relationship.get_type_display() == 'is-member-of'

    def test_set_attributes(self):
        relationship = PartyRelationshipFactory.create(
            attributes={
                'description':
                'Mad Hatter attends Tea Party'
            })
        assert relationship.attributes[
            'description'] == 'Mad Hatter attends Tea Party'


class TenureRelationshipTest(TestCase):

    def setUp(self):
        self.project = ProjectFactory.create(name='TestProject')
        self.party = PartyFactory.create(
            name='TestParty', project=self.project)
        self.spatial_unit = SpatialUnitFactory.create(
            name='TestSpatialUnit', project=self.project)

    def test_tenure_relationship_creation(self):
        tenure_relationship = TenureRelationshipFactory.create(
            party=self.party, spatial_unit=self.spatial_unit)
        assert tenure_relationship.tenure_type is not None
        d1 = date.today().isoformat()
        d2 = tenure_relationship.acquired_date.isoformat()
        assert d1 == d2
        assert tenure_relationship.acquired_how == 'HS'
        assert self.party.id == tenure_relationship.party.id
        assert self.spatial_unit.id == tenure_relationship.spatial_unit.id

    def test_set_attributes(self):
        tenure_relationship = TenureRelationshipFactory.create(
            party=self.party, spatial_unit=self.spatial_unit)
        attributes = {
            'description':
            'Additional attribute data'
        }
        tenure_relationship.attributes = attributes
        tenure_relationship.save()
        assert attributes[
            'description'] == tenure_relationship.attributes['description']

    def test_tenure_relationship_type_not_set(self):
        try:
            TenureRelationshipFactory.create(
                party=self.party,
                spatial_unit=self.spatial_unit, tenure_type=None
            )
        except ValueError:
            # expected
            pass

    def test_tenure_relationship_project_set(self):
        tenure_relationship = TenureRelationshipFactory.create(
            party=self.party,
            spatial_unit=self.spatial_unit, project=self.project
        )
        assert tenure_relationship.project is not None
        assert tenure_relationship.project.id == self.project.id


class TenureRelationshipTypeTest(TestCase):

    def test_tenure_relationship_types(self):
        tenure_types = TenureRelationshipType.objects.all()
        assert 19 == len(tenure_types)
        freehold = TenureRelationshipType.objects.get(id='FH')
        assert freehold.label == 'Freehold'


class PartyTenureRelationshipsTest(TestCase):
    """Test TenureRelationships on Party."""

    def setUp(self):
        self.party = PartyFactory.create(name='TestParty')
        self.spatial_unit = SpatialUnitFactory.create(name='TestSpatialUnit')

    def test_party_tenure_relationships(self):
        TenureRelationshipFactory.create(
            party=self.party, spatial_unit=self.spatial_unit
        )
        su = self.party.tenure_relationships.all()[0]
        assert su.id == self.spatial_unit.id


class SpatialUnitTenureRelationshipsTest(TestCase):
    """Test TenureRelationships on SpatialUnit."""

    def setUp(self):
        self.party = PartyFactory.create(name='TestParty')
        self.spatial_unit = SpatialUnitFactory.create(name='TestSpatialUnit')

    def test_spatial_unit_tenure_relationships(self):
        TenureRelationshipFactory.create(
            party=self.party, spatial_unit=self.spatial_unit
        )
        party = self.spatial_unit.tenure_relationships.all()[0]
        assert party.id == self.party.id
