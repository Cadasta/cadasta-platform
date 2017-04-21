
from django.test import TestCase
from rest_framework import serializers
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from rest_framework.settings import api_settings
from unittest.mock import patch, MagicMock

from ..util import paginate_results, get_next_link, get_previous_link


class PaginationTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def _get_request(self, *args, **kwargs):
        req = self.factory.get(*args, **kwargs)
        return APIView().initialize_request(req)

    @patch('core.util.get_next_link', MagicMock(return_value='http://nxt'))
    @patch('core.util.get_previous_link', MagicMock(return_value='http://prv'))
    def test_pagination(self):
        req = self._get_request('/foo', {'limit': 10, 'offset': 20})
        qs = [{'id': i} for i in range(50)]

        class FakeSerializer(serializers.Serializer):
            id = serializers.IntegerField()

        assert paginate_results(req, (qs, FakeSerializer)) == {
            'count': 50,
            'next': 'http://nxt',
            'previous': 'http://prv',
            'results': [{'id': 20+i} for i in range(10)]
        }

    @patch('core.util.get_next_link', MagicMock(return_value='http://nxt'))
    @patch('core.util.get_previous_link', MagicMock(return_value='http://prv'))
    def test_pagination_multiple_datatypes(self):
        req = self._get_request('/foo', {'limit': 10, 'offset': 20})
        qs1 = [{'id': i} for i in range(25)]
        qs2 = [{'name': i} for i in range(25)]

        class FakeSerializer1(serializers.Serializer):
            id = serializers.IntegerField()

        class FakeSerializer2(serializers.Serializer):
            name = serializers.IntegerField()

        resp = paginate_results(
            req, (qs1, FakeSerializer1), (qs2, FakeSerializer2))
        assert resp == {
            'count': 50,
            'next': 'http://nxt',
            'previous': 'http://prv',
            'results': (
                [{'id': 20+i} for i in range(5)] +
                [{'name': i} for i in range(5)]
            )
        }

    def test_next_link(self):
        req = self._get_request('/foo')
        assert (
            get_next_link(req, 200) ==
            'http://testserver/foo?limit={}&offset=100'.format(
                api_settings.PAGE_SIZE))

    def test_no_next_link(self):
        req = self._get_request('/foo', {'offset': 100})
        assert get_next_link(req, 200) is None

    def test_previous_link(self):
        req = self._get_request('/foo', {'offset': 200})
        resp = get_previous_link(req)
        assert (
            resp == 'http://testserver/foo?limit={}&offset=100'.format(
                api_settings.PAGE_SIZE))

        req = self._get_request('/foo', {'offset': api_settings.PAGE_SIZE})
        resp = get_previous_link(req)
        assert (
            resp == 'http://testserver/foo?limit={}'.format(
                api_settings.PAGE_SIZE))

    def test_no_previous_link(self):
        req = self._get_request('/foo')
        assert get_previous_link(req) is None
