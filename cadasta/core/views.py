import json
import re
from django.http import Http404

from django.core.exceptions import ImproperlyConfigured
from django.utils import six
from django.utils.translation import ugettext_lazy as _

from rest_framework.exceptions import NotFound
from rest_framework.views import exception_handler as drf_exception_handler

from tutelary.engine import Object


def set_exception(exception):
    if (type(exception) is Http404):
        exception_msg = str(exception)
        try:
            model = re.search(
                'No (.+?) matches the given query.', exception_msg).group(1)
            exception = NotFound(_("{name} not found.").format(name=model))
        except AttributeError:
            pass
    return exception


def eval_json(response_data):
    """
    Evaluate stringified JSON objects, so we can return structure
    error responses
    """
    for key in response_data:
        errors = []
        if not isinstance(response_data[key], six.string_types):
            for e in response_data[key]:
                try:
                    errors.append(json.loads(e))
                except ValueError:
                    errors.append(e)
            response_data[key] = errors

    return response_data


def exception_handler(exception, context):
    """
    Overwriting Django Rest Frameworks exception handler to provide more
    meaniful exception messages for 404 errors.
    """
    exception = set_exception(exception)

    response = drf_exception_handler(exception, context)
    if response:
        response.data = eval_json(response.data)
        return response


class PermissionRequiredMixin:
    def get_permission_required(self):
        """
        Override this method to override the permission_required attribute.
        Must return an iterable.
        """
        if self.permission_required is None:
            raise ImproperlyConfigured(
                '{0} is missing the permission_required attribute. Define '
                '{0}.permission_required, or override '
                '{0}.get_permission_required().'.format(
                    self.__class__.__name__)
            )
        if isinstance(self.permission_required, dict):
            perms = self.permission_required[self.request.method]
        else:
            perms = self.permission_required

        if isinstance(perms, six.string_types):
            perms = (perms, )

        if hasattr(self, 'add_permission_required'):
            perms = perms + self.add_permission_required

        return perms

    def check_permissions(self, request):
        obj = None
        allowed = {}
        if hasattr(self, 'model') and hasattr(self.model, 'TutelaryMeta'):
            obj = Object(self.model.TutelaryMeta.perm_type)
            allowed = self.model.TutelaryMeta.allowed_methods
        try:
            if hasattr(self, 'get_object') and self.get_object() is not None:
                obj = self.get_object().get_permissions_object()
        except:
            pass
        perms = self.get_permission_required()

        has_perm = all(self.request.user.has_perm(p, obj) for p in perms
                       if not (p in allowed and
                               self.request.method in allowed[p]))

        if not has_perm:
            self.permission_denied(request, message="Permission denied.")
