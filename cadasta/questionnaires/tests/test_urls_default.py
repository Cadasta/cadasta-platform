from django.test import TestCase
from django.core.urlresolvers import reverse, resolve

from ..views import default


class PDFFormUrlTest(TestCase):
    def test_pdfform_list(self):
        url = reverse('questionnaires:pdf_form_list',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug'})
        assert (url ==
                '/organizations/org-slug/projects/proj-slug/'
                'questionnaire/forms/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/questionnaire/forms/')
        assert resolved.func.__name__ == default.PDFFormList.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'

    def test_pdfform_add(self):
        url = reverse('questionnaires:pdf_form_add',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug'})
        assert (url ==
                '/organizations/org-slug/projects/proj-slug/'
                'questionnaire/forms/new/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/'
            'questionnaire/forms/new/')
        assert resolved.func.__name__ == default.PDFFormAdd.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'

    def test_pdfform_view(self):
        url = reverse('questionnaires:pdf_form_view',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'form': 'abc123'})
        assert (url ==
                '/organizations/org-slug/projects/proj-slug/'
                'questionnaire/forms/abc123/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/'
            'questionnaire/forms/abc123/')
        name = default.PDFFormDetails.__name__
        assert name == resolved.func.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['form'] == 'abc123'

    def test_pdfform_edit(self):
        url = reverse('questionnaires:pdf_form_edit',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'form': 'abc123'})
        assert (url == '/organizations/org-slug/projects/proj-slug/'
                       'questionnaire/forms/abc123/edit/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/'
            'questionnaire/forms/abc123/edit/')
        name = default.PDFFormEdit.__name__
        assert name == resolved.func.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['form'] == 'abc123'

    def test_pdfform_delete(self):
        url = reverse('questionnaires:pdf_form_delete',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'form': 'abc123'})
        assert (url == '/organizations/org-slug/projects/proj-slug/'
                       'questionnaire/forms/abc123/delete/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/'
            'questionnaire/forms/abc123/delete/')
        name = default.PDFFormDelete.__name__
        assert name == resolved.func.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['form'] == 'abc123'

    def test_pdfform_download(self):
        url = reverse('questionnaires:pdf_form_download',
                      kwargs={'organization': 'org-slug',
                              'project': 'proj-slug',
                              'form': 'abc123'})
        assert (url == '/organizations/org-slug/projects/proj-slug/'
                       'questionnaire/forms/abc123/download/')

        resolved = resolve(
            '/organizations/org-slug/projects/proj-slug/'
            'questionnaire/forms/abc123/download/')
        name = default.PDFFormDownload.__name__
        assert name == resolved.func.__name__
        assert resolved.kwargs['organization'] == 'org-slug'
        assert resolved.kwargs['project'] == 'proj-slug'
        assert resolved.kwargs['form'] == 'abc123'
