from django.test import TestCase
from django.core.urlresolvers import reverse, resolve

from .. import views


class CoreUrlTest(TestCase):
    def test_index_page(self):
        assert reverse('core:index') == '/'

        resolved = resolve('/')
        assert resolved.func.__name__ == views.IndexPage.__name__

    def test_dashboard(self):
        assert reverse('core:dashboard') == '/dashboard/'

        resolved = resolve('/dashboard/')
        assert resolved.func.__name__ == views.Dashboard.__name__
