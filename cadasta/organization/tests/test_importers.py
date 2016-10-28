import pytest

from core.tests.utils.cases import UserTestCase, FileStorageTestCase
from django.contrib.gis.geos import LineString, Point, Polygon
from django.test import TestCase
from jsonattrs.models import Attribute, Schema
from party.models import Party, TenureRelationship
from questionnaires.models import Questionnaire
from resources.tests.utils import clear_temp  # noqa
from spatial.models import SpatialUnit

from ..importers import csv, exceptions
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

    def test_done(self):
        project = ProjectFactory.create()
        importer = Importer(project)
        with pytest.raises(NotImplementedError):
            importer.import_data(config_dict=None)


@pytest.mark.usefixtures('clear_temp')
class CSVImportTest(UserTestCase, FileStorageTestCase, TestCase):

    def setUp(self):
        super().setUp()

        self.valid_csv = '/organization/tests/files/test.csv'
        self.invalid_csv = '/organization/tests/files/test_invalid.csv'
        self.invalid_col_csv = '/organization/tests/files/invalid_col.csv'
        self.geoshape_csv = '/organization/tests/files/test_geoshape.csv'
        self.geotrace_csv = '/organization/tests/files/test_geotrace.csv'
        self.no_tenure_type = '/organization/tests/files/no_tenure_type.csv'
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

        self.attributes = [
            'deed_of_land', 'amount_othersland', 'educational_qualification',
            'name_mouza', 'land_calculation', 'how_aquire_landwh',
            'female_member', 'mutation_of_land', 'amount_agriland',
            'nid_number', 'class_hh', 'j_l', 'how_aquire_landt',
            'boundary_conflict', 'dakhal_on_land', 'village_name',
            'how_aquire_landp', 'how_aquire_landd', 'ownership_conflict',
            'occupation_hh', 'others_conflict', 'how_aquire_landm',
            'khatain_of_land', 'male_member', 'mobile_no', 'how_aquire_landw',
            'everything', 'name_father_hus', 'tenure_name', 'tenure_notes',
            'location_problems'
        ]

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
        attr_map, extra_attrs, extra_headers = importer.get_attribute_map()
        assert len(attr_map.keys()) == 31
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

        # test party attribute creation
        parties = Party.objects.filter(
            attributes__contains={'Mobile_No': '০১৭৭২৫৬০১৯১'})
        assert len(parties) == 1
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

    def test_import_with_invalid_column(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.invalid_col_csv)
        config_dict = {
            'file': self.path + self.invalid_col_csv,
            'party_name_field': 'name_of_hh',
            'party_type': 'IN',
            'location_type': 'PA',
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

    def test_import_with_geoshape(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.geoshape_csv)
        config_dict = {
            'file': self.path + self.geoshape_csv,
            'party_name_field': 'name_of_hh',
            'party_type': 'IN',
            'location_type': 'PA',
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
            'geometry_field': 'location_geometry',
            'attributes': self.attributes,
            'project': self.project
        }
        with pytest.raises(exceptions.DataImportError):
            importer.import_data(config_dict)
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

    def test_import_with_wkt(self):
        importer = csv.CSVImporter(
            project=self.project, path=self.path + self.test_wkt)
        config_dict = {
            'file': self.path + self.test_wkt,
            'party_name_field': 'name_of_hh',
            'party_type': 'IN',
            'location_type': 'PA',
            'geometry_field': 'location_geometry',
            'attributes': self.attributes,
            'project': self.project
        }
        importer.import_data(config_dict)
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
