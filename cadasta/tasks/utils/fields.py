import functools

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


def validate_type(_type, val):
    """
    Throw ValidationError if the provided value is not of the provided type.
    """
    if not isinstance(val, _type):
        msg = _(
            'This field must be of type %(valid_type)r, got type %(type)r')
        raise ValidationError(
            msg, params={
                'type': type(val).__name__, 'valid_type': _type.__name__
            },
        )


def is_type(_type):
    """
    Given a type, returns a function that will validate that provided
    arguments are of that type.
    """
    assert type(_type) == type, (
        "Expects a 'type', got {!r}".format(type(_type).__name__))
    return functools.partial(validate_type, _type)


def input_field_default():
    """ Return default value for BackgroundTask.input field """
    return {'args': [], 'kwargs': {}}


def validate_input_field(val):
    """ Ensure 'input' field """
    if not isinstance(val, dict):
        raise ValidationError(
            _('This field must be of type \'dict\', got type %(type)r'),
            params={'type': type(val).__name__},
        )
    def_keys = input_field_default().keys()
    if not val.keys() == def_keys:
        raise ValidationError(
            _('%(val)s does not have correct keys, expected: %(keys)s'),
            params={'val': val, 'keys': ', '.join(repr(k) for k in def_keys)},
        )
    if not isinstance(val['args'], (list, tuple)):
        raise ValidationError(
            _('"args" value should be type \'list/tuple\', got %(type)r'),
            params={'type': type(val['args']).__name__},
        )
    if not isinstance(val['kwargs'], dict):
        raise ValidationError(
            _('"kwargs" value should be type \'dict\', got %(type)r'),
            params={'type': type(val['kwargs']).__name__},
        )
