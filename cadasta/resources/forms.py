from django import forms
from .models import Resource, ContentObject
from .fields import ResourceField


class ResourceForm(forms.ModelForm):
    class Media:
        js = ('js/file-upload.js',)

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


class AddResourceFromLibraryForm(forms.Form):
    def __init__(self, content_object, project_id, *args, **kwargs):
        kwargs.pop('contributor', None)
        super().__init__(*args, **kwargs)

        self.content_object = content_object
        self.project_resources = Resource.objects.filter(
            project_id=project_id, archived=False
        ).select_related('contributor')

        for resource in self.project_resources:
            if resource not in content_object.resources:
                self.fields[resource.id] = ResourceField(
                    label=resource.name,
                    initial=False,
                    resource=resource
                )

    def save(self):
        object_resources = self.content_object.resources.values_list('id',
                                                                     flat=True)
        for key, value in self.cleaned_data.items():
            if value and key not in object_resources:
                ContentObject.objects.create(
                    resource_id=key,
                    content_object=self.content_object
                )

        self.content_object.reload_resources()
