import pytest

import pandas as pd
from core.tests.utils.cases import FileStorageTestCase, UserTestCase
from django.contrib.gis.geos import LineString, Point, Polygon
from django.core.exceptions import ValidationError
from django.test import TestCase
from jsonattrs.models import Attribute, Schema
from party.models import Party, TenureRelationship
from questionnaires.models import Questionnaire
from resources.tests.utils import clear_temp  # noqa
from spatial.models import SpatialUnit

from ..importers import csv, exceptions, validators, xls
from ..importers.base import Importer
from ..tests.factories import ProjectFactory


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

    def test_import_data_not_implemented(self):
        project = ProjectFactory.create()
        importer = Importer(project)
        with pytest.raises(NotImplementedError):
            importer.import_data(config=None)

    def test_get_headers_not_implemented(self):
        project = ProjectFactory.create()
        importer = Importer(project)
        with pytest.raises(NotImplementedError):
            importer.get_headers()


class ImportValidatorTest(TestCase):

    def test_validate_invalid_column(self):
        config = {
            'party_name_field': 'party_name',
            'geometry_field': 'location_geometry',
            'type': 'csv'
        }
        headers = ['party_type', 'tenure_type', 'some_field', 'invalid_column']
        row = ['IN', 'FH', 'location_geometry']
        with pytest.raises(ValidationError) as e:
            validators.validate_row(
                headers, row, config)
        assert e.value.message == "Number of headers and columns do not match."

    def test_validate_party_name_field(self):
        config = {
            'party_name_field': 'party_name',
            'party_type_field': 'party_type',
            'geometry_field': 'location_geometry',
            'type': 'csv'
        }
        headers = ['party_type', 'tenure_type', 'some_field']
        row = ['IN', 'FH', 'location_geometry']
        with pytest.raises(ValidationError) as e:
            validators.validate_row(
                headers, row, config)
        assert e.value.message == "No 'party_name' column found."

    def test_validate_party_type_field(self):
        config = {
            'party_name_field': 'party_name',
            'party_type_field': 'party_type',
            'geometry_field': 'location_geometry',
            'type': 'csv'
        }
        headers = ['party_name', 'tenure_type', 'some_field']
        row = ['Test Party', 'FH', 'location_geometry']
        with pytest.raises(ValidationError) as e:
            validators.validate_row(
                headers, row, config)
        assert e.value.message == "No 'party_type' column found."

    def test_validate_tenure_type(self):
        config = {
            'party_name_field': 'party_name',
            'party_type_field': 'party_type',
            'geometry_field': 'location_geometry',
            'type': 'csv'
        }
        geometry = 'SRID=4326;POINT (30 10)'
        headers = [
            'party_name', 'party_type', 'location_geometry']
        row = ['Party Name', 'IN', geometry]
        with pytest.raises(ValidationError) as e:
            validators.validate_row(
                headers, row, config)
        assert e.value.message == "No 'tenure_type' column found."

    def test_validate_geometry_field(self):
        config = {
            'party_name_field': 'party_name',
            'party_type_field': 'party_type',
            'geometry_field': 'location_geometry',
            'type': 'csv'
        }
        geometry = 'SRID=4326;POINT (30 10)'
        headers = [
            'party_name', 'party_type', 'location_geometry_bad']
        row = ['Party Name', 'IN', geometry]
        with pytest.raises(ValidationError) as e:
            validators.validate_row(
                headers, row, config)
        assert e.value.message == "No 'geometry_field' column found."

    def test_validate_location_type_field(self):
        config = {
            'party_name_field': 'party_name',
            'party_type_field': 'party_type',
            'geometry_field': 'location_geometry',
            'type': 'xls',
            'location_type_field': 'location_type'
        }
        geometry = 'SRID=4326;POINT (30 10)'
        headers = [
            'party::party_name', 'party::party_type',
            'spatialunit::location_geometry',
            'spatialunit::bad_location_type_field']
        row = ['Party Name', 'IN', geometry, 'PA']
        with pytest.raises(ValidationError) as e:
            validators.validate_row(
                headers, row, config
            )
        assert e.value.message == "No 'location_type' column found."

    def test_validate_geometry(self):
        config = {
            'party_name_field': 'party_name',
            'party_type_field': 'party_type',
            'geometry_field': 'location_geometry',
            'type': 'csv'
        }
        geometry = 'SRID=4326;POINT (30 10, Z)'
        headers = [
            'party_name', 'party_type', 'location_geometry']
        row = ['Party Name', 'IN', geometry]
        with pytest.raises(ValidationError) as e:
            validators.validate_row(
                headers, row, config)
        assert e.value.message == "Invalid geometry."

    def test_validate_location_type_choice(self):
        config = {
            'party_name_field': 'party_name',
            'party_type_field': 'party_type',
            'geometry_field': 'location_geometry',
            'type': 'csv',
            'location_type_field': 'location_type'
        }
        geometry = 'SRID=4326;POINT (30 10)'
        headers = [
            'party_name', 'party_type', 'location_geometry',
            'location_type']
        row = ['Party Name', 'IN', geometry, 'WRONG']
        with pytest.raises(ValidationError) as e:
            validators.validate_row(
                headers, row, config
            )
        assert e.value.message == "Invalid location_type: 'WRONG'."

    def test_validate_tenure_type_choice(self):
        config = {
            'party_name_field': 'party_name',
            'party_type_field': 'party_type',
            'geometry_field': 'location_geometry',
            'type': 'csv',
            'location_type_field': 'location_type',
        }
        geometry = 'SRID=4326;POINT (30 10)'
        headers = [
            'party_name', 'party_type', 'location_geometry',
            'location_type', 'tenure_type']
        row = ['Party Name', 'IN', geometry, 'PA', 'WRONG']
        with pytest.raises(ValidationError) as e:
            validators.validate_row(
                headers, row, config
            )
        assert e.value.message == "Invalid tenure_type: 'WRONG'."


