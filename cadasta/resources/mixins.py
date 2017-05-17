import os
import magic
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import pre_delete
from .utils import io, thumbnail


class ResourceModelMixin:
    @property
    def resources(self):
        if not hasattr(self, '_resources'):
            ContentObject = apps.get_model('resources', 'ContentObject')
            Resource = apps.get_model('resources', 'Resource')

            model_type = ContentType.objects.get_for_model(self)

            cnt_objs = ContentObject.objects.filter(
                content_type__pk=model_type.id,
                object_id=self.id
            )
            self._resources = Resource.objects.filter(
                content_objects__in=cnt_objs)
        return self._resources

    def reload_resources(self):
        if hasattr(self, '_resources'):
            del self._resources


@receiver(pre_delete)
def detach_object_resources(sender, instance, **kwargs):
    list_of_models = ('Party', 'TenureRelationship', 'SpatialUnit')
    sender = sender.__base__ if hasattr(sender, '_deferred') else sender

    if sender.__name__ in list_of_models:
        for resource in instance.resources:
            content_object = resource.content_objects.get(
                object_id=instance.id,
                resource__project__slug=instance.project.slug)
            content_object.delete()


class ResourceThumbnailMixin:

    @property
    def file_name(self):
        if not hasattr(self, '_file_name'):
            self._file_name = self.file.url.split('/')[-1]

        return self._file_name

    @property
    def file_type(self):
        return self.file_name.split('.')[-1]

    @property
    def thumbnail(self):
        if self.file.url:
            if not hasattr(self, '_thumbnail'):
                mime_type = self._get_mime()
                icon = settings.ICON_LOOKUPS.get(mime_type, None)
                if 'image' in mime_type and 'tif' not in mime_type:
                    ext = self.file_name.split('.')[-1]
                    base_url = self.file.url[:self.file.url.rfind('.')]
                    self._thumbnail = base_url + '-128x128.' + ext
                elif icon:
                    self._thumbnail = settings.ICON_URL.format(icon)
                else:
                    self._thumbnail = ''

            return self._thumbnail

    def create_thumbnails(self, created):
        if self.file.url:
            if created or self._original_url != self.file.url:
                mime_type = self._get_mime()
                if 'image' in mime_type:
                    io.ensure_dirs()
                    file_name = self.file.url.split('/')[-1]
                    name = file_name[:file_name.rfind('.')]
                    ext = file_name.split('.')[-1]
                    write_path = os.path.join(settings.MEDIA_ROOT,
                                              'temp',
                                              name + '-128x128.' + ext)

                    size = 128, 128

                    file = self.file.open()
                    thumb = thumbnail.make(file, size)
                    thumb.save(write_path)
                    if self.file.field.upload_to:
                        name = self.file.field.upload_to + '/' + name
                    self.file.storage.save(
                        name + '-128x128.' + ext,
                        open(write_path, 'rb').read())

    def _get_mime(self):
        if(hasattr(self, 'mime_type')):
            mime_type = self.mime_type
        else:
            data = self.file.open().read(512)
            mime = magic.Magic(mime=True)
            mime_type = mime.from_buffer(data).decode()
        return mime_type
