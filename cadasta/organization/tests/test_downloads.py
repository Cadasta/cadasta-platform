import pytest
import time
import os
import csv
from openpyxl import load_workbook, Workbook
from zipfile import ZipFile

from django.test import TestCase
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from jsonattrs.models import Attribute, AttributeType, Schema

from core.tests.utils.files import make_dirs  # noqa
from organization.tests.factories import ProjectFactory
from spatial.tests.factories import SpatialUnitFactory
from resources.utils.io import ensure_dirs
from resources.tests.factories import ResourceFactory
from resources.tests.utils import clear_temp  # noqa
from resources.models import ContentObject
from core.tests.utils.cases import UserTestCase
from party.tests.factories import TenureRelationshipFactory, PartyFactory
from party.models import TenureRelationshipType

from ..download.base import Exporter
from ..download.xls import XLSExporter
from ..download.resources import ResourceExporter
from ..download.shape import ShapeExporter


class BaseExporterTest(UserTestCase, TestCase):
    def test_init(self):
        project = ProjectFactory.build()
        exporter = Exporter(project)
        assert exporter.project == project

    def test_get_schema_attrs_empty(self):
        project = ProjectFactory.create()
        content_type = ContentType.objects.get(app_label='spatial',
                                               model='spatialunit')
        exporter = Exporter(project)
        assert exporter.get_schema_attrs(content_type) == []
        assert exporter._schema_attrs['spatial.spatialunit'] == []

    def test_get_schema_attrs(self):
        project = ProjectFactory.create(current_questionnaire='123abc')
        content_type = ContentType.objects.get(app_label='spatial',
                                               model='spatialunit')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, '123abc', ))
        text_type = AttributeType.objects.get(name='text')
        Attribute.objects.create(
            schema=schema,
            name='key', long_name='Test field',
            attr_type=text_type, index=0,
            required=False, omit=False
        )
        Attribute.objects.create(
            schema=schema,
            name='key_2', long_name='Test field',
            attr_type=text_type, index=1,
            required=False, omit=False
        )
        Attribute.objects.create(
            schema=schema,
            name='key_3', long_name='Test field',
            attr_type=text_type, index=2,
            required=False, omit=True
        )

        exporter = Exporter(project)
        attrs = exporter.get_schema_attrs(content_type)
        assert len(attrs) == 2

    def test_get_values(self):
        project = ProjectFactory.create(current_questionnaire='123abc')
        exporter = Exporter(project)
        content_type = ContentType.objects.get(app_label='party',
                                               model='tenurerelationship')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, '123abc', ))
        text_type = AttributeType.objects.get(name='text')
        attr = Attribute.objects.create(
            schema=schema,
            name='key', long_name='Test field',
            attr_type=text_type, index=0,
            required=False, omit=False
        )

        ttype = TenureRelationshipType.objects.get(id='LH')
        item = TenureRelationshipFactory.create(project=project,
                                                tenure_type=ttype,
                                                attributes={'key': 'text'})
        model_attrs = ('id', 'party_id', 'spatial_unit_id',
                       'tenure_type.label')
        schema_attrs = [attr]
        values = exporter.get_values(item, model_attrs, schema_attrs)
        assert values == [item.id, item.party_id, item.spatial_unit_id,
                          'Leasehold', 'text']


