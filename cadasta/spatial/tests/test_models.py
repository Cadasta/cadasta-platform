from django.test import TestCase
import pytest

from spatial.tests.factories import (
    SpatialUnitFactory, SpatialUnitRelationshipFactory)


class SpatialUnitTest(TestCase):
    def test_str(self):
        spatial_unit = SpatialUnitFactory.create(name='Disneyland')
        assert str(spatial_unit) == '<SpatialUnit: Disneyland>'

    def test_has_random_id(self):
        spatial_unit = SpatialUnitFactory.create()
        assert type(spatial_unit.id) is not int

    def test_has_project_id(self):
        spatial_unit = SpatialUnitFactory.create()
        assert type(spatial_unit.project_id) is not int

    def test_geometry(self):
        spatial_unit = SpatialUnitFactory.create(
            geometry='SRID=4326;POLYGON(('
            '11.36667 47.25000, '
            '11.41667 47.25000, '
            '11.41667 47.28333, '
            '11.36667 47.28333, '
            '11.36667 47.25000))')
        assert spatial_unit.geometry is not None

    def test_defaults_no_geometry(self):
        spatial_unit = SpatialUnitFactory.create()
        assert spatial_unit.geometry is None

    def test_default_type_is_parcel(self):
        spatial_unit = SpatialUnitFactory.create()
        assert spatial_unit.type == 'PA'
        assert spatial_unit.get_type_display() == 'Parcel'

    def test_setting_type(self):
        spatial_unit = SpatialUnitFactory.create(
            type="RW")
        assert spatial_unit.type == 'RW'
        assert spatial_unit.get_type_display() == 'Right-of-way'

    def test_adding_attributes(self):
        space = SpatialUnitFactory.create(
            attributes={
                'description': 'The happiest place on earth'
            })
        assert space.attributes['description'] == 'The happiest place on earth'


