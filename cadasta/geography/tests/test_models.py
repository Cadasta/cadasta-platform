from django.test import TestCase

from geography.models import WorldBorder


class WorldBorderTest(TestCase):
    def test_str(self):
        border = WorldBorder.objects.create(
            name='Narnia', pop_est=1, un=1,
            mpoly='MULTIPOLYGON(((10 10, 10 20, 20 20, 20 15, 10 10)))'
        )
        assert str(border) == 'Narnia'
