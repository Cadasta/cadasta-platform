import pytest

from django.utils.translation import activate
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from jsonattrs.models import Attribute, AttributeType, Schema
from core.tests.utils.cases import UserTestCase
from organization.tests.factories import ProjectFactory
from resources.tests.factories import ResourceFactory
from resources.models import ContentObject
from party import exceptions
from spatial.models import SpatialUnit
from spatial.tests.factories import (SpatialUnitFactory,
                                     SpatialRelationshipFactory)
from questionnaires.tests import factories as q_factories


class SpatialUnitTest(UserTestCase, TestCase):
    def tearDown(self):
        activate('en')

    def test_str(self):
        spatial_unit = SpatialUnitFactory.create(type='PA')
        assert str(spatial_unit) == '<SpatialUnit: Parcel>'

    def test_repr(self):
        project = ProjectFactory.build(slug='prj')
        spatial_unit = SpatialUnitFactory.build(type='PA', id='abc123',
                                                project=project)
        assert repr(spatial_unit) == ('<SpatialUnit id=abc123 project=prj'
                                      ' type=PA>')

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

    def test_empty_geometries(self):
        geoms = (
            "POINT EMPTY",
            # "POLYGON EMPTY",  # Uncomment after Django 1.11 or libgeos 3.6.1
            "LINESTRING EMPTY",
            "MULTIPOINT EMPTY",
            "MULTILINESTRING EMPTY",
            "MULTIPOLYGON EMPTY",
            "GEOMETRYCOLLECTION EMPTY",
        )
        for geom in geoms:
            spatial_unit = SpatialUnitFactory.create(
                geometry=GEOSGeometry(geom))
            assert spatial_unit.geometry.wkt == geom

    def test_empty_geometry(self):
        # Temp workaround where 'POLYGON EMPTY' is cast to None. Should
        # be removed when Django is 1.11+ or libgeos is 3.6.1+
        spatial_unit = SpatialUnitFactory.create(
            geometry=GEOSGeometry('POLYGON EMPTY'))
        assert spatial_unit.geometry is None

    def test_reassign_extent(self):
        spatial_unit = SpatialUnitFactory.create(
            geometry='SRID=4326;POLYGON(('
            '211.36667 47.25000, '
            '211.41667 47.25000, '
            '211.41667 47.28333, '
            '211.36667 47.28333, '
            '211.36667 47.25000))'
        )
        assert spatial_unit.geometry.boundary.coords == (
            (-148.63333, 47.25), (-148.58333, 47.25), (-148.58333, 47.28333),
            (-148.63333, 47.28333), (-148.63333, 47.25))

    def test_defaults_no_geometry(self):
        spatial_unit = SpatialUnitFactory.create()
        assert spatial_unit.geometry is None

    def test_default_type_is_parcel(self):
        spatial_unit = SpatialUnitFactory.create()
        assert spatial_unit.type == 'PA'
        assert spatial_unit.location_type_label == 'Parcel'

    def test_setting_type(self):
        spatial_unit = SpatialUnitFactory.create(
            type="RW")
        assert spatial_unit.type == 'RW'
        assert spatial_unit.location_type_label == 'Right-of-way'

    def test_adding_attributes(self):
        # add attribute schema
        content_type = ContentType.objects.get(
            app_label='spatial', model='spatialunit')
        sch = Schema.objects.create(content_type=content_type, selectors=())
        attr_type = AttributeType.objects.get(name="text")
        Attribute.objects.create(
            schema=sch, name='description', long_name='Description',
            required=False, index=1, attr_type=attr_type
        )
        space = SpatialUnitFactory.create(
            attributes={
                'description': 'The happiest place on earth'
            })
        assert space.attributes['description'] == 'The happiest place on earth'

    def test_name(self):
        su = SpatialUnitFactory.create(type="RW")
        assert su.name == "Right-of-way"

    def test_location_type_label_standard(self):
        su = SpatialUnitFactory.create(type="RW")
        assert su.location_type_label == "Right-of-way"

    def test_location_type_label_questionnaire_default_lang(self):
        questionnaire = q_factories.QuestionnaireFactory.create(
            default_language='en')
        question = q_factories.QuestionFactory.create(
            questionnaire=questionnaire,
            name='location_type',
            type='S1'
        )
        q_factories.QuestionOptionFactory.create(
            question=question,
            name='HOUSE',
            label={'en': 'House', 'de': 'Hause'}
        )
        su = SpatialUnitFactory.create(
            project=questionnaire.project,
            type='HOUSE')
        assert su.location_type_label == 'House'

    def test_location_type_label_questionnaire_selected_lang(self):
        activate('es')
        questionnaire = q_factories.QuestionnaireFactory.create(
            default_language='en')
        question = q_factories.QuestionFactory.create(
            questionnaire=questionnaire,
            name='location_type',
            type='S1'
        )
        q_factories.QuestionOptionFactory.create(
            question=question,
            name='FREE',
            label={'en': 'House', 'es': 'Haus'}
        )
        su = SpatialUnitFactory.create(
            project=questionnaire.project,
            type='FREE')
        assert su.location_type_label == 'Haus'

    def test_location_type_label_questionnaire_single_lang(self):
        questionnaire = q_factories.QuestionnaireFactory.create()
        question = q_factories.QuestionFactory.create(
            questionnaire=questionnaire,
            name='location_type',
            type='S1'
        )
        q_factories.QuestionOptionFactory.create(
            question=question,
            name='HOUSE',
            label='Haus'
        )
        su = SpatialUnitFactory.create(
            project=questionnaire.project,
            type='HOUSE')
        assert su.location_type_label == 'Haus'

    def test_ui_class_name(self):
        su = SpatialUnitFactory.create()
        assert su.ui_class_name == "Location"

    def test_area(self):
        su = SpatialUnitFactory.create(geometry='SRID=4326;POLYGON \
            ((30 10, 20 20, 20 20, 10 20, 30 10))')
        assert su.area == 554923434497.9

    def test_area_no_geometry(self):
        su = SpatialUnitFactory.create()
        assert su.area == 0

    def test_get_absolute_url(self):
        su = SpatialUnitFactory.create()
        assert su.get_absolute_url() == (
            '/organizations/{org}/projects/{prj}/'
            'records/locations/{id}/'.format(
                org=su.project.organization.slug,
                prj=su.project.slug,
                id=su.id))

    def test_detach_spatial_unit_resources(self):
        project = ProjectFactory.create()
        su = SpatialUnitFactory.create(project=project)
        resource = ResourceFactory.create(project=project)
        resource.content_objects.create(
          content_object=su)
        assert ContentObject.objects.filter(
            object_id=su.id,
            resource=resource,).exists()
        assert resource in su.resources

        su.delete()
        assert not ContentObject.objects.filter(
            object_id=su.id, resource=resource).exists()

    def test_detach_deferred_spatial_unit_resources(self):
        project = ProjectFactory.create()
        su = SpatialUnitFactory.create(project=project)
        resource = ResourceFactory.create(project=project)
        resource.content_objects.create(
          content_object=su)
        assert ContentObject.objects.filter(
            object_id=su.id,
            resource=resource,).exists()

        su_deferred = SpatialUnit.objects.all().defer('attributes')[0]
        assert resource in su_deferred.resources

        su_deferred.delete()
        assert not ContentObject.objects.filter(
            object_id=su.id, resource=resource).exists()
        assert SpatialUnit.objects.all().count() == 0


