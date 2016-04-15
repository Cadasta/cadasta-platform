import random
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
        assert instance.id is not None

    def test_duplicate_ids(self):
        random.seed(a=10)
        instance1 = MyTestModel()
        instance1.save()
        random.seed(a=10)
        instance2 = MyTestModel()
        instance2.save()
        assert instance1.id != instance2.id