@pytest.mark.usefixtures('clear_temp')
class CSVImportTest(UserTestCase, FileStorageTestCase, TestCase):

    def setUp(self):
        super().setUp()

        self.valid_csv = '/organization/tests/files/test.csv'
        self.geoshape_csv = '/organization/tests/files/test_geoshape.csv'
        self.geotrace_csv = '/organization/tests/files/test_geotrace.csv'
        self.test_wkt = '/organization/tests/files/test_wkt.csv'

        self.project = ProjectFactory.create(name='Test CSV Import')
        xlscontent = self.get_file(
            '/organization/tests/files/uttaran_test.xlsx', 'rb')
        form = self.storage.save('xls-forms/uttaran_test.xlsx', xlscontent)
        Questionnaire.objects.create_from_form(
            xls_form=form,
            project=self.project
        )
        # test for expected schema and attribute creation
        assert 3 == Schema.objects.all().count()
        assert 42 == Attribute.objects.all().count()

        self.party_attributes = [
            'party::educational_qualification', 'party::name_mouza',
            'party::j_l', 'party::name_father_hus', 'party::village_name',
            'party::mobile_no', 'party::occupation_hh', 'party::class_hh'
        ]
        self.location_attributes = [
            'spatialunit::deed_of_land', 'spatialunit::amount_othersland',
            'spatialunit::land_calculation', 'spatialunit::how_aquire_landwh',
            'spatialunit::female_member', 'spaitalunit::mutation_of_land',
            'spatialunit::amount_agriland', 'spatialunit::nid_number',
            'spatialunit::how_aquire_landt', 'spatialunit::boundary_conflict',
            'spatialunit::dakhal_on_land', 'spatialunit::how_aquire_landp',
            'spatialunit::how_aquire_landd', 'spatialunit::ownership_conflict',
            'spatialunit::others_conflict', 'spatialunit::how_aquire_landm',
            'spatialunit::khatain_of_land', 'spatialunit::male_member',
            'spatialunit::how_aquire_landw', 'spatialunit::everything',
            'spatialunit::location_problems'
        ]
        self.tenure_attributes = [
            'tenurerelationship::tenure_name',
            'tenurerelationship::tenure_notes'
        ]

        self.attributes = (
            self.party_attributes + self.location_attributes +
            self.tenure_attributes
        )

    def test_get_schema_attrs(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.valid_csv)
        attrs = importer.get_schema_attrs()
        su_attrs = attrs['spatial.spatialunit']
        pty_attrs = attrs['party.party']
        assert len(su_attrs) == 29
        assert len(pty_attrs) == 11

    def test_get_attribute_map(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.valid_csv)
        entity_types = ['PT', 'SU']
        attr_map, extra_attrs, extra_headers = importer.get_attribute_map(
            'csv', entity_types
        )
        assert len(attr_map.keys()) == 3
        assert len(extra_attrs) == 11
        assert len(extra_headers) == 10
        assert attr_map['party']['class_hh'][1] == 'party.party'
        assert isinstance(attr_map['spatialunit']
                          ['others_conflict'][0], Attribute)

    def test_import_data(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.valid_csv)
        config = {
            'file': self.path + self.valid_csv,
            'entity_types': ['PT', 'SU'],
            'party_name_field': 'name_of_hh',
            'party_type_field': 'party_type',
            'location_type_field': 'location_type',
            'geometry_field': 'location_geometry',
            'attributes': self.attributes,
            'project': self.project
        }
        importer.import_data(config)
        assert Party.objects.all().count() == 10
        assert SpatialUnit.objects.all().count() == 10
        assert TenureRelationship.objects.all().count() == 10
        for su in SpatialUnit.objects.filter(project_id=self.project.pk).all():
            if su.geometry is not None:
                assert type(su.geometry) is Point

        # test spatial unit attribute creation
        sus = SpatialUnit.objects.filter(
            attributes__contains={'nid_number': '3913647224045'})
        assert len(sus) == 1
        su = sus[0]
        assert su.type == 'PA'
        assert len(su.attributes) == 20
        assert 'how_aquire_landwh' not in su.attributes.keys()
        assert 'how_aquire_landw' in su.attributes.keys()
        assert su.attributes[
            'others_conflict'] == ('কিছু বেখলে অাছে জোর করে দখল করে ভোগ করে '
                                   'অন্য জমির মালক।')
        assert su.attributes['female_member'] == '4'
        assert su.attributes['location_problems'] == [
            'conflict', 'risk_of_eviction'
        ]

        # test party attribute creation
        parties = Party.objects.filter(
            attributes__contains={'Mobile_No': '০১৭৭২৫৬০১৯১'})
        assert len(parties) == 1
        assert parties[0].type == 'IN'
        pty_attrs = parties[0].attributes
        assert len(pty_attrs) == 8
        assert pty_attrs['name_father_hus'] == 'মৃত কুব্বাত মন্ডল'

        # test tenure relationship attribute creation
        tenure_relationships = TenureRelationship.objects.filter(
            party=parties[0])
        tr_attrs = {'tenure_name': 'Customary', 'tenure_notes': 'a few notes'}
        assert len(tenure_relationships) == 1
        assert len(tenure_relationships[0].attributes) == 2
        assert tenure_relationships[0].attributes == tr_attrs

    def test_import_parties_only(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.valid_csv)
        config = {
            'file': self.path + self.valid_csv,
            'entity_types': ['PT'],
            'party_name_field': 'name_of_hh',
            'party_type_field': 'party_type',
            'attributes': self.party_attributes,
            'project': self.project
        }
        importer.import_data(config)
        assert Party.objects.all().count() == 10
        assert SpatialUnit.objects.all().count() == 0
        assert TenureRelationship.objects.all().count() == 0

        # test party attribute creation
        parties = Party.objects.filter(
            attributes__contains={'Mobile_No': '০১৭৭২৫৬০১৯১'})
        assert len(parties) == 1
        pty_attrs = parties[0].attributes
        assert len(pty_attrs) == 8
        assert pty_attrs['name_father_hus'] == 'মৃত কুব্বাত মন্ডল'

    def test_import_locations_only(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.valid_csv)
        config = {
            'file': self.path + self.valid_csv,
            'entity_types': ['SU'],
            'location_type_field': 'location_type',
            'geometry_field': 'location_geometry',
            'attributes': self.location_attributes,
            'project': self.project
        }
        importer.import_data(config)
        assert Party.objects.all().count() == 0
        assert SpatialUnit.objects.all().count() == 10
        assert TenureRelationship.objects.all().count() == 0
        for su in SpatialUnit.objects.filter(project_id=self.project.pk).all():
            if su.geometry is not None:
                assert type(su.geometry) is Point

        # test spatial unit attribute creation
        sus = SpatialUnit.objects.filter(
            attributes__contains={'nid_number': '3913647224045'})
        assert len(sus) == 1
        su = sus[0]
        assert su.type == 'PA'
        assert len(su.attributes) == 20
        assert 'how_aquire_landwh' not in su.attributes.keys()
        assert 'how_aquire_landw' in su.attributes.keys()
        assert su.attributes[
            'others_conflict'] == ('কিছু বেখলে অাছে জোর করে দখল করে ভোগ করে '
                                   'অন্য জমির মালক।')
        assert su.attributes['female_member'] == '4'
        assert su.attributes['location_problems'] == [
            'conflict', 'risk_of_eviction'
        ]

    def test_import_with_geoshape(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.geoshape_csv)
        config = {
            'file': self.path + self.geoshape_csv,
            'entity_types': ['SU', 'PT'],
            'party_name_field': 'name_of_hh',
            'party_type_field': 'party_type',
            'location_type_field': 'location_type',
            'geometry_field': 'location_geoshape',
            'attributes': self.attributes,
            'project': self.project
        }
        importer.import_data(config)
        assert Party.objects.all().count() == 10
        assert SpatialUnit.objects.all().count() == 10
        assert TenureRelationship.objects.all().count() == 10
        for su in SpatialUnit.objects.filter(project_id=self.project.pk).all():
            if su.geometry is not None:
                assert type(su.geometry) is Polygon

    def test_import_with_geotrace(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.geotrace_csv)
        config = {
            'file': self.path + self.geotrace_csv,
            'entity_types': ['SU', 'PT'],
            'party_name_field': 'name_of_hh',
            'party_type_field': 'party_type',
            'location_type_field': 'location_type',
            'geometry_field': 'location_geotrace',
            'attributes': self.attributes,
            'project': self.project
        }
        importer.import_data(config)
        assert Party.objects.all().count() == 10
        assert SpatialUnit.objects.all().count() == 10
        assert TenureRelationship.objects.all().count() == 10
        for su in SpatialUnit.objects.filter(project_id=self.project.pk).all():
            if su.geometry is not None:
                assert type(su.geometry) is LineString

    def test_import_with_wkt(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.test_wkt)
        config = {
            'file': self.path + self.test_wkt,
            'entity_types': ['SU', 'PT'],
            'party_name_field': 'name_of_hh',
            'party_type_field': 'party_type',
            'location_type_field': 'location_type',
            'geometry_field': 'location_geometry',
            'attributes': self.attributes,
            'project': self.project
        }
        importer.import_data(config)
        assert Party.objects.all().count() == 10
        assert SpatialUnit.objects.all().count() == 10
        assert TenureRelationship.objects.all().count() == 10

        # test wkt geom creation
        su1 = SpatialUnit.objects.filter(
            attributes__contains={'nid_number': '3913647224045'}).first()
        su2 = SpatialUnit.objects.filter(
            attributes__contains={'nid_number': '3913647224033'}).first()
        su3 = SpatialUnit.objects.filter(
            attributes__contains={'nid_number': '3913647225965'}).first()
        su4 = SpatialUnit.objects.filter(
            attributes__contains={'nid_number': '3913647224043'}).first()
        su5 = SpatialUnit.objects.filter(
            attributes__contains={'nid_number': '3913647224044'}).first()
        su6 = SpatialUnit.objects.filter(
            attributes__contains={'nid_number': '3913647224185'}).first()

        assert su1.geometry.geom_type == 'Point'
        assert su2.geometry.geom_type == 'LineString'
        assert su3.geometry.geom_type == 'Polygon'
        assert su4.geometry.geom_type == 'MultiPoint'
        assert su5.geometry.geom_type == 'MultiLineString'
        assert su6.geometry.geom_type == 'MultiPolygon'


