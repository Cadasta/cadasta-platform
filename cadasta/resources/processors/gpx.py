from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GeometryCollection

KEEP_LAYERS = ['tracks', 'routes', 'waypoints']


class GPXProcessor:

    def __init__(self, gpx_file):
        self.ds = DataSource(gpx_file)

    def get_layers(self):
        layers = {}
        for layer in self.ds:
            name = layer.name
            if name in KEEP_LAYERS:
                # geom = self._get_features(layer)
                layers[name] = GeometryCollection(layer.get_geoms(geos=True))
        return layers
