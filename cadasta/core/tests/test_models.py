from django.test import TestCase
from ..models import RandomIDModel


class MyTestModel(RandomIDModel):
    class Meta:
        app_label = 'core'


class RandomIDModelTest(TestCase):
    abstract_model = RandomIDModel

    def test_save(self):
        instance = MyTestModel()
        instance.save()
        self.assertIsNotNone(instance.id)
