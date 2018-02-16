import logging
import json
import re
from django.http import Http404
from django.utils import six
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework.exceptions import NotFound
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger('core')


def set_exception(exception, url):
    if isinstance(exception, Http404):
        exception_msg = str(exception)
        try:
            model = re.search(
                'No (.+?) matches the given query.', exception_msg).group(1)
            exception = NotFound(_("{name} not found.").format(name=model))
        except AttributeError:
            pass

    elif isinstance(exception, DjangoValidationError):
        if hasattr(exception, 'message_dict'):
            detail = exception.message_dict
        elif hasattr(exception, 'message'):
            detail = {'detail': exception.message}
        elif hasattr(exception, 'messages'):
            detail = {'detail': exception.messages}

        logger.exception(
            "ValidationError raised at {}: {}".format(url, exception))

        exception = DRFValidationError(detail=detail)

    return exception


def eval_json(response_data):
    """
    Evaluate stringified JSON objects, so we can return structured
    error responses
    """
    if not isinstance(response_data, dict):
        return response_data

    for key in response_data:
        errors = []
        if not isinstance(response_data[key], six.string_types):
            for e in response_data[key]:
                try:
                    errors.append(json.loads(e))
                except (ValueError, TypeError):
                    errors.append(e)
            response_data[key] = errors

    return response_data


def exception_handler(exception, context):
    """
    Overwriting Django Rest Frameworks exception handler to provide more
    meaningful exception messages for 404 and validation errors.
    """
    exception = set_exception(exception,
                              context['request'].build_absolute_uri())
    response = drf_exception_handler(exception, context)

    if response:
        response.data = eval_json(response.data)

        return response
