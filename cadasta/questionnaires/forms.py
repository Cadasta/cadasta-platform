from django import forms
from .models import PDFForm


class PDFFormCreateForm(forms.ModelForm):
    class Media:
        js = ('js/file-upload.js',)

    class Meta:
        model = PDFForm
        fields = ['file', 'name', 'description', 'instructions']

    def __init__(self, data=None, contributor=None,
                 project_id=None, questionnaire=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        self.contributor = contributor
        self.project_id = project_id
        self.questionnaire = questionnaire

    def save(self, *args, **kwargs):
        pdfform = super().save(commit=False, *args, **kwargs)

        if not self.instance.id:
            pdfform.contributor = self.contributor
            pdfform.questionnaire = self.questionnaire
            pdfform.project_id = self.project_id

        pdfform.save()
        return self.instance
