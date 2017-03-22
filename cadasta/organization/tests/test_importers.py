import pytest

import pandas as pd
from core.tests.utils.cases import FileStorageTestCase, UserTestCase
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import LineString, Point, Polygon
from django.core.exceptions import ValidationError
from django.test import TestCase
from jsonattrs.models import Attribute, AttributeType, Schema
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
        assert importer.get_schema_attrs()['spatial.spatialunit'] == {}

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

    def test_cast_to_type(self):
        project = ProjectFactory.create()
        importer = Importer(project)
        val = importer._cast_to_type('1.0', 'integer')
        assert type(val) is int
        assert val == 1
        val = importer._cast_to_type('not an integer', 'integer')
        assert type(val) is int
        assert val == 0
        val = importer._cast_to_type('1', 'decimal')
        assert type(val) is float
        assert val == 1.0
        val = importer._cast_to_type('not a decimal', 'decimal')
        assert type(val) is float
        assert val == 0.0


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

    def test_validate_empty_geometry(self):
        config = {
            'party_type_field': 'party_type',
            'geometry_field': 'location_geometry',
            'type': 'csv'
        }
        geometry = 'POLYGON EMPTY'
        headers = ['party_type', 'location_geometry']
        row = ['IN', geometry]
        _, _, geo, _, _ = validators.validate_row(headers, row, config)
        assert geo.empty is True

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
        self.test_wkb = '/organization/tests/files/test_wkb.csv'

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
        self.party_gr_attributes = [
            'party::test_group_attr'
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
        su_attrs = attrs['spatial.spatialunit']['DEFAULT']
        pty_attrs_in = attrs['party.party']['IN']
        pty_attrs_gr = attrs['party.party']['GR']
        pty_attrs_co = attrs['party.party']['CO']
        tenure_attrs = attrs['party.tenurerelationship']['DEFAULT']
        assert len(su_attrs) == 29
        assert len(pty_attrs_in) == 11
        assert len(pty_attrs_gr) == 11
        assert len(pty_attrs_co) == 11
        assert len(tenure_attrs) == 2

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

        # assert correct length of conditional selectors
        assert len(attr_map['party.party']) == 3
        assert len(attr_map['party.party']['CO']) == 8
        assert len(attr_map['party.party']['GR']) == 8
        assert len(attr_map['party.party']['IN']) == 8

        # assert correct length of default selectors
        assert len(attr_map['spatial.spatialunit']) == 1
        assert len(attr_map['spatial.spatialunit']['DEFAULT']) == 21
        assert len(attr_map['party.tenurerelationship']['DEFAULT']) == 2

        # assert correctness of attribute map contents
        (attr, content_type, label) = attr_map['party.party'][
            'CO']['name_mouza']
        assert isinstance(attr, Attribute)
        assert attr.name == 'name_mouza'
        assert content_type == 'party.party'
        assert label == 'Party'

    def test_get_attribute_map_parties_only(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.valid_csv)
        entity_types = ['PT']
        attr_map, extra_attrs, extra_headers = importer.get_attribute_map(
            'csv', entity_types
        )
        assert len(attr_map.keys()) == 1
        assert len(extra_attrs) == 3
        assert len(extra_headers) == 10

        # assert correct length of conditional selectors
        assert len(attr_map['party.party']) == 3
        assert len(attr_map['party.party']['CO']) == 8
        assert len(attr_map['party.party']['GR']) == 8
        assert len(attr_map['party.party']['IN']) == 8

        # assert correctness of attribute map contents
        (attr, content_type, label) = attr_map['party.party'][
            'CO']['name_mouza']
        assert isinstance(attr, Attribute)
        assert attr.name == 'name_mouza'
        assert content_type == 'party.party'
        assert label == 'Party'

    def test_get_flattened_attribute_map(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.valid_csv)
        entity_types = ['PT', 'SU']
        attr_map, extra_attrs, extra_headers = importer.get_attribute_map(
            'csv', entity_types, flatten=True
        )
        party_attrs = attr_map['party']
        su_attrs = attr_map['spatialunit']
        tenure_attrs = attr_map['tenurerelationship']
        assert len(party_attrs) == 8
        assert len(su_attrs) == 21
        assert len(tenure_attrs) == 2

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
        assert su.attributes['female_member'] == 4
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
        assert su.attributes['female_member'] == 4
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

    def _run_import_test(self, filename):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + filename)
        config = {
            'file': self.path + filename,
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

    def test_import_with_wkt(self):
        self._run_import_test(self.test_wkt)

    def test_import_with_wkb(self):
        self._run_import_test(self.test_wkb)


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
        assert su.attributes['female_member'] == 4
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
        assert su.attributes['female_member'] == 4
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


class ImportConditionalAttributesTest(UserTestCase, FileStorageTestCase,
                                      TestCase):

    def setUp(self):
        super().setUp()

        self.conditionals_csv = (
            '/organization/tests/files/test_conditionals.csv')
        self.conditionals_xls = (
            '/organization/tests/files/test_conditionals.xlsx')
        self.project = ProjectFactory.create(current_questionnaire='123abc')
        self.spatial_content_type = ContentType.objects.get(
            app_label='spatial', model='spatialunit'
        )
        sp_schema = Schema.objects.create(
            content_type=self.spatial_content_type,
            selectors=(
                self.project.organization.id, self.project.id, '123abc', ))
        attr_type = AttributeType.objects.get(name='text')
        Attribute.objects.create(
            schema=sp_schema,
            name='su_attr', long_name='Test field',
            attr_type=attr_type, index=0,
            required=False, omit=False
        )

        self.party_content_type = ContentType.objects.get(
            app_label='party', model='party'
        )
        pt_schema = Schema.objects.create(
            content_type=self.party_content_type,
            selectors=(
                self.project.organization.id, self.project.id, '123abc', ))
        pt_schema_in = Schema.objects.create(
            content_type=self.party_content_type,
            selectors=(
                self.project.organization.id, self.project.id, '123abc', 'IN'))
        pt_schema_gr = Schema.objects.create(
            content_type=self.party_content_type,
            selectors=(
                self.project.organization.id, self.project.id, '123abc', 'GR'))
        attr_type_txt = AttributeType.objects.get(name='text')
        attr_type_int = AttributeType.objects.get(name='integer')
        attr_type_dec = AttributeType.objects.get(name='decimal')

        Attribute.objects.create(
            schema=pt_schema,
            name='default_attr', long_name='Test field',
            attr_type=attr_type_txt, index=0,
            required=False, omit=False
        )
        Attribute.objects.create(
            schema=pt_schema,
            name='default_int_attr', long_name='Test integer field',
            attr_type=attr_type_int, index=1,
            required=False, omit=False
        )
        Attribute.objects.create(
            schema=pt_schema_in,
            name='party_in', long_name='Test IN field',
            attr_type=attr_type_txt, index=0,
            required=False, omit=False
        )
        Attribute.objects.create(
            schema=pt_schema_gr,
            name='party_gr', long_name='Test GR field',
            attr_type=attr_type_txt, index=0,
            required=False, omit=False
        )
        Attribute.objects.create(
            schema=pt_schema_gr,
            name='party_gr_dec', long_name='Test GR dec field',
            attr_type=attr_type_dec, index=1,
            required=False, omit=False
        )

        self.party_default_attributes = [
            'party::default_attr', 'party::default_int_attr'
        ]
        self.party_in_attributes = [
            'party::party_in'
        ]
        self.party_gr_attributes = [
            'party::party_gr', 'party::party_gr_dec'
        ]
        self.party_attributes = (
            self.party_default_attributes + self.party_in_attributes +
            self.party_gr_attributes
        )

        self.location_attributes = ['spatialunit::su_attr']
        self.attributes = (
            self.location_attributes + self.party_attributes
        )

    def test_get_flattened_attribute_map(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.conditionals_csv)
        entity_types = ['PT', 'SU']
        attr_map, extra_attrs, extra_headers = importer.get_attribute_map(
            'csv', entity_types, flatten=True
        )
        party_attrs = attr_map['party']
        assert len(party_attrs) == 5

    def test_import_csv(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.conditionals_csv)
        config = {
            'file': self.path + self.conditionals_csv,
            'entity_types': ['PT', 'SU'],
            'party_name_field': 'party_name',
            'party_type_field': 'party_type',
            'location_type_field': 'location_type',
            'geometry_field': 'location_geometry',
            'attributes': self.attributes,
            'project': self.project
        }
        importer.import_data(config)
        assert Party.objects.all().count() == 2
        assert SpatialUnit.objects.all().count() == 2
        assert TenureRelationship.objects.all().count() == 2
        for su in SpatialUnit.objects.filter(project_id=self.project.pk).all():
            if su.geometry is not None:
                assert type(su.geometry) is Point

        # test spatial unit attribute creation
        sus = SpatialUnit.objects.filter(
            attributes__contains={'su_attr': 'some value'})
        assert len(sus) == 1
        su = sus[0]
        assert su.type == 'PA'
        assert len(su.attributes) == 1

        # test party attribute creation
        party_in = Party.objects.filter(type='IN').first()
        assert party_in.name == 'Test Party'
        pty_attrs = party_in.attributes
        assert len(pty_attrs) == 3
        assert pty_attrs['default_attr'] == 'test default attr in'
        assert pty_attrs['default_int_attr'] == 10
        assert pty_attrs['party_in'] == 'some individual value'

        party_gr = Party.objects.filter(type='GR').first()
        assert party_gr.name == 'Another Test Party'
        pty_attrs = party_gr.attributes
        assert len(pty_attrs) == 4
        assert pty_attrs['default_attr'] == 'test default attr gr'
        assert pty_attrs['default_int_attr'] == 20
        assert pty_attrs['party_gr'] == 'some group value'
        assert pty_attrs['party_gr_dec'] == 2.00

        # test tenure relationship creation
        tenure_relationships = TenureRelationship.objects.all()
        assert len(tenure_relationships) == 2

    def test_import_xlsx(self):
        importer = xls.XLSImporter(
            project=self.project, path=self.path + self.conditionals_xls)
        config = {
            'file': self.path + self.conditionals_xls,
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
        assert Party.objects.all().count() == 2
        assert SpatialUnit.objects.all().count() == 2
        assert TenureRelationship.objects.all().count() == 2
        for su in SpatialUnit.objects.filter(project_id=self.project.pk).all():
            if su.geometry is not None:
                assert type(su.geometry) is Point

        # test spatial unit attribute creation
        sus = SpatialUnit.objects.filter(
            attributes__contains={'su_attr': 'some value'})
        assert len(sus) == 1
        su = sus[0]
        assert su.type == 'PA'
        assert len(su.attributes) == 1

        # test party attribute creation
        party_in = Party.objects.filter(type='IN').first()
        assert party_in.name == 'Another Test Party'
        pty_attrs = party_in.attributes
        assert len(pty_attrs) == 3
        assert pty_attrs['default_attr'] == 'test default attr in'
        assert pty_attrs['default_int_attr'] == 10
        assert pty_attrs['party_in'] == 'some individual value'

        party_gr = Party.objects.filter(type='GR').first()
        assert party_gr.name == 'Test Party'
        pty_attrs = party_gr.attributes
        assert len(pty_attrs) == 4
        assert pty_attrs['default_attr'] == 'test default attr gr'
        assert pty_attrs['default_int_attr'] == 20
        assert pty_attrs['party_gr'] == 'some group value'
        assert pty_attrs['party_gr_dec'] == 2.0

        # test tenure relationship creation
        tenure_relationships = TenureRelationship.objects.all()
        assert len(tenure_relationships) == 2