class XLSImportTest(UserTestCase, FileStorageTestCase, TestCase):

    def setUp(self):
        super().setUp()
        self.valid_xls = '/organization/tests/files/test_download.xlsx'
        self.one_to_many_xls = (
            '/organization/tests/files/test_one_to_many.xlsx')
        self.project = ProjectFactory.create(name='Test CSV Import')
        xlscontent = self.get_file(
            '/organization/tests/files/uttaran_test.xlsx', 'rb')
        form = self.storage.save('xls-forms/uttaran_test.xlsx', xlscontent)
        Questionnaire.objects.create_from_form(
            xls_form=form,
            project=self.project
        )
        # test for expected schema and attribute creation
        assert 3 == Schema.objects.all().count()
        assert 42 == Attribute.objects.all().count()

        self.party_attributes = [
            'party::educational_qualification', 'party::name_mouza',
            'party::j_l', 'party::name_father_hus', 'party::village_name',
            'party::mobile_no', 'party::occupation_hh', 'party::class_hh'
        ]
        self.location_attributes = [
            'spatialunit::deed_of_land', 'spatialunit::amount_othersland',
            'spatialunit::land_calculation', 'spatialunit::how_aquire_landwh',
            'spatialunit::female_member', 'spaitalunit::mutation_of_land',
            'spatialunit::amount_agriland', 'spatialunit::nid_number',
            'spatialunit::how_aquire_landt', 'spatialunit::boundary_conflict',
            'spatialunit::dakhal_on_land', 'spatialunit::how_aquire_landp',
            'spatialunit::how_aquire_landd', 'spatialunit::ownership_conflict',
            'spatialunit::others_conflict', 'spatialunit::how_aquire_landm',
            'spatialunit::khatain_of_land', 'spatialunit::male_member',
            'spatialunit::how_aquire_landw', 'spatialunit::everything',
            'spatialunit::location_problems',
            'spatialunit::multiple_landowners'
        ]
        self.tenure_attributes = [
            'tenurerelationship::tenure_name',
            'tenurerelationship::tenure_notes'
        ]

        self.attributes = (
            self.party_attributes + self.location_attributes +
            self.tenure_attributes
        )

    def test_import_data(self):
        importer = xls.XLSImporter(
            project=self.project, path=self.path + self.valid_xls)
        config = {
            'file': self.path + self.valid_xls,
            'type': 'xls',
            'entity_types': ['SU', 'PT'],
            'party_name_field': 'name',
            'party_type_field': 'type',
            'location_type_field': 'type',
            'geometry_field': 'geometry.ewkt',
            'attributes': self.attributes,
            'project': self.project
        }
        importer.import_data(config)
        assert Party.objects.all().count() == 10
        assert SpatialUnit.objects.all().count() == 10
        assert TenureRelationship.objects.all().count() == 10
        for su in SpatialUnit.objects.filter(project_id=self.project.pk).all():
            if su.geometry is not None:
                assert type(su.geometry) is Point

        # test spatial unit attribute creation
        sus = SpatialUnit.objects.filter(
            attributes__contains={'nid_number': '3913647224045'})
        assert len(sus) == 1
        su = sus[0]
        assert su.type == 'PA'
        assert len(su.attributes) == 20
        assert 'how_aquire_landwh' not in su.attributes.keys()
        assert 'how_aquire_landw' in su.attributes.keys()
        assert su.attributes[
            'others_conflict'] == ('কিছু বেখলে অাছে জোর করে দখল করে ভোগ করে '
                                   'অন্য জমির মালক।')
        assert su.attributes['female_member'] == '4'
        assert su.attributes['location_problems'] == [
            'conflict', 'risk_of_eviction'
        ]

        # test party attribute creation
        parties = Party.objects.filter(
            attributes__contains={'Mobile_No': '০১৭৭২৫৬০১৯১'})
        assert len(parties) == 1
        assert parties[0].type == 'IN'
        pty_attrs = parties[0].attributes
        assert len(pty_attrs) == 8
        assert pty_attrs['name_father_hus'] == 'মৃত কুব্বাত মন্ডল'

        # test tenure relationship attribute creation
        tenure_relationships = TenureRelationship.objects.filter(
            party=parties[0])
        tr_attrs = {'tenure_name': 'Customary', 'tenure_notes': 'a few notes'}
        assert len(tenure_relationships) == 1
        assert len(tenure_relationships[0].attributes) == 2
        assert tenure_relationships[0].attributes == tr_attrs

    def test_import_locations_only(self):
        importer = xls.XLSImporter(
            project=self.project, path=self.path + self.valid_xls)
        config = {
            'file': self.path + self.valid_xls,
            'type': 'xls',
            'entity_types': ['SU'],
            'location_type_field': 'type',
            'geometry_field': 'geometry.ewkt',
            'attributes': self.location_attributes,
            'project': self.project
        }
        importer.import_data(config)
        assert Party.objects.all().count() == 0
        assert SpatialUnit.objects.all().count() == 10
        assert TenureRelationship.objects.all().count() == 0
        for su in SpatialUnit.objects.filter(project_id=self.project.pk).all():
            if su.geometry is not None:
                assert type(su.geometry) is Point

        # test spatial unit attribute creation
        sus = SpatialUnit.objects.filter(
            attributes__contains={'nid_number': '3913647224045'})
        assert len(sus) == 1
        su = sus[0]
        assert len(su.attributes) == 20
        assert 'how_aquire_landwh' not in su.attributes.keys()
        assert 'how_aquire_landw' in su.attributes.keys()
        assert su.attributes[
            'others_conflict'] == ('কিছু বেখলে অাছে জোর করে দখল করে ভোগ করে '
                                   'অন্য জমির মালক।')
        assert su.attributes['female_member'] == '4'
        assert su.attributes['location_problems'] == [
            'conflict', 'risk_of_eviction'
        ]

    def test_import_parties_only(self):
        importer = xls.XLSImporter(
            project=self.project, path=self.path + self.valid_xls)
        config = {
            'file': self.path + self.valid_xls,
            'type': 'xls',
            'entity_types': ['PT'],
            'party_name_field': 'name',
            'party_type_field': 'type',
            'attributes': self.party_attributes,
            'project': self.project
        }
        importer.import_data(config)
        assert Party.objects.all().count() == 10
        assert SpatialUnit.objects.all().count() == 0
        assert TenureRelationship.objects.all().count() == 0

        # test party attribute creation
        parties = Party.objects.filter(
            attributes__contains={'Mobile_No': '০১৭৭২৫৬০১৯১'})
        assert len(parties) == 1
        assert parties[0].type == 'IN'
        pty_attrs = parties[0].attributes
        assert len(pty_attrs) == 8
        assert pty_attrs['name_father_hus'] == 'মৃত কুব্বাত মন্ডল'

    def test_one_to_many_relationships(self):
        importer = xls.XLSImporter(
            project=self.project, path=self.path + self.one_to_many_xls)
        config = {
            'file': self.path + self.one_to_many_xls,
            'type': 'xls',
            'entity_types': ['SU', 'PT'],
            'party_name_field': 'name',
            'party_type_field': 'type',
            'location_type_field': 'type',
            'geometry_field': 'geometry.ewkt',
            'attributes': self.attributes,
            'project': self.project
        }
        importer.import_data(config)
        assert Party.objects.all().count() == 10
        assert SpatialUnit.objects.all().count() == 9
        assert TenureRelationship.objects.all().count() == 6

        # test one-to-many location-party
        sus = SpatialUnit.objects.filter(
            attributes__contains={'multiple_landowners': 'yes'})
        assert sus.count() == 1
        su = sus[0]
        assert len(su.tenure_relationships.all()) == 2

        # test one-to-many party-location
        parties = Party.objects.filter(name='অাব্দুল জলিল মন্ডল')
        assert parties.count() == 1
        party = parties[0]
        assert party.tenure_relationships.all().count() == 3

    def test_missing_relationship_tab(self):
        df = pd.read_excel(self.path + self.valid_xls, sheetname=None)
        del df['relationships']
        entity_types = ['SU', 'PT']
        with pytest.raises(exceptions.DataImportError) as e:
            xls.get_csv_from_dataframe(df, entity_types)
        assert e is not None
        assert str(e.value) == (
            "Error importing file: Missing 'relationships' worksheet."
        )

    def test_empty_party_data(self):
        df = pd.read_excel(self.path + self.valid_xls, sheetname=None)
        empty_parties = pd.DataFrame()
        df['parties'] = empty_parties
        entity_types = ['SU', 'PT']
        with pytest.raises(exceptions.DataImportError) as e:
            xls.get_csv_from_dataframe(df, entity_types)
        assert e is not None
        assert str(e.value) == (
            'Error importing file: Empty worksheet.'
        )

    def test_invalid_entity_type(self):
        df = pd.read_excel(self.path + self.valid_xls, sheetname=None)
        entity_types = ['INVALID']
        with pytest.raises(exceptions.DataImportError) as e:
            xls.get_csv_from_dataframe(df, entity_types)
        assert e is not None
        assert str(e.value) == (
            'Error importing file: Unsupported import format.'
        )
