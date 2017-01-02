from organization.views.mixins import ProjectMixin
from django.core.urlresolvers import reverse
from ..forms import PDFFormCreateForm
from django.http import Http404
from ..models import PDFForm, Questionnaire


class ProjectQuestionnairePDFFormMixin(ProjectMixin):

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['object'] = self.get_project()
        return context


class PDFFormViewMixin:
    form_class = PDFFormCreateForm

    def get_model_context(self):
        project = self.get_project()
        questionnaire = None
        try:
            questionnaire = Questionnaire.objects.get(
                id=project.current_questionnaire)
        except Questionnaire.DoesNotExist:
            pass

        return {
            'contributor': self.request.user,
            'questionnaire': questionnaire
        }

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs.update(self.get_model_context())
        return form_kwargs


class ProjectPDFFormMixin(ProjectMixin, PDFFormViewMixin):

    def get_model_context(self):
        context = super().get_model_context()
        context['project_id'] = self.get_project().id
        return context

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        project = self.get_project()
        context['object'] = project
        try:
            questionnaire = Questionnaire.objects.get(
                        id=project.current_questionnaire)
            context['questionnaire'] = questionnaire
            context['has_questionnaire'] = True
        except Questionnaire.DoesNotExist:
            context['has_questionnaire'] = False

        return context

    def get_success_url(self):
        return reverse('questionnaires:pdf_form_list', kwargs=self.kwargs)


class PDFFormObjectMixin(ProjectPDFFormMixin):

    def get_object(self):
        try:
            pdfform = PDFForm.objects.get(
                project__organization__slug=self.kwargs['organization'],
                project__slug=self.kwargs['project'],
                id=self.kwargs['form']
            )
        except PDFForm.DoesNotExist as e:
            raise Http404(e)

        self.pdfform = pdfform
        return pdfform

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        pdfform = self.get_object()
        user = self.request.user
        context['pdfform'] = pdfform
        context['can_delete'] = user.has_perm('pdfform.delete', pdfform)
        context['can_edit'] = user.has_perm('pdfform.edit', pdfform)
        context['can_generate'] = user.has_perm('pdfform.generate', pdfform)
        return context

    def get_success_url(self):
        return reverse('questionnaires:pdf_form_view', kwargs=self.kwargs)
