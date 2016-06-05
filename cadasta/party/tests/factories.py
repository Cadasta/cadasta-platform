"""Factories for Party model creation."""

import factory

from core.tests.factories import ExtendedFactory
from organization.tests.factories import ProjectFactory
from spatial.tests.factories import SpatialUnitFactory
from party.models import (Party, PartyRelationship,
                          TenureRelationship, TenureRelationshipType)


class PartyFactory(ExtendedFactory):
    """Party model factory."""

    class Meta:
        model = Party

    name = factory.Sequence(lambda n: "Party #%s" % n)
    project = factory.SubFactory(ProjectFactory)
    contacts = []


class PartyRelationshipFactory(ExtendedFactory):
    """Factory for PartyRelationships."""

    class Meta:
        model = PartyRelationship

    project = factory.SubFactory(ProjectFactory)
    party1 = factory.SubFactory(PartyFactory, project=project)
    party2 = factory.SubFactory(PartyFactory, project=project)
    type = 'M'


class TenureRelationshipFactory(ExtendedFactory):
    """Factory for TenureRelationships."""

    class Meta:
        model = TenureRelationship

    party = factory.SubFactory(PartyFactory)
    spatial_unit = factory.SubFactory(SpatialUnitFactory)
    acquired_how = 'HS'
    tenure_type = factory.Iterator(TenureRelationshipType.objects.all())