@pytest.mark.usefixtures('clear_temp')
class ShapeTest(UserTestCase, TestCase):
    def test_init(self):
        project = ProjectFactory.build()
        exporter = ShapeExporter(project)
        assert exporter.project == project

    def test_create_datasource(self):
        ensure_dirs()
        project = ProjectFactory.create()
        exporter = ShapeExporter(project)

        dst_dir = os.path.join(settings.MEDIA_ROOT, 'temp/file')
        ds = exporter.create_datasource(dst_dir, 'file0')
        assert (ds.GetName() ==
                os.path.join(settings.MEDIA_ROOT, 'temp/file/file0-point.shp'))
        ds.Destroy()

    def test_create_shp_layers(self):
        ensure_dirs()
        project = ProjectFactory.create()
        exporter = ShapeExporter(project)

        dst_dir = os.path.join(settings.MEDIA_ROOT, 'temp/file6')
        ds = exporter.create_datasource(dst_dir, 'file6')
        layers = exporter.create_shp_layers(ds, 'file6')
        assert len(layers) == 3
        assert layers[0].GetName() == 'file6-point'
        assert layers[1].GetName() == 'file6-line'
        assert layers[2].GetName() == 'file6-polygon'
        ds.Destroy()

    def test_write_items(self):
        project = ProjectFactory.create(current_questionnaire='123abc')

        content_type = ContentType.objects.get(app_label='party',
                                               model='party')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, '123abc', ))

        for idx, type in enumerate(['text', 'boolean', 'dateTime', 'integer']):
            attr_type = AttributeType.objects.get(name=type)
            Attribute.objects.create(
                schema=schema,
                name=type, long_name=type,
                attr_type=attr_type, index=idx,
                required=False, omit=False
            )

        party = PartyFactory.create(
            project=project,
            name='Donald Duck',
            type='IN',
            attributes={
                'text': 'text',
                'boolean': True,
                'dateTime': '2011-08-12 11:13',
                'integer': 1,
            }
        )

        exporter = ShapeExporter(project)
        dst_dir = os.path.join(settings.MEDIA_ROOT, 'temp/party')
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        filename = os.path.join(dst_dir, 'parties.csv')
        exporter.write_items(filename,
                             [party],
                             content_type,
                             ('id', 'name', 'type'))

        with open(filename) as csvfile:
            csvreader = csv.reader(csvfile)

            for i, row in enumerate(csvreader):
                assert len(row) == 7
                if i == 0:
                    assert row == ['id', 'name', 'type', 'text', 'boolean',
                                   'dateTime', 'integer']
                else:
                    assert row == [party.id, party.name, party.type, 'text',
                                   'True', '2011-08-12 11:13', '1']

    def test_write_features(self):
        ensure_dirs()
        project = ProjectFactory.create(current_questionnaire='123abc')
        exporter = ShapeExporter(project)

        content_type = ContentType.objects.get(app_label='spatial',
                                               model='spatialunit')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, '123abc', ))
        attr_type = AttributeType.objects.get(name='text')
        Attribute.objects.create(
            schema=schema,
            name='key', long_name='Test field',
            attr_type=attr_type, index=0,
            required=False, omit=False
        )

        su1 = SpatialUnitFactory.create(
            project=project,
            geometry='POINT (1 1)',
            attributes={'key': 'value 1'})
        su2 = SpatialUnitFactory.create(
            project=project,
            geometry='POINT (2 2)',
            attributes={'key': 'value 2'})

        dst_dir = os.path.join(settings.MEDIA_ROOT, 'temp/file4')
        ds = exporter.create_datasource(dst_dir, 'file4')
        layers = exporter.create_shp_layers(ds, 'file4')

        csvfile = os.path.join(dst_dir, 'locations.csv')
        exporter.write_features(layers, csvfile)

        assert len(layers[0]) == 2
        f = layers[0].GetNextFeature()
        while f:
            geom = f.geometry()
            assert geom.ExportToWkt() in ['POINT (1 1)', 'POINT (2 2)']
            assert f.GetFieldAsString('id') in [su1.id, su2.id]

            f = layers[0].GetNextFeature()

        ds.Destroy()

        with open(csvfile) as csvfile:
            csvreader = csv.reader(csvfile)
            for i, row in enumerate(csvreader):
                if i == 0:
                    assert row == ['id', 'type', 'key']
                elif row[0] == su1.id:
                    assert row == [su1.id, su1.type, 'value 1']
                elif row[1] == su2.id:
                    assert row == [su2.id, su2.type, 'value 2']

    def test_write_relationships(self):
        dst_dir = os.path.join(settings.MEDIA_ROOT, 'temp/rels')
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        filename = os.path.join(dst_dir, 'releationships.csv')

        project = ProjectFactory.create()
        exporter = ShapeExporter(project)
        exporter.write_relationships(filename)

        with open(filename) as csvfile:
            csvreader = csv.reader(csvfile)
            for i, row in enumerate(csvreader):
                if i == 0:
                    assert row == ['id', 'party_id', 'spatial_unit_id',
                                   'tenure_type.label']
                else:
                    assert False, "Too many rows in CSV."

    def test_write_parties(self):
        dst_dir = os.path.join(settings.MEDIA_ROOT, 'temp/party')
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        filename = os.path.join(dst_dir, 'parties.csv')

        project = ProjectFactory.create()
        exporter = ShapeExporter(project)
        exporter.write_parties(filename)

        with open(filename) as csvfile:
            csvreader = csv.reader(csvfile)
            for i, row in enumerate(csvreader):
                if i == 0:
                    assert row == ['id', 'name', 'type']
                else:
                    assert False, "Too many rows in CSV."

    def test_make_download(self):
        ensure_dirs()
        project = ProjectFactory.create(current_questionnaire='123abc')
        exporter = ShapeExporter(project)

        content_type = ContentType.objects.get(app_label='spatial',
                                               model='spatialunit')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, '123abc', ))
        attr_type = AttributeType.objects.get(name='text')
        Attribute.objects.create(
            schema=schema,
            name='key', long_name='Test field',
            attr_type=attr_type, index=0,
            required=False, omit=False
        )

        SpatialUnitFactory.create(
            project=project,
            geometry='POINT (1 1)',
            attributes={'key': 'value 1'})

        path, mime = exporter.make_download('file5')

        assert path == os.path.join(settings.MEDIA_ROOT, 'temp/file5.zip')
        assert mime == 'application/zip'

        with ZipFile(path, 'r') as testzip:
            assert len(testzip.namelist()) == 16
            assert project.slug + '-point.dbf' in testzip.namelist()
            assert project.slug + '-point.prj' in testzip.namelist()
            assert project.slug + '-point.shp' in testzip.namelist()
            assert project.slug + '-point.shx' in testzip.namelist()
            assert project.slug + '-line.dbf' in testzip.namelist()
            assert project.slug + '-line.prj' in testzip.namelist()
            assert project.slug + '-line.shp' in testzip.namelist()
            assert project.slug + '-line.shx' in testzip.namelist()
            assert project.slug + '-polygon.dbf' in testzip.namelist()
            assert project.slug + '-polygon.prj' in testzip.namelist()
            assert project.slug + '-polygon.shp' in testzip.namelist()
            assert project.slug + '-polygon.shx' in testzip.namelist()
            assert 'relationships.csv' in testzip.namelist()
            assert 'parties.csv' in testzip.namelist()
            assert 'locations.csv' in testzip.namelist()
            assert 'README.txt' in testzip.namelist()


