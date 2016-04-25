import os
from django.contrib.gis.utils import LayerMapping
from .models import WorldBorder


world_mapping = {
    'fips': 'FIPS_10_',
    'iso2': 'ISO_A2',
    'iso3': 'ISO_A3',
    'un': 'UN_A3',
    'name': 'NAME',
    'pop_est': 'POP_EST',
    'region': 'REGION_UN',
    'subregion': 'SUBREGION',
    'mpoly': 'MULTIPOLYGON',
}

world_shp = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'data', 'ne_10m_admin_0_countries.shp'
))


def run(verbose=True):
    WorldBorder.objects.all().delete()
    lm = LayerMapping(WorldBorder, world_shp, world_mapping,
                      transform=False, encoding='iso-8859-1')

    lm.save(strict=True, verbose=verbose)
