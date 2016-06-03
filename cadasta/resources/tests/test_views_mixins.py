import pytest
from django.test import TestCase
from django.views.generic import TemplateView
from ..views.mixins import ResourceViewMixin


class ResourceView(ResourceViewMixin, TemplateView):
    pass


class ResourceViewMixinTest(TestCase):
    def test_get_content_object(self):
        view = ResourceView()
        with pytest.raises(NotImplementedError):
            view.get_content_object()
