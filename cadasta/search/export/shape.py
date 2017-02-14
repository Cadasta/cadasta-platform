import csv
import os

from zipfile import ZipFile
from osgeo import ogr, osr
from django.template.loader import render_to_string

from .base import Exporter

MIME_TYPE = 'application/zip'
shp_types = {
    'point': ogr.wkbPoint,
    'linestring': ogr.wkbLineString,
    'polygon': ogr.wkbPolygon,
    'multipoint': ogr.wkbMultiPoint,
    'multilinestring': ogr.wkbMultiLineString,
    'multipolygon': ogr.wkbMultiPolygon
}


class ShapeExporter(Exporter):

    def __init__(self, project, is_standalone=True):
        self.is_standalone = is_standalone
        super().__init__(project)

    def make_download(self, es_dump_path):
        base_path = os.path.splitext(es_dump_path)[0]

        # CSV files do not need the EWKT geometry
        self.metadata['location']['model_attrs'] = ['id', 'type']
        self.metadata['location']['attr_columns'].pop('geometry.ewkt')

        self.dir_path = base_path + '-shp-dir'
        self.shp_datasource = self.create_shp_datasource()

        f = open(es_dump_path, encoding='utf-8')
        while True:
            # Read 2 lines in the dump file
            type_line = f.readline()
            source_line = f.readline()
            if not type_line:
                break
            self.process_entity(
                type_line, source_line, self.write_csv_row_and_shp)

        # Clean up
        for metadatum in self.metadata.values():
            f = metadatum.get('csv_file')
            if f:
                f.close()
        self.shp_datasource.Destroy()

        # Add readme only if any file has been created
        if os.listdir(self.dir_path):
            readme_body = render_to_string(
                'organization/download/shp_readme.txt',
                {'project_name': self.project.name}
            )
            f = open(os.path.join(self.dir_path, 'README.txt'), 'w')
            f.write(readme_body)
            f.close()

        if self.is_standalone:
            zip_path = base_path + '-shp.zip'
            with ZipFile(zip_path, 'a') as myzip:
                for f in os.listdir(self.dir_path):
                    myzip.write(os.path.join(self.dir_path, f), arcname=f)
            return zip_path, MIME_TYPE
        else:
            return self.dir_path

    def create_shp_datasource(self):
        self.shp_layers = {}
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)
        driver = ogr.GetDriverByName('ESRI Shapefile')
        return driver.CreateDataSource(self.dir_path)

    def write_csv_row_and_shp(self, entity, metadatum):
        if self.is_standalone:
            # Create CSV file if not yet created
            if not metadatum.get('csv_file'):
                fn = os.path.join(self.dir_path, metadatum['title'] + '.csv')
                f = open(fn, 'w+', newline='')
                metadatum['csv_file'] = f
                w = csv.writer(f)
                metadatum['csv_writer'] = w
                w.writerow(metadatum['attr_columns'].keys())

            attr_values = self.get_attr_values(entity, metadatum)
            data = metadatum['attr_columns'].copy()
            data.update(attr_values)
            writer = metadatum['csv_writer']
            writer.writerow(list(data.values()))

        if metadatum['title'] == 'locations':
            self.write_shp_layer(entity)

    def write_shp_layer(self, loc_data):
        geom = ogr.CreateGeometryFromWkt(loc_data['geometry']['wkt'])
        layer_type = geom.GetGeometryName().lower()
        layer = self.shp_layers.get(layer_type, None)
        if layer is None:
            layer = self.create_shp_layer(layer_type)
            self.shp_layers[layer_type] = layer
        if layer:
            feature = ogr.Feature(layer.GetLayerDefn())
            feature.SetGeometry(geom)
            feature.SetField('id', loc_data['id'])
            layer.CreateFeature(feature)
            feature.Destroy()

    def create_shp_layer(self, layer_type):
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)

        if layer_type in shp_types.keys():
            layer = self.shp_datasource.CreateLayer(
                layer_type, srs, geom_type=shp_types[layer_type])
            field = ogr.FieldDefn('id', ogr.OFTString)
            layer.CreateField(field)
            return layer
