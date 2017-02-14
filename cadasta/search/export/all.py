import os

from zipfile import ZipFile

from .shape import ShapeExporter
from .xls import XLSExporter
from .resource import ResourceExporter


class AllExporter():

    def __init__(self, project):
        self.project = project

    def make_download(self, es_dump_path):
        shp_exporter = ShapeExporter(self.project, is_standalone=False)
        xls_exporter = XLSExporter(self.project)
        res_exporter = ResourceExporter(self.project)
        shp_dir_path = shp_exporter.make_download(es_dump_path)
        xls_path, _ = xls_exporter.make_download(es_dump_path)
        path, mime_type = res_exporter.make_download(es_dump_path)

        with ZipFile(path, 'a') as myzip:
            myzip.write(xls_path, arcname='data.xlsx')
            for f in os.listdir(shp_dir_path):
                myzip.write(os.path.join(shp_dir_path, f),
                            arcname='shape_files/' + f)
            myzip.close()

        return path, mime_type
