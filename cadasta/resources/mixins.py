from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from django.dispatch import receiver
from django.db.models.signals import pre_delete


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