@pytest.mark.usefixtures('clear_temp')
class XLSTest(UserTestCase, TestCase):
    def test_init(self):
        project = ProjectFactory.build()
        exporter = XLSExporter(project)
        assert exporter.project == project

    def test_write_items(self):
        project = ProjectFactory.create(current_questionnaire='123abc')

        content_type = ContentType.objects.get(app_label='spatial',
                                               model='spatialunit')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, '123abc', ))
        attr_type = AttributeType.objects.get(name='text')
        Attribute.objects.create(
            schema=schema,
            name='key', long_name='Test field',
            attr_type=attr_type, index=0,
            required=False, omit=False
        )

        spatialunit_1 = SpatialUnitFactory.create(
            project=project,
            geometry='POINT (1 1)',
            attributes={'key': 'value 1'})
        spatialunit_2 = SpatialUnitFactory.create(
            project=project,
            geometry='POINT (2 2)',
            attributes={'key': 'value 2'})
        spatialunits = [spatialunit_1, spatialunit_2]
        attrs = ['id', 'geometry.ewkt']

        workbook = Workbook()
        worksheet = workbook.create_sheet()
        worksheet.title = 'locations'

        exporter = XLSExporter(project)
        exporter.write_items(worksheet, spatialunits, content_type, attrs)

        assert worksheet['A1'].value == 'id'
        assert worksheet['B1'].value == 'geometry.ewkt'
        assert worksheet['C1'].value == 'key'

        assert worksheet['A2'].value == spatialunit_1.id
        assert worksheet['B2'].value == spatialunit_1.geometry.ewkt
        assert worksheet['C2'].value == 'value 1'

        assert worksheet['A3'].value == spatialunit_2.id
        assert worksheet['B3'].value == spatialunit_2.geometry.ewkt
        assert worksheet['C3'].value == 'value 2'

    def test_write_locations(self):
        workbook = Workbook()

        project = ProjectFactory.build()
        exporter = XLSExporter(project)
        exporter.workbook = workbook
        exporter.write_locations()
        assert workbook['locations']
        assert len(workbook['locations'].rows) == 1

    def test_write_parties(self):
        workbook = Workbook()

        project = ProjectFactory.build()
        exporter = XLSExporter(project)
        exporter.workbook = workbook
        exporter.write_parties()
        assert workbook['parties']
        assert len(workbook['parties'].rows) == 1

    def test_write_relationships(self):
        workbook = Workbook()

        project = ProjectFactory.build()
        exporter = XLSExporter(project)
        exporter.workbook = workbook

        exporter.write_relationships()
        assert workbook['relationships']
        assert len(workbook['relationships'].rows) == 1

    def test_make_download(self):
        ensure_dirs()
        project = ProjectFactory.create()
        exporter = XLSExporter(project)
        path, mime = exporter.make_download('file')

        assert path == os.path.join(settings.MEDIA_ROOT, 'temp/file.xlsx')
        assert (mime == 'application/vnd.openxmlformats-officedocument.'
                        'spreadsheetml.sheet')


