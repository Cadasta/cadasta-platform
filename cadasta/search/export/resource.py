import itertools
import json
import os
import subprocess

from openpyxl import Workbook
from zipfile import ZipFile

from resources.models import ContentObject

MIME_TYPE = 'application/zip'


class ResourceExporter():

    def __init__(self, project):
        self.project = project

    def make_download(self, es_dump_path):
        base_path = os.path.splitext(es_dump_path)[0]
        has_resources = False

        # Create worksheet for resources metadata
        workbook = Workbook(write_only=True)
        worksheet = workbook.create_sheet(title='resources')
        worksheet.append(['id', 'name', 'description', 'filename',
                          'locations', 'parties', 'relationships'])

        # Create temp dir where S3 files will be downloaded
        dir_path = base_path + '-res-dir'
        os.makedirs(dir_path)

        # Create zip file and start processing
        zip_path = base_path + '-res.zip'
        filenames = set()
        with ZipFile(zip_path, 'a') as myzip:

            f = open(es_dump_path, encoding='utf-8')
            while True:
                # Read 2 lines in the dump file
                type_line = f.readline()
                source_line = f.readline()
                if not type_line:
                    break

                # Extract ES type and source and skip if not resource
                es_type = json.loads(type_line)['index']['_type']
                if es_type != 'resource':
                    continue
                has_resources = True
                source = json.loads(source_line)

                # Fetch file from S3 using curl and add to zip file
                # and ensuring filenames are unique
                temp_resource_path = dir_path + '/' + source['original_file']
                subprocess.run([
                    'curl', '-o', temp_resource_path, '-XGET', source['file']
                ])
                filename = source['original_file']
                if filename in filenames:
                    basename, ext = os.path.splitext(filename)
                    for x in itertools.count(2):
                        trial = '{} ({}){}'.format(basename, x, ext)
                        if trial not in filenames:
                            filename = trial
                            source['original_file'] = trial
                            break
                filenames.add(filename)
                myzip.write(temp_resource_path,
                            arcname='resources/' + filename)

                self.append_resource_metadata(source, worksheet)

            if has_resources:
                xls_path = base_path + '-res.xlsx'
                workbook.save(filename=xls_path)
                myzip.write(xls_path, arcname='resources.xlsx')

            myzip.close()

        return zip_path, MIME_TYPE

    def append_resource_metadata(self, source, worksheet):
        location_ids = []
        party_ids = []
        tenure_rel_ids = []

        links = ContentObject.objects.filter(
            resource__id=source['id']).values_list(
                'content_type__model', 'object_id')
        for link in links:
            if link[0] == 'spatialunit':
                location_ids.append(link[1])
            elif link[0] == 'party':
                party_ids.append(link[1])
            elif link[0] == 'tenurerelationship':
                tenure_rel_ids.append(link[1])

        worksheet.append([
            source['id'],
            source['name'],
            source['description'],
            source['original_file'],
            ','.join(location_ids),
            ','.join(party_ids),
            ','.join(tenure_rel_ids),
        ])
