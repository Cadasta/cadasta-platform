from django.test import TestCase

from geography.models import WorldBorder


class WorldBorderTest(TestCase):
    def test_str(self):
        border = WorldBorder.objects.create(
            name='Narnia', area=1, pop2005=1, un=1, region=1, subregion=1,
            lat=0, lon=0,
            mpoly='MULTIPOLYGON(((10 10, 10 20, 20 20, 20 15, 10 10)))'
        )
        assert str(border) == 'Narnia'
