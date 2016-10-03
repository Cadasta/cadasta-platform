from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from jsonattrs.models import Schema

ATTRIBUTE_GROUPS = settings.ATTRIBUTE_GROUPS

EXCLUDE_HEADERS = [
    'deviceid', 'sim_serial', 'start', 'end', 'today',
    'meta/instanceid', 'subscriberid'
]


class Importer():

    def __init__(self, project):
        self.project = project
        self._schema_attrs = {}

    def get_content_type_keys(self):
        content_type_keys = []
        for attribute_group in ATTRIBUTE_GROUPS:
            app_label = ATTRIBUTE_GROUPS[attribute_group]['app_label']
            model = ATTRIBUTE_GROUPS[attribute_group]['model']
            content_type_key = '{}.{}'.format(app_label, model)
            content_type_keys.append(content_type_key)
        return content_type_keys

    def get_schema_attrs(self):
        for attribute_group in ATTRIBUTE_GROUPS:
            app_label = ATTRIBUTE_GROUPS[attribute_group]['app_label']
            model = ATTRIBUTE_GROUPS[attribute_group]['model']
            content_type_key = '{}.{}'.format(app_label, model)
            content_type = ContentType.objects.get(
                app_label=app_label, model=model)

            if content_type_key not in self._schema_attrs.keys():
                selectors = [
                    self.project.organization.id,
                    self.project.id,
                    self.project.current_questionnaire
                ]
                schemas = Schema.objects.lookup(
                    content_type=content_type, selectors=selectors
                )
                attrs = []
                if schemas:
                    attrs = [
                        a for s in schemas
                        for a in s.attributes.all() if not a.omit
                    ]
                self._schema_attrs[content_type_key] = attrs

        return self._schema_attrs

    def import_data(self, config_dict, **kwargs):
        raise NotImplementedError(
            "Your %s class has not defined an import_data() method."
            % self.__class__.__name__
        )
