"""TestCases for Party models."""

from django.test import TestCase

from party.models import Party
from party.tests.factories import PartyFactory, PartyRelationshipFactory


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


class PartRelationshipTest(TestCase):

    def test_relationships_creation(self):
        relationship = PartyRelationshipFactory(
            party1__name='Mad Hatter',
            party2__name='Mad Hatters Tea Party')
        party2_name = str(relationship.party1.relationships.all()[0])
        assert party2_name == '<Party: Mad Hatters Tea Party>'

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
