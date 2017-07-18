import pickle

from django.db import models


class PickledObjectField(models.BinaryField):
    """
    A simplified version of the more popular PickleField designed to work
    with binary-encoded data.
    https://github.com/gintas/django-picklefield
    """

    def to_python(self, value):
        if value is None:
            return
        return pickle.loads(value.tobytes())

    def from_db_value(self, value, expression, connection, context):
        return self.to_python(value)

    def get_db_prep_value(self, value, connection=None, prepared=False):
        value = pickle.dumps(value)
        return super().get_db_prep_value(value, connection, prepared)

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return self.get_db_prep_value(value)

    def get_lookup(self, lookup_name):
        """
        We need to limit the lookup types.
        """
        if lookup_name not in ['exact', 'in', 'isnull']:
            raise TypeError('Lookup type %s is not supported.' % lookup_name)
        return super(PickledObjectField, self).get_lookup(lookup_name)
