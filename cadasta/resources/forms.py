from django import forms
from core.form_mixins import SanitizeFieldsForm
from .models import Resource


class ResourceForm(SanitizeFieldsForm, forms.ModelForm):
    class Media:
        js = ('js/file-upload.js',  'js/sanitize.js', )

    class Meta:
        model = Resource
        fields = ['file', 'original_file', 'name', 'description', 'mime_type']

    def __init__(self, data=None, content_object=None, contributor=None,
                 project_id=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        self.cnt_obj = content_object
        self.contributor = contributor
        self.project_id = project_id

    def save(self, *args, **kwargs):
        if self.instance.id:
            self.instance.contributor = self.contributor
            super().save(*args, **kwargs)
        else:
            self.instance = Resource.objects.create(
                content_object=self.cnt_obj,
                contributor=self.contributor,
                project_id=self.project_id,
                **self.cleaned_data
            )
        return self.instance