class SpatialRelationshipTest(UserTestCase, TestCase):

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory(name='TestProject')

    def test_str(self):
        relationship = SpatialRelationshipFactory(
            project=self.project,
            su1__project=self.project,
            su1__type='PA',
            su2__project=self.project,
            su2__type='CB',
            type='C')
        assert str(relationship) == (
            "<SpatialRelationship: "
            "<Parcel> is-contained-in <Community boundary>>"
        )

    def test_repr(self):
        project = ProjectFactory.build(slug='prj')
        su1 = SpatialUnitFactory.build(type='PA', id='abc123', project=project)
        su2 = SpatialUnitFactory.build(type='PA', id='def456', project=project)
        relationship = SpatialRelationshipFactory.build(
            id='abc123',
            project=project,
            su1=su1,
            su2=su2,
            type='C')
        assert repr(relationship) == ('<SpatialRelationship id=abc123'
                                      ' project=prj su1=abc123 su2=def456'
                                      ' type=C>')

    def test_relationships_creation(self):
        relationship = SpatialRelationshipFactory(
            project=self.project,
            su1__project=self.project,
            su1__type='PA',
            su2__project=self.project,
            su2__type='CB')
        su2_type = str(relationship.su1.relationships.all()[0])
        assert su2_type == '<SpatialUnit: Community boundary>'

    def test_relationship_type(self):
        relationship = SpatialRelationshipFactory(type='S')

        assert relationship.type == 'S'
        assert relationship.get_type_display() == 'is-split-of'

    def test_adding_attributes(self):
        # add attribute schema
        content_type = ContentType.objects.get(
            app_label='spatial', model='spatialrelationship')
        sch = Schema.objects.create(content_type=content_type, selectors=())
        attr_type = AttributeType.objects.get(name="text")
        Attribute.objects.create(
            schema=sch, name='test', long_name='Test',
            required=False, index=1, attr_type=attr_type
        )
        relationship = SpatialRelationshipFactory(
            su1__type='BU',
            su2__type='AP',
            attributes={'test': 'Partner amusement parks.'})

        assert relationship.attributes['test'] == 'Partner amusement parks.'

    def test_traversing_contained_spatial_unit(self):
        relationship = SpatialRelationshipFactory(
            su1__type='BU',
            su2__type='AP',
            type='C')
        su1_contains = str(relationship.su1.relationships.all()[0])
        su2_is_contained_in = str(relationship.su2.relationships_set.all()[0])

        assert relationship.get_type_display() == 'is-contained-in'
        assert su1_contains == '<SpatialUnit: Apartment>'
        assert su2_is_contained_in == '<SpatialUnit: Building>'

    def test_traversing_split_spatial_unit(self):
        relationship = SpatialRelationshipFactory(
            su1__type='BU',
            su2__type='AP',
            type='S')
        su1_split_into = str(relationship.su1.relationships.all()[0])
        su2_split_from = str(relationship.su2.relationships_set.all()[0])

        assert relationship.get_type_display() == 'is-split-of'
        assert su1_split_into == '<SpatialUnit: Apartment>'
        assert su2_split_from == '<SpatialUnit: Building>'

    def test_traversing_merged_spatial_unit(self):
        relationship = SpatialRelationshipFactory(
            su1__type='BU',
            su2__type='AP',
            type='M')
        su1_merged_from = str(relationship.su1.relationships.all()[0])
        su2_merged_into = str(relationship.su2.relationships_set.all()[0])

        assert relationship.get_type_display() == 'is-merge-of'
        assert su1_merged_from == '<SpatialUnit: Apartment>'
        assert su2_merged_into == '<SpatialUnit: Building>'

    def test_spatial_unit_contains_anothers_geometry(self):
        relationship = SpatialRelationshipFactory(
            su1__type='BU',
            su1__geometry='SRID=4326;POLYGON(('
                          '-91.9947 34.7994, '
                          '-91.9950 34.7846, '
                          '-92.0000 34.7798, '
                          '-92.0032 34.7644, '
                          '-91.9174 34.7627, '
                          '-91.9153 34.8032, '
                          '-91.9947 34.7994))',
            su2__type='AP',
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
            SpatialRelationshipFactory(
                su1__type='BU',
                su2__geometry='SRID=4326;POLYGON(('
                              '-91.9947 34.7994, '
                              '-91.9950 34.7846, '
                              '-92.0000 34.7798, '
                              '-92.0032 34.7644, '
                              '-91.9174 34.7627, '
                              '-91.9153 34.8032, '
                              '-91.9947 34.7994))',
                su2__type='AP',
                su1__geometry='SRID=4326;POLYGON(('
                              '-91.9320 34.7918, '
                              '-91.9335 34.7846, '
                              '-91.9176 34.7846, '
                              '-91.9167 34.7915, '
                              '-91.9320 34.7918))',
                type='C')

    def test_spatial_unit_does_not_contain_anothers_geometry(self):
        with pytest.raises(Exception):
            SpatialRelationshipFactory(
                su1__type='BU',
                su1__geometry='SRID=4326;POLYGON(('
                              '-91.9960 34.7850, '
                              '-91.9960 34.8016, '
                              '-91.9785 34.8016, '
                              '-91.9785 34.7850, '
                              '-91.9960 34.7850))',
                su2__type='AP',
                su2__geometry='SRID=4326;POLYGON(('
                              '11.36667 47.25000, '
                              '11.41667 47.25000, '
                              '11.41667 47.28333, '
                              '11.36667 47.28333, '
                              '11.36667 47.25000))',
                type='C')

    def test_spatial_unit_contains_a_point(self):
        relationship = SpatialRelationshipFactory(
            su1__type='BU',
            su1__geometry='SRID=4326;POLYGON(('
                          '-109.0461 40.2617, '
                          '-108.6039 40.2459,'
                          '-108.3966 40.3831, '
                          '-108.4309 40.6108, '
                          '-108.8841 40.7836, '
                          '-109.0434 40.8657, '
                          '-109.0461 40.2617))',
            su2__type='AP',
            su2__geometry='SRID=4326;POINT('
                          '-108.7536 40.5054)',
            type='C')
        assert relationship is not None

    def test_spatial_unit_does_not_contain_point(self):
        with pytest.raises(Exception):
            SpatialRelationshipFactory(
                su1__type='BU',
                su1__geometry='SRID=4326;POLYGON(('
                              '-109.0461 40.2617, '
                              '-108.6039 40.2459,'
                              '-108.3966 40.3831, '
                              '-108.4309 40.6108, '
                              '-108.8841 40.7836, '
                              '-109.0434 40.8657, '
                              '-109.0461 40.2617))',
                su2__type='AP',
                su2__geometry='SRID=4326;POINT('
                              '-108.0972 40.9508)',
                type='C')

    def test_spatial_unit_point_contains_relationship_still_created(self):
        relationship = SpatialRelationshipFactory(
            su1__type='BU',
            su1__geometry='SRID=4326;POINT('
                          '-108.7536 40.5054)',
            su2__type='AP',
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

    def test_project_relationship_invalid(self):
        with pytest.raises(exceptions.ProjectRelationshipError):
            project = ProjectFactory()
            SpatialRelationshipFactory(
                su1__project=project,
                su2__project=project
            )

    def test_left_and_right_project_ids(self):
        with pytest.raises(exceptions.ProjectRelationshipError):
            project = ProjectFactory()
            SpatialRelationshipFactory(
                su1__project=project
            )
