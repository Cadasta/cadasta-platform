import os
from datetime import datetime

import magic
from buckets.fields import S3FileField
from core.models import ID_FIELD_LENGTH, RandomIDModel
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db.models import GeometryCollectionField
from django.contrib.gis.gdal.error import GDALException
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext as _
from django.utils.encoding import iri_to_uri
from jsonattrs.fields import JSONAttributeField
from simple_history.models import HistoricalRecords
from tutelary.decorators import permissioned_model

from . import messages
from .exceptions import InvalidGPXFile
from .managers import ResourceManager
from .processors.gpx import GPXProcessor
from .utils import io, thumbnail
from .validators import ACCEPTED_TYPES, validate_file_type

content_types = models.Q(app_label='organization', model='project')

GPX_MIME_TYPES = ('application/xml', 'text/xml', 'application/gpx+xml')


@permissioned_model
class Resource(RandomIDModel):
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    file = S3FileField(upload_to='resources', accepted_types=ACCEPTED_TYPES)
    original_file = models.CharField(max_length=200)
    file_versions = JSONField(null=True, blank=True)
    mime_type = models.CharField(max_length=100,
                                 validators=[validate_file_type])
    archived = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)
    contributor = models.ForeignKey('accounts.User')
    project = models.ForeignKey('organization.Project')

    objects = ResourceManager()

    history = HistoricalRecords()

    class Meta:
        ordering = ('name',)

    class TutelaryMeta:
        perm_type = 'resource'
        path_fields = ('project', 'pk')
        actions = (
            ('resource.list',
             {'description': _("List resources"),
              'permissions_object': 'project',
              'error_message': messages.RESOURCE_LIST}),
            ('resource.add',
             {'description': _("Add resources"),
              'permissions_object': 'project',
              'error_message': messages.RESOURCE_ADD}),
            ('resource.view',
             {'description': _("View resource"),
              'error_message': messages.RESOURCE_VIEW}),
            ('resource.edit',
             {'description': _("Edit resource"),
              'error_message': messages.RESOURCE_EDIT}),
            ('resource.archive',
             {'description': _("Archive resource"),
              'error_message': messages.RESOURCE_ARCHIVE}),
            ('resource.unarchive',
             {'description': _("Unarchive resource"),
              'error_message': messages.RESOURCE_UNARCHIVE}),
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_url = self.file.url

    def __repr__(self):
        repr_string = ('<Resource id={obj.id} name={obj.name}'
                       ' file={obj.file.url} project={obj.project.slug}>')
        return repr_string.format(obj=self)

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
        if not hasattr(self, '_thumbnail'):
            icon = settings.ICON_LOOKUPS.get(self.mime_type, None)
            if 'image' in self.mime_type and 'tif' not in self.mime_type:
                ext = self.file_name.split('.')[-1]
                base_url = self.file.url[:self.file.url.rfind('.')]
                self._thumbnail = base_url + '-128x128.' + ext
            elif icon:
                self._thumbnail = settings.ICON_URL.format(icon)
            else:
                self._thumbnail = ''

        return self._thumbnail

    @property
    def num_entities(self):
        if not hasattr(self, '_num_entities'):
            self._num_entities = ContentObject.objects.filter(
                resource=self).count()
        return self._num_entities

    def save(self, *args, **kwargs):
        create_thumbnails(self, (not self.id))
        super().save(*args, **kwargs)

    @property
    def ui_class_name(self):
        return _("Resource")

    def get_absolute_url(self):
        return iri_to_uri(reverse(
            'resources:project_detail',
            kwargs={
                'organization': self.project.organization.slug,
                'project': self.project.slug,
                'resource': self.id,
            },
        ))


@receiver(models.signals.pre_save, sender=Resource)
def archive_file(sender, instance, **kwargs):
    if instance._original_url and instance._original_url != instance.file.url:
        now = str(datetime.now())
        if not instance.file_versions:
            instance.file_versions = {}
        instance.file_versions[now] = instance._original_url
    instance._original_url = instance.file.url

    # Detach the resource when it is archived
    if instance.archived:
        ContentObject.objects.filter(resource=instance).delete()


def create_thumbnails(instance, created):
    if created or instance._original_url != instance.file.url:
        if 'image' in instance.mime_type:
            io.ensure_dirs()
            file_name = instance.file.url.split('/')[-1]
            name = file_name[:file_name.rfind('.')]
            ext = file_name.split('.')[-1]
            write_path = os.path.join(settings.MEDIA_ROOT,
                                      'temp',
                                      name + '-128x128.' + ext)

            size = 128, 128

            file = instance.file.open()
            thumb = thumbnail.make(file, size)
            thumb.save(write_path)
            if instance.file.field.upload_to:
                name = instance.file.field.upload_to + '/' + name
            instance.file.storage.save(name + '-128x128.' + ext,
                                       open(write_path, 'rb').read())


@receiver(models.signals.post_save, sender=Resource)
def create_spatial_resource(sender, instance, created, **kwargs):
    if created or instance._original_url != instance.file.url:
        if instance.mime_type in GPX_MIME_TYPES:
            io.ensure_dirs()
            file_name = instance.file.url.split('/')[-1]
            write_path = os.path.join(settings.MEDIA_ROOT,
                                      'temp', file_name)
            file = instance.file.open().read()
            with open(write_path, 'wb') as f:
                f.write(file)
            # need to double check the mime-type here as browser detection
            # of gpx mime type is not reliable
            mime = magic.Magic(mime=True)
            mime_type = str(mime.from_file(write_path), 'utf-8')

            if mime_type in GPX_MIME_TYPES:
                try:
                    processor = GPXProcessor(write_path)
                    layers = processor.get_layers()
                except GDALException:
                    raise InvalidGPXFile(
                        _('Invalid GPX file')
                    )
                for layer in layers.keys():
                    if len(layers[layer]) > 0:
                        SpatialResource.objects.create(
                            resource=instance, name=layer, geom=layers[layer])
            else:
                os.remove(write_path)
                raise InvalidGPXFile(
                    _('Invalid GPX mime type: {error}'.format(
                        error=mime_type))
                )


class ContentObject(RandomIDModel):
    resource = models.ForeignKey(Resource, related_name='content_objects')

    content_type = models.ForeignKey(ContentType,
                                     on_delete=models.CASCADE,
                                     null=True,
                                     blank=True,
                                     limit_choices_to=content_types)
    object_id = models.CharField(max_length=ID_FIELD_LENGTH,
                                 null=True,
                                 blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    history = HistoricalRecords()


@permissioned_model
class SpatialResource(RandomIDModel):

    class Meta:
        ordering = ('name',)

    class TutelaryMeta:
        perm_type = 'resource'
        path_fields = ('resource', 'pk')
        actions = (
            ('resource.list',
             {'description': _("List resources"),
              'permissions_object': 'resource',
              'error_message': messages.RESOURCE_LIST}),
            ('resource.view',
             {'description': _("View resource"),
              'error_message': messages.RESOURCE_VIEW}),
            ('resource.archive',
             {'description': _("Archive resource"),
              'error_message': messages.RESOURCE_ARCHIVE}),
            ('resource.unarchive',
             {'description': _("Unarchive resource"),
              'error_message': messages.RESOURCE_UNARCHIVE}),
        )

    name = models.CharField(max_length=256, null=True, blank=True)

    time = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE, related_name='spatial_resources'
    )
    geom = GeometryCollectionField(
        srid=4326, blank=True, null=True
    )
    attributes = JSONAttributeField(default={})

    def __repr__(self):
        repr_string = ('<SpatialResource id={obj.id}'
                       ' resource={obj.resource.id}>')
        return repr_string.format(obj=self)

    @property
    def archived(self):
        return self.resource.archived

    @property
    def project(self):
        return self.resource.project
