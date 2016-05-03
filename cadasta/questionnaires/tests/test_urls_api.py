from django.test import TestCase
from django.core.urlresolvers import reverse, resolve
from core.tests.url_utils import version_ns, version_url

from ..views import api


class QuestionnaireUrlTest(TestCase):
    def test_questionnaire(self):
        assert (reverse(version_ns('questionnaires:detail'),
                        kwargs={'organization': 'org', 'project_id': 'prj'}) ==
                version_url('/organizations/org/projects/prj/questionnaire/'))

        resolved = resolve(
            version_url('/organizations/org/projects/prj/questionnaire/'))
        assert resolved.func.__name__ == api.QuestionnaireDetail.__name__
        assert resolved.kwargs['organization'] == 'org'
        assert resolved.kwargs['project_id'] == 'prj'
