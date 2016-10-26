import pytest

from django.test import TestCase

from ..utils import InvalidODKGeometryError, odk_geom_to_wkt


class TestODKGeomToWKT(TestCase):

    def setUp(self):
        self.geoshape = ('45.56342779158167 -122.67650283873081 0.0 0.0;'
                         '45.56176327330353 -122.67669159919024 0.0 0.0;'
                         '45.56151562182025 -122.67490658909082 0.0 0.0;'
                         '45.563479432877415 -122.67494414001703 0.0 0.0;'
                         '45.56176327330353 -122.67669159919024 0.0 0.0')

        self.line = ('45.56342779158167 -122.67650283873081 0.0 0.0;'
                     '45.56176327330353 -122.67669159919024 0.0 0.0;'
                     '45.56151562182025 -122.67490658909082 0.0 0.0;')

        self.simple_line = (
            '45.56342779158167 -122.67650283873081 0.0 0.0;'
            '45.56176327330353 -122.67669159919024 0.0 0.0;'
        )

        self.geotrace_as_poly = (
            '52.9414478 -8.034659 0.0 0.0;'
            '52.94134675 -8.0354197 0.0 0.0;'
            '52.94129841 -8.03517551 0.0 0.0;'
            '52.94142406 -8.03487897 0.0 0.0;'
            '52.9414478 -8.034659 0.0 0.0;'
        )

        self.point = '45.56342779158167 -122.67650283873081 0.0 0.0;'

    def test_geoshape(self):
        poly = (
            'POLYGON ((-122.6765028387308121 45.5634277915816668, '
            '-122.6766915991902351 45.5617632733035265, -122.6749065890908241 '
            '45.5615156218202486, -122.6749441400170326 45.5634794328774149, '
            '-122.6765028387308121 45.5634277915816668))'
        )
        geom = odk_geom_to_wkt(self.geoshape)
        assert geom == poly

    def test_geotrace(self):
        line = (
            'LINESTRING (-122.6765028387308121 45.5634277915816668, '
            '-122.6766915991902351 45.5617632733035265, -122.6749065890908241 '
            '45.5615156218202486)'
        )
        geom = odk_geom_to_wkt(self.line)
        assert geom == line

    def test_geopoint(self):
        point = 'POINT (-122.6765028387308121 45.5634277915816668)'
        geom = odk_geom_to_wkt(self.point)
        assert geom == point

    def test_line_two_points(self):
        line = (
            'LINESTRING (-122.6765028387308121 45.5634277915816668, '
            '-122.6766915991902351 45.5617632733035265)'
        )
        geom = odk_geom_to_wkt(self.simple_line)
        assert geom == line

    def test_geotrace_as_poly(self):
        poly = (
            'POLYGON ((-8.0346589999999996 52.9414477999999988, '
            '-8.0354197000000003 52.9413467500000010, -8.0351755100000002 '
            '52.9412984100000017, -8.0348789699999994 52.9414240600000028, '
            '-8.0346589999999996 52.9414477999999988))'
        )
        geom = odk_geom_to_wkt(self.geotrace_as_poly)
        assert geom == poly

    def test_bad_geom(self):
        bad_geom = 'this is not a geometry'
        with pytest.raises(InvalidODKGeometryError) as e:
            odk_geom_to_wkt(bad_geom)
        assert str(e.value) == (
            "Invalid ODK Geometry: could not convert string to float: 'is'"
        )
