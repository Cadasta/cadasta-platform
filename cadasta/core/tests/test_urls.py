from django.test import TestCase
from django.core.urlresolvers import reverse, resolve

from ..views import default


class CoreUrlTest(TestCase):
    def test_index_page(self):
        assert reverse('core:index') == '/'

        resolved = resolve('/')
        assert resolved.func.__name__ == default.IndexPage.__name__

    def test_dashboard(self):
        assert reverse('core:dashboard') == '/dashboard/'

        resolved = resolve('/dashboard/')
        assert resolved.func.__name__ == default.Dashboard.__name__
