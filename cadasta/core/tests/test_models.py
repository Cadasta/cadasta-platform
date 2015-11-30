from .testcases import AbstractModelTestCase
from ..models import RandomIDModel


class RandomIDModelTest(AbstractModelTestCase):
    abstract_model = RandomIDModel

    def test_save(self):
        instance = self.model()
        instance.save()
        self.assertIsNotNone(instance.id)
