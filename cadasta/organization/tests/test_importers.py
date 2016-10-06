import os

import pytest

from buckets.test.storage import FakeS3Storage
from core.tests.utils.cases import UserTestCase
from django.conf import settings
from django.contrib.gis.geos import LineString, Point, Polygon
from jsonattrs.models import Attribute, Schema
from party.models import Party, TenureRelationship
from questionnaires.models import Questionnaire
from resources.tests.utils import clear_temp  # noqa
from spatial.models import SpatialUnit

from django.test import TestCase

from ..importers import csv, exceptions
from ..importers.base import Importer
from ..tests.factories import ProjectFactory

path = os.path.dirname(settings.BASE_DIR)


class BaseImporterTest(UserTestCase, TestCase):

    def test_init(self):
        project = ProjectFactory.build()
        importer = Importer(project)
        assert importer.project == project

    def test_get_schema_attrs(self):
        project = ProjectFactory.create()
        importer = Importer(project)
        assert len(importer.get_schema_attrs().keys()) == 5
        assert importer.get_schema_attrs()['spatial.spatialunit'] == []

    def test_done(self):
        project = ProjectFactory.create()
        importer = Importer(project)
        with pytest.raises(NotImplementedError):
            importer.import_data(config_dict=None)


# @pytest.mark.usefixtures('clear_temp')
class CSVImportTest(UserTestCase, TestCase):

    def setUp(self):
        super().setUp()

        self.path = os.path.dirname(settings.BASE_DIR)
        self.valid_csv = '/organization/tests/files/test.csv'
        self.invalid_csv = '/organization/tests/files/test_invalid.csv'
        self.geoshape_csv = '/organization/tests/files/test_geoshape.csv'
        self.geotrace_csv = '/organization/tests/files/test_geotrace.csv'
        self.invalid_col_csv = '/organization/tests/files/invalid_col.csv'
        self.invalid_geom_type = (
            '/organization/tests/files/invalid_geom_type.csv')
        self.no_tenure_type = '/organization/tests/files/no_tenure_type.csv'

        self.project = ProjectFactory.create(name='Test CSV Import')
        storage = FakeS3Storage()
        xlscontent = open(
            path + '/organization/tests/files/uttaran_test.xlsx', 'rb'
        ).read()
        form = storage.save('xls-forms/uttaran_test.xlsx', xlscontent)
        Questionnaire.objects.create_from_form(
            xls_form=form,
            project=self.project
        )
        # test for expected schema and attribute creation
        assert 2 == Schema.objects.all().count()
        assert 39 == Attribute.objects.all().count()

        self.attributes = [
            'deed_of_land', 'amount_othersland', 'educational_qualification',
            'name_mouza', 'land_calculation', 'how_aquire_landwh',
            'female_member', 'mutation_of_land', 'amount_agriland',
            'nid_number', 'class_hh', 'j_l', 'how_aquire_landt',
            'boundary_conflict', 'dakhal_on_land', 'village_name',
            'how_aquire_landp', 'how_aquire_landd', 'ownership_conflict',
            'occupation_hh', 'others_conflict', 'how_aquire_landm',
            'khatain_of_land', 'male_member', 'mobile_no', 'how_aquire_landw',
            'everything', 'name_father_hus'
        ]

    def test_get_schema_attrs(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.valid_csv)
        attrs = importer.get_schema_attrs()
        su_attrs = attrs['spatial.spatialunit']
        pty_attrs = attrs['party.party']
        assert len(su_attrs) == 28
        assert len(pty_attrs) == 11

    def test_get_attribute_map(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.valid_csv)
        attr_map, extra_attrs, extra_headers = importer.get_attribute_map()
        assert len(attr_map.keys()) == 28
        assert len(extra_attrs) == 11
        assert len(extra_headers) == 10
        assert attr_map['class_hh'][1] == 'party.party'
        assert isinstance(attr_map[
            'others_conflict'][0], Attribute)

    def test_import_data(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.valid_csv)
        config_dict = {
            'file': self.path + self.valid_csv,
            'party_name_field': 'name_of_hh',
            'party_type': 'IN',
            'location_type': 'PA',
            'geometry_type_field': 'geo_type',
            'geometry_field': 'location_geometry',
            'attributes': self.attributes,
            'project': self.project
        }
        importer.import_data(config_dict)
        assert Party.objects.all().count() == 10
        assert SpatialUnit.objects.all().count() == 10
        assert TenureRelationship.objects.all().count() == 10
        for su in SpatialUnit.objects.filter(project_id=self.project.pk).all():
            if su.geometry is not None:
                assert type(su.geometry) is Point

        # test attribute creation
        su = SpatialUnit.objects.first()
        assert 'how_aquire_landwh' not in su.attributes.keys()
        assert 'how_aquire_landw' in su.attributes.keys()

    def test_import_with_geoshape(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.geoshape_csv)
        config_dict = {
            'file': self.path + self.geoshape_csv,
            'party_name_field': 'name_of_hh',
            'party_type': 'IN',
            'location_type': 'PA',
            'geometry_type_field': 'geo_type',
            'geometry_field': 'location_geoshape',
            'attributes': self.attributes,
            'project': self.project
        }
        importer.import_data(config_dict)
        assert Party.objects.all().count() == 10
        assert SpatialUnit.objects.all().count() == 10
        assert TenureRelationship.objects.all().count() == 10
        for su in SpatialUnit.objects.filter(project_id=self.project.pk).all():
            if su.geometry is not None:
                assert type(su.geometry) is Polygon

    def test_import_with_geotrace(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.geotrace_csv)
        config_dict = {
            'file': self.path + self.geotrace_csv,
            'party_name_field': 'name_of_hh',
            'party_type': 'IN',
            'location_type': 'PA',
            'geometry_type_field': 'geo_type',
            'geometry_field': 'location_geotrace',
            'attributes': self.attributes,
            'project': self.project
        }
        importer.import_data(config_dict)
        assert Party.objects.all().count() == 10
        assert SpatialUnit.objects.all().count() == 10
        assert TenureRelationship.objects.all().count() == 10
        for su in SpatialUnit.objects.filter(project_id=self.project.pk).all():
            if su.geometry is not None:
                assert type(su.geometry) is LineString

    def test_import_with_bad_defaults(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.valid_csv)
        config_dict = {
            'file': self.path + self.valid_csv,
            'party_name_field': 'bad_party_name_field',
            'party_type': 'IN',
            'location_type': 'PA',
            'geometry_type_field': 'geo_type',
            'geometry_field': 'location_geometry',
            'attributes': self.attributes,
            'project': self.project
        }
        with pytest.raises(exceptions.DataImportError):
            importer.import_data(config_dict)
        assert Party.objects.all().count() == 0
        assert SpatialUnit.objects.all().count() == 0
        assert TenureRelationship.objects.all().count() == 0

    def test_import_with_invalid_column(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.invalid_col_csv)
        config_dict = {
            'file': self.path + self.invalid_col_csv,
            'party_name_field': 'name_of_hh',
            'party_type': 'IN',
            'location_type': 'PA',
            'geometry_type_field': 'geo_type',
            'geometry_field': 'location_geometry',
            'attributes': self.attributes,
            'project': self.project,
        }
        with pytest.raises(exceptions.DataImportError) as e:
            importer.import_data(config_dict)
        assert str(e.value) == (
            "Error importing file at line 2: "
            "Number of headers and columns "
            "do not match"
        )
        assert Party.objects.all().count() == 0
        assert SpatialUnit.objects.all().count() == 0
        assert TenureRelationship.objects.all().count() == 0

    def test_import_with_invalid_geom_type(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.invalid_geom_type)
        config_dict = {
            'file': self.path + self.invalid_geom_type,
            'party_name_field': 'name_of_hh',
            'party_type': 'IN',
            'location_type': 'PA',
            'geometry_type_field': 'geo_type',
            'geometry_field': 'location_geotrace',
            'attributes': self.attributes,
            'project': self.project
        }
        with pytest.raises(exceptions.DataImportError) as e:
            importer.import_data(config_dict)
        assert str(e.value) == ("Error importing file at line 5: "
                                "Invalid geometry type")
        assert Party.objects.all().count() == 0
        assert SpatialUnit.objects.all().count() == 0
        assert TenureRelationship.objects.all().count() == 0

    def test_import_with_missing_tenure_type(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.no_tenure_type)
        config_dict = {
            'file': self.path + self.no_tenure_type,
            'party_name_field': 'name_of_hh',
            'party_type': 'IN',
            'location_type': 'PA',
            'geometry_type_field': 'geo_type',
            'geometry_field': 'location_geometry',
            'attributes': self.attributes,
            'project': self.project
        }
        with pytest.raises(exceptions.DataImportError) as e:
            importer.import_data(config_dict)
        assert str(e.value) == ("Error importing file at line 2: "
                                "No 'tenure_type' column found")
        assert Party.objects.all().count() == 0
        assert SpatialUnit.objects.all().count() == 0
        assert TenureRelationship.objects.all().count() == 0
