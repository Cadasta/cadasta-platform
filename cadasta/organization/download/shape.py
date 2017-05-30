import csv
import os
from collections import OrderedDict
from zipfile import ZipFile

from osgeo import ogr, osr

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string

from .base import Exporter

MIME_TYPE = 'application/zip'


class ShapeExporter(Exporter):

    def write_items(self, filename, queryset, content_type, model_attrs):
        schema_attrs = self.get_schema_attrs(content_type)

        # build column labels
        attr_columns = OrderedDict()
        for a in model_attrs:
            attr_columns[a] = ''
        for _, attrs in schema_attrs.items():
            for a in attrs.values():
                if a.name not in attr_columns.keys():
                    attr_columns[a.name] = None

        with open(filename, 'w+', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(attr_columns.keys())

            for item in queryset:
                values = self.get_values(item, model_attrs, schema_attrs)
                data = attr_columns.copy()
                data.update(values)
                csvwriter.writerow(data.values())

    def write_relationships(self, filename):
        relationships = self.project.tenure_relationships.all()
        if relationships.count() == 0:
            return

        content_type = ContentType.objects.get(app_label='party',
                                               model='tenurerelationship')
        self.write_items(filename, relationships, content_type,
                         ('id', 'party_id', 'spatial_unit_id', 'tenure_type'))

    def write_parties(self, filename):
        parties = self.project.parties.all()
        if parties.count() == 0:
            return

        content_type = ContentType.objects.get(app_label='party',
                                               model='party')
        self.write_items(filename, parties, content_type,
                         ('id', 'name', 'type'))

    def write_features(self, ds, filename):
        spatial_units = self.project.spatial_units.all()
        if spatial_units.count() == 0:
            return

        content_type = ContentType.objects.get(app_label='spatial',
                                               model='spatialunit')
        model_attrs = ('id', 'type')

        self.write_items(
            filename, spatial_units, content_type, model_attrs)

        layers = {}

        for su in spatial_units:
            # Excluding empty geometries from export
            if not su.geometry:
                continue

            geom = ogr.CreateGeometryFromWkt(su.geometry.wkt)
            layer_type = geom.GetGeometryName().lower()
            layer = layers.get(layer_type, None)
            if layer is None:
                layer = self.create_layer(ds, layer_type)
                layers[layer_type] = layer
            if layer:
                feature = ogr.Feature(layer.GetLayerDefn())
                feature.SetGeometry(geom)
                feature.SetField('id', su.id)
                layer.CreateFeature(feature)
                feature.Destroy()
        return layers

    def create_datasource(self, dst_dir):
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        driver = ogr.GetDriverByName('ESRI Shapefile')
        return driver.CreateDataSource(dst_dir)

    def create_layer(self, datasource, layer_type):
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)

        types = {
            'point': ogr.wkbPoint,
            'linestring': ogr.wkbLineString,
            'polygon': ogr.wkbPolygon,
            'multipoint': ogr.wkbMultiPoint,
            'multilinestring': ogr.wkbMultiLineString,
            'multipolygon': ogr.wkbMultiPolygon
        }

        if layer_type in types.keys():
            layer = datasource.CreateLayer(
                layer_type, srs, geom_type=types[layer_type])
            field = ogr.FieldDefn('id', ogr.OFTString)
            layer.CreateField(field)
            return layer

    def make_download(self, f_name):
        dst_dir = os.path.join(settings.MEDIA_ROOT, 'temp/{}'.format(f_name))

        ds = self.create_datasource(dst_dir)

        self.write_features(ds, os.path.join(dst_dir, 'locations.csv'))
        self.write_relationships(os.path.join(dst_dir, 'relationships.csv'))
        self.write_parties(os.path.join(dst_dir, 'parties.csv'))

        ds.Destroy()

        path = os.path.join(settings.MEDIA_ROOT, 'temp/{}.zip'.format(f_name))
        readme = render_to_string(
            'organization/download/shp_readme.txt',
            {'project_name': self.project.name}
        )
        with ZipFile(path, 'a') as myzip:
            myzip.writestr('README.txt', readme)
            for f in os.listdir(dst_dir):
                myzip.write(os.path.join(dst_dir, f), arcname=f)

        return path, MIME_TYPE