@pytest.mark.usefixtures('clear_temp')
@pytest.mark.usefixtures('make_dirs')
class ResourcesTest(UserTestCase, TestCase):
    def test_init(self):
        project = ProjectFactory.build()
        exporter = ResourceExporter(project)
        assert exporter.project == project

    def test_make_resource_worksheet(self):
        ensure_dirs()
        project = ProjectFactory.create()
        exporter = ResourceExporter(project)

        data = [
            ['1', 'n1', 'd1', 'f1', 'l1', 'p1', 'r1'],
            ['2', 'n2', 'd2', 'f2', 'l2', 'p2', 'r2']
        ]

        res_path = exporter.make_resource_worksheet('test-res', data)
        wb = load_workbook(filename=res_path, read_only=True)
        sheet = wb[wb.get_sheet_names()[0]]

        expected_headers = ['id', 'name', 'description', 'filename',
                            'locations', 'parties', 'relationships']
        for i, h in enumerate(expected_headers):
            assert sheet[chr(i + 97) + '1'].value == h

        for i in range(0, len(data[0])):
            assert sheet[chr(i + 97) + '2'].value == data[0][i]
            assert sheet[chr(i + 97) + '3'].value == data[1][i]

    def test_pack_resource_data(self):
        project = ProjectFactory.create()
        exporter = ResourceExporter(project)

        res = ResourceFactory.create(project=project)
        loc = SpatialUnitFactory.create(project=project)
        loc2 = SpatialUnitFactory.create(project=project)
        par = PartyFactory.create(project=project)
        rel = TenureRelationshipFactory.create(project=project)

        ContentObject.objects.create(resource=res, content_object=loc)
        ContentObject.objects.create(resource=res, content_object=loc2)
        ContentObject.objects.create(resource=res, content_object=par)
        ContentObject.objects.create(resource=res, content_object=rel)

        packed = exporter.pack_resource_data(res)
        assert packed[0] == res.id
        assert packed[1] == res.name
        assert packed[2] == res.description
        assert packed[3] == res.original_file
        assert loc.id in packed[4]
        assert loc2.id in packed[4]
        assert par.id in packed[5]
        assert rel.id in packed[6]

    def test_make_download(self):
        ensure_dirs()
        project = ProjectFactory.create()
        exporter = ResourceExporter(project)
        res = ResourceFactory.create(project=project)

        t = round(time.time() * 1000)
        path, mime = exporter.make_download('res-test-' + str(t))
        assert path == os.path.join(settings.MEDIA_ROOT,
                                    'temp/res-test-{}.zip'.format(t))
        assert mime == 'application/zip'

        with ZipFile(path, 'r') as testzip:
            assert len(testzip.namelist()) == 2
            assert res.original_file in testzip.namelist()
            assert 'resources.xlsx' in testzip.namelist()
