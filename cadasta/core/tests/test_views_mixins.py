import pytest
from django.test import TestCase
from ..views.mixins import AsyncList


class TestView(AsyncList):
    pass


class AsyncListTest(TestCase):
    def test_build_search_query(self):
        view = TestView()
        with pytest.raises(NotImplementedError):
            view.build_search_query('term')

    def test_get_results(self):
        view = TestView()
        with pytest.raises(AssertionError):
            view.get_results()
