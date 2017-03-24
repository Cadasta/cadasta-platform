"""TestCases for Party models."""

import pytest

from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.db.utils import IntegrityError
from jsonattrs.models import Attribute, AttributeType, Schema
from core.tests.utils.cases import UserTestCase
from organization.tests.factories import ProjectFactory
from resources.tests.factories import ResourceFactory
from resources.models import ContentObject
from party.models import Party, TenureRelationshipType, TenureRelationship
from party.tests.factories import (PartyFactory, PartyRelationshipFactory,
                                   TenureRelationshipFactory)
from spatial.tests.factories import SpatialUnitFactory

from .. import exceptions


class PartyTest(UserTestCase, TestCase):

    def test_str(self):
        party = PartyFactory.build(name='TeaParty')
        assert str(party) == '<Party: TeaParty>'

    def test_repr(self):
        project = ProjectFactory.build(slug='prj')
        party = PartyFactory.build(id='abc123', name='TeaParty',
                                   project=project, type='IN')
        assert repr(party) == ('<Party id=abc123 name=TeaParty project=prj'
                               ' type=IN>')

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
        # add attribute schema
        content_type = ContentType.objects.get(
            app_label='party', model='party')
        sch = Schema.objects.create(content_type=content_type, selectors=())
        attr_type = AttributeType.objects.get(name="text")
        Attribute.objects.create(
            schema=sch, name='description', long_name='Description',
            required=False, index=1, attr_type=attr_type
        )
        party = PartyFactory.create(
            attributes={
                'description': 'Mad Hatters Tea Party'
            })
        assert party.attributes['description'] == 'Mad Hatters Tea Party'

    def test_ui_class_name(self):
        party = PartyFactory.create()
        assert party.ui_class_name == "Party"

    def test_get_absolute_url(self):
        party = PartyFactory.create()
        assert party.get_absolute_url() == (
            '/organizations/{org}/projects/{prj}/records/parties/{id}/'.format(
                org=party.project.organization.slug,
                prj=party.project.slug,
                id=party.id))

    def test_detach_party_resources(self):
        project = ProjectFactory.create()
        party = PartyFactory.create(project=project)
        resource = ResourceFactory.create(project=project)
        resource.content_objects.create(
            content_object=party)

        assert ContentObject.objects.filter(
            object_id=party.id, resource=resource).exists()
        assert resource in party.resources

        party.delete()
        assert not ContentObject.objects.filter(
            object_id=party.id, resource=resource).exists()

    def test_detach_deferred_party_resources(self):
        project = ProjectFactory.create()
        party = PartyFactory.create(project=project)
        resource = ResourceFactory.create(project=project)
        resource.content_objects.create(
            content_object=party)

        assert ContentObject.objects.filter(
            object_id=party.id, resource=resource).exists()

        party_deferred = Party.objects.all().defer('attributes')[0]
        assert resource in party_deferred.resources

        party_deferred.delete()
        assert not ContentObject.objects.filter(
            object_id=party.id, resource=resource).exists()
        assert Party.objects.all().count() == 0


