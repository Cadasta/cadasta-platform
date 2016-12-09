from collections import OrderedDict

from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from jsonattrs.models import Schema, compose_schemas
from tutelary import mixins


class PermissionRequiredMixin(mixins.PermissionRequiredMixin):

    def handle_no_permission(self):
        msg = super().handle_no_permission()
        messages.add_message(self.request, messages.WARNING,
                             msg[0] if len(msg) > 0 and len(msg[0]) > 0
                             else _("You don't have permission "
                                    "for this action."))

        referer = self.request.META.get('HTTP_REFERER')
        redirect_url = self.request.META.get('HTTP_REFERER', '/')

        if (referer and '/account/login/' in referer and
                not self.request.user.is_anonymous()):

            if 'organization' in self.kwargs and 'project' in self.kwargs:
                redirect_url = reverse(
                    'organization:project-dashboard',
                    kwargs={'organization': self.kwargs['organization'],
                            'project': self.kwargs['project']}
                )
                if redirect_url == self.request.get_full_path():
                    redirect_url = reverse(
                        'organization:dashboard',
                        kwargs={'slug': self.kwargs['organization']}
                    )

            elif 'slug' in self.kwargs:
                redirect_url = reverse(
                    'organization:dashboard',
                    kwargs={'slug': self.kwargs['slug']}
                )
                if redirect_url == self.request.get_full_path():
                    redirect_url = reverse('core:dashboard')

        return redirect(redirect_url)


class LoginPermissionRequiredMixin(PermissionRequiredMixin,
                                   mixins.LoginPermissionRequiredMixin):
    pass


def update_permissions(permission, obj=None):
    def set_permissions(self, request, view=None):
        if (hasattr(self, 'get_organization') and
                self.get_organization().archived):
            return False
        if (hasattr(self, 'get_project') and self.get_project().archived):
            return False
        if obj and self.get_object().archived:
            return False
        return permission
    return set_permissions


class SchemaSelectorMixin():

    def get_attributes(self, project):
        content_type_to_selectors = self._get_content_types_to_selectors()
        attributes_for_models = {}
        for content_type, selector_fields in content_type_to_selectors.items():
            label = '{}.{}'.format(content_type.app_label, content_type.model)
            model = content_type.model_class()
            choices = []
            selectors = OrderedDict({})
            attributes_for_models[label] = OrderedDict({})

            for selector_field in selector_fields:
                field = model._meta.get_field(selector_field.partition('.')[0])
                if field.choices:
                    choices = [choice[0] for choice in field.choices]
                else:
                    selector = project
                    sf = selector_field.partition('.')[-1]
                    sf = sf.replace('.pk', '_id')
                    selector = getattr(selector, sf, None)
                    if selector:
                        selectors[sf] = selector

            if selectors and not choices:
                defaults = list(selectors.values())
                schemas = Schema.objects.lookup(
                    content_type=content_type, selectors=defaults)
                if schemas:
                    attributes, _, _ = compose_schemas(*schemas)
                    attributes_for_models[label]['DEFAULT'] = attributes

            if selectors and choices:
                for choice in choices:
                    conditionals = list(selectors.values()) + [choice]
                    schemas = Schema.objects.lookup(
                        content_type=content_type,
                        selectors=conditionals)
                    if schemas:
                        attributes, _, _ = compose_schemas(*schemas)
                        attributes_for_models[label][choice] = attributes

        return attributes_for_models

    def get_model_attributes(self, project, content_type):
        attributes_for_models = self.get_attributes(project)
        return attributes_for_models[content_type]

    def get_conditional_selector(self, content_type):
        content_type_to_selectors = self._get_content_types_to_selectors()
        selectors = list(content_type_to_selectors[content_type])
        if '.' in selectors[-1]:
            return None
        else:
            return selectors[-1]

    def _get_content_types_to_selectors(self):
        content_type_to_selectors = dict()
        for k, v in settings.JSONATTRS_SCHEMA_SELECTORS.items():
            a, m = k.split('.')
            content_type_to_selectors[
                ContentType.objects.get(app_label=a, model=m)
            ] = v
        return content_type_to_selectors
