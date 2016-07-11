from django.test import TestCase
from django.core.urlresolvers import reverse, resolve

from ..views import api


class XFormsUrlTest(TestCase):
    def test_xforms_list(self):
        assert reverse('form-list') == '/collect/formList/'

        resolved = resolve('/collect/')
        assert resolved.func.__name__ == api.XFormListView.__name__

    def test_xforms_submission(self):
        assert reverse('submissions') == '/collect/submission'

        resolved = resolve('/collect/submission')
        assert resolved.func.__name__ == api.XFormSubmissionViewSet.__name__
