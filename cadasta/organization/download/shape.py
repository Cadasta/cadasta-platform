import os
import csv
from osgeo import ogr, osr
from zipfile import ZipFile
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string

from .base import Exporter

MIME_TYPE = 'application/zip'


class ShapeExporter(Exporter):
    def write_items(self, filename, queryset, content_type, model_attrs):
        schema_attrs = self.get_schema_attrs(content_type)
        fields = list(model_attrs) + [a.name for a in schema_attrs]

        with open(filename, 'w+', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(fields)

            for item in queryset:
                values = self.get_values(item, model_attrs, schema_attrs)
                csvwriter.writerow(values)

    def write_relationships(self, filename):
        content_type = ContentType.objects.get(app_label='party',
                                               model='tenurerelationship')
        self.write_items(filename,
                         self.project.tenure_relationships.all(),
                         content_type,
                         ('id', 'party_id', 'spatial_unit_id',
                          'tenure_type.label'))

    def write_parties(self, filename):
        content_type = ContentType.objects.get(app_label='party',
                                               model='party')
        self.write_items(filename,
                         self.project.parties.all(),
                         content_type,
                         ('id', 'name', 'type'))

    def write_features(self, layers, filename):
        content_type = ContentType.objects.get(app_label='spatial',
                                               model='spatialunit')
        model_attrs = ('id', 'type')
        schema_attrs = self.get_schema_attrs(content_type)

        with open(filename, 'w+', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(list(model_attrs) +
                               [a.name for a in schema_attrs])

            for su in self.project.spatial_units.all():
                geom = ogr.CreateGeometryFromWkt(su.geometry.wkt)
                layer_type = geom.GetGeometryType() - 1
                layer = layers[layer_type]

                feature = ogr.Feature(layer.GetLayerDefn())
                feature.SetGeometry(ogr.CreateGeometryFromWkt(su.geometry.wkt))
                feature.SetField('id', su.id)
                layer.CreateFeature(feature)
                feature.Destroy()

                values = self.get_values(su, model_attrs, schema_attrs)
                csvwriter.writerow(values)

    def create_datasource(self, dst_dir, f_name):
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        path = os.path.join(dst_dir, f_name + '-point.shp')
        driver = ogr.GetDriverByName('ESRI Shapefile')
        return driver.CreateDataSource(path)

    def create_shp_layers(self, datasource, f_name):
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)

        layers = (
            datasource.CreateLayer(f_name + '-point', srs, geom_type=1),
            datasource.CreateLayer(f_name + '-line', srs, geom_type=2),
            datasource.CreateLayer(f_name + '-polygon', srs, geom_type=3)
        )

        for layer in layers:
            field = ogr.FieldDefn('id', ogr.OFTString)
            layer.CreateField(field)

        return layers

    def make_download(self, f_name):
        dst_dir = os.path.join(settings.MEDIA_ROOT, 'temp/{}'.format(f_name))

        ds = self.create_datasource(dst_dir, self.project.slug)
        layers = self.create_shp_layers(ds, self.project.slug)

        self.write_features(layers, os.path.join(dst_dir, 'locations.csv'))
        self.write_relationships(os.path.join(dst_dir, 'relationships.csv'))
        self.write_parties(os.path.join(dst_dir, 'parties.csv'))

        ds.Destroy()

        path = os.path.join(settings.MEDIA_ROOT, 'temp/{}.zip'.format(f_name))
        readme = render_to_string(
            'organization/download/shp_readme.txt',
            {'project_name': self.project.name,
             'project_slug': self.project.slug}
        )
        with ZipFile(path, 'a') as myzip:
            myzip.writestr('README.txt', readme)
            for file in os.listdir(dst_dir):
                myzip.write(os.path.join(dst_dir, file), arcname=file)

        return path, MIME_TYPE
