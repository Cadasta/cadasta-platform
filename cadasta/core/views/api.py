import json
import re
from django.http import Http404
from django.utils import six
from django.utils.translation import ugettext_lazy as _

from rest_framework.exceptions import NotFound
from rest_framework.views import exception_handler as drf_exception_handler


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
