from core.views import generic
from questionnaires.models import PDFForm
from organization.views import mixins as organization_mixins
from . import mixins
from .. import messages as error_messages
from core.mixins import LoginPermissionRequiredMixin
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from ..download.generator import PDFGenerator


class PDFFormList(LoginPermissionRequiredMixin,
                  organization_mixins.ProjectAdminCheckMixin,
                  mixins.ProjectQuestionnairePDFFormMixin,
                  generic.ListView):
    template_name = 'questionnaires/form_list.html'
    permission_required = 'pdfform.list'
    permission_denied_message = error_messages.QUESTIONNAIRE_PDF_FORM_VIEW
    model = PDFForm

    def get_perms_objects(self):
        return [self.get_project()]

    def get_queryset(self):
        self.proj = self.get_project()
        pdfforms = self.proj.pdfforms.all()
        return pdfforms


class PDFFormAdd(LoginPermissionRequiredMixin,
                 organization_mixins.ProjectAdminCheckMixin,
                 mixins.ProjectPDFFormMixin, generic.CreateView):
    template_name = 'questionnaires/form_add_new.html'
    permission_required = 'pdfform.add'
    permission_denied_message = error_messages.QUESTIONNAIRE_PDF_FORM_ADD
    model = PDFForm

    def get_perms_objects(self):
        return [self.get_project()]


class PDFFormDelete(LoginPermissionRequiredMixin,
                    mixins.PDFFormObjectMixin,
                    generic.DeleteView):

    template_name = 'questionnaires/modal_delete.html'
    permission_required = 'pdfform.delete'
    permission_denied_message = error_messages.QUESTIONNAIRE_PDF_FORM_DELETE

    def get_success_url(self):
        kwargs = self.kwargs
        del kwargs['form']
        return reverse('questionnaires:pdf_form_list', kwargs=self.kwargs)


class PDFFormDetails(LoginPermissionRequiredMixin,
                     mixins.PDFFormObjectMixin,
                     organization_mixins.ProjectAdminCheckMixin,
                     generic.DetailView):
    template_name = 'questionnaires/form_detail.html'
    permission_required = 'pdfform.view'
    permission_denied_message = error_messages.QUESTIONNAIRE_PDF_FORM_VIEW
    model = PDFForm


class PDFFormEdit(LoginPermissionRequiredMixin,
                  mixins.PDFFormObjectMixin,
                  organization_mixins.ProjectAdminCheckMixin,
                  generic.UpdateView):
    template_name = 'questionnaires/form_edit.html'
    permission_required = 'pdfform.edit'
    permission_denied_message = error_messages.QUESTIONNAIRE_PDF_FORM_EDIT
    model = PDFForm


class PDFFormDownload(LoginPermissionRequiredMixin, mixins.PDFFormObjectMixin,
                      organization_mixins.ProjectAdminCheckMixin,
                      generic.DetailView):
    permission_required = 'pdfform.download'
    permission_denied_message = error_messages.QUESTIONNAIRE_PDF_FORM_GENERATE
    template_name = 'questionnaires/pdf_form_generator.html'

    def get(self, request, *args, **kwargs):
        pdfform = self.get_object()
        absolute_uri = request.build_absolute_uri()
        pdf_generator = PDFGenerator(self.get_project(), pdfform)
        pdf = pdf_generator.generate_pdf(absolute_uri)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = ('attachment; '
                                           'filename='+pdfform.name+'.pdf')
        return response
