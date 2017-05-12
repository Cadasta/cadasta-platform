import logging

import gpxpy
from django.contrib.gis.geos import (GeometryCollection, LineString,
                                     MultiLineString, MultiPoint, Point)
from django.utils.translation import ugettext as _

from ..exceptions import InvalidGPXFile

logger = logging.getLogger(__name__)


class GPXProcessor:

    def __init__(self, gpx_file):
        with open(gpx_file) as f:
            try:
                self.gpx = gpxpy.parse(f)
            except gpxpy.gpx.GPXException as e:
                logger.exception(e)
                raise InvalidGPXFile(_("Invalid GPX file: %s" % e))

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
