import time
import os
from openpyxl import load_workbook, Workbook
from zipfile import ZipFile
from django.test import TestCase
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from jsonattrs.models import Attribute, AttributeType, Schema

from organization.tests.factories import ProjectFactory
from spatial.tests.factories import SpatialUnitFactory
from resources.utils.io import ensure_dirs
from resources.tests.factories import ResourceFactory
from resources.models import ContentObject
from core.tests.base_test_case import UserTestCase
from party.tests.factories import TenureRelationshipFactory, PartyFactory

from ..download.xls import XLSExporter
from ..download.resources import ResourceExporter


class XLSTest(TestCase):
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


class ResourcesTest(UserTestCase):
    def test_init(self):
        project = ProjectFactory.build()
        exporter = ResourceExporter(project)
        assert exporter.project == project

    def test_make_resource_worksheet(self):
        ensure_dirs()
        project = ProjectFactory.create()
        exporter = ResourceExporter(project)

        # path = os.path.join(settings.MEDIA_ROOT, 'temp/test-res.xlsx')
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