class PartyRelationshipTest(UserTestCase, TestCase):

    def test_str(self):
        project = ProjectFactory.build(name='TestProject')
        relationship = PartyRelationshipFactory.build(
            project=project,
            party1__project=project,
            party1__name='Simba',
            party2__project=project,
            party2__name='Mufasa',
            type='C')
        assert str(relationship) == (
            "<PartyRelationship: <Simba> is-child-of <Mufasa>>")

    def test_repr(self):
        project = ProjectFactory.build(slug='prj')
        party1 = PartyFactory.build(id='abc123', project=project)
        party2 = PartyFactory.build(id='def456', project=project)
        relationship = PartyRelationshipFactory.build(
            id='abc123',
            project=project,
            party1=party1,
            party2=party2,
            type='C')
        assert repr(relationship) == ('<PartyRelationship id=abc123'
                                      ' party1=abc123 party2=def456'
                                      ' project=prj type=C>')

    def test_relationships_creation(self):
        relationship = PartyRelationshipFactory(
            party1__name='Mad Hatter', party2__name='Mad Hatters Tea Party')
        party2_name = str(relationship.party1.relationships.all()[0])
        assert party2_name == '<Party: Mad Hatters Tea Party>'

    def test_party_reverse_relationship(self):
        relationship = PartyRelationshipFactory(
            party1__name='Mad Hatter', party2__name='Mad Hatters Tea Party')
        party1_name = str(relationship.party2.relationships_set.all()[0])
        assert party1_name == '<Party: Mad Hatter>'

    def test_project_reverse_relationship(self):
        relationship = PartyRelationshipFactory()
        assert len(relationship.project.party_relationships.all()) == 1

    def test_relationship_type(self):
        relationship = PartyRelationshipFactory(type='M')
        assert relationship.type == 'M'
        assert relationship.get_type_display() == 'is-member-of'

    def test_set_attributes(self):
        # add attribute schema
        content_type = ContentType.objects.get(
            app_label='party', model='partyrelationship')
        sch = Schema.objects.create(content_type=content_type, selectors=())
        attr_type = AttributeType.objects.get(name="text")
        Attribute.objects.create(
            schema=sch, name='description', long_name='Description',
            required=False, index=1, attr_type=attr_type
        )
        relationship = PartyRelationshipFactory.create(
            attributes={
                'description':
                'Mad Hatter attends Tea Party'
            })
        assert relationship.attributes[
            'description'] == 'Mad Hatter attends Tea Party'

    def test_project_relationship_invalid(self):
        with pytest.raises(exceptions.ProjectRelationshipError):
            project = ProjectFactory()
            PartyRelationshipFactory.create(party1__project=project)

    def test_left_and_right_project_ids(self):
        with pytest.raises(exceptions.ProjectRelationshipError):
            project1 = ProjectFactory()
            project2 = ProjectFactory()
            PartyRelationshipFactory.create(
                party1__project=project1,
                party2__project=project2
            )


