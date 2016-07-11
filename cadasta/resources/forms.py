from django import forms
from django.contrib.contenttypes.models import ContentType
from buckets.widgets import S3FileUploadWidget
from .models import Resource, ContentObject
from .fields import ResourceField
from .validators import ACCEPTED_TYPES


class ResourceForm(forms.ModelForm):
    file = forms.CharField(
        widget=S3FileUploadWidget(upload_to='resources',
                                  accepted_types=ACCEPTED_TYPES))

    class Meta:
        model = Resource
        fields = ['file', 'original_file', 'name', 'description']

    def __init__(self, data=None, content_object=None, contributor=None,
                 project_id=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        self.cnt_obj = content_object
        self.contributor = contributor
        self.project_id = project_id

    def clean(self):
        pass

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
        self.project_resources = Resource.objects.filter(project_id=project_id)

        for resource in self.project_resources:
            self.fields[resource.id] = ResourceField(
                label=resource.name,
                initial=(resource in content_object.resources),
                resource=resource
            )

    def save(self):
        model_type = ContentType.objects.get_for_model(self.content_object)
        object_resources = self.content_object.resources.values_list('id',
                                                                     flat=True)
        for key, value in self.cleaned_data.items():
            if value and key not in object_resources:
                ContentObject.objects.create(
                    resource_id=key,
                    content_object=self.content_object
                )
            elif not value and key in object_resources:
                ContentObject.objects.filter(
                    resource_id=key,
                    content_type__pk=model_type.id,
                    object_id=self.content_object.id
                ).delete()

        self.content_object.reload_resources()
