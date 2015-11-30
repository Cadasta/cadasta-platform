from django.test import TestCase
from django.db import connection
from django.core.management.color import no_style
from django.db.models.base import ModelBase


class AbstractModelTestCase(TestCase):
    def setUp(self):
        # Create a dummy model which extends the abstract model
        self.model = ModelBase(
            '__TestModel__' + self.abstract_model.__name__,
            (self.abstract_model,),
            {'__module__': self.abstract_model.__module__}
        )

        # Create the schema for our test model
        self._style = no_style()
        sql, _ = connection.creation.sql_create_model(self.model, self._style)

        self._cursor = connection.cursor()
        for statement in sql:
            self._cursor.execute(statement)

    def tearDown(self):
        # Delete the schema for the test model
        sql = connection.creation.sql_destroy_model(
            self.model, (), self._style
        )
        for statement in sql:
            self._cursor.execute(statement)