class TenureRelationshipTest(UserTestCase, TestCase):

    def test_str(self):
        project = ProjectFactory.build(name='TestProject')
        tenure_type = TenureRelationshipType(id='LS', label="Leasehold")
        relationship = TenureRelationshipFactory.build(
            project=project,
            party__project=project,
            party__name='Family',
            spatial_unit__project=project,
            spatial_unit__type='PA',
            tenure_type=tenure_type)
        assert str(relationship) == (
            "<TenureRelationship: <Family> Leasehold <Parcel>>")

    def test_repr(self):
        project = ProjectFactory.build(slug='prj')
        party = PartyFactory.build(id='abc123', project=project)
        su = SpatialUnitFactory.build(id='def456', project=project)
        relationship = TenureRelationshipFactory.build(
            id='abc123',
            project=project,
            party=party,
            spatial_unit=su,
            tenure_type=TenureRelationshipType(id='CR'))
        assert repr(relationship) == ('<TenureRelationship id=abc123'
                                      ' party=abc123 spatial_unit=def456'
                                      ' project=prj tenure_type=CR>')

    def test_tenure_relationship_creation(self):
        tenure_relationship = TenureRelationshipFactory.create()
        assert tenure_relationship.tenure_type is not None

    def test_project_reverse_tenure_relationships(self):
        relationship = TenureRelationshipFactory.create()
        assert len(relationship.project.tenure_relationships.all()) == 1

    def test_set_attributes(self):
        tenure_relationship = TenureRelationshipFactory.create()
        attributes = {
            'description':
            'Additional attribute data'
        }
        tenure_relationship.attributes = attributes
        tenure_relationship.save()
        assert attributes[
            'description'] == tenure_relationship.attributes['description']

    def test_tenure_relationship_type_not_set(self):
        with pytest.raises(IntegrityError):
            TenureRelationshipFactory.create(tenure_type=None)

    def test_project_relationship_invalid(self):
        with pytest.raises(exceptions.ProjectRelationshipError):
            project = ProjectFactory()
            TenureRelationshipFactory.create(
                party__project=project,
                spatial_unit__project=project
            )

    def test_left_and_right_project_ids(self):
        with pytest.raises(exceptions.ProjectRelationshipError):
            project = ProjectFactory()
            TenureRelationshipFactory.create(
                party__project=project
            )

    def test_name(self):
        tenurerel = TenureRelationshipFactory.create()
        assert tenurerel.name == "<{party}> {type} <{su}>".format(
            party=tenurerel.party.name,
            type=tenurerel.tenure_type_label,
            su=tenurerel.spatial_unit.get_type_display())

    def test_ui_class_name(self):
        tenurerel = TenureRelationshipFactory.create()
        assert tenurerel.ui_class_name == "Relationship"

    def test_get_absolute_url(self):
        tenurerel = TenureRelationshipFactory.create()
        assert tenurerel.get_absolute_url() == (
            '/organizations/{org}/projects/{prj}/'
            '#/records/relationship/{id}'.format(
                org=tenurerel.project.organization.slug,
                prj=tenurerel.project.slug,
                id=tenurerel.id))

    def test_tenure_type_label(self):
        tenurerel = TenureRelationshipFactory.create()
        assert tenurerel.tenure_type_label == tenurerel.tenure_type.label

    def test_detach_tenure_relationship_resources(self):
        project = ProjectFactory.create()
        tenure = TenureRelationshipFactory.create(project=project)
        resource = ResourceFactory.create(project=project)
        resource.content_objects.create(
            content_object=tenure)
        assert ContentObject.objects.filter(
            object_id=tenure.id,
            resource=resource,).exists()
        assert resource in tenure.resources

        tenure.delete()
        assert not ContentObject.objects.filter(
            object_id=tenure.id, resource=resource).exists()

    def test_detach_deferred_tenure_relationship_resources(self):
        project = ProjectFactory.create()
        tenure = TenureRelationshipFactory.create(project=project)
        resource = ResourceFactory.create(project=project)
        resource.content_objects.create(
            content_object=tenure)
        assert ContentObject.objects.filter(
            object_id=tenure.id,
            resource=resource,).exists()
        tenure_deferred = TenureRelationship.objects.all()[0]

        assert resource in tenure_deferred.resources

        tenure_deferred.delete()
        assert not ContentObject.objects.filter(
            object_id=tenure.id, resource=resource).exists()
        assert TenureRelationship.objects.all().count() == 0


class TenureRelationshipTypeTest(UserTestCase, TestCase):
    """Test TenureRelationshipType."""

    def test_repr(self):
        tenure_type = TenureRelationshipType(id='FH', label='Freehold')
        assert repr(tenure_type) == ('<TenureRelationshipType id=FH'
                                     ' label=Freehold>')

    def test_tenure_relationship_types(self):
        tenure_types = TenureRelationshipType.objects.all()
        assert 18 == len(tenure_types)
        freehold = TenureRelationshipType.objects.get(id='FH')
        assert freehold.label == 'Freehold'


class PartyTenureRelationshipsTest(UserTestCase, TestCase):
    """Test TenureRelationships on Party."""

    def test_party_tenure_relationships(self):
        relationship = TenureRelationshipFactory.create()
        queryset = relationship.party.tenure_relationships.all()
        assert len(queryset) == 1
        assert queryset[0] is not None


class SpatialUnitTenureRelationshipsTest(UserTestCase, TestCase):
    """Test TenureRelationships on SpatialUnit."""

    def test_spatial_unit_tenure_relationships(self):
        relationship = TenureRelationshipFactory.create()
        queryset = relationship.spatial_unit.tenure_relationships.all()
        assert len(queryset) == 1
        assert queryset[0] is not None
