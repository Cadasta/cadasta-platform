from django.contrib.gis.gdal import OGRGeometry

from ..exceptions import NotWgs84EwkbValueError


def convert_postgis_ewkb_to_ewkt(ewkb_hex):
    # Assert that format is little endian, capitalized, and SRID=4326
    if ewkb_hex[6:18] != '0020E6100000':
        raise NotWgs84EwkbValueError(ewkb_hex)
    wkb_hex = ewkb_hex[0:6] + '0000' + ewkb_hex[18:]
    return 'SRID=4326;' + OGRGeometry(wkb_hex).wkt