class SpatialUnitRelationshipTest(TestCase):
    def test_relationships_creation(self):
        relationship = SpatialUnitRelationshipFactory(
            su1__name='Disneyworld',
            su2__name='Disneyland')
        su2_name = str(relationship.su1.relationships.all()[0])

        assert su2_name == '<SpatialUnit: Disneyland>'

    def test_relationship_type(self):
        relationship = SpatialUnitRelationshipFactory(type='S')

        assert relationship.type == 'S'
        assert relationship.get_type_display() == 'is-split-of'

    def test_adding_attributes(self):
        relationship = SpatialUnitRelationshipFactory(
            su1__name='Disneyworld',
            su2__name='Disneyland',
            attributes={'test': 'Partner amusement parks.'})

        assert relationship.attributes['test'] == 'Partner amusement parks.'

    def test_traversing_contained_spatial_unit(self):
        relationship = SpatialUnitRelationshipFactory(
            su1__name='Building',
            su2__name='Apartment',
            type='C')
        su1_contains = str(relationship.su1.relationships.all()[0])
        su2_is_contained_in = str(relationship.su2.relationships_set.all()[0])

        assert relationship.get_type_display() == 'is-contained-in'
        assert su1_contains == '<SpatialUnit: Apartment>'
        assert su2_is_contained_in == '<SpatialUnit: Building>'

    def test_traversing_split_spatial_unit(self):
        relationship = SpatialUnitRelationshipFactory(
            su1__name='Parent Property',
            su2__name='Inheritance',
            type='S')
        su1_split_into = str(relationship.su1.relationships.all()[0])
        su2_split_from = str(relationship.su2.relationships_set.all()[0])

        assert relationship.get_type_display() == 'is-split-of'
        assert su1_split_into == '<SpatialUnit: Inheritance>'
        assert su2_split_from == '<SpatialUnit: Parent Property>'

    def test_traversing_merged_spatial_unit(self):
        relationship = SpatialUnitRelationshipFactory(
            su1__name='Married Property',
            su2__name='Individual Property',
            type='M')
        su1_merged_from = str(relationship.su1.relationships.all()[0])
        su2_merged_into = str(relationship.su2.relationships_set.all()[0])

        assert relationship.get_type_display() == 'is-merge-of'
        assert su1_merged_from == '<SpatialUnit: Individual Property>'
        assert su2_merged_into == '<SpatialUnit: Married Property>'

    def test_spatial_unit_contains_anothers_geometry(self):
        relationship = SpatialUnitRelationshipFactory(
            su1__name='Building',
            su1__geometry='SRID=4326;POLYGON(('
                          '-91.9947 34.7994, '
                          '-91.9950 34.7846, '
                          '-92.0000 34.7798, '
                          '-92.0032 34.7644, '
                          '-91.9174 34.7627, '
                          '-91.9153 34.8032, '
                          '-91.9947 34.7994))',
            su2__name='Apartment',
            su2__geometry='SRID=4326;POLYGON(('
                          '-91.9320 34.7918, '
                          '-91.9335 34.7846, '
                          '-91.9176 34.7846, '
                          '-91.9167 34.7915, '
                          '-91.9320 34.7918))',
            type='C')
        assert relationship is not None

    def test_relationship_fails_if_contained_unit_expands_outside_parent(self):
        with pytest.raises(Exception):
            SpatialUnitRelationshipFactory(
                su1__name='Building',
                su2__geometry='SRID=4326;POLYGON(('
                              '-91.9947 34.7994, '
                              '-91.9950 34.7846, '
                              '-92.0000 34.7798, '
                              '-92.0032 34.7644, '
                              '-91.9174 34.7627, '
                              '-91.9153 34.8032, '
                              '-91.9947 34.7994))',
                su2__name='Apartment',
                su1__geometry='SRID=4326;POLYGON(('
                              '-91.9320 34.7918, '
                              '-91.9335 34.7846, '
                              '-91.9176 34.7846, '
                              '-91.9167 34.7915, '
                              '-91.9320 34.7918))',
                type='C')

    def test_spatial_unit_does_not_contain_anothers_geometry(self):
        with pytest.raises(Exception):
            SpatialUnitRelationshipFactory(
                su1__name='Building',
                su1__geometry='SRID=4326;POLYGON(('
                              '-91.9960 34.7850, '
                              '-91.9960 34.8016, '
                              '-91.9785 34.8016, '
                              '-91.9785 34.7850, '
                              '-91.9960 34.7850))',
                su2__name='Apartment',
                su2__geometry='SRID=4326;POLYGON(('
                              '11.36667 47.25000, '
                              '11.41667 47.25000, '
                              '11.41667 47.28333, '
                              '11.36667 47.28333, '
                              '11.36667 47.25000))',
                type='C')

    def test_spatial_unit_contains_a_point(self):
        relationship = SpatialUnitRelationshipFactory(
            su1__name='Building',
            su1__geometry='SRID=4326;POLYGON(('
                          '-109.0461 40.2617, '
                          '-108.6039 40.2459,'
                          '-108.3966 40.3831, '
                          '-108.4309 40.6108, '
                          '-108.8841 40.7836, '
                          '-109.0434 40.8657, '
                          '-109.0461 40.2617))',
            su2__name='Apartment',
            su2__geometry='SRID=4326;POINT('
                          '-108.7536 40.5054)',
            type='C')
        assert relationship is not None

    def test_spatial_unit_does_not_contain_point(self):
        with pytest.raises(Exception):
            SpatialUnitRelationshipFactory(
                su1__name='Building',
                su1__geometry='SRID=4326;POLYGON(('
                              '-109.0461 40.2617, '
                              '-108.6039 40.2459,'
                              '-108.3966 40.3831, '
                              '-108.4309 40.6108, '
                              '-108.8841 40.7836, '
                              '-109.0434 40.8657, '
                              '-109.0461 40.2617))',
                su2__name='Apartment',
                su2__geometry='SRID=4326;POINT('
                              '-108.0972 40.9508)',
                type='C')

    def test_spatial_unit_point_contains_relationship_still_created(self):
        relationship = SpatialUnitRelationshipFactory(
            su1__name='Building',
            su1__geometry='SRID=4326;POINT('
                          '-108.7536 40.5054)',
            su2__name='Apartment',
            su2__geometry='SRID=4326;POLYGON(('
                          '-109.0461 40.2617, '
                          '-108.6039 40.2459,'
                          '-108.3966 40.3831, '
                          '-108.4309 40.6108, '
                          '-108.8841 40.7836, '
                          '-109.0434 40.8657, '
                          '-109.0461 40.2617))',
            type='C')
        assert relationship is not None
