import os

from django.conf import settings
from django.contrib.gis.geos import GeometryCollection
from django.test import TestCase

from ..processors.gpx import GPXProcessor

path = os.path.dirname(settings.BASE_DIR)


class GPXProcessorTest(TestCase):

    def test_get_tracks(self):
        file_path = path + '/resources/tests/files/tracks.gpx'
        g = GPXProcessor(file_path)
        layers = g.get_layers()
        assert len(layers.keys()) == 1

        # test tracks
        tracks = layers['tracks']
        assert type(tracks) is GeometryCollection
        assert len(tracks) == 1

    def test_get_waypoints(self):
        file_path = path + '/resources/tests/files/waypoints.gpx'
        g = GPXProcessor(file_path)
        layers = g.get_layers()
        assert len(layers.keys()) == 1

        # test waypoints
        waypoints = layers['waypoints']
        assert type(waypoints) is GeometryCollection
        assert len(waypoints[0]) == 16

    def test_get_routes(self):
        file_path = path + '/resources/tests/files/routes.gpx'
        g = GPXProcessor(file_path)
        layers = g.get_layers()
        assert len(layers.keys()) == 1

        # test routes
        routes = layers['routes']
        assert type(routes) is GeometryCollection
        assert len(routes) == 1

    def test_get_track_segments(self):
        file_path = path + '/resources/tests/files/track_seg.gpx'
        g = GPXProcessor(file_path)
        layers = g.get_layers()
        assert len(layers.keys()) == 1

        # test tracks
        tracks = layers['tracks']
        assert type(tracks) is GeometryCollection
        assert len(tracks[0]) == 2

    def test_tracks_and_routes(self):
        file_path = path + '/resources/tests/files/routes_tracks.gpx'
        g = GPXProcessor(file_path)
        layers = g.get_layers()
        assert len(layers.keys()) == 2
