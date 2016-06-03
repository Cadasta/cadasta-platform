import magic
from django.db import models, transaction
from django.apps import apps


class ResourceManager(models.Manager):
    def create(self, content_object=None, *args, **kwargs):
        with transaction.atomic():
            resource = self.model(**kwargs)
            file = resource.file.open().name

            resource.mime_type = magic.from_file(file, mime=True).decode()
            resource.save()

            if content_object:
                ContentObject = apps.get_model('resources', 'ContentObject')
                ContentObject.objects.create(
                    resource=resource,
                    content_object=content_object
                )

            return resource
