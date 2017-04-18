import os
from openpyxl import Workbook
from zipfile import ZipFile
from django.conf import settings

from resources.models import Resource, ContentObject

MIME_TYPE = 'application/zip'


class ResourceExporter():
    def __init__(self, project):
        self.project = project

    def make_resource_worksheet(self, f_name, data):
        path = os.path.join(settings.MEDIA_ROOT,
                            'temp/{}.xlsx'.format(f_name))

        workbook = Workbook(write_only=True)
        worksheet = workbook.create_sheet()
        worksheet.append(['id', 'name', 'description', 'filename',
                          'locations', 'parties', 'relationships'])

        for d in data:
            worksheet.append(d)

        workbook.save(filename=path)

        return path

    def pack_resource_data(self, res):
        locations = []
        parties = []
        rels = []
        links = ContentObject.objects.filter(resource=res).values_list(
            'object_id', 'content_type__model')
        for l in links:
            if l[1] == 'spatialunit':
                locations.append(l[0])
            elif l[1] == 'party':
                parties.append(l[0])
            elif l[1] == 'tenurerelationship':
                rels.append(l[0])

        return [res.id, res.name, res.description, res.original_file,
                ', '.join(locations), ', '.join(parties), ', '.join(rels)]

    def make_download(self, f_name):
        path = os.path.join(settings.MEDIA_ROOT,
                            'temp/{}.zip'.format(f_name))

        resources = Resource.objects.filter(
            project=self.project,
            archived=False)
        res_data = []
        file_names = dict()
        file_names['resources.xlsx'] = 1

        with ZipFile(path, 'a') as myzip:
            for r in resources:
                if r.original_file not in file_names:
                    zip_fname = r.original_file
                    file_names[r.original_file] = 1
                else:
                    name, ext = os.path.splitext(r.original_file)
                    counter = str(file_names[r.original_file])
                    zip_fname = '{}_{}{}'.format(name, counter, ext)
                    file_names[r.original_file] += 1
                    r.original_file = zip_fname

                res_data.append(self.pack_resource_data(r))
                myzip.write(r.file.open().name, arcname=zip_fname)
            resources_xls = self.make_resource_worksheet(f_name, res_data)
            myzip.write(resources_xls, arcname='resources.xlsx')
            myzip.close()

        return path, MIME_TYPE
