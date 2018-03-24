from django.contrib.gis.geos import (GeometryCollection, LineString,
                                     MultiLineString, MultiPoint, Point)
from django.utils.translation import ugettext as _
from gpxpy import gpx, parser

from ..exceptions import InvalidGPXFile


class GPXParser(parser.GPXParser):

    def parse(self, version=None):
        try:
            self.xml_parser = parser.XMLParser(self.xml)
            self.__parse_dom(version)
            return self.gpx
        except Exception as e:
            raise gpx.GPXXMLSyntaxException(
                'Error parsing XML: %s' % str(e), e)


class GPXProcessor:

    def __init__(self, gpx_file):
        with open(gpx_file, 'r') as f:
            try:
                parser = GPXParser(f)
                self.gpx = parser.parse(f)
            except gpx.GPXException as e:
                raise InvalidGPXFile(_("Invalid GPX file: %s" % str(e)))

    def get_layers(self):
        layers = {}
        if self.gpx.tracks:
            layers['tracks'] = GeometryCollection(
                MultiLineString(parse_tracks(self.gpx.tracks))
            )
        if self.gpx.routes:
            layers['routes'] = GeometryCollection(
                MultiLineString(parse_routes(self.gpx.routes))
            )
        if self.gpx.waypoints:
            layers['waypoints'] = GeometryCollection(
                MultiPoint(parse_waypoints(self.gpx.waypoints))
            )
        if not layers:
            raise InvalidGPXFile(
                _("Error parsing GPX file: no geometry found."))

        return layers


def parse_segment(segment):
    return [Point(p.longitude, p.latitude).coords for p in segment.points]


def parse_tracks(tracks):
    multiline = []
    for track in tracks:
        for segment in track.segments:
            points = parse_segment(segment)
            if len(points) > 1:
                multiline.append(LineString(points))
    return multiline


def parse_waypoints(waypoints):
    return [Point(point.longitude, point.latitude) for point in waypoints]


def parse_routes(routes):
    multiline = []
    for route in routes:
        points = parse_segment(route)
        if len(points) > 1:
            multiline.append(LineString(points))
    return multiline
